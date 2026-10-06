from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Department, OperationLog, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber

router = APIRouter(prefix="/api/departments", tags=["departments"])

class DeptIn(BaseModel):
    name: str
    manager: Optional[str] = None
    note: Optional[str] = None

@router.get("")
def list_depts(db: Session = Depends(get_db)):
    rows = db.query(Department).order_by(Department.id).all()
    return [{"id": r.id, "name": r.name, "manager": r.manager, "note": r.note} for r in rows]

@router.post("")
def create_dept(data: DeptIn, db: Session = Depends(get_db)):
    if db.query(Department).filter(Department.name == data.name).first():
        raise HTTPException(400, "部门已存在")
    item = Department(name=data.name, manager=data.manager, note=data.note)
    db.add(item)
    db.add(OperationLog(user="admin", module="部门管理", action="新增", detail=f"新增部门：{data.name}"))
    db.commit()
    db.refresh(item)
    return {"id": item.id, "name": item.name, "manager": item.manager, "note": item.note}

@router.put("/{dept_id}")
def update_dept(dept_id: int, data: DeptIn, db: Session = Depends(get_db)):
    item = db.query(Department).get(dept_id)
    if not item:
        raise HTTPException(404, "部门不存在")
    item.name = data.name
    item.manager = data.manager
    item.note = data.note
    db.commit()
    db.refresh(item)
    return {"id": item.id, "name": item.name, "manager": item.manager, "note": item.note}

@router.delete("/{dept_id}")
def delete_dept(dept_id: int, db: Session = Depends(get_db)):
    item = db.query(Department).get(dept_id)
    if not item:
        raise HTTPException(404, "部门不存在")
    for model in [ITAsset, PhoneAsset, MedicalAsset, PhoneNumber]:
        db.query(model).filter(model.department == item.name).update({model.department: None})
    db.delete(item)
    db.add(OperationLog(user="admin", module="部门管理", action="删除", detail=f"删除部门：{item.name}"))
    db.commit()
    return {"ok": True}
