from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from models import WeChatAccount, OperationLog, User
from deps import get_current_user

router = APIRouter(prefix="/api/wechat", tags=["微信账号"])

class WeChatIn(BaseModel):
    wx_account: str
    wx_password: Optional[str] = None
    real_name: Optional[str] = None
    user_name: Optional[str] = None
    purpose: Optional[str] = None
    status: Optional[str] = "idle"
    notes: Optional[str] = None

@router.get("")
def list(db: Session = Depends(get_db)):
    return db.query(WeChatAccount).order_by(WeChatAccount.id.desc()).all()

@router.post("")
def create(data: WeChatIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if db.query(WeChatAccount).filter(WeChatAccount.wx_account == data.wx_account).first():
        raise HTTPException(400, "微信账号已存在")
    data.status = "in_use" if data.user_name else "idle"
    item = WeChatAccount(**data.dict())
    db.add(item)
    db.add(OperationLog(user=current_user.name, module="微信账号", action="新增", detail=f"新增微信账号 {item.wx_account}"))
    db.commit()
    db.refresh(item)
    return item

@router.put("/{item_id}")
def update(item_id: int, data: WeChatIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(WeChatAccount).get(item_id)
    if not item: raise HTTPException(404, "不存在")
    data.status = "in_use" if data.user_name else "idle"
    for k, v in data.dict().items():
        setattr(item, k, v)
    db.add(OperationLog(user=current_user.name, module="微信账号", action="编辑", detail=f"编辑微信账号 {item.wx_account}"))
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(WeChatAccount).get(item_id)
    if not item: raise HTTPException(404, "不存在")
    db.add(OperationLog(user=current_user.name, module="微信账号", action="删除", detail=f"删除微信账号 {item.wx_account}"))
    db.delete(item)
    db.commit()
    return {"ok": True}

