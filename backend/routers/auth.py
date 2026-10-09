from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Literal
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from database import get_db, get_write_db
from models import User, OperationLog, Role, Department, ScrapRequest, DeleteRequest, TransferRecord
from deps import require_super_admin, get_current_user, get_user_permissions, SECRET_KEY, ALGORITHM
import json

router = APIRouter(prefix="/api/auth", tags=["auth"])

from permissions import ALL_PERMISSIONS, PERMISSION_KEYS, GLOBAL_PERMISSIONS, PERMISSION_DEPENDENCIES

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    username: str
    password: str

def create_token(username: str, token_version: int, user_id: int):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire, "ver": token_version, "uid": user_id}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_write_db)):
    user = db.query(User).filter(User.username == req.username, User.is_active == 1).first()
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = create_token(user.username, user.token_version or 0, user.id)
    log = OperationLog(user=user.name, module="权限管理", action="登录", detail=f"{user.name} 登录系统")
    db.add(log)
    db.commit()
    return {"token": token, "user": user_view(user, db)}

def user_view(user, db):
    return {
        "id": user.id, "username": user.username, "name": user.name,
        "role": user.role, "role_id": user.role_id,
        "department": user.department, "department_id": user.department_id,
        "is_active": user.is_active, "data_scope": user.data_scope or "department",
        "permissions": get_user_permissions(user, db),
    }

@router.get("/me")
def me(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return user_view(user, db)

def validate_access(data):
    if data.role == 'super_admin':
        data.permissions = []  # Super-admin rights come from identity, never configurable grants.
    allowed = {key for key, label in ALL_PERMISSIONS}
    if data.permissions is not None and set(data.permissions) - allowed:
        raise HTTPException(400, "包含未知或保留的权限")
    if data.data_scope == 'department' and not data.department and data.role != 'super_admin':
        raise HTTPException(400, "仅本部门范围必须选择所属部门")
    if data.role != 'super_admin' and data.data_scope != 'all' and GLOBAL_PERMISSIONS.intersection(data.permissions or []):
        raise HTTPException(400, "部门管理、全局日志和微信管理权限需要全部部门数据范围")

    for permission, dependencies in PERMISSION_DEPENDENCIES.items():
        if permission in (data.permissions or []) and not dependencies.issubset(data.permissions):
            raise HTTPException(400, '微信密码权限必须同时配置微信管理权限')


class UserIn(BaseModel):
    username: str
    password: Optional[str] = None
    name: str
    role: str = "asset_admin"
    department: Optional[str] = None
    permissions: Optional[list[str]] = None
    data_scope: Literal["all", "department"] = "department"

@router.get("/users")
def list_users(db: Session = Depends(get_db), user = Depends(require_super_admin)):
    return [user_view(item, db) for item in db.query(User).all()]

@router.post("/users")
def create_user(data: UserIn, db: Session = Depends(get_write_db), current_user = Depends(require_super_admin)):
    validate_access(data)
    if not data.password or len(data.password) < 10:
        raise HTTPException(400, "新用户密码至少需要10个字符")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "用户名已存在")
    role = None if data.role == "super_admin" else db.query(Role).filter(Role.name == data.role).first()
    if data.role not in ("super_admin", "") and not role:
        raise HTTPException(400, "角色不存在")
    department = db.query(Department).filter(Department.name == data.department).first() if data.department else None
    if data.department and not department:
        raise HTTPException(400, "部门不存在")
    if data.permissions is None:
        data.permissions = get_user_permissions(User(role=data.role, role_id=role.id if role else None, permissions=None), db)
    validate_access(data)
    new_user = User(username=data.username, name=data.name, role=data.role,
                role_id=role.id if role else None, department=data.department,
                department_id=department.id if department else None,
                permissions=json.dumps(data.permissions if data.permissions is not None else get_user_permissions(User(role=data.role, role_id=role.id if role else None, permissions=None), db)),
                data_scope=data.data_scope, password_hash=pwd_context.hash(data.password))
    db.add(new_user)
    db.commit()
    return user_view(new_user, db)

@router.put("/users/{user_id}")
def update_user(user_id: int, data: UserIn, db: Session = Depends(get_write_db), user = Depends(require_super_admin)):
    acting_user = user
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    validate_access(data)
    if user.id == acting_user.id and data.role != 'super_admin':
        raise HTTPException(400, '不能移除自己的超级管理员身份')
    if data.permissions is None:
        data.permissions = get_user_permissions(user, db)
    validate_access(data)
    user.name = data.name
    role = None if data.role == "super_admin" else db.query(Role).filter(Role.name == data.role).first()
    if data.role not in ("super_admin", "") and not role:
        raise HTTPException(400, "角色不存在")
    department = db.query(Department).filter(Department.name == data.department).first() if data.department else None
    if data.department and not department:
        raise HTTPException(400, "部门不存在")
    user.role = data.role
    user.role_id = role.id if role else None
    user.department = data.department
    user.department_id = department.id if department else None
    user.permissions = json.dumps(data.permissions) if data.permissions is not None else user.permissions
    user.data_scope = data.data_scope
    if data.password and len(data.password) < 10:
        raise HTTPException(400, '密码至少需要10个字符')
    if data.password:
        user.password_hash = pwd_context.hash(data.password)
        user.token_version = (user.token_version or 0) + 1
    db.commit()
    return user_view(user, db)

@router.put("/users/{user_id}/toggle")
def toggle_user(user_id: int, db: Session = Depends(get_write_db), user = Depends(require_super_admin)):
    acting_user = user
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.id == acting_user.id:
        raise HTTPException(400, "不能停用当前登录账号")
    user.token_version = (user.token_version or 0) + 1
    user.is_active = 0 if user.is_active == 1 else 1
    db.commit()
    return user_view(user, db)

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_write_db), user = Depends(require_super_admin)):
    if user_id == user.id:
        raise HTTPException(400, "不能删除当前登录账号")
    target = db.query(User).get(user_id)
    if not target:
        raise HTTPException(404, "用户不存在")
    for model, fields in [(ScrapRequest, ['applicant_id', 'approver_id']),
                          (DeleteRequest, ['applicant_id', 'approver_id']),
                          (TransferRecord, ['operator_id'])]:
        if any(db.query(model).filter(getattr(model, field) == target.id).first() for field in fields):
            raise HTTPException(409, '用户关联历史申请或审批记录，请停用账号以保留身份关联')
    if db.query(ScrapRequest).filter(ScrapRequest.applicant_id.is_(None), ScrapRequest.applicant == target.name).first() or db.query(DeleteRequest).filter(DeleteRequest.applicant_id.is_(None), DeleteRequest.applicant == target.name).first():
        raise HTTPException(409, '同名历史申请归属未确定，请停用账号以保留核对信息')
    db.delete(target)
    log = OperationLog(user=user.name, module="权限管理", action="删除用户", detail=f"删除用户 {target.name}({target.username})")
    db.add(log)
    db.commit()
    return {"ok": True}


# ===== 角色管理（仅超级管理员）=====
class RoleIn(BaseModel):
    name: str
    permissions: list[str] = []

@router.get("/roles")
def list_roles(db: Session = Depends(get_db), user = Depends(require_super_admin)):
    roles = db.query(Role).all()
    result = []
    for r in roles:
        try:
            perms = sorted(PERMISSION_KEYS.intersection(json.loads(r.permissions))) if r.permissions else []
        except Exception:
            perms = []
        result.append({"id": r.id, "name": r.name, "permissions": perms})
    return result

@router.get("/permissions")
def list_permissions(user=Depends(require_super_admin)):
    return [{"key": k, "label": v} for k, v in ALL_PERMISSIONS]

@router.post("/roles")
def create_role(data: RoleIn, db: Session = Depends(get_write_db), user = Depends(require_super_admin)):
    if set(data.permissions) - PERMISSION_KEYS:
        raise HTTPException(400, "包含未知或保留的权限")
    if data.name == "super_admin":
        raise HTTPException(400, "不能创建超级管理员")
    if db.query(Role).filter(Role.name == data.name).first():
        raise HTTPException(400, "角色名已存在")
    role = Role(name=data.name, permissions=json.dumps(data.permissions, ensure_ascii=False))
    db.add(role)
    db.commit()
    return role

@router.put("/roles/{role_id}")
def update_role(role_id: int, data: RoleIn, db: Session = Depends(get_write_db), user = Depends(require_super_admin)):
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(404, "角色不存在")
    if set(data.permissions) - PERMISSION_KEYS:
        raise HTTPException(400, "包含未知或保留的权限")
    if data.name == "super_admin":
        raise HTTPException(400, "不能使用保留角色名")
    duplicate = db.query(Role).filter(Role.name == data.name, Role.id != role_id).first()
    if duplicate:
        raise HTTPException(400, "角色名已存在")
    old_name = role.name
    role.name = data.name
    role.permissions = json.dumps(data.permissions, ensure_ascii=False)
    db.query(User).filter(User.role_id == role.id).update({User.role: data.name})
    db.query(User).filter(User.role_id.is_(None), User.role == old_name).update({User.role: data.name, User.role_id: role.id})
    db.commit()
    return role

@router.delete("/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_write_db), user = Depends(require_super_admin)):
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(404, "角色不存在")
    # 检查是否有用户在用
    count = db.query(User).filter((User.role_id == role.id) | (User.role == role.name)).count()
    if count > 0:
        raise HTTPException(400, f"该角色下还有 {count} 个用户，不能删除")
    db.delete(role)
    db.commit()
    return {"ok": True}
