from database import get_db
from deps import can_view_fire, can_view_medical, require_perm
from fastapi import APIRouter, Depends
from models import OperationLog
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
def list_logs(db: Session = Depends(get_db), user=Depends(require_perm("logs"))):
    query = db.query(OperationLog)
    if not can_view_fire(user):
        # Untyped mixed workflow logs can contain fire equipment names in free text.
        query = query.filter(
            OperationLog.module.in_(
                ["IT设备", "手机设备", "医疗设备", "电话号码", "微信账号", "部门管理", "权限管理"]
            )
        )
    if not can_view_medical(user):
        # Legacy workflow logs have no asset-type field; only demonstrably non-medical
        # modules can be disclosed without revealing medical names in free-text details.
        query = query.filter(
            OperationLog.module.in_(
                ["IT设备", "手机设备", "电话号码", "微信账号", "部门管理", "权限管理"]
            )
        )
    return query.order_by(OperationLog.id.desc()).limit(100).all()
