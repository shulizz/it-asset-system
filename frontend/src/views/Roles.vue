<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>角色权限管理</h2>
      <button class="btn-primary" @click="openForm">+ 新建角色</button>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>角色名称</th><th>权限</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="r in list" :key="r.id">
            <td style="font-weight:500">{{ r.name }}</td>
            <td>
              <span v-for="p in r.permissions" :key="p" class="badge blue">{{ permLabel(p) }}</span>
            </td>
            <td>
              <a @click="edit(r)" style="color:#2563eb;cursor:pointer;margin-right:10px">编辑</a>
              <a @click="del(r)" style="color:#ef4444;cursor:pointer">删除</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>{{ form.id ? '编辑角色' : '新建角色' }}</h3>
        <div class="form-row"><label>角色名称</label><input v-model="form.name" placeholder="如：设备科科长"></div>
        <div class="form-row"><label>权限配置</label>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:10px;border:1px solid #e2e8f0;border-radius:6px">
            <label v-for="p in allPerms" :key="p.key" style="display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer">
              <input type="checkbox" :value="p.key" v-model="form.permissions"> {{ p.label }}
            </label>
          </div>
        </div>
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
const list = ref([]), showForm = ref(false), allPerms = ref([])
const form = ref({ id:null, name:'', permissions:[] })
async function load(){
  const [r, p] = await Promise.all([api.get('/auth/roles'), api.get('/auth/permissions')])
  list.value = r.data
  allPerms.value = p.data
}
function permLabel(k){ return allPerms.value.find(p=>p.key===k)?.label || k }
function openForm(){ form.value = { id:null, name:'', permissions:[] }; showForm.value = true }
function edit(r){ form.value = { id:r.id, name:r.name, permissions:[...r.permissions] }; showForm.value = true }
async function save(){
  if (!form.value.name) { alert('请输入角色名称'); return }
  if (form.value.id) await api.put(`/auth/roles/${form.value.id}`, form.value)
  else await api.post('/auth/roles', form.value)
  showForm.value = false; load()
}
async function del(r){
  if(!confirm(`确定删除角色「${r.name}」？`)) return
  try { await api.delete(`/auth/roles/${r.id}`); load() }
  catch(e){ alert(e.response?.data?.detail || '删除失败') }
}
onMounted(load)
</script>
<style scoped>
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.badge{padding:2px 8px;border-radius:4px;font-size:12px;margin-right:4px;display:inline-block}
.blue{background:#dbeafe;color:#2563eb}
.btn-primary{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.btn-outline{background:#fff;border:1px solid #e2e8f0;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:12px;padding:24px;width:500px}
.modal h3{margin-bottom:16px}
.form-row{margin-bottom:12px}
.form-row label{display:block;font-size:13px;color:#64748b;margin-bottom:4px}
.form-row input{width:100%;height:36px;border:1px solid #e2e8f0;border-radius:6px;padding:0 10px}
</style>
