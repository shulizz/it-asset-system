from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from models import WeChatAccount, OperationLog, User
from deps import get_current_user, require_perm, get_user_permissions
from credential_crypto import encrypt_credential, decrypt_credential

def wechat_access(user=Depends(require_perm('wechat'))):
    if user.role != 'super_admin' and user.data_scope != 'all':
        raise HTTPException(403, '微信账号没有部门归属，需要全部部门数据范围')
    return user

def account_view(item, user, db):
    data = {c.name: getattr(item, c.name) for c in WeChatAccount.__table__.columns}
    if 'wechat_secret' not in get_user_permissions(user, db):
        data['wx_password'] = None
    else:
        try:
            data['wx_password'] = decrypt_credential(data['wx_password'])
        except RuntimeError:
            data['wx_password'] = None
            data['password_error'] = '密码无法解密，请重新设置此记录密码'
    return data

def check_password_access(data, user, db):
    if data.wx_password is not None and 'wechat_secret' not in get_user_permissions(user, db):
        raise HTTPException(403, '没有微信密码权限')

router = APIRouter(
    prefix="/api/wechat",
    tags=["微信账号"],
    dependencies=[Depends(wechat_access)],
)

class WeChatIn(BaseModel):
    wx_account: str
    wx_password: Optional[str] = None
    real_name: Optional[str] = None
    user_name: Optional[str] = None
    purpose: Optional[str] = None
    status: Optional[str] = "idle"
    notes: Optional[str] = None

@router.get("")
def list(db: Session = Depends(get_db), current_user=Depends(wechat_access)):
    return [account_view(item, current_user, db) for item in db.query(WeChatAccount).order_by(WeChatAccount.id.desc()).all()]

@router.post("")
def create(data: WeChatIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_password_access(data, current_user, db)
    if db.query(WeChatAccount).filter(WeChatAccount.wx_account == data.wx_account).first():
        raise HTTPException(400, "微信账号已存在")
    data.status = "in_use" if data.user_name else "idle"
    values = data.dict()
    values['wx_password'] = encrypt_credential(values.get('wx_password'))
    item = WeChatAccount(**values)
    db.add(item)
    db.add(OperationLog(user=current_user.name, module="微信账号", action="新增", detail=f"新增微信账号 {item.wx_account}"))
    db.commit()
    db.refresh(item)
    return account_view(item, current_user, db)

@router.put("/{item_id}")
def update(item_id: int, data: WeChatIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_password_access(data, current_user, db)
    item = db.query(WeChatAccount).get(item_id)
    if not item: raise HTTPException(404, "不存在")
    data.status = "in_use" if data.user_name else "idle"
    for k, v in data.dict().items():
        if k == 'wx_password' and v is None:
            continue
        setattr(item, k, encrypt_credential(v) if k == 'wx_password' and v is not None else v)
    db.add(OperationLog(user=current_user.name, module="微信账号", action="编辑", detail=f"编辑微信账号 {item.wx_account}"))
    db.commit()
    db.refresh(item)
    return account_view(item, current_user, db)

@router.delete("/{item_id}")
def delete(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(WeChatAccount).get(item_id)
    if not item: raise HTTPException(404, "不存在")
    db.add(OperationLog(user=current_user.name, module="微信账号", action="删除", detail=f"删除微信账号 {item.wx_account}"))
    db.delete(item)
    db.commit()
    return {"ok": True}

