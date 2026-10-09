from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Optional
from database import get_db, get_write_db
from models import TransferRecord, OperationLog, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, User, Department
from deps import get_current_user, require_perm, scope_query, check_scope

router = APIRouter(prefix="/api/transfer", tags=["transfer"])

MODEL_MAP = {'it': ITAsset, 'phone': PhoneAsset, 'medical': MedicalAsset, 'number': PhoneNumber}

def set_asset_user(asset, value):
    """统一设置设备使用人：IT/手机/号码用 user_name，医疗设备用 keeper"""
    if hasattr(asset, 'user_name'):
        asset.user_name = value
    elif hasattr(asset, 'keeper'):
        asset.keeper = value

class TransferIn(BaseModel):
    transfer_number: str
    type: str
    asset_desc: str
    operator: Optional[str] = "管理员"
    counterparty: Optional[str] = None
    department: Optional[str] = None
    transfer_date: Optional[date] = None
    notes: Optional[str] = None
    asset_type: Optional[str] = None   # it / phone / medical / number
    asset_id: Optional[int] = None
    new_user: Optional[str] = None
    new_dept: Optional[str] = None

@router.get("")
def list_transfers(db: Session = Depends(get_db), current_user: User = Depends(require_perm("transfer"))):
    return scope_query(db.query(TransferRecord), TransferRecord, current_user).order_by(TransferRecord.id.desc()).all()

@router.post("")
def create_transfer(data: TransferIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("transfer"))):
    from workflow import validate_transition, apply_transition
    model = MODEL_MAP.get(data.asset_type)
    asset = db.get(model, data.asset_id) if model and data.asset_id else None
    if not asset:
        raise HTTPException(404, '请选择存在的资产')
    target = db.query(Department).filter(Department.name == data.new_dept).first() if data.new_dept else None
    if data.new_dept and not target:
        raise HTTPException(400, '目标部门不存在')
    validate_transition(db, asset, data.type, current_user, data.new_user, target.id if target else None)
    item = apply_transition(db, asset, data.asset_type, data.type, current_user, data.new_user, target, data.notes)
    db.add(OperationLog(user=current_user.name, module='设备流转', action=data.type, detail=item.asset_desc))
    db.commit()
    db.refresh(item)
    return item
