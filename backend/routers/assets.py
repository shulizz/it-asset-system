from numbering import next_asset_number
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from database import get_db, get_write_db
from models import ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, OperationLog, User, Department
from deps import get_current_user, require_perm, scope_query, check_scope, require_any

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

def gen_number(db, model, prefix):
    return next_asset_number(db, model, prefix)


def sync_department_id(db, item):
    department = db.query(Department).filter(Department.name == item.department).first() if item.department else None
    if item.department and not department:
        raise HTTPException(400, "部门不存在")
    item.department_id = department.id if department else None

@router.get("/it")
def list_it(db: Session = Depends(get_db), current_user: User = Depends(require_any("assets", "assets_write", "import", "export", "reports", "idle", "scrapped", "apply", "transfer", "scrap", "approval"))):
    return scope_query(db.query(ITAsset), ITAsset, current_user).all()

@router.post("/it")
def create_it(data: ITAssetIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("assets_write"))):
    number = data.asset_number or gen_number(db, ITAsset, "IT")
    if data.user_name:
        data.status = "in_use"
    if db.query(ITAsset).filter(ITAsset.asset_number == number).first():
        raise HTTPException(409, "资产编号已存在")
    item = ITAsset(asset_number=number, **{k:v for k,v in data.dict().items() if k != 'asset_number'})
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(item)
    db.add(OperationLog(user=current_user.name, module="IT设备", action="新增", detail=f"新增设备 {number}"))
    db.commit()
    db.refresh(item)
    return item

@router.put("/it/{item_id}")
def update_it(item_id: int, data: ITAssetIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("assets_write"))):
    item = scope_query(db.query(ITAsset), ITAsset, current_user).filter(ITAsset.id == item_id).first()
    if not item:
        raise HTTPException(404, "设备不存在")
    if item.status == "scrapped":
        raise HTTPException(400, "已报废设备不能直接编辑，如需恢复请走审批流程")
    if db.query(ITAsset).filter(ITAsset.asset_number == data.asset_number, ITAsset.id != item_id).first():
        raise HTTPException(400, f"资产编号 {data.asset_number} 已存在，不能重复")
    data.status = "in_use" if data.user_name else "idle"
    for k, v in data.dict().items():
        setattr(item, k, v)
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(OperationLog(user=current_user.name, module="IT设备", action="编辑", detail=f"编辑设备 {item.asset_number}"))
    db.commit()
    db.refresh(item)
    return item

# ===== 手机设备 =====
class PhoneAssetIn(BaseModel):
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
def list_phone(db: Session = Depends(get_db), current_user: User = Depends(require_any("assets", "assets_write", "import", "export", "reports", "idle", "scrapped", "apply", "transfer", "scrap", "approval"))):
    return scope_query(db.query(PhoneAsset), PhoneAsset, current_user).all()

@router.post("/phone")
def create_phone(data: PhoneAssetIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("assets_write"))):
    number = data.asset_number or gen_number(db, PhoneAsset, "PH")
    if data.user_name:
        data.status = "in_use"
    if db.query(PhoneAsset).filter(PhoneAsset.asset_number == number).first():
        raise HTTPException(409, "资产编号已存在")
    item = PhoneAsset(asset_number=number, **{k:v for k,v in data.dict().items() if k != 'asset_number'})
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(item)
    db.add(OperationLog(user=current_user.name, module="手机设备", action="新增", detail=f"新增手机 {number}"))
    db.commit()
    db.refresh(item)
    return item

@router.put("/phone/{item_id}")
def update_phone(item_id: int, data: PhoneAssetIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("assets_write"))):
    item = scope_query(db.query(PhoneAsset), PhoneAsset, current_user).filter(PhoneAsset.id == item_id).first()
    if not item:
        raise HTTPException(404, "设备不存在")
    if item.status == "scrapped":
        raise HTTPException(400, "已报废设备不能直接编辑，如需恢复请走审批流程")
    if db.query(PhoneAsset).filter(PhoneAsset.asset_number == data.asset_number, PhoneAsset.id != item_id).first():
        raise HTTPException(400, f"资产编号 {data.asset_number} 已存在")
    data.status = "in_use" if data.user_name else "idle"
    for k, v in data.dict().items():
        setattr(item, k, v)
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(OperationLog(user=current_user.name, module="手机设备", action="编辑", detail=f"编辑手机 {item.asset_number}"))
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
    calibration_expiry: Optional[date] = None
    status: str = "idle"
    warranty_expiry: Optional[str] = None
    purchase_date: Optional[date] = None
    use_years: Optional[float] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None

@router.get("/medical")
def list_medical(db: Session = Depends(get_db), current_user: User = Depends(require_any("assets", "assets_write", "import", "export", "reports", "idle", "scrapped", "apply", "transfer", "scrap", "approval"))):
    return scope_query(db.query(MedicalAsset), MedicalAsset, current_user).all()

@router.post("/medical")
def create_medical(data: MedicalAssetIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("assets_write"))):
    number = data.asset_number or gen_number(db, MedicalAsset, "MED")
    if data.keeper:
        data.status = "in_use"
    if db.query(MedicalAsset).filter(MedicalAsset.asset_number == number).first():
        raise HTTPException(409, "资产编号已存在")
    item = MedicalAsset(asset_number=number, **{k:v for k,v in data.dict().items() if k != 'asset_number'})
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(item)
    db.add(OperationLog(user=current_user.name, module="医疗设备", action="新增", detail=f"新增医疗设备 {number}"))
    db.commit()
    db.refresh(item)
    return item

@router.put("/medical/{item_id}")
def update_medical(item_id: int, data: MedicalAssetIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("assets_write"))):
    item = scope_query(db.query(MedicalAsset), MedicalAsset, current_user).filter(MedicalAsset.id == item_id).first()
    if not item:
        raise HTTPException(404, "设备不存在")
    if item.status == "scrapped":
        raise HTTPException(400, "已报废设备不能直接编辑，如需恢复请走审批流程")
    if db.query(MedicalAsset).filter(MedicalAsset.asset_number == data.asset_number, MedicalAsset.id != item_id).first():
        raise HTTPException(400, f"资产编号 {data.asset_number} 已存在")
    data.status = "in_use" if data.keeper else "idle"
    for k, v in data.dict().items():
        setattr(item, k, v)
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(OperationLog(user=current_user.name, module="医疗设备", action="编辑", detail=f"编辑医疗设备 {item.asset_number}"))
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
def list_numbers(db: Session = Depends(get_db), current_user: User = Depends(require_any("assets", "assets_write", "import", "export", "reports", "idle", "scrapped", "apply", "transfer", "scrap", "approval"))):
    return scope_query(db.query(PhoneNumber), PhoneNumber, current_user).all()

@router.post("/numbers")
def create_number(data: PhoneNumberIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("assets_write"))):
    if db.query(PhoneNumber).filter(PhoneNumber.number == data.number).first():
        raise HTTPException(400, f"号码 {data.number} 已存在")
    data.status = "in_use" if data.user_name else "idle"
    item = PhoneNumber(**data.dict())
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(item)
    db.add(OperationLog(user=current_user.name, module="电话号码", action="新增", detail=f"新增号码 {data.number}"))
    db.commit()
    db.refresh(item)
    return item

@router.put("/numbers/{item_id}")
def update_number(item_id: int, data: PhoneNumberIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("assets_write"))):
    item = scope_query(db.query(PhoneNumber), PhoneNumber, current_user).filter(PhoneNumber.id == item_id).first()
    if not item:
        raise HTTPException(404, "号码不存在")
    if item.status not in ("cancelled", "unused"):
        data.status = "in_use" if data.user_name else "idle"
    for k, v in data.dict().items():
        setattr(item, k, v)
    sync_department_id(db, item)
    check_scope(item, current_user)
    db.add(OperationLog(user=current_user.name, module="电话号码", action="编辑", detail=f"编辑号码 {item.number}"))
    db.commit()
    db.refresh(item)
    return item


# ===== 医疗设备到期提醒邮件 =====
@router.get("/medical/expiring")
def list_expiring(days: int = 30, db: Session = Depends(get_db), current_user: User = Depends(require_any("assets", "reports", "idle", "scrapped", "apply", "transfer", "scrap", "approval"))):
    from notifier import get_expiring_medical
    return get_expiring_medical(db, days, current_user)

@router.post("/medical/send-expiry-email")
def send_expiry_email(days: int = 30, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("assets_write"))):
    if current_user.role != 'super_admin' and current_user.data_scope != 'all':
        raise HTTPException(403, '发送全局到期提醒需要全部部门数据范围')
    from notifier import send_expiry_notice
    result = send_expiry_notice(db, days)
    db.add(OperationLog(user=current_user.name, module="邮件提醒", action="发送到期提醒",
                        detail=f"到期提醒邮件，{result.get('count',0)}台设备: {result.get('message','')}"))
    db.commit()
    return result


