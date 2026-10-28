"""Shared rules for direct transfers and approval of device applications."""

from datetime import date
from uuid import uuid4

from deps import check_scope
from fastapi import HTTPException
from models import Department, PhoneAsset, TransferRecord
from numbering import next_asset_number


def asset_user(asset):
    return getattr(asset, "user_name", getattr(asset, "keeper", None))


def set_asset_user(asset, value):
    setattr(asset, "user_name" if hasattr(asset, "user_name") else "keeper", value)


def validate_quantity(asset, quantity):
    available = asset.quantity if isinstance(asset, PhoneAsset) else 1
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise HTTPException(400, "数量必须是正整数")
    if quantity > available:
        raise HTTPException(409, "本次数量超过设备现有数量，请刷新后重新申请")


def check_source_revision(asset, revision):
    if hasattr(asset, "revision") and (revision is None or asset.revision != revision):
        raise HTTPException(409, "资产已变更或旧申请缺少版本信息，请驳回旧申请并重新提交")


def validate_transition(db, asset, action, user, recipient=None, target_id=None, quantity=1):
    check_scope(asset, user)
    validate_quantity(asset, quantity)
    expected = {
        "checkout": {"idle"},
        "transfer": {"in_use"},
        "return": {"in_use"},
        "offboard": {"in_use"},
        "scrap": {"idle", "in_use"},
    }
    if action not in expected or asset.status not in expected[action]:
        raise HTTPException(409, "资产当前状态不允许此操作，请刷新后重新申请")
    if action in ("checkout", "transfer") and not (recipient or "").strip():
        raise HTTPException(400, "请填写接收人")
    target = db.get(Department, target_id) if target_id else None
    if target_id and not target:
        raise HTTPException(400, "目标部门已不存在")
    if (
        target
        and user.role != "super_admin"
        and user.data_scope != "all"
        and target.id != user.department_id
    ):
        raise HTTPException(403, "不能操作其他部门的目标归属")
    return target


def apply_transition(
    db, asset, asset_type, action, user, recipient=None, target=None, notes=None, quantity=1
):
    validate_quantity(asset, quantity)
    source = asset
    # Keep the unprocessed remainder at its original owner/status; split only at execution.
    if isinstance(asset, PhoneAsset) and quantity < asset.quantity:
        asset.quantity -= quantity
        values = {
            column.name: getattr(asset, column.name)
            for column in PhoneAsset.__table__.columns
            if column.name not in {"id", "asset_number", "quantity"}
        }
        asset = PhoneAsset(
            asset_number=next_asset_number(db, PhoneAsset, "PH"), quantity=quantity, **values
        )
        db.add(asset)
        db.flush()
    record = TransferRecord(
        transfer_number="TR-" + uuid4().hex,
        type=action,
        asset_desc=f"{getattr(asset, 'asset_number', getattr(asset, 'number', ''))} {getattr(asset, 'name', getattr(asset, 'brand_model', ''))}",
        asset_type=asset_type,
        asset_id=source.id,
        result_asset_id=asset.id,
        quantity=quantity,
        operator=user.name,
        operator_id=user.id,
        counterparty=recipient or asset_user(asset),
        department=asset.department,
        department_id=asset.department_id,
        old_user=asset_user(asset),
        new_user=recipient if action in ("checkout", "transfer") else None,
        new_dept=target.name if target else asset.department,
        new_department_id=target.id if target else asset.department_id,
        transfer_date=date.today(),
        notes=notes,
    )
    if action in ("checkout", "transfer"):
        asset.status = "in_use"
        set_asset_user(asset, recipient.strip())
        if target:
            asset.department, asset.department_id = target.name, target.id
    else:
        asset.status = "scrapped" if action == "scrap" else "idle"
        set_asset_user(asset, None)
    db.add(record)
    return record
