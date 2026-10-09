from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# ===== 部门 =====
class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    manager = Column(String(50))
    note = Column(String(200))

# ===== 自定义角色 =====
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # 角色名称，如"设备科科长"
    permissions = Column(Text, default="")  # JSON数组，权限key列表

# ===== 用户 =====
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    name = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)  # 角色名，关联 Role.name，或 super_admin
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True, index=True)
    permissions = Column(Text, nullable=True)
    data_scope = Column(String(20), nullable=False, default="department")
    department = Column(String(50))
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    is_active = Column(Integer, default=1)  # 1启用 0停用

# ===== IT设备 =====
class ITAsset(Base):
    __tablename__ = "it_assets"
    id = Column(Integer, primary_key=True, index=True)
    asset_number = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    model = Column(String(100))                     # 型号
    category = Column(String(50))                     # 笔记本/台式机/显示器/打印机/网络设备
    user_name = Column(String(50))                    # 使用人
    department = Column(String(50))                   # 部门
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    status = Column(String(20), default="in_use")     # in_use/idle/scrapped/archived
    purchase_date = Column(Date)
    warranty_expiry = Column(Date)
    price = Column(Float)
    notes = Column(Text)

# ===== 手机设备 =====
class PhoneAsset(Base):
    __tablename__ = "phone_assets"
    id = Column(Integer, primary_key=True, index=True)
    asset_number = Column(String(50), unique=True, index=True, nullable=False)
    brand_model = Column(String(100), nullable=False)
    imei = Column(String(50))
    bound_number = Column(String(20))               # 绑定号码
    user_name = Column(String(50))
    department = Column(String(50))
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    status = Column(String(20), default="in_use")
    purchase_date = Column(Date)
    notes = Column(Text)

# ===== 医疗设备 =====
class MedicalAsset(Base):
    __tablename__ = "medical_assets"
    id = Column(Integer, primary_key=True, index=True)
    asset_number = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    model = Column(String(100))
    department = Column(String(50))                   # 科室
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    keeper = Column(String(50))                       # 保管人
    calibration_expiry = Column(Date)                 # 校准到期日
    status = Column(String(20), default="in_use")
    warranty_expiry = Column(String(50))
    purchase_date = Column(Date)
    use_years = Column(Float)                         # 使用年限（年）
    expiry_date = Column(Date)                        # 设备到期时间
    notes = Column(Text)

# ===== 电话号码 =====
class PhoneNumber(Base):
    __tablename__ = "phone_numbers"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(20), unique=True, index=True, nullable=False)
    carrier = Column(String(20))                      # 移动/联通/电信
    card_type = Column(String(20))                    # main(主卡)/sub(副卡)/landline(座机)
    plan = Column(String(50))                         # 套餐
    department = Column(String(50))
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    user_name = Column(String(50))
    bound_device = Column(String(100))                # 绑定设备
    status = Column(String(20), default="in_use")     # in_use/idle/cancelled/unused
    notes = Column(Text)

# ===== 设备流转记录 =====
class TransferRecord(Base):
    __tablename__ = "transfer_records"
    id = Column(Integer, primary_key=True, index=True)
    transfer_number = Column(String(50), unique=True, index=True, nullable=False)
    type = Column(String(20), nullable=False)
    asset_desc = Column(String(200))
    asset_type = Column(String(20))
    asset_id = Column(Integer)
    operator = Column(String(50))
    counterparty = Column(String(100))
    department = Column(String(50))
    transfer_date = Column(Date)
    new_user = Column(String(50))
    new_dept = Column(String(50))
    notes = Column(Text)

# ===== 报废申请 =====
class ScrapRequest(Base):
    __tablename__ = "scrap_requests"
    id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String(50), unique=True, index=True, nullable=False)
    asset_desc = Column(String(200), nullable=False)
    asset_type = Column(String(20))  # it/phone/medical/number
    asset_id = Column(Integer)
    applicant = Column(String(50))
    department = Column(String(50))
    reason = Column(Text)
    status = Column(String(20), default="pending_approval")
    auditor = Column(String(50))
    submit_date = Column(Date)
    approve_date = Column(Date)
    notes = Column(Text)

# ===== 删除申请 =====
class DeleteRequest(Base):
    __tablename__ = "delete_requests"
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False)   # 从哪张表删
    record_id = Column(Integer, nullable=False)        # 删哪条
    record_desc = Column(String(200))                 # 记录描述
    reason = Column(Text, nullable=False)
    applicant = Column(String(50))
    status = Column(String(20), default="pending")     # pending/approved/rejected
    approver = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    approved_at = Column(DateTime)

# ===== 操作日志 =====
class OperationLog(Base):
    __tablename__ = "operation_logs"
    id = Column(Integer, primary_key=True, index=True)
    user = Column(String(50))
    module = Column(String(50))
    action = Column(String(50))
    detail = Column(Text)
    ip = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
# ===== 微信账号 =====
class WeChatAccount(Base):
    __tablename__ = "wechat_accounts"
    id = Column(Integer, primary_key=True, index=True)
    wx_account = Column(String(100), unique=True, index=True, nullable=False)
    wx_password = Column(Text)
    real_name = Column(String(50))
    user_name = Column(String(50))
    purpose = Column(String(200))
    status = Column(String(20), default="in_use")
    notes = Column(Text)
