from database import SessionLocal
from models import *
db = SessionLocal()
print('=== IT设备 ===')
for i in db.query(ITAsset).all():
    print(f'  {i.id} {i.asset_number} {i.name} status={i.status} user={i.user_name} dept={i.department}')
print('=== 手机 ===')
for i in db.query(PhoneAsset).all():
    print(f'  {i.id} {i.asset_number} {i.brand_model} status={i.status} user={i.user_name} dept={i.department}')
print('=== 医疗 ===')
for i in db.query(MedicalAsset).all():
    print(f'  {i.id} {i.asset_number} {i.name} status={i.status} keeper={i.keeper} dept={i.department}')
print('=== 部门 ===')
for d in db.query(Department).all():
    print(f'  {d.id} {d.name}')
print('=== 流转 ===')
for t in db.query(TransferRecord).all():
    print(f'  {t.id} {t.transfer_number} type={t.type} desc={t.asset_desc}')
print('=== 报废 ===')
for s in db.query(ScrapRequest).all():
    print(f'  {s.id} {s.request_number} status={s.status} type={s.asset_type} aid={s.asset_id}')
print('=== 申请 ===')
for r in db.query(DeleteRequest).filter(DeleteRequest.table_name=='apply_requests').all():
    print(f'  {r.id} status={r.status} reason={r.reason}')
