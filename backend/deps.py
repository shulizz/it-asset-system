from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from database import get_db
from models import User, Role
import json

SECRET_KEY = "it-asset-secret-key-change-in-production"
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
                "scrapped", "departments", "logs", "users", "roles"]
    role_obj = db.query(Role).filter(Role.name == user.role).first()
    if role_obj and role_obj.permissions:
        try:
            return json.loads(role_obj.permissions)
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
