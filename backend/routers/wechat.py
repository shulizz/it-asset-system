from typing import Optional

from credential_crypto import decrypt_credential, encrypt_credential
from database import get_db, get_write_db
from deps import get_current_user, get_user_permissions, require_perm
from fastapi import APIRouter, Depends, HTTPException
from models import OperationLog, User, WeChatAccount
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session


def legacy_wechat_access(user, db):
    return "wechat" in get_user_permissions(user, db) and (
        user.role == "super_admin" or user.data_scope == "all"
    )


def wechat_access(user=Depends(get_current_user), db=Depends(get_db)):
    if not legacy_wechat_access(user, db) and "wechat_read" not in get_user_permissions(user, db):
        raise HTTPException(403, "没有微信账号查看权限")
    return user


def wechat_edit_access(user=Depends(wechat_access), db=Depends(get_db)):
    if not legacy_wechat_access(user, db) and "wechat_edit" not in get_user_permissions(user, db):
        raise HTTPException(403, "没有微信账号编辑权限")
    return user


def account_view(item, user, db):
    data = {c.name: getattr(item, c.name) for c in WeChatAccount.__table__.columns}
    if "wechat_secret" not in get_user_permissions(user, db):
        data["wx_password"] = None
    else:
        try:
            data["wx_password"] = decrypt_credential(data["wx_password"])
        except RuntimeError:
            data["wx_password"] = None
            data["password_error"] = "密码无法解密，请重新设置此记录密码"
    return data


def check_password_access(data, user, db):
    if data.wx_password is not None and "wechat_secret" not in get_user_permissions(user, db):
        raise HTTPException(403, "没有微信密码权限")


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

    @field_validator("wx_account")
    @classmethod
    def valid_account_name(cls, value):
        value = value.strip()
        if not value or len(value) > 100:
            raise HTTPException(400, "微信账号不能为空，最多100个字符")
        return value


@router.get("")
def list(db: Session = Depends(get_db), current_user=Depends(wechat_access)):
    return [
        account_view(item, current_user, db)
        for item in db.query(WeChatAccount)
        .filter(WeChatAccount.status != "archived")
        .order_by(WeChatAccount.id.desc())
        .all()
    ]


@router.post("")
def create(
    data: WeChatIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(wechat_edit_access),
):
    check_password_access(data, current_user, db)
    if db.query(WeChatAccount).filter(WeChatAccount.wx_account == data.wx_account).first():
        raise HTTPException(400, "微信账号已存在")
    data.status = "in_use" if data.user_name else "idle"
    values = data.model_dump()
    values["wx_password"] = encrypt_credential(values.get("wx_password"))
    item = WeChatAccount(**values)
    db.add(item)
    db.add(
        OperationLog(
            user=current_user.name,
            module="微信账号",
            action="新增",
            detail=f"新增微信账号 {item.wx_account}",
        )
    )
    db.commit()
    db.refresh(item)
    return account_view(item, current_user, db)


@router.put("/{item_id}")
def update(
    item_id: int,
    data: WeChatIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(wechat_edit_access),
):
    check_password_access(data, current_user, db)
    item = db.get(WeChatAccount, item_id)
    if not item:
        raise HTTPException(404, "不存在")
    if item.status == "archived":
        raise HTTPException(409, "账号已移出档案，不能编辑")
    if (
        db.query(WeChatAccount)
        .filter(WeChatAccount.wx_account == data.wx_account, WeChatAccount.id != item_id)
        .first()
    ):
        raise HTTPException(409, "微信账号已存在")
    values = data.model_dump(exclude_unset=True)
    if "status" in values and values["status"] not in ("in_use", "idle", "stopped"):
        raise HTTPException(400, "账号状态无效")
    if "status" not in values and "user_name" in values:
        values["status"] = "in_use" if values["user_name"] else "idle"
    for k, v in values.items():
        if k == "wx_password" and v is None:
            continue
        setattr(item, k, encrypt_credential(v) if k == "wx_password" and v is not None else v)
    db.add(
        OperationLog(
            user=current_user.name,
            module="微信账号",
            action="编辑",
            detail=f"编辑微信账号 {item.wx_account}",
        )
    )
    db.commit()
    db.refresh(item)
    return account_view(item, current_user, db)


@router.delete("/{item_id}")
def delete(
    item_id: int,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_perm("wechat")),
):
    item = db.get(WeChatAccount, item_id)
    if not item:
        raise HTTPException(404, "不存在")
    from routers.delete_req import DeleteReqIn, create_request

    return create_request(
        DeleteReqIn(
            table_name="wechat_accounts",
            record_id=item_id,
            record_desc=f"微信账号 {item.wx_account}",
            reason="申请移出微信账号档案",
        ),
        db,
        current_user,
    )
