from datetime import datetime, date
from uuid import uuid4
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, get_write_db
from models import DeleteRequest, OperationLog, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, ScrapRequest, TransferRecord, User, Department
from deps import get_current_user, require_approver, get_user_permissions, check_scope
from workflow import validate_transition, apply_transition

router = APIRouter(prefix='/api/delete-request', tags=['delete-request'])
TABLE_MAP = {'it_assets': ITAsset, 'phone_assets': PhoneAsset, 'medical_assets': MedicalAsset,
             'phone_numbers': PhoneNumber, 'scrap_requests': ScrapRequest, 'transfer_records': TransferRecord}
ASSET_MAP = {'it': ITAsset, 'phone': PhoneAsset, 'medical': MedicalAsset}


def request_in_scope(item, user, db):
    if user.role == 'super_admin' or user.data_scope == 'all':
        return True
    return bool(user.department_id and item.department_id == user.department_id)


def is_self_request(item, user):
    return item.applicant_id == user.id or (not item.applicant_id and item.applicant == user.name)


def pending_request(item_id, db, user):
    item = db.get(DeleteRequest, item_id)
    if not item:
        raise HTTPException(404, '申请不存在')
    if not request_in_scope(item, user, db):
        raise HTTPException(403, '只能审批本部门申请')
    if item.status != 'pending':
        raise HTTPException(409, '申请已处理，请刷新后重试')
    if is_self_request(item, user):
        raise HTTPException(400, '不能审批自己提交的申请')
    return item


class DeleteReqIn(BaseModel):
    table_name: str
    record_id: int = 0
    record_desc: str
    reason: str
    applicant: Optional[str] = None
    application_type: Optional[Literal['checkout', 'transfer', 'scrap']] = None
    target_user: Optional[str] = None
    target_department_id: Optional[int] = None
    asset_type: Optional[str] = None
    asset_id: Optional[int] = None


@router.get('')
def list_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(DeleteRequest)
    if 'approval' not in get_user_permissions(current_user, db):
        query = query.filter(DeleteRequest.applicant_id == current_user.id)
    elif current_user.role != 'super_admin' and current_user.data_scope != 'all':
        query = query.filter(DeleteRequest.department_id == current_user.department_id) if current_user.department_id else query.filter(False)
    rows = query.order_by(DeleteRequest.id.desc()).all()
    departments = {d.id: d.name for d in db.query(Department).all()}
    return [dict({c.name: getattr(row, c.name) for c in DeleteRequest.__table__.columns},
                 department=departments.get(row.target_department_id or row.department_id)) for row in rows]


@router.post('')
def create_request(data: DeleteReqIn, db: Session = Depends(get_write_db), current_user: User = Depends(get_current_user)):
    values = data.dict()
    if data.table_name == 'apply_requests':
        if 'apply' not in get_user_permissions(current_user, db):
            raise HTTPException(403, '没有设备申请权限')
        if not data.application_type:
            # Decode old clients only at the input boundary; new requests use typed fields.
            parts = data.reason.split('|')
            if len(parts) != 5 or parts[0] not in ('checkout', 'transfer', 'scrap'):
                raise HTTPException(400, '请提供有效的结构化设备申请')
            try:
                values.update(application_type=parts[0], target_user=parts[1], asset_type=parts[3], asset_id=int(parts[4]))
            except ValueError:
                raise HTTPException(400, '申请资产无效')
            target = db.query(Department).filter(Department.name == parts[2]).first() if parts[2] else None
            if parts[2] and not target:
                raise HTTPException(400, '申请目标部门不存在')
            values['target_department_id'] = target.id if target else None
        model = ASSET_MAP.get(values['asset_type'])
        record = db.get(model, values['asset_id']) if model and values['asset_id'] else None
        if not record:
            raise HTTPException(404, '申请资产不存在')
        validate_transition(db, record, values['application_type'], current_user, values['target_user'], values['target_department_id'])
    else:
        if data.table_name not in TABLE_MAP:
            raise HTTPException(400, '不允许申请删除该类型记录')
        if 'assets_write' not in get_user_permissions(current_user, db):
            raise HTTPException(403, '没有申请删除权限')
        record = db.get(TABLE_MAP[data.table_name], data.record_id)
        if not record:
            raise HTTPException(404, '记录不存在')
        if getattr(record, 'status', None) == 'archived':
            raise HTTPException(409, '资产已移出档案，无需重复申请')
        check_scope(record, current_user)
        for field in ('application_type', 'target_user', 'target_department_id', 'asset_type', 'asset_id'):
            values[field] = None
    values.update(applicant=current_user.name, applicant_id=current_user.id, department_id=record.department_id)
    item = DeleteRequest(**values)
    db.add(item)
    db.add(OperationLog(user=current_user.name, module='申请管理', action='提交申请', detail=data.record_desc))
    db.commit()
    db.refresh(item)
    return item


@router.put('/{item_id}/approve')
def approve_request(item_id: int, db: Session = Depends(get_write_db), current_user: User = Depends(require_approver)):
    item = pending_request(item_id, db, current_user)
    if item.table_name == 'apply_requests':
        model = ASSET_MAP.get(item.asset_type)
        asset = db.get(model, item.asset_id) if model and item.asset_id else None
        if not asset or not item.application_type:
            raise HTTPException(409, '申请资产或旧申请内容无效，请重新提交')
        target = validate_transition(db, asset, item.application_type, current_user, item.target_user, item.target_department_id)
        apply_transition(db, asset, item.asset_type, item.application_type, current_user, item.target_user, target, '设备申请审批通过')
        if item.application_type == 'scrap':
            db.add(ScrapRequest(request_number='SC-' + uuid4().hex, asset_desc=item.record_desc,
                asset_type=item.asset_type, asset_id=item.asset_id, applicant=item.applicant,
                applicant_id=item.applicant_id, department=asset.department, department_id=asset.department_id,
                reason=item.reason, status='approved', auditor=current_user.name, approver_id=current_user.id,
                submit_date=item.created_at.date(), approve_date=date.today()))
    else:
        model = TABLE_MAP.get(item.table_name)
        record = db.get(model, item.record_id) if model else None
        if not record:
            raise HTTPException(404, '申请对应的记录已不存在')
        check_scope(record, current_user)
        if item.table_name in ('it_assets', 'phone_assets', 'medical_assets', 'phone_numbers'):
            record.status = 'archived'  # preserve stable asset identity and audit history
        else:
            db.delete(record)
    item.status, item.approver, item.approver_id, item.approved_at = 'approved', current_user.name, current_user.id, datetime.now()
    db.add(OperationLog(user=current_user.name, module='审批管理', action='审批通过', detail=item.record_desc))
    db.commit()
    return item


@router.put('/{item_id}/reject')
def reject_request(item_id: int, db: Session = Depends(get_write_db), current_user: User = Depends(require_approver)):
    item = pending_request(item_id, db, current_user)
    item.status, item.approver, item.approver_id, item.approved_at = 'rejected', current_user.name, current_user.id, datetime.now()
    db.add(OperationLog(user=current_user.name, module='审批管理', action='审批驳回', detail=item.record_desc))
    db.commit()
    return item
