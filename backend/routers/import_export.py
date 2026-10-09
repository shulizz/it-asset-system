from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from io import BytesIO
from datetime import date, datetime
from typing import Optional, List
from database import get_db
from models import (
    ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, WeChatAccount,
    Department, OperationLog, User
)
from deps import get_current_user, get_user_permissions

router = APIRouter(prefix="/api/ie", tags=["导入导出"])

# 模块配置：Excel列名 -> 模型字段名
MODULES = {
    "it": {
        "model": ITAsset,
        "label": "IT设备",
        "fields": [
            ("资产编号", "asset_number", False),
            ("设备名称", "name", True),
            ("型号", "model", False),
            ("类别", "category", False),
            ("使用人", "user_name", False),
            ("部门", "department", False),
            ("状态", "status", False),
            ("购入日期", "purchase_date", False),
            ("保修到期", "warranty_expiry", False),
            ("价格", "price", False),
            ("备注", "notes", False),
        ],
        "user_field": "user_name",
        "auto_number_prefix": "IT",
    },
    "phone": {
        "model": PhoneAsset,
        "label": "手机设备",
        "fields": [
            ("资产编号", "asset_number", False),
            ("品牌型号", "brand_model", True),
            ("IMEI", "imei", False),
            ("绑定号码", "bound_number", False),
            ("使用人", "user_name", False),
            ("部门", "department", False),
            ("状态", "status", False),
            ("购入日期", "purchase_date", False),
            ("备注", "notes", False),
        ],
        "user_field": "user_name",
        "auto_number_prefix": "PH",
    },
    "medical": {
        "model": MedicalAsset,
        "label": "医疗设备",
        "fields": [
            ("资产编号", "asset_number", False),
            ("设备名称", "name", True),
            ("型号", "model", False),
            ("科室", "department", False),
            ("保管人", "keeper", False),
            ("校准到期", "calibration_expiry", False),
            ("状态", "status", False),
            ("保修到期", "warranty_expiry", False),
            ("购入日期", "purchase_date", False),
            ("使用年限", "use_years", False),
            ("到期时间", "expiry_date", False),
            ("备注", "notes", False),
        ],
        "user_field": "keeper",
        "auto_number_prefix": "MED",
    },
    "number": {
        "model": PhoneNumber,
        "label": "电话号码",
        "fields": [
            ("电话号码", "number", True),
            ("运营商", "carrier", False),
            ("卡类型", "card_type", False),
            ("套餐", "plan", False),
            ("部门", "department", False),
            ("使用人", "user_name", False),
            ("绑定设备", "bound_device", False),
            ("状态", "status", False),
            ("备注", "notes", False),
        ],
        "user_field": "user_name",
        "auto_number_prefix": None,
    },
    "wechat": {
        "model": WeChatAccount,
        "label": "微信账号",
        "fields": [
            ("微信号", "wx_account", True),
            ("密码", "wx_password", False),
            ("实名人", "real_name", False),
            ("使用人", "user_name", False),
            ("用途", "purpose", False),
            ("状态", "status", False),
            ("备注", "notes", False),
        ],
        "user_field": "user_name",
        "auto_number_prefix": None,
    },
    "department": {
        "model": Department,
        "label": "部门",
        "fields": [
            ("部门名称", "name", True),
            ("负责人", "manager", False),
            ("备注", "note", False),
        ],
        "user_field": None,
        "auto_number_prefix": None,
    },
}


def _get_module(name: str):
    if name not in MODULES:
        raise HTTPException(404, f"未知模块: {name}")
    return MODULES[name]


def _authorize_module(module: str, user: User, db: Session):
    required = "departments" if module == "department" else "assets"
    if required not in get_user_permissions(user, db):
        raise HTTPException(403, f"没有「{required}」权限")


def _gen_asset_number(db, model, prefix):
    year = date.today().year
    count = db.query(model).filter(model.asset_number.like(f"{prefix}-{year}-%")).count()
    return f"{prefix}-{year}-{count+1:03d}"


def _parse_date(val):
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_float(val):
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


@router.get("/{module}/export")
def export_excel(
    module: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cfg = _get_module(module)
    _authorize_module(module, current_user, db)
    model = cfg["model"]
    rows = db.query(model).all()

    import openpyxl
    from urllib.parse import quote
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = cfg["label"]

    # 表头
    export_fields = [
        field for field in cfg["fields"]
        if not (module == "wechat" and field[1] == "wx_password")
    ]
    headers = [f[0] for f in export_fields]
    ws.append(headers)

    for row in rows:
        line = []
        for cn_name, field_name, _ in export_fields:
            v = getattr(row, field_name, None)
            if isinstance(v, date):
                v = v.strftime("%Y-%m-%d")
            line.append(v if v is not None else "")
        ws.append(line)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"{cfg['label']}_导出_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/{module}/template")
def download_template(
    module: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cfg = _get_module(module)
    _authorize_module(module, current_user, db)
    from urllib.parse import quote
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = cfg["label"]
    ws.append([f[0] for f in cfg["fields"]])
    # 加一行示例
    example = []
    for cn_name, field_name, required in cfg["fields"]:
        if field_name == "name" or field_name == "brand_model":
            example.append("示例：电脑")
        elif field_name == "number":
            example.append("13800000000")
        elif field_name == "wx_account":
            example.append("example_wx")
        elif field_name == "user_name" or field_name == "keeper":
            example.append("张三")
        elif field_name == "department":
            example.append("IT部")
        else:
            example.append("")
    ws.append(example)
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"{cfg['label']}_导入模板.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.post("/{module}/import")
async def import_excel(
    module: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cfg = _get_module(module)
    _authorize_module(module, current_user, db)
    model = cfg["model"]

    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(400, "只允许上传 .xlsx 文件")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "导入文件不能超过 10MB")
    import openpyxl
    try:
        wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
    except Exception:
        raise HTTPException(400, "无法读取文件，请上传 .xlsx 格式")

    ws = wb.active
    all_rows = list(ws.iter_rows(values_only=True))
    if len(all_rows) < 2:
        return {"imported": 0, "skipped": 0, "message": "文件中没有数据行"}

    # 建立 列索引 -> 字段名 映射
    header_row = all_rows[0]
    col_map = {}
    for idx, cell in enumerate(header_row):
        if cell is None:
            continue
        cn = str(cell).strip()
        for cn_name, field_name, required in cfg["fields"]:
            if cn == cn_name:
                col_map[idx] = field_name
                break

    required_fields = [(idx, fn) for idx, (cn, fn, req) in enumerate(cfg["fields"]) if req]
    # 找到必填列在 col_map 中的位置
    required_cn = [cn for cn, fn, req in cfg["fields"] if req]

    imported = 0
    skipped = 0
    errors = []

    for row_idx, row in enumerate(all_rows[1:], start=2):
        data = {}
        for idx, field_name in col_map.items():
            val = row[idx] if idx < len(row) else None
            if val == "":
                val = None
            data[field_name] = val

        # 校验必填
        missing = [cn for cn, fn, req in cfg["fields"] if req and not data.get(fn)]
        if missing:
            skipped += 1
            errors.append(f"第{row_idx}行：缺少必填字段 {','.join(missing)}")
            continue

        # 日期/数字类型转换
        for cn_name, field_name, _ in cfg["fields"]:
            if field_name in ("purchase_date", "warranty_expiry", "calibration_expiry", "expiry_date"):
                data[field_name] = _parse_date(data.get(field_name))
            elif field_name == "price" or field_name == "use_years":
                data[field_name] = _parse_float(data.get(field_name))

        # 去重检查
        unique_fields = {
            "it": "asset_number", "phone": "asset_number", "medical": "asset_number",
            "number": "number", "wechat": "wx_account", "department": "name",
        }
        uniq_field = unique_fields.get(module)
        if uniq_field and data.get(uniq_field):
            exists = db.query(model).filter(getattr(model, uniq_field) == data[uniq_field]).first()
            if exists:
                skipped += 1
                continue

        # 资产编号自动生成
        if cfg["auto_number_prefix"] and not data.get("asset_number"):
            data["asset_number"] = _gen_asset_number(db, model, cfg["auto_number_prefix"])

        # 自动状态：有使用人→in_use，无使用人→idle
        if cfg["user_field"]:
            has_user = bool(data.get(cfg["user_field"]))
            data["status"] = "in_use" if has_user else "idle"

        # 过滤掉模型中不存在的字段
        mapper = inspect(model).columns.keys()
        clean_data = {k: v for k, v in data.items() if k in mapper}

        try:
            item = model(**clean_data)
            db.add(item)
            db.add(OperationLog(user=current_user.name, module=cfg["label"], action="导入", detail=f"导入数据: {clean_data.get('asset_number') or clean_data.get('number') or clean_data.get('wx_account') or clean_data.get('name')}"))
            imported += 1
        except Exception as e:
            skipped += 1
            errors.append(f"第{row_idx}行：{str(e)[:100]}")

    db.commit()
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:20],
        "message": f"成功导入 {imported} 条，跳过 {skipped} 条"
    }
