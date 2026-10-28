import json
import os

from database import get_db
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from models import Department, ScrapRequest, TransferRecord, User
from permissions import GLOBAL_PERMISSIONS, PERMISSION_KEYS
from sqlalchemy.orm import Session, object_session

SECRET_KEY = os.getenv("IT_ASSET_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "it-asset-secret-key-change-in-production":
    raise RuntimeError("IT_ASSET_SECRET_KEY must be configured with a strong secret")
ALGORITHM = "HS256"

security = HTTPBearer()


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)
):
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(401, "无效登录")
    except JWTError:
        raise HTTPException(401, "登录已过期，请重新登录")
    user = db.query(User).filter(User.username == username, User.is_active == 1).first()
    if not user:
        raise HTTPException(401, "用户不存在或已停用")
    if payload.get("ver") != (user.token_version or 0) or payload.get("uid") != user.id:
        raise HTTPException(401, "登录状态已失效，请重新登录")
    return user


def get_user_permissions(user: User, db: Session) -> list:
    """获取用户权限列表"""
    if user.role == "super_admin":
        return sorted(PERMISSION_KEYS | {"users"})
    if user.permissions is not None:
        try:
            permissions = json.loads(user.permissions)
            if not isinstance(permissions, list):
                return []
            return sorted(
                PERMISSION_KEYS.intersection(p for p in permissions if isinstance(p, str))
            )
        except (ValueError, TypeError):
            return []
    return []


def require_perm(perm: str):
    """权限依赖工厂：要求用户拥有指定权限"""

    def checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        perms = get_user_permissions(user, db)
        if perm not in perms:
            raise HTTPException(403, f"没有「{perm}」权限")
        if perm in GLOBAL_PERMISSIONS and user.role != "super_admin" and user.data_scope != "all":
            raise HTTPException(403, "此权限需要全部部门数据范围")
        return user

    return checker


# 兼容旧代码


def require_approver(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    perms = get_user_permissions(user, db)
    if "approval" not in perms:
        raise HTTPException(403, "没有审批权限")
    return user


def require_super_admin(user: User = Depends(get_current_user)):
    if user.role != "super_admin":
        raise HTTPException(403, "需要超级管理员权限")
    return user


def can_view_fire(user):
    return user.role == "super_admin" or (
        user.data_scope == "all" and "fire" in get_user_permissions(user, None)
    )


def require_fire_view(user):
    if not can_view_fire(user):
        raise HTTPException(403, "需要超级管理员或明确分配的消防设备管理权限")


def is_fire_record(item):
    return (
        getattr(item, "__tablename__", "") == "fire_assets"
        or getattr(item, "asset_type", None) == "fire"
        or getattr(item, "table_name", None) == "fire_assets"
    )


def can_view_medical(user):
    # Ordinary role names are display labels and must never grant administrator access.
    if user.role == "super_admin":
        return True
    db = object_session(user)
    department = db.get(Department, user.department_id) if db and user.department_id else None
    return bool(department and department.medical_access)


def require_medical_view(user):
    if not can_view_medical(user):
        raise HTTPException(403, "医疗设备仅医院、护理部及超级管理员可查看")


def check_medical_record(item, user):
    if is_fire_record(item):
        require_fire_view(user)
    if (
        getattr(item, "__tablename__", "") == "medical_assets"
        or getattr(item, "asset_type", None) == "medical"
        or getattr(item, "table_name", None) == "medical_assets"
    ):
        require_medical_view(user)


def filter_medical_records(query, model, user):
    # Older deletion requests may lack asset_type; resolve their history source in SQL.
    if getattr(model, "__tablename__", "") == "delete_requests":
        if user.role != "super_admin":
            for source in (ScrapRequest, TransferRecord):
                source_exists = (
                    query.session.query(source.id).filter(source.id == model.record_id).exists()
                )
                query = query.filter(
                    ~(
                        (model.table_name == source.__tablename__)
                        & model.asset_type.is_(None)
                        & ~source_exists
                    )
                )
        for kind, allowed in (("medical", can_view_medical(user)), ("fire", can_view_fire(user))):
            if not allowed:
                for source in (ScrapRequest, TransferRecord):
                    sensitive_source = (
                        query.session.query(source.id)
                        .filter(source.id == model.record_id, source.asset_type == kind)
                        .exists()
                    )
                    query = query.filter(
                        ~((model.table_name == source.__tablename__) & sensitive_source)
                    )
    if not can_view_fire(user):
        if getattr(model, "__tablename__", "") == "fire_assets":
            return query.filter(False)
        if hasattr(model, "asset_type"):
            query = query.filter((model.asset_type.is_(None)) | (model.asset_type != "fire"))
        if hasattr(model, "table_name"):
            query = query.filter(model.table_name != "fire_assets")
    if can_view_medical(user):
        return query
    if getattr(model, "__tablename__", "") == "medical_assets":
        return query.filter(False)
    if hasattr(model, "asset_type"):
        query = query.filter((model.asset_type.is_(None)) | (model.asset_type != "medical"))
    if hasattr(model, "table_name"):
        query = query.filter(model.table_name != "medical_assets")
    return query


def scope_query(query, model, user):
    query = filter_medical_records(query, model, user)
    if hasattr(model, "asset_number") or getattr(model, "__tablename__", "") == "phone_numbers":
        query = query.filter(model.status != "archived")
    if user.role == "super_admin" or user.data_scope in ("all", "all_read_dept_write"):
        return query
    if not user.department_id:
        return query.filter(False)
    if hasattr(model, "department_id"):
        if hasattr(model, "new_department_id"):
            return query.filter(
                (model.department_id == user.department_id)
                | (model.new_department_id == user.department_id)
            )
        return query.filter(model.department_id == user.department_id)
    if hasattr(model, "department"):
        return query.filter(model.department == user.department)
    return query.filter(False)


def check_scope(item, user):
    check_medical_record(item, user)
    if user.role == "super_admin" or user.data_scope == "all":
        return
    item_department_id = getattr(item, "department_id", None)
    same_legacy_department = (
        not item_department_id and getattr(item, "department", None) == user.department
    )
    if not user.department_id or (
        item_department_id != user.department_id and not same_legacy_department
    ):
        raise HTTPException(403, "只能操作本部门数据")


def require_any(*permissions):
    def checker(user=Depends(get_current_user), db: Session = Depends(get_db)):
        if not set(permissions).intersection(get_user_permissions(user, db)):
            raise HTTPException(403, "没有访问权限")
        return user

    return checker
