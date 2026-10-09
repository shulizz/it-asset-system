from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Optional
from database import get_db
from models import ScrapRequest, OperationLog, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, TransferRecord, User
from deps import require_admin, get_current_user, require_approver, require_perm, require_any, get_user_permissions, scope_query, check_scope

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
    query = db.query(ScrapRequest)
    if 'approval' not in get_user_permissions(current_user, db) and 'scrap' not in get_user_permissions(current_user, db):
        query = query.filter(ScrapRequest.applicant == current_user.name)
    return scope_query(query, ScrapRequest, current_user).order_by(ScrapRequest.id.desc()).all()

@router.post("")
def create_scrap(data: ScrapIn, db: Session = Depends(get_db), current_user: User = Depends(require_any("scrap", "apply"))):
    model = ASSET_MAP.get(data.asset_type)
    if not model or not data.asset_id:
        raise HTTPException(400, '请选择有效资产')
    asset = db.query(model).get(data.asset_id)
    if not asset:
        raise HTTPException(404, '资产不存在')
    check_scope(asset, current_user)
    if asset.status == 'scrapped':
        raise HTTPException(400, '资产已经报废')
    data.submit_date = date.today()
    data.applicant = current_user.name
    data.department = asset.department
    data.status = "pending_approval"
    data.auditor = None
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
    if current_user.role != "super_admin" and current_user.data_scope != "all" and (not current_user.department or item.department != current_user.department):
        raise HTTPException(403, "只能审批本部门申请")
    if item.status != "pending_approval":
        raise HTTPException(400, f"申请已{ '审批通过' if item.status=='approved' else '已驳回' }，请勿重复操作")
    if item.applicant == current_user.name:
        raise HTTPException(400, "不能审批自己提交的申请")
    if not item.asset_type or not item.asset_id or item.asset_type not in ASSET_MAP:
        raise HTTPException(400, "申请缺少有效的资产信息")
    asset = db.query(ASSET_MAP[item.asset_type]).get(item.asset_id)
    if not asset:
        raise HTTPException(404, "申请对应的资产不存在")
    check_scope(asset, current_user)
    if asset.status == "scrapped":
        raise HTTPException(400, "资产已经报废")
    item.status = "approved"
    item.approve_date = date.today()
    item.auditor = current_user.name
    # 更新设备状态为已报废
    asset.status = "scrapped"
    set_asset_user(asset, None)
    # 保留资产归属部门，方便按部门查询历史报废数据
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
    if current_user.role != "super_admin" and current_user.data_scope != "all" and (not current_user.department or item.department != current_user.department):
        raise HTTPException(403, "只能审批本部门申请")
    if item.status != "pending_approval":
        raise HTTPException(400, "申请已处理，请勿重复操作")
    if item.applicant == current_user.name:
        raise HTTPException(400, "不能审批自己提交的申请")
    item.status = "rejected"
    db.add(OperationLog(user=current_user.name, module="报废管理", action="审批驳回", detail=item.asset_desc))
    db.commit()
    return item


