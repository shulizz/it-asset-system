from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, get_write_db
from models import Department, OperationLog, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, User, ScrapRequest, TransferRecord, DeleteRequest
from deps import get_current_user, require_perm

router = APIRouter(prefix="/api/departments", tags=["departments"])

class DeptIn(BaseModel):
    name: str
    manager: Optional[str] = None
    note: Optional[str] = None

@router.get("")
def list_depts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Department).order_by(Department.id).all()
    return [{"id": r.id, "name": r.name, "manager": r.manager, "note": r.note} for r in rows]

@router.post("")
def create_dept(data: DeptIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("departments"))):
    if db.query(Department).filter(Department.name == data.name).first():
        raise HTTPException(400, "部门已存在")
    item = Department(name=data.name, manager=data.manager, note=data.note)
    db.add(item)
    db.add(OperationLog(user=current_user.name, module="部门管理", action="新增", detail=f"新增部门：{data.name}"))
    db.commit()
    db.refresh(item)
    return {"id": item.id, "name": item.name, "manager": item.manager, "note": item.note}

@router.put("/{dept_id}")
def update_dept(dept_id: int, data: DeptIn, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("departments"))):
    item = db.query(Department).get(dept_id)
    if not item:
        raise HTTPException(404, "部门不存在")
    if db.query(Department).filter(Department.name == data.name, Department.id != dept_id).first():
        raise HTTPException(400, "部门已存在")
    old_name = item.name
    item.name = data.name
    item.manager = data.manager
    item.note = data.note
    for model in [User, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, ScrapRequest, TransferRecord]:
        db.query(model).filter(model.department_id == item.id).update({model.department: data.name})
        db.query(model).filter(model.department_id.is_(None), model.department == old_name).update({model.department: data.name, model.department_id: item.id})
    db.query(TransferRecord).filter(TransferRecord.new_department_id == item.id).update({TransferRecord.new_dept: data.name})
    db.add(OperationLog(user=current_user.name, module="部门管理", action="编辑", detail=f"编辑部门：{old_name} → {data.name}"))
    db.commit()
    db.refresh(item)
    return {"id": item.id, "name": item.name, "manager": item.manager, "note": item.note}

@router.delete("/{dept_id}")
def delete_dept(dept_id: int, db: Session = Depends(get_write_db), current_user: User = Depends(require_perm("departments"))):
    item = db.query(Department).get(dept_id)
    if not item:
        raise HTTPException(404, "部门不存在")
    for model in [User, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber, ScrapRequest, TransferRecord, DeleteRequest]:
        if db.query(model).filter(model.department_id == item.id).first():
            raise HTTPException(409, '部门仍有关联用户、资产或历史记录，请迁移归属后保留此部门')
    if db.query(TransferRecord).filter(TransferRecord.new_department_id == item.id).first() or db.query(DeleteRequest).filter(DeleteRequest.target_department_id == item.id).first():
        raise HTTPException(409, '部门仍关联历史调拨或申请，不能删除')
    db.delete(item)
    db.add(OperationLog(user=current_user.name, module="部门管理", action="删除", detail=f"删除部门：{item.name}"))
    db.commit()
    return {"ok": True}
