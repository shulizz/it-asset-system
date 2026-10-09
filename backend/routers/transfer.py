from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Optional
from database import get_db
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
def create_transfer(data: TransferIn, db: Session = Depends(get_db), current_user: User = Depends(require_perm("transfer"))):
    if data.type not in ('checkout', 'return', 'transfer', 'offboard'):
        raise HTTPException(400, '无效流转类型')
    model = MODEL_MAP.get(data.asset_type)
    asset = db.query(model).get(data.asset_id) if model and data.asset_id else None
    if not asset:
        raise HTTPException(404, '请选择存在的资产')
    check_scope(asset, current_user)
    expected_status = 'idle' if data.type == 'checkout' else 'in_use'
    if asset.status != expected_status:
        raise HTTPException(400, '资产当前状态不允许此操作')
    target = db.query(Department).filter(Department.name == data.new_dept).first() if data.new_dept else None
    if data.new_dept and not target:
        raise HTTPException(400, '目标部门不存在')
    if current_user.role != 'super_admin' and current_user.data_scope != 'all' and target and target.id != current_user.department_id:
        raise HTTPException(403, '不能调拨到其他部门')
    if data.type in ('checkout', 'transfer') and not data.new_user:
        raise HTTPException(400, '请选择接收人')
    data.operator = current_user.name
    data.department = asset.department
    item = TransferRecord(**data.dict(exclude={'new_user','new_dept'}))
    db.add(item)
    db.add(OperationLog(user=current_user.name, module="设备流转", action=data.type, detail=data.asset_desc))

    # 自动更新设备档案
    if data.asset_type and data.asset_id:
        model = MODEL_MAP.get(data.asset_type)
        if model:
            asset = db.query(model).get(data.asset_id)
            if asset:
                if data.type == 'checkout':  # 领用 → 状态在用，更新使用人和部门
                    asset.status = 'in_use'
                    if data.new_user:
                        set_asset_user(asset, data.new_user)
                    if data.new_dept:
                        asset.department = data.new_dept
                        asset.department_id = target.id
                elif data.type == 'return':  # 归还 → 状态闲置，清空使用人和部门
                    asset.status = 'idle'
                    set_asset_user(asset, None)
                    pass  # 归还后保留归属部门
                elif data.type == 'transfer':  # 调拨 → 改部门和使用人
                    if data.new_dept:
                        asset.department = data.new_dept
                        asset.department_id = target.id
                    if data.new_user:
                        set_asset_user(asset, data.new_user)
                elif data.type == 'offboard':  # 离职回收 → 状态闲置，清空使用人和部门
                    asset.status = 'idle'
                    set_asset_user(asset, None)
                    pass  # 归还后保留归属部门

    db.commit()
    db.refresh(item)
    return item
