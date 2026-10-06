from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Optional
from database import get_db
from models import TransferRecord, OperationLog, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber

router = APIRouter(prefix="/api/transfer", tags=["transfer"])

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
def list_transfers(db: Session = Depends(get_db)):
    return db.query(TransferRecord).order_by(TransferRecord.id.desc()).all()

@router.post("")
def create_transfer(data: TransferIn, db: Session = Depends(get_db)):
    item = TransferRecord(**data.dict(exclude={'new_user','new_dept'}))
    db.add(item)
    db.add(OperationLog(user=data.operator or "管理员", module="设备流转", action=data.type, detail=data.asset_desc))

    # 自动更新设备档案
    if data.asset_type and data.asset_id:
        model_map = {'it': ITAsset, 'phone': PhoneAsset, 'medical': MedicalAsset, 'number': PhoneNumber}
        model = model_map.get(data.asset_type)
        if model:
            asset = db.query(model).get(data.asset_id)
            if asset:
                if data.type == 'checkout':  # 领用 → 状态在用，更新使用人和部门
                    asset.status = 'in_use'
                    if data.new_user:
                        asset.user_name = data.new_user
                    if data.new_dept:
                        asset.department = data.new_dept
                elif data.type == 'return':  # 归还 → 状态闲置，清空使用人和部门
                    asset.status = 'idle'
                    asset.user_name = None
                    asset.department = None
                elif data.type == 'transfer':  # 调拨 → 改部门和使用人
                    if data.new_dept:
                        asset.department = data.new_dept
                    if data.new_user:
                        asset.user_name = data.new_user
                elif data.type == 'offboard':  # 离职回收 → 状态闲置，清空使用人和部门
                    asset.status = 'idle'
                    asset.user_name = None
                    asset.department = None

    db.commit()
    db.refresh(item)
    return item
