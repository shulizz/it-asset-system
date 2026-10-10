"""Run with python -m unittest discover -s backend/tests -v. Uses temporary synthetic data only."""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from datetime import date

workspace = tempfile.TemporaryDirectory(prefix='asset-regression-')
os.environ['IT_ASSET_DATABASE_URL'] = 'sqlite:///' + str(Path(workspace.name) / 'test.db').replace('\\', '/')
os.environ['IT_ASSET_SECRET_KEY'] = 'isolated-test-secret-never-use-in-production'
os.environ['IT_ASSET_BACKUP_DIR'] = str(Path(workspace.name) / 'backups')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from sqlalchemy import text, create_engine
import openpyxl
from main import app
from database import Base, SessionLocal, engine
from models import User, Role, Department, ITAsset, ScrapRequest, DeleteRequest, TransferRecord, WeChatAccount
from routers.auth import create_token, pwd_context
from credential_crypto import encrypt_credential, decrypt_credential
from migrations import migrate_workflow
from unittest.mock import patch
from models import MedicalAsset


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = pwd_context.hash('testing-password-123')

    def setUp(self):
        with SessionLocal() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.add_all([Department(id=1, name='甲部门'), Department(id=2, name='乙部门')])
            db.add_all([
                User(id=1, username='admin', name='管理员', role='super_admin', password_hash=self.password_hash, data_scope='all'),
                User(id=2, username='applicant', name='同名', role='', password_hash=self.password_hash, department='甲部门', department_id=1, permissions=json.dumps(['apply']), data_scope='department'),
                User(id=3, username='approver', name='同名', role='', password_hash=self.password_hash, department='甲部门', department_id=1, permissions=json.dumps(['approval', 'transfer', 'assets_write']), data_scope='department'),
                User(id=4, username='foreign', name='乙用户', role='', password_hash=self.password_hash, department='乙部门', department_id=2, permissions=json.dumps(['apply', 'approval']), data_scope='department'),
                User(id=5, username='report', name='报表员', role='', password_hash=self.password_hash, department='甲部门', department_id=1, permissions=json.dumps(['reports']), data_scope='department'),
            ])
            db.commit()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def headers(self, user_id):
        with SessionLocal() as db:
            u = db.get(User, user_id)
            return {'Authorization': 'Bearer ' + create_token(u.username, u.token_version or 0, u.id)}

    def test_user_email_create_update_clear_and_legacy_preserve(self):
        payload={'username':'mailuser','password':'testing-password-123','name':'邮箱用户','role':'','department':'甲部门','data_scope':'department','permissions':[], 'email':' test@qq.com '}
        response=self.client.post('/api/auth/users',headers=self.headers(1),json=payload)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['email'],'test@qq.com')
        user_id=response.json()['id']
        payload.pop('email');payload.pop('password')
        response=self.client.put(f'/api/auth/users/{user_id}',headers=self.headers(1),json=payload)
        self.assertEqual(response.json()['email'],'test@qq.com')
        payload['email']='not-an-email'
        self.assertEqual(self.client.put(f'/api/auth/users/{user_id}',headers=self.headers(1),json=payload).status_code,422)
        payload['email']=''
        self.assertIsNone(self.client.put(f'/api/auth/users/{user_id}',headers=self.headers(1),json=payload).json()['email'])

    def test_expiry_recipient_permissions_and_selected_delivery(self):
        with SessionLocal() as db:
            db.get(User,2).email='selected@qq.com'
            db.get(User,4).email='unselected@qq.com'
            db.add(MedicalAsset(asset_number='MAIL-TEST',name='<script>测试</script>',expiry_date=date.today(),status='in_use'))
            db.commit()
        self.assertEqual(self.client.get('/api/assets/medical/notice-recipients',headers=self.headers(3)).status_code,403)
        self.assertEqual(self.client.get('/api/assets/medical/notice-recipients').status_code,403)
        response=self.client.get('/api/assets/medical/notice-recipients',headers=self.headers(1))
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual({u['id'] for u in response.json()['users']},{2,4})
        with patch('notifier.send_email',return_value={'success':True,'message':'已发送'}) as mock:
            response=self.client.post('/api/assets/medical/send-expiry-email',headers=self.headers(1),json={'recipient_user_ids':[2,2]})
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(mock.call_args.args[0],['selected@qq.com'])
            self.assertIn('&lt;script&gt;',mock.call_args.args[2])
            self.assertNotIn('<script>',mock.call_args.args[2])
        with SessionLocal() as db:
            db.get(User,2).is_active=0;db.commit()
        with patch('notifier.send_email') as mock:
            response=self.client.post('/api/assets/medical/send-expiry-email',headers=self.headers(1),json={'recipient_user_ids':[2]})
            self.assertEqual(response.status_code,400)
            mock.assert_not_called()
        self.assertEqual(self.client.post('/api/assets/medical/send-expiry-email',headers=self.headers(1),json={'recipient_user_ids':[]}).status_code,422)

    def asset(self, department_id=1, status='idle', number=None):
        with SessionLocal() as db:
            asset = ITAsset(asset_number=number or f'TEST-{department_id}', name='测试设备', department_id=department_id,
                            department='甲部门' if department_id == 1 else '乙部门', status=status)
            db.add(asset); db.commit(); return asset.id

    def apply(self, asset_id, user_id=2, action='checkout'):
        return self.client.post('/api/delete-request', headers=self.headers(user_id), json={
            'table_name': 'apply_requests', 'record_desc': '测试申请', 'reason': '用途中包含|也应正常',
            'application_type': action, 'asset_type': 'it', 'asset_id': asset_id,
            'target_user': '接收人', 'target_department_id': 1 if user_id != 4 else 2,
        })

    def test_role_label_never_assigns_permissions(self):
        with SessionLocal() as db:
            db.add(Role(name='只读',permissions=json.dumps(['assets','assets_write'])));db.commit()
        response = self.client.post('/api/auth/users', headers=self.headers(1), json={
            'username': 'reader', 'password': 'reader-password-123', 'name': '只读用户',
            'role': '只读', 'department': '甲部门', 'data_scope': 'department'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['permissions'], [])
        self.assertIsNone(response.json()['role_id'])
        user_id=response.json()['id']
        payload={'username':'reader','name':'只读用户','role':'自定义岗位','department':'甲部门','data_scope':'department','permissions':['assets']}
        response=self.client.put(f'/api/auth/users/{user_id}',headers=self.headers(1),json=payload)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['role'],'自定义岗位')
        self.assertEqual(response.json()['permissions'],['assets'])
        payload.pop('permissions');payload['role']='修改名称'
        self.assertEqual(self.client.put(f'/api/auth/users/{user_id}',headers=self.headers(1),json=payload).json()['permissions'],['assets'])

    def test_retired_roles_and_superadmin_only_assignment(self):
        for method,path in [('get','/api/auth/roles'),('post','/api/auth/roles'),('put','/api/auth/roles/1'),('delete','/api/auth/roles/1')]:
            self.assertEqual(getattr(self.client,method)(path,headers=self.headers(1)).status_code,410)
            self.assertEqual(getattr(self.client,method)(path,headers=self.headers(3)).status_code,403)
        self.assertNotIn('roles',self.client.get('/api/auth/me',headers=self.headers(1)).json()['permissions'])
        payload={'username':'applicant','name':'同名','role':'超级管理员','department':'甲部门','data_scope':'all','permissions':['assets']}
        self.assertEqual(self.client.put('/api/auth/users/2',headers=self.headers(3),json=payload).status_code,403)
        self.assertEqual(self.client.put('/api/auth/users/2',headers=self.headers(1),json=payload).status_code,200)
        self.assertEqual(self.client.get('/api/auth/users',headers=self.headers(2)).status_code,403)

    def test_legacy_template_is_snapshotted_once_then_decoupled(self):
        from main import seed_admin
        from deps import get_user_permissions
        with SessionLocal() as db:
            legacy=Role(name='旧角色',permissions=json.dumps(['assets']));db.add(legacy);db.flush()
            user=db.get(User,2);user.role='旧角色';user.role_id=legacy.id;user.permissions=None;db.commit()
            self.assertEqual(get_user_permissions(user,db),[])
        seed_admin()
        with SessionLocal() as db:
            user=db.get(User,2);self.assertEqual(get_user_permissions(user,db),['assets'])
            db.get(Role,user.role_id).permissions=json.dumps(['assets','assets_write']);db.commit()
            self.assertEqual(get_user_permissions(user,db),['assets'])

    def test_global_permissions_rejected_for_department_scope(self):
        for permission in ['departments', 'logs', 'wechat']:
            with SessionLocal() as db:
                db.get(User, 2).permissions = json.dumps([permission]); db.commit()
            endpoint = '/api/logs' if permission == 'logs' else '/api/wechat' if permission == 'wechat' else '/api/departments'
            response = self.client.get(endpoint, headers=self.headers(2)) if permission != 'departments' else self.client.put(endpoint+'/2', headers=self.headers(2), json={'name': '篡改'})
            self.assertEqual(response.status_code, 403, response.text)
        response = self.client.put('/api/auth/users/2', headers=self.headers(1), json={
            'username': 'applicant', 'name': '同名', 'role': '', 'department': '甲部门', 'permissions': ['logs'], 'data_scope': 'department'})
        self.assertEqual(response.status_code, 400)

    def test_cross_department_approve_and_reject_denied(self):
        asset = self.asset(2)
        response = self.apply(asset, user_id=4)
        self.assertEqual(response.status_code, 200, response.text)
        for action in ['approve', 'reject']:
            result = self.client.put(f"/api/delete-request/{response.json()['id']}/{action}", headers=self.headers(3))
            self.assertEqual(result.status_code, 403, result.text)

    def test_scrapped_asset_cannot_be_resurrected(self):
        asset = self.asset(); req = self.apply(asset)
        self.assertEqual(req.status_code, 200, req.text)
        with SessionLocal() as db:
            db.get(ITAsset, asset).status = 'scrapped'; db.commit()
        result = self.client.put(f"/api/delete-request/{req.json()['id']}/approve", headers=self.headers(3))
        self.assertEqual(result.status_code, 409, result.text)
        with SessionLocal() as db:
            self.assertEqual(db.get(ITAsset, asset).status, 'scrapped')
            self.assertEqual(db.get(DeleteRequest, req.json()['id']).status, 'pending')

    def test_same_name_accounts_have_distinct_ownership(self):
        asset = self.asset(); req = self.apply(asset)
        self.assertEqual(req.status_code, 200, req.text)
        result = self.client.put(f"/api/delete-request/{req.json()['id']}/approve", headers=self.headers(3))
        self.assertEqual(result.status_code, 200, result.text)
        with SessionLocal() as db:
            self.assertEqual(db.get(DeleteRequest, req.json()['id']).approver_id, 3)

    def test_self_approval_denied_by_id_after_name_change(self):
        asset = self.asset(); req = self.apply(asset)
        with SessionLocal() as db:
            u = db.get(User, 2); u.name = '新姓名'; u.permissions = json.dumps(['approval']); db.commit()
        result = self.client.put(f"/api/delete-request/{req.json()['id']}/approve", headers=self.headers(2))
        self.assertEqual(result.status_code, 400, result.text)

    def test_concurrent_approval_applies_once(self):
        req = self.apply(self.asset()).json()
        headers = self.headers(3)
        def approve(_):
            with TestClient(app) as client:
                return client.put(f"/api/delete-request/{req['id']}/approve", headers=headers).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(approve, range(2))), [200, 409])
        with SessionLocal() as db:
            self.assertEqual(db.query(TransferRecord).count(), 1)

    def test_numbering_survives_deletion_and_manual_high_number(self):
        stem = f'IT-{date.today().year}-'
        self.asset(number=stem+'001')
        self.asset(number=stem+'003')
        payload = {'name': '新增', 'department': '甲部门'}
        result = self.client.post('/api/assets/it', headers=self.headers(3), json=payload)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['asset_number'], stem+'004')
        with SessionLocal() as db:
            db.delete(db.get(ITAsset, result.json()['id'])); db.commit()
        result = self.client.post('/api/assets/it', headers=self.headers(3), json=payload)
        self.assertEqual(result.json()['asset_number'], stem+'005')
        self.asset(number=stem+'099')
        result = self.client.post('/api/assets/it', headers=self.headers(3), json=payload)
        self.assertEqual(result.json()['asset_number'], stem+'100')

    def test_concurrent_number_generation_is_unique(self):
        headers=self.headers(3)
        def create(i):
            response=self.client.post('/api/assets/it', headers=headers, json={'name': f'设备{i}', 'department': '甲部门'})
            self.assertEqual(response.status_code, 200, response.text)
            return response.json()['asset_number']
        with ThreadPoolExecutor(max_workers=4) as pool:
            numbers=list(pool.map(create, range(6)))
        self.assertEqual(len(set(numbers)), 6)

    def test_department_rename_preserves_pending_and_history(self):
        asset=self.asset(); req=self.client.post('/api/scrap',headers=self.headers(2),json={'asset_desc':'测试','asset_type':'it','asset_id':asset})
        self.assertEqual(req.status_code,200,req.text)
        rename=self.client.put('/api/departments/1',headers=self.headers(1),json={'name':'甲部门新名'})
        self.assertEqual(rename.status_code,200,rename.text)
        result=self.client.put(f"/api/scrap/{req.json()['id']}/approve",headers=self.headers(3))
        self.assertEqual(result.status_code,200,result.text)
        history=self.client.get('/api/transfer',headers=self.headers(3)).json()
        self.assertEqual(history[0]['department_id'],1)
        self.assertEqual(history[0]['department'],'甲部门新名')
        self.assertEqual(history[0]['asset_id'],asset)
        delete=self.client.delete('/api/departments/1',headers=self.headers(1))
        self.assertEqual(delete.status_code,409)

    def test_transfer_records_before_and_after(self):
        asset=self.asset(status='in_use')
        with SessionLocal() as db:
            db.get(ITAsset,asset).user_name='原使用人';db.commit()
        result=self.client.post('/api/transfer',headers=self.headers(1),json={
            'transfer_number':'ignored-client-number','type':'transfer','asset_desc':'测试','asset_type':'it',
            'asset_id':asset,'new_user':'新使用人','new_dept':'乙部门'})
        self.assertEqual(result.status_code,200,result.text)
        data=result.json()
        self.assertEqual((data['department_id'],data['new_department_id'],data['old_user'],data['new_user']),(1,2,'原使用人','新使用人'))
        with SessionLocal() as db:
            db.get(User,4).permissions=json.dumps(['transfer']);db.commit()
        self.assertEqual(len(self.client.get('/api/transfer',headers=self.headers(4)).json()),1)

    def test_asset_removal_preserves_identity_and_hides_archive(self):
        asset=self.asset()
        request=self.client.post('/api/delete-request',headers=self.headers(3),json={
            'table_name':'it_assets','record_id':asset,'record_desc':'移出档案','reason':'重复档案'})
        self.assertEqual(request.status_code,200,request.text)
        approved=self.client.put(f"/api/delete-request/{request.json()['id']}/approve",headers=self.headers(1))
        self.assertEqual(approved.status_code,200,approved.text)
        with SessionLocal() as db:
            self.assertEqual(db.get(ITAsset,asset).status,'archived')
        self.assertEqual(self.client.get('/api/assets/it',headers=self.headers(3)).json(),[])
        edit=self.client.put(f'/api/assets/it/{asset}',headers=self.headers(3),json={'name':'恢复','department':'甲部门'})
        self.assertEqual(edit.status_code,404)
        request=self.client.post('/api/delete-request',headers=self.headers(3),json={
            'table_name':'it_assets','record_id':asset,'record_desc':'再次删除','reason':'重复'})
        self.assertEqual(request.status_code,409)

    def test_user_with_history_cannot_be_deleted(self):
        self.apply(self.asset())
        result=self.client.delete('/api/auth/users/2',headers=self.headers(1))
        self.assertEqual(result.status_code,409,result.text)

    def test_superadmin_can_save_existing_full_permission_list(self):
        me=self.client.get('/api/auth/me',headers=self.headers(1)).json()
        me['password']=''
        result=self.client.put('/api/auth/users/1',headers=self.headers(1),json=me)
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['role'],'super_admin')

    def test_password_reset_and_toggle_revoke_old_tokens(self):
        old=self.headers(2)
        update=self.client.put('/api/auth/users/2',headers=self.headers(1),json={
            'username':'applicant','name':'同名','role':'','department':'甲部门','permissions':['apply'],
            'data_scope':'department','password':'changed-password-123'})
        self.assertEqual(update.status_code,200,update.text)
        self.assertEqual(self.client.get('/api/auth/me',headers=old).status_code,401)
        fresh=self.headers(2)
        self.client.put('/api/auth/users/2/toggle',headers=self.headers(1))
        self.client.put('/api/auth/users/2/toggle',headers=self.headers(1))
        self.assertEqual(self.client.get('/api/auth/me',headers=fresh).status_code,401)

    def test_login_and_recreated_account_do_not_restore_deleted_session(self):
        login=self.client.post('/api/auth/login',json={'username':'report','password':'testing-password-123'})
        self.assertEqual(login.status_code,200,login.text)
        old={'Authorization':'Bearer '+login.json()['token']}
        self.assertEqual(self.client.get('/api/auth/me',headers=old).status_code,200)
        deleted=self.client.delete('/api/auth/users/5',headers=self.headers(1))
        self.assertEqual(deleted.status_code,200,deleted.text)
        recreated=self.client.post('/api/auth/users',headers=self.headers(1),json={
            'username':'report','name':'新账号','role':'','department':'甲部门','data_scope':'department',
            'permissions':['reports'],'password':'new-password-123'})
        self.assertEqual(recreated.status_code,200,recreated.text)
        self.assertEqual(self.client.get('/api/auth/me',headers=old).status_code,401)

    def test_reports_export_permission_scope_and_no_wechat(self):
        self.asset(1);self.asset(2)
        self.assertEqual(self.client.get('/api/reports/export',headers=self.headers(5)).status_code,403)
        with SessionLocal() as db:
            db.get(User,5).permissions=json.dumps(['reports','export']);db.commit()
        result=self.client.get('/api/reports/export',headers=self.headers(5))
        self.assertEqual(result.status_code,200,result.text if result.status_code!=200 else '')
        wb=openpyxl.load_workbook(BytesIO(result.content))
        self.assertNotIn('微信账号',wb.sheetnames)
        rows=list(wb[wb.sheetnames[0]].values)
        self.assertEqual(len(rows),2)
        self.assertIn('TEST-1',rows[1]);self.assertNotIn('TEST-2',rows[1])
        wb.close()

    def test_password_prefix_and_corrupt_row_are_isolated(self):
        value='enc:v1:hello'
        self.assertEqual(decrypt_credential(encrypt_credential(value)),value)
        with SessionLocal() as db:
            db.add_all([WeChatAccount(wx_account='valid',wx_password=encrypt_credential(value)),
                        WeChatAccount(wx_account='broken',wx_password='enc:v1:bad')]);db.commit()
        result=self.client.get('/api/wechat',headers=self.headers(1))
        self.assertEqual(result.status_code,200,result.text)
        bad=next(row for row in result.json() if row['wx_account']=='broken')
        self.assertIsNone(bad['wx_password']);self.assertIn('password_error',bad)

    def test_import_uses_shared_sequence_and_rejects_invalid_dates(self):
        self.asset(number=f'IT-{date.today().year}-003')
        wb=openpyxl.Workbook();ws=wb.active
        ws.append(['设备名称','部门','购入日期'])
        ws.append(['正确','甲部门','2026-10-09']);ws.append(['错误','甲部门','不是日期'])
        data=BytesIO();wb.save(data);wb.close()
        result=self.client.post('/api/ie/it/import',headers=self.headers(1),files={'file':('test.xlsx',data.getvalue())})
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual((result.json()['imported'],result.json()['skipped']),(1,1))
        self.assertIn('日期',result.json()['errors'][0])
        with SessionLocal() as db:
            self.assertEqual(db.query(ITAsset).filter(ITAsset.name=='正确').one().asset_number,f'IT-{date.today().year}-004')

    def test_import_rejects_excess_rows_and_upload_size(self):
        wb=openpyxl.Workbook();ws=wb.active;ws.cell(10002,1,'过多行')
        data=BytesIO();wb.save(data);wb.close()
        result=self.client.post('/api/ie/it/import',headers=self.headers(1),files={'file':('test.xlsx',data.getvalue())})
        self.assertEqual(result.status_code,413,result.text)
        result=self.client.post('/api/ie/it/import',headers=self.headers(1),files={'file':('test.xlsx',b'x'*(10*1024*1024+1))})
        self.assertEqual(result.status_code,413,result.text)


class MigrationTests(unittest.TestCase):
    def test_legacy_ids_are_unique_and_migration_runs_once(self):
        other=create_engine('sqlite:///'+str(Path(workspace.name)/'migration.db').replace('\\','/'))
        with other.begin() as conn:
            conn.execute(text('CREATE TABLE departments(id INTEGER PRIMARY KEY, name TEXT)'))
            conn.execute(text('CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT,name TEXT,role TEXT,password_hash TEXT,data_scope TEXT)'))
            conn.execute(text('CREATE TABLE transfer_records(id INTEGER PRIMARY KEY, department TEXT,new_dept TEXT,operator TEXT)'))
            conn.execute(text('CREATE TABLE scrap_requests(id INTEGER PRIMARY KEY,request_number TEXT,asset_desc TEXT,applicant TEXT,department TEXT,auditor TEXT)'))
            conn.execute(text('CREATE TABLE delete_requests(id INTEGER PRIMARY KEY,table_name TEXT,record_id INTEGER,reason TEXT,applicant TEXT,approver TEXT)'))
            for table in ['it_assets','phone_assets','medical_assets','phone_numbers']:
                conn.execute(text(f'CREATE TABLE {table}(id INTEGER PRIMARY KEY,asset_number TEXT,name TEXT,department TEXT,department_id INTEGER,status TEXT)'))
            conn.execute(text("INSERT INTO departments(id,name) VALUES(1,'旧部门')"))
            conn.execute(text("INSERT INTO users(id,username,name,role,password_hash,data_scope) VALUES(1,'one','重名','','x','all'),(2,'two','重名','','x','all'),(3,'unique','唯一','','x','all')"))
            conn.execute(text("INSERT INTO it_assets(id,asset_number,name,department,department_id,status) VALUES(1,'IT-1','测试','旧部门',1,'idle')"))
            conn.execute(text("INSERT INTO scrap_requests(request_number,asset_desc,applicant,department) VALUES('SC-1','测试','重名','旧部门'),('SC-2','测试','唯一','旧部门')"))
            conn.execute(text("INSERT INTO delete_requests(table_name,record_id,reason,applicant) VALUES('apply_requests',0,'checkout|接收人|旧部门|it|1','唯一')"))
        migrate_workflow(other)
        with other.begin() as conn:
            rows=conn.execute(text('SELECT applicant_id,department_id FROM scrap_requests ORDER BY id')).all()
            self.assertEqual(rows,[(None,1),(3,1)])
            request=conn.execute(text('SELECT application_type,target_department_id,department_id,asset_id FROM delete_requests')).one()
            self.assertEqual(tuple(request),('checkout',1,1,1))
            conn.execute(text('DELETE FROM users WHERE id=2'))
        migrate_workflow(other)
        with other.connect() as conn:
            self.assertIsNone(conn.execute(text('SELECT applicant_id FROM scrap_requests WHERE id=1')).scalar())
        other.dispose()


def tearDownModule():
    engine.dispose()
    workspace.cleanup()


if __name__ == '__main__':
    unittest.main()
