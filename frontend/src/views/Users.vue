<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>用户权限</h2>
      <button class="btn-primary" @click="openForm">+ 新增用户</button>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>用户名</th><th>姓名</th><th>邮箱</th><th>角色</th><th>部门</th><th>数据范围</th><th>已分配权限</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="u in list" :key="u.id">
            <td>{{ u.username }}</td><td>{{ u.name }}</td>
            <td>{{ u.email || '未填写' }}</td>
            <td><span class="badge" :class="roleClass(u.role)">{{ roleText(u.role) }}</span></td>
            <td>{{ u.department || '—' }}</td>
            <td>{{ u.role === "super_admin" || u.data_scope === "all" ? "全部部门" : "仅本部门" }}</td>
            <td>{{ u.role === "super_admin" ? "全部权限" : (u.permissions || []).map(key => permissionList.find(p => p.key === key)?.label || key).join("、") || "无" }}</td>
            <td><span class="badge" :class="u.is_active ? 'green' : 'gray'">{{ u.is_active ? '启用' : '停用' }}</span></td>
            <td>
              <a @click="edit(u)" style="color:#0d9488;cursor:pointer;margin-right:10px">编辑</a>
              <a @click="toggle(u)" style="color:#d97706;cursor:pointer;margin-right:10px">{{ u.is_active ? '停用' : '启用' }}</a>
              <a @click="del(u)" style="color:#ef4444;cursor:pointer">删除</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="panel" style="margin-top:24px;padding:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <h3 style="font-size:15px">数据备份</h3>
        <button class="btn-primary" @click="backupNow">立即备份</button>
      </div>
      <table v-if="backups.length">
        <thead><tr><th>备份文件</th><th>大小</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="b in backups" :key="b.name">
            <td>{{ b.name }}</td>
            <td>{{ (b.size/1024).toFixed(1) }} KB</td>
            <td><FileDownloadButton :endpoint="`/backup/download/${encodeURIComponent(b.name)}`" :filename="b.name" label="下载" /></td>
          </tr>
        </tbody>
      </table>
      <p v-else style="color:#94a3b8;font-size:13px">暂无备份</p>
    </div>
    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>{{ form.id ? '编辑用户' : '新增用户' }}</h3>
        <div class="form-row"><label>用户名</label><input v-model="form.username" :disabled="form.id"></div>
        <div class="form-row"><label>姓名</label><input v-model="form.name"></div>
        <div class="form-row"><label for="user-email">邮箱（用于接收设备到期提醒）</label><input id="user-email" v-model="form.email" type="email" maxlength="254" placeholder="如：name@qq.com"><p style="font-size:12px;color:#64748b;margin-top:5px">可选；填写后可在发送提醒时选择该用户。</p></div>
        <div class="form-row"><label>密码</label><input v-model="form.password" type="password" :placeholder="form.id ? '不修改请留空' : '至少10个字符'"></div>
        <div class="form-row"><label for="user-identity">账号身份</label>
          <select id="user-identity" v-model="form.account_type"><option value="regular">普通用户</option><option value="super_admin">超级管理员</option></select>
        </div>
        <div v-if="form.account_type !== 'super_admin'" class="form-row"><label for="user-role-name">角色名称</label><input id="user-role-name" v-model="form.role" maxlength="50" placeholder="如：资产管理员、部门负责人"><p style="font-size:12px;color:#64748b;margin-top:5px">角色只用于显示，操作权限由下方勾选项决定。</p></div>
        <div class="form-row"><label>部门</label>
          <select v-model="form.department">
            <option value="">-- 无 --</option>
            <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-row"><label>数据范围</label>
          <select v-model="form.data_scope" :disabled="form.account_type === 'super_admin'">
            <option value="department">仅本部门</option><option value="all">全部部门</option>
          </select>
        </div>
        <p style="font-size:12px;color:#64748b">部门管理、全局日志、微信管理需要全部部门范围；微信密码需同时勾选微信管理。导入和导出需同时勾选对应模块权限。</p>
        <div class="form-row"><label>用户操作权限（可单独调整）</label>
          <p v-if="form.account_type === 'super_admin'">超级管理员拥有全部权限。</p>
          <div v-else style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
            <label v-for="p in permissionList" :key="p.key" style="display:flex;gap:6px;align-items:center">
              <input type="checkbox" :value="p.key" v-model="form.permissions" style="width:16px;height:16px">{{ p.label }}
            </label>
          </div>
        </div>
        <p v-if="formError" style="color:#dc2626">{{ formError }}</p>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
          <button class="btn-outline" @click="showForm = false">取消</button>
          <button class="btn-primary" @click="save">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import FileDownloadButton from '../components/FileDownloadButton.vue'
const list = ref([]), showForm = ref(false), deptList = ref([]), backups = ref([])
const permissionList = ref([]), formError = ref('')
const form = ref({ id:null, username:'', name:'', email:'', password:'', role:'', account_type:'regular', department:'' })
async function load(){
  const [u, d, b, p] = await Promise.all([api.get('/auth/users'), api.get('/departments'), api.get('/backup/list'), api.get('/auth/permissions')])
  list.value = u.data
  deptList.value = d.data
  backups.value = b.data  permissionList.value = p.data
}
async function backupNow(){
  await api.post('/backup/')
  await load()
}

function openForm(){ formError.value = ''; form.value = { id:null, username:'', name:'', email:'', password:'', role:'', account_type:'regular', department:'', permissions:[], data_scope:'department' }; showForm.value = true }
function edit(u){ formError.value = ''; form.value = {...u, account_type:u.role === 'super_admin' ? 'super_admin' : 'regular', role:u.role === 'super_admin' ? '' : u.role, permissions:[...(u.permissions || [])], password:''}; showForm.value = true }
async function save(){
  formError.value = ''; try {
  const email=(form.value.email || '').trim()
  if(email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { formError.value='请输入有效的邮箱地址'; return }
  form.value.email=email || null
  if(form.value.account_type !== 'super_admin' && form.value.role.trim() === 'super_admin') { formError.value='请通过账号身份选择超级管理员'; return }
  const payload={...form.value,role:form.value.account_type === 'super_admin' ? 'super_admin' : form.value.role.trim(), data_scope:form.value.account_type === 'super_admin' ? 'all' : form.value.data_scope}
  delete payload.account_type
  if (form.value.id) await api.put(`/auth/users/${form.value.id}`, payload)
  else await api.post('/auth/users', payload)
  showForm.value = false
  load()
  } catch(e) { const detail=e.response?.data?.detail; formError.value = typeof detail === 'string' ? detail : (Array.isArray(detail) && detail.some(item => item.loc?.includes('email')) ? '请输入有效的邮箱地址' : '保存失败，请检查填写内容后重试') }
}
async function toggle(u){ await api.put(`/auth/users/${u.id}/toggle`); load() }
async function del(u){
  if(!confirm(`确定删除用户「${u.name}」？此操作不可恢复`)) return
  try { await api.delete(`/auth/users/${u.id}`); await load() }
  catch(e) { alert(e.response?.data?.detail || '删除失败') }
}
function roleClass(r){ return r==='super_admin' ? 'red' : 'blue' }
function roleText(r){ return r==='super_admin' ? '超级管理员' : r }
onMounted(load)
</script>
<style scoped>
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.badge{padding:2px 8px;border-radius:4px;font-size:12px}
.red{background:#fee2e2;color:#dc2626}.blue{background:#dbeafe;color:#2563eb}.green{background:#dcfce7;color:#16a34a}.purple{background:#ede9fe;color:#7c3aed}.gray{background:#f1f5f9;color:#64748b}
.btn-primary{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.btn-outline{background:#fff;border:1px solid #e2e8f0;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:12px;padding:24px;width:640px;max-height:90vh;overflow-y:auto}
.modal h3{margin-bottom:16px}
.form-row{margin-bottom:12px}
.form-row label{display:block;font-size:13px;color:#64748b;margin-bottom:4px}
.form-row input,.form-row select{width:100%;height:36px;border:1px solid #e2e8f0;border-radius:6px;padding:0 10px}
</style>

