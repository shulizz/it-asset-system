import json
import logging
import re
from datetime import datetime, timedelta
from typing import Literal, Optional

from database import get_db, get_write_db
from deps import ALGORITHM, SECRET_KEY, get_current_user, get_user_permissions, require_super_admin
from fastapi import APIRouter, Depends, HTTPException, Request
from jose import jwt
from login_limits import login_limiter
from models import DeleteRequest, Department, OperationLog, ScrapRequest, TransferRecord, User
from passlib.context import CryptContext
from pydantic import BaseModel, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

from permissions import ALL_PERMISSIONS, GLOBAL_PERMISSIONS, PERMISSION_DEPENDENCIES

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username", "password")
    @classmethod
    def bounded_login_input(cls, value, info):
        limit = 72 if info.field_name == "password" else 256
        if len(value.encode("utf-8")) > limit:
            raise ValueError("登录信息过长")
        return value


def create_token(username: str, token_version: int, user_id: int):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire, "ver": token_version, "uid": user_id}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    address = request.client.host if request.client else "unknown"
    login_limiter.check(address, req.username)
    user = db.query(User).filter(User.username == req.username, User.is_active == 1).first()
    snapshot = (user.id, user.password_hash, user.token_version) if user else None
    db.rollback()  # Password hashing must never hold the SQLite write lock.
    if not snapshot or not pwd_context.verify(req.password, snapshot[1]):
        logger.warning("Login rejected account=%r source=%r", req.username, address)
        raise HTTPException(status_code=401, detail="账号或密码错误")
    db.execute(text("BEGIN IMMEDIATE"))
    user = (
        db.query(User)
        .filter(
            User.id == snapshot[0],
            User.is_active == 1,
            User.password_hash == snapshot[1],
            User.token_version == snapshot[2],
        )
        .first()
    )
    if not user:
        raise HTTPException(401, "账号状态已改变，请重新登录")
    token = create_token(user.username, user.token_version or 0, user.id)
    log = OperationLog(
        user=user.name, module="权限管理", action="登录", detail=f"{user.name} 登录系统"
    )
    db.add(log)
    db.commit()
    return {"token": token, "user": user_view(user, db)}


def user_view(user, db):
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "role_id": user.role_id,
        "department": user.department,
        "department_id": user.department_id,
        "is_active": user.is_active,
        "data_scope": user.data_scope or "department",
        "permissions": get_user_permissions(user, db),
    }


@router.get("/me")
def me(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return user_view(user, db)


def validate_access(data):
    if data.role == "super_admin":
        data.permissions = []  # Super-admin rights come from identity, never configurable grants.
    allowed = {key for key, label in ALL_PERMISSIONS}
    if data.permissions is not None and set(data.permissions) - allowed:
        raise HTTPException(400, "包含未知或保留的权限")
    if data.data_scope == "department" and not data.department and data.role != "super_admin":
        raise HTTPException(400, "仅本部门范围必须选择所属部门")
    if (
        data.role != "super_admin"
        and data.data_scope != "all"
        and GLOBAL_PERMISSIONS.intersection(data.permissions or [])
    ):
        raise HTTPException(400, "部门管理、全局日志和微信管理权限需要全部部门数据范围")

    for permission, dependencies in PERMISSION_DEPENDENCIES.items():
        if permission in (data.permissions or []) and not dependencies.issubset(data.permissions):
            raise HTTPException(400, "微信密码权限必须同时配置微信管理权限")


class UserIn(BaseModel):
    username: str
    password: Optional[str] = None
    name: str
    email: Optional[str] = None
    role: str = ""
    department: Optional[str] = None
    permissions: Optional[list[str]] = None
    data_scope: Literal["all", "department"] = "department"

    @field_validator("username", "name")
    @classmethod
    def validate_identity_text(cls, value):
        value = value.strip()
        if not value or len(value) > 50:
            raise ValueError("账号和姓名不能为空，且最多50个字符")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_size(cls, value):
        if value and len(value.encode("utf-8")) > 72:
            raise ValueError("密码最多72个UTF-8字节")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if value is None or not value.strip():
            return None
        value = value.strip()
        if len(value) > 254 or not re.fullmatch(
            r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+",
            value,
        ):
            raise ValueError("请输入有效的邮箱地址")
        return value

    @field_validator("role")
    @classmethod
    def validate_role_label(cls, value):
        value = value.strip()
        if len(value) > 50:
            raise ValueError("角色名称最多50个字符")
        return value

    @field_validator("department")
    @classmethod
    def normalize_department(cls, value):
        return value.strip() or None if value is not None else None


@router.get("/users")
def list_users(db: Session = Depends(get_db), user=Depends(require_super_admin)):
    return [user_view(item, db) for item in db.query(User).all()]


def new_user_values(data: UserIn, db: Session):
    validate_access(data)
    if not data.password or len(data.password) < 10:
        raise HTTPException(400, "新用户密码至少需要10个字符")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "用户名已存在")
    department = (
        db.query(Department).filter(Department.name == data.department).first()
        if data.department
        else None
    )
    if data.department and not department:
        raise HTTPException(400, "部门不存在")
    if data.permissions is None:
        data.permissions = []
    validate_access(data)
    return dict(
        username=data.username,
        name=data.name,
        email=data.email,
        role=data.role,
        role_id=None,
        department=data.department,
        department_id=department.id if department else None,
        permissions=json.dumps(data.permissions),
        data_scope=data.data_scope,
    )


@router.post("/users")
def create_user(
    data: UserIn, db: Session = Depends(get_write_db), current_user=Depends(require_super_admin)
):
    new_user = User(**new_user_values(data, db), password_hash=pwd_context.hash(data.password))
    db.add(new_user)
    db.commit()
    return user_view(new_user, db)


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserIn,
    db: Session = Depends(get_write_db),
    user=Depends(require_super_admin),
):
    acting_user = user
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    validate_access(data)
    if user.id == acting_user.id and data.role != "super_admin":
        raise HTTPException(400, "不能移除自己的超级管理员身份")
    if data.permissions is None:
        data.permissions = get_user_permissions(user, db)
    validate_access(data)
    user.name = data.name
    if "email" in data.model_fields_set:
        user.email = data.email
    department = (
        db.query(Department).filter(Department.name == data.department).first()
        if data.department
        else None
    )
    if data.department and not department:
        raise HTTPException(400, "部门不存在")
    user.role = data.role
    user.role_id = None
    user.department = data.department
    user.department_id = department.id if department else None
    user.permissions = (
        json.dumps(data.permissions) if data.permissions is not None else user.permissions
    )
    user.data_scope = data.data_scope
    if data.password and len(data.password) < 10:
        raise HTTPException(400, "密码至少需要10个字符")
    if data.password:
        user.password_hash = pwd_context.hash(data.password)
        user.token_version = (user.token_version or 0) + 1
    db.commit()
    return user_view(user, db)


@router.put("/users/{user_id}/toggle")
def toggle_user(
    user_id: int, db: Session = Depends(get_write_db), user=Depends(require_super_admin)
):
    acting_user = user
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.id == acting_user.id:
        raise HTTPException(400, "不能停用当前登录账号")
    user.token_version = (user.token_version or 0) + 1
    user.is_active = 0 if user.is_active == 1 else 1
    db.commit()
    return user_view(user, db)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int, db: Session = Depends(get_write_db), user=Depends(require_super_admin)
):
    if user_id == user.id:
        raise HTTPException(400, "不能删除当前登录账号")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "用户不存在")
    for model, fields in [
        (ScrapRequest, ["applicant_id", "approver_id"]),
        (DeleteRequest, ["applicant_id", "approver_id"]),
        (TransferRecord, ["operator_id"]),
    ]:
        if any(
            db.query(model).filter(getattr(model, field) == target.id).first() for field in fields
        ):
            raise HTTPException(409, "用户关联历史申请或审批记录，请停用账号以保留身份关联")
    if (
        db.query(ScrapRequest)
        .filter(ScrapRequest.applicant_id.is_(None), ScrapRequest.applicant == target.name)
        .first()
        or db.query(DeleteRequest)
        .filter(DeleteRequest.applicant_id.is_(None), DeleteRequest.applicant == target.name)
        .first()
    ):
        raise HTTPException(409, "同名历史申请归属未确定，请停用账号以保留核对信息")
    db.delete(target)
    log = OperationLog(
        user=user.name,
        module="权限管理",
        action="删除用户",
        detail=f"删除用户 {target.name}({target.username})",
    )
    db.add(log)
    db.commit()
    return {"ok": True}


@router.get("/permissions")
def list_permissions(user=Depends(require_super_admin)):
    return [{"key": k, "label": v} for k, v in ALL_PERMISSIONS]


@router.api_route("/roles", methods=["GET", "POST"])
@router.api_route("/roles/{role_id}", methods=["GET", "PUT", "DELETE"])
def retired_role_templates(user=Depends(require_super_admin)):
    raise HTTPException(410, "角色权限模块已移除，请在用户权限中逐个分配权限")
