from database import get_db
from deps import require_perm
from fastapi import APIRouter, Depends
from models import OperationLog
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
def list_logs(db: Session = Depends(get_db), user=Depends(require_perm("logs"))):
    return db.query(OperationLog).order_by(OperationLog.id.desc()).limit(100).all()
