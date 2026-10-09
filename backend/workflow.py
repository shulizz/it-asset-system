"""Shared rules for direct transfers and approval of device applications."""
from datetime import date
from uuid import uuid4
from fastapi import HTTPException
from deps import check_scope
from models import Department, TransferRecord


def asset_user(asset):
    return getattr(asset, 'user_name', getattr(asset, 'keeper', None))


def set_asset_user(asset, value):
    setattr(asset, 'user_name' if hasattr(asset, 'user_name') else 'keeper', value)


def validate_transition(db, asset, action, user, recipient=None, target_id=None):
    check_scope(asset, user)
    expected = {'checkout': {'idle'}, 'transfer': {'in_use'},
                'return': {'in_use'}, 'offboard': {'in_use'}, 'scrap': {'idle', 'in_use'}}
    if action not in expected or asset.status not in expected[action]:
        raise HTTPException(409, '资产当前状态不允许此操作，请刷新后重新申请')
    if action in ('checkout', 'transfer') and not (recipient or '').strip():
        raise HTTPException(400, '请填写接收人')
    target = db.get(Department, target_id) if target_id else None
    if target_id and not target:
        raise HTTPException(400, '目标部门已不存在')
    if target and user.role != 'super_admin' and user.data_scope != 'all' and target.id != user.department_id:
        raise HTTPException(403, '不能操作其他部门的目标归属')
    return target


def apply_transition(db, asset, asset_type, action, user, recipient=None, target=None, notes=None):
    record = TransferRecord(
        transfer_number='TR-' + uuid4().hex, type=action,
        asset_desc=f"{getattr(asset, 'asset_number', getattr(asset, 'number', ''))} {getattr(asset, 'name', getattr(asset, 'brand_model', ''))}",
        asset_type=asset_type, asset_id=asset.id, operator=user.name, operator_id=user.id,
        counterparty=recipient or asset_user(asset), department=asset.department,
        department_id=asset.department_id, old_user=asset_user(asset),
        new_user=recipient if action in ('checkout', 'transfer') else None,
        new_dept=target.name if target else asset.department,
        new_department_id=target.id if target else asset.department_id,
        transfer_date=date.today(), notes=notes,
    )
    if action in ('checkout', 'transfer'):
        asset.status = 'in_use'
        set_asset_user(asset, recipient.strip())
        if target:
            asset.department, asset.department_id = target.name, target.id
    else:
        asset.status = 'scrapped' if action == 'scrap' else 'idle'
        set_asset_user(asset, None)
    db.add(record)
    return record
