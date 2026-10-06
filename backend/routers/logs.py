from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import OperationLog

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("")
def list_logs(db: Session = Depends(get_db)):
    return db.query(OperationLog).order_by(OperationLog.id.desc()).limit(100).all()
