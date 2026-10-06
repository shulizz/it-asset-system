from database import SessionLocal
from models import *
import sys
db = SessionLocal()
out = []
out.append('=== 1. 状态一致性检查 ===')
for m, name in [(ITAsset,'IT'), (PhoneAsset,'手机')]:
    for a in db.query(m).filter(m.status=='in_use').all():
        if not a.user_name:
            out.append(f'  问题: {name} {a.asset_number} {a.name or a.brand_model} 在用但无使用人')
for m, name in [(ITAsset,'IT'), (PhoneAsset,'手机')]:
    for a in db.query(m).filter(m.status=='idle').all():
        if a.user_name:
            out.append(f'  问题: {name} {a.asset_number} {a.name or a.brand_model} 闲置但有使用人={a.user_name}')
for m, name in [(ITAsset,'IT'), (PhoneAsset,'手机'), (MedicalAsset,'医疗')]:
    for a in db.query(m).filter(m.status=='scrapped').all():
        un = getattr(a, 'user_name', None) or getattr(a, 'keeper', None)
        if un or a.department:
            out.append(f'  问题: {name} {a.asset_number} 报废但还有 user={un} dept={a.department}')

out.append('=== 2. 部门引用检查 ===')
dept_names = [d.name for d in db.query(Department).all()]
out.append(f'  现有部门: {dept_names}')
for m, name in [(ITAsset,'IT'), (PhoneAsset,'手机'), (MedicalAsset,'医疗')]:
    for a in db.query(m).all():
        if a.department and a.department not in dept_names:
            out.append(f'  问题: {name} {a.asset_number} 部门="{a.department}" 不在部门列表')

out.append('=== 3. 报废记录完整性 ===')
for s in db.query(ScrapRequest).all():
    if not s.asset_type or not s.asset_id:
        out.append(f'  问题: 报废申请{s.id} 缺asset_type或asset_id')
    else:
        model_map = {'it':ITAsset,'phone':PhoneAsset,'medical':MedicalAsset}
        model = model_map.get(s.asset_type)
        if model:
            asset = db.query(model).get(s.asset_id)
            if not asset:
                out.append(f'  问题: 报废申请{s.id} 指向的设备不存在')
            elif asset.status != 'scrapped' and s.status == 'approved':
                out.append(f'  问题: 报废申请{s.id}已批准但设备状态={asset.status}')

out.append('=== 4. 申请记录检查 ===')
for r in db.query(DeleteRequest).filter(DeleteRequest.table_name=='apply_requests').all():
    parts = (r.reason or '').split('|')
    if len(parts) < 5:
        out.append(f'  问题: 申请{r.id} reason格式不对: {r.reason}')

out.append('=== 5. 数据统计 ===')
out.append(f'  IT设备: {db.query(ITAsset).count()}台 (在用{db.query(ITAsset).filter(ITAsset.status=="in_use").count()}, 闲置{db.query(ITAsset).filter(ITAsset.status=="idle").count()}, 报废{db.query(ITAsset).filter(ITAsset.status=="scrapped").count()})')
out.append(f'  手机: {db.query(PhoneAsset).count()}台 (在用{db.query(PhoneAsset).filter(PhoneAsset.status=="in_use").count()}, 闲置{db.query(PhoneAsset).filter(PhoneAsset.status=="idle").count()}, 报废{db.query(PhoneAsset).filter(PhoneAsset.status=="scrapped").count()})')
out.append(f'  医疗: {db.query(MedicalAsset).count()}台 (在用{db.query(MedicalAsset).filter(MedicalAsset.status=="in_use").count()}, 闲置{db.query(MedicalAsset).filter(MedicalAsset.status=="idle").count()}, 报废{db.query(MedicalAsset).filter(MedicalAsset.status=="scrapped").count()})')
out.append(f'  部门: {db.query(Department).count()}个')
out.append(f'  流转记录: {db.query(TransferRecord).count()}条')
out.append(f'  报废申请: {db.query(ScrapRequest).count()}条')
out.append(f'  用户: {db.query(User).count()}个')
out.append('=== 检查完成 ===')

with open('check_result.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(out))

