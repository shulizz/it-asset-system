from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from database import get_db
from models import User

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

def require_admin(user: User = Depends(get_current_user)):
    if user.role not in ("super_admin", "asset_admin"):
        raise HTTPException(403, "需要管理员权限")
    return user

def require_super_admin(user: User = Depends(get_current_user)):
    if user.role != "super_admin":
        raise HTTPException(403, "需要超级管理员权限")
    return user
