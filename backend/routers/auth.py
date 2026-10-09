from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from database import get_db
from models import User, OperationLog, Role
from deps import require_super_admin, SECRET_KEY, ALGORITHM
import json

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 所有可用权限项
ALL_PERMISSIONS = [
    ("assets", "资产档案（IT/手机/医疗/号码/微信）"),
    ("transfer", "设备流转"),
    ("scrap", "报废管理"),
    ("approval", "审批中心"),
    ("reports", "报表统计"),
    ("idle", "空闲设备"),
    ("scrapped", "报废设备"),
    ("departments", "部门管理"),
    ("logs", "操作日志"),
]

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    username: str
    password: str

def create_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username, User.is_active == 1).first()
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = create_token(user.username)
    log = OperationLog(user=user.name, module="权限管理", action="登录", detail=f"{user.name} 登录系统")
    db.add(log)
    db.commit()
    # 查权限
    perms = []
    if user.role == "super_admin":
        perms = [p[0] for p in ALL_PERMISSIONS] + ["users", "roles"]
    else:
        role_obj = db.query(Role).filter(Role.name == user.role).first()
        if role_obj and role_obj.permissions:
            try:
                perms = json.loads(role_obj.permissions)
            except Exception:
                perms = []
    return {
        "token": token,
        "user": {"username": user.username, "name": user.name, "role": user.role,
                 "department": user.department, "permissions": perms}
    }

class UserIn(BaseModel):
    username: str
    password: Optional[str] = None
    name: str
    role: str = "asset_admin"
    department: Optional[str] = None

@router.get("/users")
def list_users(db: Session = Depends(get_db), user = Depends(require_super_admin)):
    return db.query(User).all()

@router.post("/users")
def create_user(data: UserIn, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "用户名已存在")
    new_user = User(username=data.username, name=data.name, role=data.role,
                department=data.department, password_hash=pwd_context.hash(data.password or "123456"))
    db.add(new_user)
    db.commit()
    return new_user

@router.put("/users/{user_id}")
def update_user(user_id: int, data: UserIn, db: Session = Depends(get_db), user = Depends(require_super_admin)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    user.name = data.name
    user.role = data.role
    user.department = data.department
    if data.password:
        user.password_hash = pwd_context.hash(data.password)
    db.commit()
    return user

@router.put("/users/{user_id}/toggle")
def toggle_user(user_id: int, db: Session = Depends(get_db), user = Depends(require_super_admin)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    user.is_active = 0 if user.is_active == 1 else 1
    db.commit()
    return user

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), user = Depends(require_super_admin)):
    if user_id == user.id:
        raise HTTPException(400, "不能删除当前登录账号")
    target = db.query(User).get(user_id)
    if not target:
        raise HTTPException(404, "用户不存在")
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
            perms = json.loads(r.permissions) if r.permissions else []
        except Exception:
            perms = []
        result.append({"id": r.id, "name": r.name, "permissions": perms})
    return result

@router.get("/permissions")
def list_permissions():
    return [{"key": k, "label": v} for k, v in ALL_PERMISSIONS]

@router.post("/roles")
def create_role(data: RoleIn, db: Session = Depends(get_db), user = Depends(require_super_admin)):
    if data.name == "super_admin":
        raise HTTPException(400, "不能创建超级管理员")
    if db.query(Role).filter(Role.name == data.name).first():
        raise HTTPException(400, "角色名已存在")
    role = Role(name=data.name, permissions=json.dumps(data.permissions, ensure_ascii=False))
    db.add(role)
    db.commit()
    return role

@router.put("/roles/{role_id}")
def update_role(role_id: int, data: RoleIn, db: Session = Depends(get_db), user = Depends(require_super_admin)):
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(404, "角色不存在")
    role.name = data.name
    role.permissions = json.dumps(data.permissions, ensure_ascii=False)
    db.commit()
    return role

@router.delete("/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db), user = Depends(require_super_admin)):
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(404, "角色不存在")
    # 检查是否有用户在用
    count = db.query(User).filter(User.role == role.name).count()
    if count > 0:
        raise HTTPException(400, f"该角色下还有 {count} 个用户，不能删除")
    db.delete(role)
    db.commit()
    return {"ok": True}
