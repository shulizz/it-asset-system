from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Optional
from database import get_db
from models import ScrapRequest, OperationLog, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, TransferRecord, User
from deps import require_admin, get_current_user, require_approver, require_perm

router = APIRouter(prefix="/api/scrap", tags=["scrap"])

ASSET_MAP = {
    "it": ITAsset,
    "phone": PhoneAsset,
    "medical": MedicalAsset,
    "number": PhoneNumber,
}

def set_asset_user(asset, value):
    """统一设置设备使用人：IT/手机/号码用 user_name，医疗设备用 keeper"""
    if hasattr(asset, 'user_name'):
        asset.user_name = value
    elif hasattr(asset, 'keeper'):
        asset.keeper = value

class ScrapIn(BaseModel):
    request_number: str
    asset_desc: str
    asset_type: Optional[str] = None
    asset_id: Optional[int] = None
    applicant: Optional[str] = None
    department: Optional[str] = None
    reason: Optional[str] = None
    status: str = "pending_approval"
    auditor: Optional[str] = None
    submit_date: Optional[date] = None
    notes: Optional[str] = None

@router.get("")
def list_scraps(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ScrapRequest).order_by(ScrapRequest.id.desc()).all()

@router.post("")
def create_scrap(data: ScrapIn, db: Session = Depends(get_db), current_user: User = Depends(require_perm("scrap"))):
    data.submit_date = date.today()
    item = ScrapRequest(**data.dict())
    db.add(item)
    db.add(OperationLog(user=current_user.name, module="报废管理", action="发起申请", detail=data.asset_desc))
    db.commit()
    db.refresh(item)
    return item

@router.put("/{item_id}/approve")
def approve_scrap(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_approver)):
    item = db.query(ScrapRequest).get(item_id)
    if not item:
        raise HTTPException(404, "申请不存在")
    if item.status != "pending_approval":
        raise HTTPException(400, f"申请已{ '审批通过' if item.status=='approved' else '已驳回' }，请勿重复操作")
    item.status = "approved"
    item.approve_date = date.today()
    item.auditor = current_user.name
    # 更新设备状态为已报废
    if item.asset_type and item.asset_id:
        model = ASSET_MAP.get(item.asset_type)
        if model:
            asset = db.query(model).get(item.asset_id)
            if asset:
                asset.status = "scrapped"
                set_asset_user(asset, None)
                asset.department = None
                tr = TransferRecord(
                    transfer_number='TR-SCRAP-' + str(item.id),
                    type='scrap', asset_desc=item.asset_desc,
                    operator=current_user.name, department=item.department, notes='报废审批通过'
                )
                db.add(tr)
    db.add(OperationLog(user=current_user.name, module="报废管理", action="审批通过", detail=item.asset_desc))
    db.commit()
    return item

@router.put("/{item_id}/reject")
def reject_scrap(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_approver)):
    item = db.query(ScrapRequest).get(item_id)
    if not item:
        raise HTTPException(404, "申请不存在")
    if item.status != "pending_approval":
        raise HTTPException(400, "申请已处理，请勿重复操作")
    item.status = "rejected"
    db.add(OperationLog(user=current_user.name, module="报废管理", action="审批驳回", detail=item.asset_desc))
    db.commit()
    return item


