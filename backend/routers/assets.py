from datetime import date
from typing import Literal, Optional

from database import get_db, get_write_db
from deps import (
    can_view_medical,
    check_scope,
    require_any,
    require_medical_view,
    require_perm,
    scope_query,
)
from fastapi import APIRouter, Depends, HTTPException
from medical_dates import validate_calibration_dates
from models import Department, ITAsset, MedicalAsset, OperationLog, PhoneAsset, PhoneNumber, User
from numbering import next_asset_number
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/assets", tags=["assets"])


# ===== IT 设备 =====
class ITAssetIn(BaseModel):
    asset_number: Optional[str] = None
    name: str
    model: Optional[str] = None
    category: Optional[str] = None
    user_name: Optional[str] = None
    department: Optional[str] = None
    status: str = "idle"
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    price: Optional[float] = None
    notes: Optional[str] = None


def sync_department_id(db, item):
    department = (
        db.query(Department).filter(Department.name == item.department).first()
        if item.department
        else None
    )
    if item.department and not department:
        raise HTTPException(400, "部门不存在")
    item.department_id = department.id if department else None


def update_asset_fields(db, item, data, user, user_field):
    """Merge submitted fields; only an explicit null clears an optional value."""
    # Authorize the original owner before accepting a new department in the payload.
    check_scope(item, user)
    values = data.model_dump(exclude_unset=True)
    identity = "asset_number" if hasattr(item, "asset_number") else "number"
    if identity in values:
        value = values[identity]
        if not value or not value.strip():
            raise HTTPException(400, "编号或号码不能为空")
        model = type(item)
        if (
            db.query(model.id)
            .filter(getattr(model, identity) == value, model.id != item.id)
            .first()
        ):
            raise HTTPException(409, "编号或号码已存在")
    final_user = values.get(user_field, getattr(item, user_field))
    requested_status = values.get("status", item.status)
    values["status"] = (
        requested_status
        if isinstance(item, PhoneNumber) and requested_status in ("cancelled", "unused")
        else ("in_use" if final_user else "idle")
    )
    for key, value in values.items():
        setattr(item, key, value)
    sync_department_id(db, item)
    check_scope(item, user)
    if isinstance(item, PhoneAsset):
        item.revision += 1


@router.get("/it")
def list_it(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_any(
            "assets",
            "assets_write",
            "import",
            "export",
            "reports",
            "idle",
            "scrapped",
            "apply",
            "transfer",
            "scrap",
            "scrap_apply",
            "approval",
        )
    ),
):
    return scope_query(db.query(ITAsset), ITAsset, current_user).all()


@router.post("/it")
def create_it(
    data: ITAssetIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_perm("assets_write")),
):
    number = data.asset_number or next_asset_number(db, ITAsset, "IT")
    if data.user_name:
        data.status = "in_use"
    if db.query(ITAsset).filter(ITAsset.asset_number == number).first():
        raise HTTPException(409, "资产编号已存在")
    item = ITAsset(
        asset_number=number, **{k: v for k, v in data.model_dump().items() if k != "asset_number"}
    )
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(item)
    db.add(
        OperationLog(
            user=current_user.name, module="IT设备", action="新增", detail=f"新增设备 {number}"
        )
    )
    db.commit()
    db.refresh(item)
    return item


@router.put("/it/{item_id}")
def update_it(
    item_id: int,
    data: ITAssetIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_perm("assets_write")),
):
    item = (
        scope_query(db.query(ITAsset), ITAsset, current_user).filter(ITAsset.id == item_id).first()
    )
    if not item:
        raise HTTPException(404, "设备不存在")
    if item.status == "scrapped":
        raise HTTPException(400, "已报废设备不能直接编辑，如需恢复请走审批流程")
    update_asset_fields(db, item, data, current_user, "user_name")
    db.add(
        OperationLog(
            user=current_user.name,
            module="IT设备",
            action="编辑",
            detail=f"编辑设备 {item.asset_number}",
        )
    )
    db.commit()
    db.refresh(item)
    return item


# ===== 手机设备 =====
class PhoneAssetIn(BaseModel):
    quantity: int = Field(default=1, ge=1, le=100000, strict=True)
    asset_number: Optional[str] = None
    brand_model: str
    imei: Optional[str] = None
    bound_number: Optional[str] = None
    user_name: Optional[str] = None
    department: Optional[str] = None
    status: str = "idle"
    purchase_date: Optional[date] = None
    notes: Optional[str] = None


@router.get("/phone")
def list_phone(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_any(
            "assets",
            "assets_write",
            "import",
            "export",
            "reports",
            "idle",
            "scrapped",
            "apply",
            "transfer",
            "scrap",
            "scrap_apply",
            "approval",
        )
    ),
):
    return scope_query(db.query(PhoneAsset), PhoneAsset, current_user).all()


@router.post("/phone")
def create_phone(
    data: PhoneAssetIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_perm("assets_write")),
):
    number = data.asset_number or next_asset_number(db, PhoneAsset, "PH")
    if data.user_name:
        data.status = "in_use"
    if db.query(PhoneAsset).filter(PhoneAsset.asset_number == number).first():
        raise HTTPException(409, "资产编号已存在")
    if data.quantity > 1 and (data.imei or data.bound_number):
        raise HTTPException(400, "合并登记多台手机时不能填写单台 IMEI 或绑定号码，请拆分登记")
    item = PhoneAsset(
        asset_number=number, **{k: v for k, v in data.model_dump().items() if k != "asset_number"}
    )
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(item)
    db.add(
        OperationLog(
            user=current_user.name,
            module="手机设备",
            action="新增",
            detail=f"新增手机 {number}，数量 {item.quantity} 台",
        )
    )
    db.commit()
    db.refresh(item)
    return item


@router.put("/phone/{item_id}")
def update_phone(
    item_id: int,
    data: PhoneAssetIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_perm("assets_write")),
):
    item = (
        scope_query(db.query(PhoneAsset), PhoneAsset, current_user)
        .filter(PhoneAsset.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(404, "设备不存在")
    if item.status == "scrapped":
        raise HTTPException(400, "已报废设备不能直接编辑，如需恢复请走审批流程")
    quantity = data.quantity if "quantity" in data.model_fields_set else item.quantity
    if quantity > 1 and (
        (data.imei if "imei" in data.model_fields_set else item.imei)
        or (data.bound_number if "bound_number" in data.model_fields_set else item.bound_number)
    ):
        raise HTTPException(400, "合并登记多台手机时不能填写单台 IMEI 或绑定号码，请拆分登记")
    update_asset_fields(db, item, data, current_user, "user_name")
    db.add(
        OperationLog(
            user=current_user.name,
            module="手机设备",
            action="编辑",
            detail=f"编辑手机 {item.asset_number}，现有数量 {item.quantity} 台",
        )
    )
    db.commit()
    db.refresh(item)
    return item


# ===== 医疗设备 =====
class MedicalAssetIn(BaseModel):
    asset_number: Optional[str] = None
    name: str
    model: Optional[str] = None
    department: Optional[str] = None
    keeper: Optional[str] = None
    calibration_date: Optional[date] = None
    calibration_expiry: Optional[date] = None
    status: str = "idle"
    warranty_expiry: Optional[str] = None
    purchase_date: Optional[date] = None
    use_years: Optional[float] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def valid_calibration_period(self):
        validate_calibration_dates(self.calibration_date, self.calibration_expiry)
        return self


@router.get("/medical")
def list_medical(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_any(
            "assets",
            "assets_write",
            "import",
            "export",
            "reports",
            "idle",
            "scrapped",
            "apply",
            "transfer",
            "scrap",
            "scrap_apply",
            "approval",
        )
    ),
):
    require_medical_view(current_user)
    return scope_query(db.query(MedicalAsset), MedicalAsset, current_user).all()


@router.post("/medical")
def create_medical(
    data: MedicalAssetIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_perm("assets_write")),
):
    number = data.asset_number or next_asset_number(db, MedicalAsset, "MED")
    if data.keeper:
        data.status = "in_use"
    if db.query(MedicalAsset).filter(MedicalAsset.asset_number == number).first():
        raise HTTPException(409, "资产编号已存在")
    item = MedicalAsset(
        asset_number=number, **{k: v for k, v in data.model_dump().items() if k != "asset_number"}
    )
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(item)
    db.add(
        OperationLog(
            user=current_user.name,
            module="医疗设备",
            action="新增",
            detail=f"新增医疗设备 {number}",
        )
    )
    db.commit()
    db.refresh(item)
    return item


@router.put("/medical/{item_id}")
def update_medical(
    item_id: int,
    data: MedicalAssetIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_perm("assets_write")),
):
    item = (
        scope_query(db.query(MedicalAsset), MedicalAsset, current_user)
        .filter(MedicalAsset.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(404, "设备不存在")
    if item.status == "scrapped":
        raise HTTPException(400, "已报废设备不能直接编辑，如需恢复请走审批流程")
    try:
        validate_calibration_dates(
            data.calibration_date
            if "calibration_date" in data.model_fields_set
            else item.calibration_date,
            data.calibration_expiry
            if "calibration_expiry" in data.model_fields_set
            else item.calibration_expiry,
        )
    except ValueError as error:
        raise HTTPException(400, str(error))
    update_asset_fields(db, item, data, current_user, "keeper")
    db.add(
        OperationLog(
            user=current_user.name,
            module="医疗设备",
            action="编辑",
            detail=f"编辑医疗设备 {item.asset_number}",
        )
    )
    db.commit()
    db.refresh(item)
    return item


# ===== 电话号码 =====
class PhoneNumberIn(BaseModel):
    number: str = Field(..., max_length=11, description="电话号码，最多11个字符")
    carrier: Optional[str] = None
    card_type: Optional[str] = None
    plan: Optional[str] = None
    department: Optional[str] = None
    user_name: Optional[str] = None
    bound_device: Optional[str] = None
    status: str = "idle"
    notes: Optional[str] = None


@router.get("/numbers")
def list_numbers(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_any(
            "assets",
            "assets_write",
            "import",
            "export",
            "reports",
            "idle",
            "scrapped",
            "apply",
            "transfer",
            "scrap",
            "scrap_apply",
            "approval",
        )
    ),
):
    return scope_query(db.query(PhoneNumber), PhoneNumber, current_user).all()


@router.post("/numbers")
def create_number(
    data: PhoneNumberIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_perm("assets_write")),
):
    if db.query(PhoneNumber).filter(PhoneNumber.number == data.number).first():
        raise HTTPException(400, f"号码 {data.number} 已存在")
    data.status = "in_use" if data.user_name else "idle"
    item = PhoneNumber(**data.model_dump())
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(item)
    db.add(
        OperationLog(
            user=current_user.name,
            module="电话号码",
            action="新增",
            detail=f"新增号码 {data.number}",
        )
    )
    db.commit()
    db.refresh(item)
    return item


@router.put("/numbers/{item_id}")
def update_number(
    item_id: int,
    data: PhoneNumberIn,
    db: Session = Depends(get_write_db),
    current_user: User = Depends(require_perm("assets_write")),
):
    item = (
        scope_query(db.query(PhoneNumber), PhoneNumber, current_user)
        .filter(PhoneNumber.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(404, "号码不存在")
    update_asset_fields(db, item, data, current_user, "user_name")
    db.add(
        OperationLog(
            user=current_user.name,
            module="电话号码",
            action="编辑",
            detail=f"编辑号码 {item.number}",
        )
    )
    db.commit()
    db.refresh(item)
    return item


# ===== 医疗设备到期提醒邮件 =====
@router.get("/medical/expiring")
def list_expiring(
    days: int = 30,
    reminder_type: Literal["expiry", "calibration"] = "expiry",
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_any(
            "assets", "reports", "idle", "scrapped", "apply", "transfer", "scrap", "approval"
        )
    ),
):
    require_medical_view(current_user)
    if not 1 <= days <= 365:
        raise HTTPException(400, "提醒天数必须在1至365之间")
    from notifier import get_expiring_medical

    return get_expiring_medical(db, days, current_user, reminder_type)


class ExpiryEmailIn(BaseModel):
    recipient_user_ids: list[int] = Field(min_length=1, max_length=100)


def require_global_notice_sender(user):
    require_medical_view(user)
    if user.role != "super_admin" and user.data_scope != "all":
        raise HTTPException(403, "发送全局到期提醒需要全部部门数据范围")


@router.get("/medical/notice-recipients")
def notice_recipients(
    db: Session = Depends(get_db), current_user: User = Depends(require_perm("assets_write"))
):
    require_global_notice_sender(current_user)
    from notifier import smtp_configured

    users = (
        db.query(User)
        .filter(User.is_active == 1, User.email.isnot(None), User.email != "")
        .order_by(User.id)
        .all()
    )
    return {
        "users": [
            {"id": u.id, "name": u.name, "email": u.email} for u in users if can_view_medical(u)
        ],
        "smtp_configured": smtp_configured(),
    }


@router.post("/medical/send-expiry-email")
def send_expiry_email(
    data: ExpiryEmailIn,
    days: int = 30,
    reminder_type: Literal["expiry", "calibration"] = "expiry",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_perm("assets_write")),
):
    require_global_notice_sender(current_user)
    if not 1 <= days <= 365:
        raise HTTPException(400, "提醒天数必须在1至365之间")
    ids = set(data.recipient_user_ids)
    users = (
        db.query(User)
        .filter(User.id.in_(ids), User.is_active == 1, User.email.isnot(None), User.email != "")
        .all()
    )
    if len(users) != len(ids):
        raise HTTPException(400, "所选用户已停用、被删除或未填写邮箱，请刷新收件人列表")
    if any(not can_view_medical(user) for user in users):
        raise HTTPException(403, "医疗提醒只能发送给医院、护理部及超级管理员")
    recipients = list(dict.fromkeys(u.email for u in users))
    from notifier import send_expiry_notice

    result = send_expiry_notice(db, days, recipients, reminder_type)
    db.add(
        OperationLog(
            user=current_user.name,
            module="邮件提醒",
            action="发送校准到期提醒" if reminder_type == "calibration" else "发送到期提醒",
            detail=f"到期提醒邮件，{result.get('count', 0)}台设备: {result.get('message', '')}",
        )
    )
    db.commit()
    return result
