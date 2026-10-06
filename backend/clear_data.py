from database import SessionLocal
from models import *
db = SessionLocal()
for m in [TransferRecord, ScrapRequest, DeleteRequest, OperationLog, ITAsset, PhoneAsset, MedicalAsset, PhoneNumber]:
    db.query(m).delete()
db.commit()
print('清空完成，保留了用户和部门数据')
