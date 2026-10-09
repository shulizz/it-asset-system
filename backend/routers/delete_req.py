from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from database import get_db
from models import DeleteRequest, OperationLog, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, ScrapRequest, TransferRecord, User, Department
from deps import require_admin, get_current_user, require_approver, get_user_permissions, require_any, check_scope

router = APIRouter(prefix="/api/delete-request", tags=["delete-request"])

TABLE_MAP = {
    "it_assets": ITAsset,
    "phone_assets": PhoneAsset,
    "medical_assets": MedicalAsset,
    "phone_numbers": PhoneNumber,
    "scrap_requests": ScrapRequest,
    "transfer_records": TransferRecord,
}

def set_asset_user(asset, value):
    """统一设置设备使用人：IT/手机/号码用 user_name，医疗设备用 keeper"""
    if hasattr(asset, 'user_name'):
        asset.user_name = value
    elif hasattr(asset, 'keeper'):
        asset.keeper = value

def request_in_scope(item, user, db):
    if user.role == 'super_admin' or user.data_scope == 'all' or item.applicant == user.name:
        return True
    if item.table_name == 'apply_requests':
        parts = (item.reason or '').split('|')
        model = {'it': ITAsset, 'phone': PhoneAsset, 'medical': MedicalAsset}.get(parts[3]) if len(parts) > 4 else None
        try:
            asset_id = int(parts[4]) if len(parts) > 4 else 0
        except (TypeError, ValueError):
            return False
        record = db.query(model).filter(model.id == asset_id).first() if model else None
    else:
        model = TABLE_MAP.get(item.table_name)
        record = db.query(model).filter(model.id == item.record_id).first() if model else None
    return bool(record and (getattr(record, 'department_id', None) == user.department_id or getattr(record, 'department', None) == user.department))

class DeleteReqIn(BaseModel):
    table_name: str
    record_id: int
    record_desc: str
    reason: str
    applicant: Optional[str] = "管理员"

@router.get("")
def list_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(DeleteRequest).order_by(DeleteRequest.id.desc()).all()
    if "approval" not in get_user_permissions(current_user, db):
        return [row for row in rows if row.applicant == current_user.name]
    return [row for row in rows if request_in_scope(row, current_user, db)]

@router.post("")
def create_request(data: DeleteReqIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.table_name == 'apply_requests':
        if 'apply' not in get_user_permissions(current_user, db):
            raise HTTPException(403, '没有设备申请权限')
        parts = (data.reason or '').split('|')
        if len(parts) < 5 or parts[0] not in ('checkout', 'transfer', 'scrap'):
            raise HTTPException(400, '申请内容无效')
        model = {'it': ITAsset, 'phone': PhoneAsset, 'medical': MedicalAsset}.get(parts[3])
        try:
            asset_id = int(parts[4])
        except (TypeError, ValueError):
            raise HTTPException(400, '申请资产无效')
        asset = db.query(model).filter(model.id == asset_id).first() if model else None
        if not asset:
            raise HTTPException(404, '申请资产不存在')
        check_scope(asset, current_user)
        target_department = parts[2].strip()
        if target_department and not db.query(Department).filter(Department.name == target_department).first():
            raise HTTPException(400, '申请目标部门不存在')
        if current_user.role != 'super_admin' and current_user.data_scope != 'all' and target_department and target_department != current_user.department:
            raise HTTPException(403, '不能向其他部门发起申请')
        if parts[0] == 'checkout' and asset.status != 'idle':
            raise HTTPException(400, '只有闲置资产可以申请领用')
        if parts[0] in ('transfer', 'scrap') and asset.status == 'scrapped':
            raise HTTPException(400, '已报废资产不能申请此操作')
    else:
        if data.table_name not in TABLE_MAP:
            raise HTTPException(400, '不允许申请删除该类型记录')
        if 'assets_write' not in get_user_permissions(current_user, db):
            raise HTTPException(403, '没有申请删除权限')
        model = TABLE_MAP[data.table_name]
        record = db.query(model).filter(model.id == data.record_id).first()
        if not record:
            raise HTTPException(404, '记录不存在')
        check_scope(record, current_user)
    data.applicant = current_user.name
    item = DeleteRequest(**data.dict())
    db.add(item)
    db.add(OperationLog(user=current_user.name, module="删除管理", action="申请删除", detail=f"{data.record_desc}，原因：{data.reason}"))
    db.commit()
    return item

@router.put("/{item_id}/approve")
def approve_request(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_approver)):
    item = db.query(DeleteRequest).get(item_id)
    if not item:
        raise HTTPException(404, "申请不存在")
    if item.status != "pending":
        raise HTTPException(400, "申请已处理，请勿重复操作")
    if item.applicant == current_user.name:
        raise HTTPException(400, "不能审批自己提交的申请")
    if item.table_name not in TABLE_MAP and item.table_name != 'apply_requests':
        raise HTTPException(400, '申请记录类型无效')

    if item.table_name == 'apply_requests':
        parts = (item.reason or '').split('|')
        if len(parts) < 5:
            raise HTTPException(400, '申请内容无效')
        model = {'it': ITAsset, 'phone': PhoneAsset, 'medical': MedicalAsset}.get(parts[3])
        try:
            asset_id = int(parts[4])
        except (TypeError, ValueError):
            raise HTTPException(400, '申请资产无效')
        asset = db.query(model).filter(model.id == asset_id).first() if model else None
        if not asset:
            raise HTTPException(404, '申请资产不存在')
        if current_user.role != 'super_admin' and current_user.data_scope != 'all':
            if not current_user.department or asset.department != current_user.department:
                raise HTTPException(403, '只能审批本部门申请')
            if parts[2].strip() and parts[2].strip() != current_user.department:
                raise HTTPException(403, '不能审批调拨到其他部门的申请')
    else:
        model = TABLE_MAP[item.table_name]
        record = db.query(model).filter(model.id == item.record_id).first()
        if not record:
            raise HTTPException(404, '申请对应的记录已不存在')
        check_scope(record, current_user)
    item.status = "approved"
    item.approver = current_user.name
    item.approved_at = datetime.now()

    # 设备申请 → 自动触发对应操作
    if item.table_name == 'apply_requests':
        parts = (item.reason or '').split('|')
        apply_type = parts[0] if len(parts) > 0 else ''
        apply_user = parts[1] if len(parts) > 1 else ''
        apply_dept = parts[2] if len(parts) > 2 else ''
        apply_asset_type = parts[3] if len(parts) > 3 else ''
        apply_asset_id = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0

        if apply_type == 'scrap' and apply_asset_id:
            # 直接报废设备
            model_map = {'it': ITAsset, 'phone': PhoneAsset, 'medical': MedicalAsset}
            model = model_map.get(apply_asset_type)
            if model:
                asset = db.query(model).get(apply_asset_id)
                if asset:
                    asset.status = 'scrapped'
                    set_asset_user(asset, None)
            # 在报废管理里留记录
            sr = ScrapRequest(
                request_number='SC-' + str(int(datetime.now().timestamp()*1000)),
                asset_desc=item.record_desc,
                asset_type=apply_asset_type,
                asset_id=apply_asset_id,
                applicant=apply_user,
                department=apply_dept,
                reason='部门主管申请报废，审批通过',
                status='approved'
            )
            db.add(sr)
            # 记一条流转记录
            tr = TransferRecord(
                transfer_number='TR-' + str(int(datetime.now().timestamp()*1000)),
                type='scrap',
                asset_desc=item.record_desc,
                operator=current_user.name,
                notes='来自部门主管报废申请审批通过'
            )
            db.add(tr)
        elif apply_type in ('checkout', 'transfer') and apply_asset_id:
            # 自动创建流转记录
            tr = TransferRecord(
                transfer_number='TR-' + str(int(datetime.now().timestamp()*1000)),
                type=apply_type,
                asset_desc=item.record_desc,
                operator=current_user.name,
                counterparty=apply_user,
                department=apply_dept or None,
                asset_type=apply_asset_type,
                asset_id=apply_asset_id,
                new_user=apply_user,
                notes='来自部门主管申请审批通过'
            )
            db.add(tr)
            # 同时更新设备状态
            model_map = {'it': ITAsset, 'phone': PhoneAsset, 'medical': MedicalAsset}
            model = model_map.get(apply_asset_type)
            if model:
                asset = db.query(model).get(apply_asset_id)
                if asset:
                    if apply_type == 'checkout':
                        asset.status = 'in_use'
                        set_asset_user(asset, apply_user or getattr(asset, 'user_name', None) or getattr(asset, 'keeper', None))
                        if apply_dept:
                            target = db.query(Department).filter(Department.name == apply_dept).first()
                            asset.department, asset.department_id = apply_dept, target.id if target else None
                    elif apply_type == 'transfer':
                        if apply_dept:
                            target = db.query(Department).filter(Department.name == apply_dept).first()
                            asset.department, asset.department_id = apply_dept, target.id if target else None
                        if apply_user: set_asset_user(asset, apply_user)
    else:
        # 普通删除申请 → 真正删除记录
        model = TABLE_MAP.get(item.table_name)
        if model:
            record = db.query(model).get(item.record_id)
            if record:
                db.delete(record)

    db.add(OperationLog(user=current_user.name, module="审批管理", action="审批通过", detail=item.record_desc))
    db.commit()
    return item

@router.put("/{item_id}/reject")
def reject_request(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_approver)):
    item = db.query(DeleteRequest).get(item_id)
    if not item:
        raise HTTPException(404, "申请不存在")
    if item.status != "pending":
        raise HTTPException(400, "申请已处理，请勿重复操作")
    if item.applicant == current_user.name:
        raise HTTPException(400, "不能审批自己提交的申请")
    item.status = "rejected"
    item.approver = current_user.name
    item.approved_at = datetime.now()
    db.add(OperationLog(user=current_user.name, module="删除管理", action="审批驳回", detail=item.record_desc))
    db.commit()
    return item


