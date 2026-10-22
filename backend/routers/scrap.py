from datetime import date
from typing import Optional
from uuid import uuid4

from database import get_db, get_write_db
from deps import (
    check_scope,
    get_current_user,
    get_user_permissions,
    require_any,
    require_approver,
    scope_query,
)
from fastapi import APIRouter, Depends, HTTPException
from models import ITAsset, MedicalAsset, OperationLog, PhoneAsset, PhoneNumber, ScrapRequest, User
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from workflow import apply_transition, check_source_revision, validate_transition

router = APIRouter(prefix="/api/scrap", tags=["scrap"])

ASSET_MAP = {
    "it": ITAsset,
    "phone": PhoneAsset,
    "medical": MedicalAsset,
    "number": PhoneNumber,
}


class ScrapIn(BaseModel):
    quantity: int = Field(default=1, ge=1, le=100000, strict=True)
    request_number: Optional[str] = None
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
    if "approval" not in get_user_permissions(
        current_user, db
    ) and "scrap" not in get_user_permissions(current_user, db):
        query = query.filter(ScrapRequest.applicant_id == current_user.id)
    return scope_query(query, ScrapRequest, current_user).order_by(ScrapRequest.id.desc()).all()


@router.post("")
def create_scrap(
    data: ScrapIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_any("scrap_apply", "scrap", "apply")),
):
    model = ASSET_MAP.get(data.asset_type)
    if not model or not data.asset_id:
        raise HTTPException(400, "请选择有效资产")
    asset = db.query(model).get(data.asset_id)
    if not asset:
        raise HTTPException(404, "资产不存在")
    check_scope(asset, current_user)
    validate_transition(db, asset, "scrap", current_user, quantity=data.quantity)
    data.submit_date = date.today()
    data.applicant = current_user.name
    data.department = asset.department
    # The application and printed form must describe the asset actually selected.
    data.asset_desc = (
        f"{getattr(asset, 'asset_number', getattr(asset, 'number', ''))} "
        f"{getattr(asset, 'name', getattr(asset, 'brand_model', ''))}"
    ).strip()
    data.status = "pending_approval"
    data.auditor = None
    data.request_number = "SC-" + uuid4().hex
    item = ScrapRequest(
        **data.model_dump(),
        applicant_id=current_user.id,
        department_id=asset.department_id,
        source_revision=getattr(asset, "revision", None),
    )
    db.add(item)
    db.add(
        OperationLog(
            user=current_user.name, module="报废管理", action="发起申请", detail=data.asset_desc
        )
    )
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}/approve")
def approve_scrap(
    item_id: int,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_approver),
):
    item = db.get(ScrapRequest, item_id)
    if not item:
        raise HTTPException(404, "申请不存在")
    check_scope(item, current_user)
    if item.status != "pending_approval":
        raise HTTPException(
            400, f"申请已{'审批通过' if item.status == 'approved' else '已驳回'}，请勿重复操作"
        )
    if item.applicant_id == current_user.id or (
        not item.applicant_id and item.applicant == current_user.name
    ):
        raise HTTPException(400, "不能审批自己提交的申请")
    if not item.asset_type or not item.asset_id or item.asset_type not in ASSET_MAP:
        raise HTTPException(400, "申请缺少有效的资产信息")
    asset = db.query(ASSET_MAP[item.asset_type]).get(item.asset_id)
    if not asset:
        raise HTTPException(404, "申请对应的资产不存在")
    check_source_revision(asset, item.source_revision)
    validate_transition(db, asset, "scrap", current_user, quantity=item.quantity)
    item.status = "approved"
    item.approve_date = date.today()
    item.auditor, item.approver_id = current_user.name, current_user.id
    apply_transition(
        db,
        asset,
        item.asset_type,
        "scrap",
        current_user,
        notes="报废审批通过",
        quantity=item.quantity,
    )
    db.add(
        OperationLog(
            user=current_user.name, module="报废管理", action="审批通过", detail=item.asset_desc
        )
    )
    db.commit()
    return item


@router.put("/{item_id}/reject")
def reject_scrap(
    item_id: int,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_approver),
):
    item = db.get(ScrapRequest, item_id)
    if not item:
        raise HTTPException(404, "申请不存在")
    check_scope(item, current_user)
    if item.status != "pending_approval":
        raise HTTPException(400, "申请已处理，请勿重复操作")
    if item.applicant_id == current_user.id or (
        not item.applicant_id and item.applicant == current_user.name
    ):
        raise HTTPException(400, "不能审批自己提交的申请")
    item.status = "rejected"
    item.auditor, item.approver_id = current_user.name, current_user.id
    item.approve_date = date.today()
    db.add(
        OperationLog(
            user=current_user.name, module="报废管理", action="审批驳回", detail=item.asset_desc
        )
    )
    db.commit()
    return item
