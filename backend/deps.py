from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from database import get_db
from models import User
import json
import os
from permissions import PERMISSION_KEYS, GLOBAL_PERMISSIONS

SECRET_KEY = os.getenv("IT_ASSET_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "it-asset-secret-key-change-in-production":
    raise RuntimeError("IT_ASSET_SECRET_KEY must be configured with a strong secret")
ALGORITHM = "HS256"

security = HTTPBearer()

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(401, "无效登录")
    except JWTError:
        raise HTTPException(401, "登录已过期，请重新登录")
    user = db.query(User).filter(User.username == username, User.is_active == 1).first()
    if not user:
        raise HTTPException(401, "用户不存在或已停用")
    if payload.get("ver") != (user.token_version or 0) or payload.get("uid") != user.id:
        raise HTTPException(401, "登录状态已失效，请重新登录")
    return user

def get_user_permissions(user: User, db: Session) -> list:
    """获取用户权限列表"""
    if user.role == "super_admin":
        return sorted(PERMISSION_KEYS | {"users"})
    if user.permissions is not None:
        try:
            permissions = json.loads(user.permissions)
            if not isinstance(permissions, list):
                return []
            return sorted(PERMISSION_KEYS.intersection(p for p in permissions if isinstance(p, str)))
        except (ValueError, TypeError):
            return []
    return []

def require_perm(perm: str):
    """权限依赖工厂：要求用户拥有指定权限"""
    def checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        perms = get_user_permissions(user, db)
        if perm not in perms:
            raise HTTPException(403, f"没有「{perm}」权限")
        if perm in GLOBAL_PERMISSIONS and user.role != 'super_admin' and user.data_scope != 'all':
            raise HTTPException(403, '此权限需要全部部门数据范围')
        return user
    return checker

# 兼容旧代码
def require_admin(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    perms = get_user_permissions(user, db)
    if "assets" not in perms:
        raise HTTPException(403, "需要管理员权限")
    return user

def require_approver(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    perms = get_user_permissions(user, db)
    if "approval" not in perms:
        raise HTTPException(403, "没有审批权限")
    return user

def require_super_admin(user: User = Depends(get_current_user)):
    if user.role != "super_admin":
        raise HTTPException(403, "需要超级管理员权限")
    return user


def scope_query(query, model, user):
    if hasattr(model, 'asset_number') or getattr(model, '__tablename__', '') == 'phone_numbers':
        query = query.filter(model.status != 'archived')
    if user.role == 'super_admin' or user.data_scope == 'all':
        return query
    if not user.department_id:
        return query.filter(False)
    if hasattr(model, 'department_id'):
        if hasattr(model, 'new_department_id'):
            return query.filter((model.department_id == user.department_id) | (model.new_department_id == user.department_id))
        return query.filter(model.department_id == user.department_id)
    if hasattr(model, 'department'):
        return query.filter(model.department == user.department)
    return query.filter(False)

def check_scope(item, user):
    if user.role == 'super_admin' or user.data_scope == 'all':
        return
    item_department_id = getattr(item, 'department_id', None)
    same_legacy_department = not item_department_id and getattr(item, 'department', None) == user.department
    if not user.department_id or (item_department_id != user.department_id and not same_legacy_department):
        raise HTTPException(403, '只能操作本部门数据')


def require_any(*permissions):
    def checker(user=Depends(get_current_user), db: Session=Depends(get_db)):
        if not set(permissions).intersection(get_user_permissions(user, db)):
            raise HTTPException(403, '没有访问权限')
        return user
    return checker
