from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from database import get_db
from models import User, Role
import json
import os

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
    return user

def get_user_permissions(user: User, db: Session) -> list:
    """获取用户权限列表"""
    if user.role == "super_admin":
        return ["assets", "transfer", "scrap", "approval", "reports", "idle",
                "scrapped", "departments", "logs", "users", "roles", "assets_write", "import", "export", "wechat", "wechat_secret", "apply"]
    if user.permissions is not None:
        try:
            permissions = json.loads(user.permissions)
            if not isinstance(permissions, list):
                return []
            return sorted(set(p for p in permissions if isinstance(p, str)))
        except (ValueError, TypeError):
            return []
    role_obj = db.query(Role).filter(Role.id == user.role_id).first() if user.role_id else None
    if not role_obj:
        role_obj = db.query(Role).filter(Role.name == user.role).first()
    if role_obj and role_obj.permissions:
        try:
            return expand_legacy_permissions(json.loads(role_obj.permissions))
        except Exception:
            return []
    return []

def require_perm(perm: str):
    """权限依赖工厂：要求用户拥有指定权限"""
    def checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        perms = get_user_permissions(user, db)
        if perm not in perms:
            raise HTTPException(403, f"没有「{perm}」权限")
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


def expand_legacy_permissions(perms):
    result = set(perms)
    if 'assets' in result:
        result.update(['assets_write', 'import', 'export', 'wechat', 'wechat_secret'])
    result.add('apply')
    return sorted(result)

def scope_query(query, model, user):
    if user.role == 'super_admin' or user.data_scope == 'all':
        return query
    if not user.department_id:
        return query.filter(False)
    if hasattr(model, 'department_id'):
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
