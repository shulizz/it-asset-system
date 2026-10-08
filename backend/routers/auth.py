from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from database import get_db
from models import User, OperationLog
from deps import require_super_admin, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/auth", tags=["auth"])

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
    log = OperationLog(user=user.username, module="权限管理", action="登录", detail=f"{user.name} 登录系统")
    db.add(log)
    db.commit()
    return {
        "token": token,
        "user": {"username": user.username, "name": user.name, "role": user.role, "department": user.department}
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
    log = OperationLog(user=user.username, module="权限管理", action="删除用户", detail=f"删除用户 {target.name}({target.username})")
    db.add(log)
    db.commit()
    return {"ok": True}
