<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>部门管理</h2>
      <div style="display:flex;gap:8px;align-items:center">
        <ImportExportButtons module="department" />
        <button class="btn-primary" @click="openForm">+ 新增部门</button>
      </div>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>部门名称</th><th>负责人</th><th>备注</th><th>设备数</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in list" :key="item.id">
            <td>{{ item.name }}</td><td>{{ item.manager || '—' }}</td><td>{{ item.note || '—' }}</td>
            <td>{{ countMap[item.name] || 0 }}</td>
            <td><a @click="edit(item)" style="color:#2563eb;cursor:pointer;margin-right:10px">编辑</a><a @click="askDelete(item)" style="color:#ef4444;cursor:pointer">删除</a></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>{{ form.id ? '编辑部门' : '新增部门' }}</h3>
        <div class="form-row"><label>部门名称</label><input v-model="form.name"></div>
        <div class="form-row"><label>负责人</label><input v-model="form.manager"></div>
        <div class="form-row"><label>备注</label><input v-model="form.note"></div>
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
import ImportExportButtons from '../components/ImportExportButtons.vue'
const list = ref([]), showForm = ref(false), countMap = ref({})
const form = ref({ id:null, name:'', manager:'', note:'' })
async function load(){
  const res = await api.get('/departments')
  list.value = res.data
  const [it, phone, medical, numbers] = await Promise.all([
    api.get('/assets/it'), api.get('/assets/phone'),
    api.get('/assets/medical'), api.get('/assets/numbers')
  ])
  const map = {}
  ;[...it.data, ...phone.data, ...medical.data, ...numbers.data].forEach(a => {
    if(a.department) map[a.department] = (map[a.department]||0) + 1
  })
  countMap.value = map
}
function openForm(){ form.value = { id:null, name:'', manager:'', note:'' }; showForm.value = true }
function edit(item){ Object.assign(form.value, item); showForm.value = true }
async function askDelete(item){
  if (!confirm(`确定删除部门"${item.name}"？部门下的设备不会被删除，但部门字段会清空。`)) return
  await api.delete(`/departments/${item.id}`)
  load()
}
async function save(){
  if (form.value.id) await api.put(`/departments/${form.value.id}`, form.value)
  else await api.post('/departments', form.value)
  showForm.value = false
  load()
}
onMounted(load)
</script>
<style scoped>
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.btn-primary{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.btn-outline{background:#fff;border:1px solid #e2e8f0;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:12px;padding:24px;width:420px}
.modal h3{margin-bottom:16px}
.form-row{margin-bottom:12px}
.form-row label{display:block;font-size:13px;color:#64748b;margin-bottom:4px}
.form-row input{width:100%;height:36px;border:1px solid #e2e8f0;border-radius:6px;padding:0 10px}
</style>
