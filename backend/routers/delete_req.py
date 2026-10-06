from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from database import get_db
from models import DeleteRequest, OperationLog, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, ScrapRequest, TransferRecord
from deps import require_admin

router = APIRouter(prefix="/api/delete-request", tags=["delete-request"])

TABLE_MAP = {
    "it_assets": ITAsset,
    "phone_assets": PhoneAsset,
    "medical_assets": MedicalAsset,
    "phone_numbers": PhoneNumber,
    "scrap_requests": ScrapRequest,
    "transfer_records": TransferRecord,
}

class DeleteReqIn(BaseModel):
    table_name: str
    record_id: int
    record_desc: str
    reason: str
    applicant: Optional[str] = "管理员"

@router.get("")
def list_requests(db: Session = Depends(get_db)):
    return db.query(DeleteRequest).order_by(DeleteRequest.id.desc()).all()

@router.post("")
def create_request(data: DeleteReqIn, db: Session = Depends(get_db)):
    item = DeleteRequest(**data.dict())
    db.add(item)
    db.add(OperationLog(user=data.applicant, module="删除管理", action="申请删除", detail=f"{data.record_desc}，原因：{data.reason}"))
    db.commit()
    return item

@router.put("/{item_id}/approve")
def approve_request(item_id: int, db: Session = Depends(get_db)):
    item = db.query(DeleteRequest).get(item_id)
    if not item:
        raise HTTPException(404, "申请不存在")
    item.status = "approved"
    item.approver = "管理员"
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
                    asset.user_name = None
                    asset.department = None
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
                operator='管理员',
                notes='来自部门主管报废申请审批通过'
            )
            db.add(tr)
        elif apply_type in ('checkout', 'transfer') and apply_asset_id:
            # 自动创建流转记录
            tr = TransferRecord(
                transfer_number='TR-' + str(int(datetime.now().timestamp()*1000)),
                type=apply_type,
                asset_desc=item.record_desc,
                operator='管理员',
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
                        asset.user_name = apply_user or asset.user_name
                        if apply_dept: asset.department = apply_dept
                    elif apply_type == 'transfer':
                        if apply_dept: asset.department = apply_dept
                        if apply_user: asset.user_name = apply_user
    else:
        # 普通删除申请 → 真正删除记录
        model = TABLE_MAP.get(item.table_name)
        if model:
            record = db.query(model).get(item.record_id)
            if record:
                db.delete(record)

    db.add(OperationLog(user='管理员', module="审批管理", action="审批通过", detail=item.record_desc))
    db.commit()
    return item

@router.put("/{item_id}/reject")
def reject_request(item_id: int, db: Session = Depends(get_db)):
    item = db.query(DeleteRequest).get(item_id)
    if not item:
        raise HTTPException(404, "申请不存在")
    item.status = "rejected"
    item.approver = "管理员"
    item.approved_at = datetime.now()
    db.add(OperationLog(user="管理员", module="删除管理", action="审批驳回", detail=item.record_desc))
    db.commit()
    return item


