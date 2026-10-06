import requests

# 登录
r = requests.post('http://localhost:8000/api/auth/login', json={'username':'admin','password':'admin123'})
print(f'login status={r.status_code} body={r.text[:200]}')
token = r.json()['token']
h = {'Authorization': f'Bearer {token}'}
print('1. 登录OK')

# 新增设备
r = requests.post('http://localhost:8000/api/assets/it', json={'name':'测试笔记本','category':'笔记本电脑'}, headers=h)
print(f'  status={r.status_code} body={r.text[:200]}')
new = r.json()
print(f'2. 新增设备响应: {new}')

tid = new['id']

# 领用
r = requests.post('http://localhost:8000/api/transfer', json={
    'transfer_number':'TR-TEST','type':'checkout',
    'asset_desc':f'{new["asset_number"]} 测试笔记本',
    'asset_type':'it','asset_id':tid,
    'new_user':'测试员','department':'IT部'
}, headers=h)
after = requests.get(f'http://localhost:8000/api/assets/it', headers=h).json()
asset = [a for a in after if a['id']==tid][0]
print(f'3. 领用后: 状态={asset["status"]} 使用人={asset["user_name"]} 部门={asset["department"]}')

# 归还
r = requests.post('http://localhost:8000/api/transfer', json={
    'transfer_number':'TR-TEST2','type':'return',
    'asset_desc':f'{new["asset_number"]} 测试笔记本',
    'asset_type':'it','asset_id':tid
}, headers=h)
after2 = requests.get(f'http://localhost:8000/api/assets/it', headers=h).json()
asset2 = [a for a in after2 if a['id']==tid][0]
print(f'4. 归还后: 状态={asset2["status"]} 使用人={asset2["user_name"]} 部门={asset2["department"]}')

# 报废
r = requests.post('http://localhost:8000/api/scrap', json={
    'request_number':'SC-TEST','asset_desc':f'{new["asset_number"]} 测试笔记本',
    'asset_type':'it','asset_id':tid,
    'applicant':'admin','reason':'测试报废'
}, headers=h)
sc = r.json()
print(f'5. 报废申请: ID={sc["id"]} 状态={sc["status"]}')
r = requests.put(f'http://localhost:8000/api/scrap/{sc["id"]}/approve', headers=h)
after3 = requests.get(f'http://localhost:8000/api/assets/it', headers=h).json()
asset3 = [a for a in after3 if a['id']==tid][0]
print(f'6. 报废后: 状态={asset3["status"]}')

print('=== 流程测试完成 ===')
