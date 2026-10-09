<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>医疗设备档案</h2>
      <div style="display:flex;gap:8px;align-items:center">
        <ImportExportButtons module="medical" />
        <button class="btn-primary" @click="form={id:null,asset_number:'',name:'',model:'',department:'',keeper:'',use_years:null,expiry_date:''};showForm=true">+ 新增设备</button>
      </div>
    </div>
    <div style="display:flex;gap:12px;margin-bottom:16px">
      <input v-model="filter.keyword" placeholder="搜索编号/名称/保管人" style="flex:1;padding:8px 12px;border:1px solid #e2e8f0;border-radius:6px">
      <select v-model="filter.department" style="width:150px;padding:8px;border:1px solid #e2e8f0;border-radius:6px">
        <option value="">全部科室</option>
        <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
      </select>
      <select v-model="filter.status" style="width:120px;padding:8px;border:1px solid #e2e8f0;border-radius:6px">
        <option value="">全部状态</option>
        <option value="in_use">在用</option>
        <option value="idle">闲置</option>
        <option value="scrapped">已报废</option>
      </select>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>资产编号</th><th>设备名称</th><th>型号</th><th>科室</th><th>保管人</th><th>使用年限</th><th>到期时间</th><th>剩余天数</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in filteredList" :key="item.id" :class="{ 'expiring-row': daysLeft(item.expiry_date) !== null && daysLeft(item.expiry_date) <= 30 }">
            <td>{{ item.asset_number }}</td><td>{{ item.name }}</td><td>{{ item.model || '—' }}</td>
            <td>{{ item.department || '—' }}</td><td>{{ item.keeper || '—' }}</td>
            <td>{{ item.use_years != null ? item.use_years + ' 年' : '—' }}</td>
            <td>{{ formatDate(item.expiry_date) }}</td>
            <td>
              <span v-if="daysLeft(item.expiry_date) === null" style="color:#94a3b8">—</span>
              <span v-else-if="daysLeft(item.expiry_date) < 0" class="badge red">已过期</span>
              <span v-else-if="daysLeft(item.expiry_date) <= 30" class="badge red">{{ daysLeft(item.expiry_date) }}天</span>
              <span v-else class="badge green">{{ daysLeft(item.expiry_date) }}天</span>
            </td>
            <td><span class="badge" :class="statusClass(item.status)">{{ statusText(item.status) }}</span></td>
            <td><a v-if="canWriteAssets" @click="edit(item)" style="color:#2563eb;cursor:pointer;margin-right:10px">编辑</a><a v-if="canWriteAssets" @click="askDelete(item)" style="color:#ef4444;cursor:pointer">申请删除</a></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>{{ form.id ? '编辑医疗设备' : '新增医疗设备' }}</h3>
        <div class="form-row" v-if="form.id"><label>资产编号</label><input v-model="form.asset_number" disabled></div>
        <div class="form-row"><label>设备名称</label><input v-model="form.name"></div>
        <div class="form-row"><label>型号</label><input v-model="form.model"></div>
        <div class="form-row"><label>科室</label>
          <select v-model="form.department">
            <option value="">-- 请选择 --</option>
            <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-row"><label>保管人</label><input v-model="form.keeper"></div>
        <div class="form-row"><label>使用年限（年）</label><input type="number" step="0.5" min="0" v-model.number="form.use_years" placeholder="如：5"></div>
        <div class="form-row"><label>设备到期时间</label><input type="date" v-model="form.expiry_date"></div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
          <button class="btn-outline" @click="showForm = false">取消</button>
          <button class="btn-primary" @click="save">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { usePermissions } from '../usePermissions'
const { canWriteAssets } = usePermissions()
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import ImportExportButtons from '../components/ImportExportButtons.vue'
const list = ref([]), showForm = ref(false), deptList = ref([])
const filter = ref({ keyword:'', department:'', status:'' })
const filteredList = computed(() => {
  return list.value.filter(item => {
    if (filter.value.department && item.department !== filter.value.department) return false
    if (filter.value.status && item.status !== filter.value.status) return false
    if (filter.value.keyword) {
      const kw = filter.value.keyword.toLowerCase()
      const text = `${item.asset_number||''} ${item.name||''} ${item.keeper||''}`.toLowerCase()
      if (!text.includes(kw)) return false
    }
    return true
  })
})
const form = ref({ id:null, asset_number:'', name:'', model:'', department:'', keeper:'', use_years:null, expiry_date:'' })
async function load(){ const res = await api.get('/assets/medical'); list.value = res.data }
function edit(item){ Object.assign(form.value, item); showForm.value = true }
async function askDelete(item){
  const reason = prompt(`申请删除设备 ${item.asset_number} ${item.name}，审批通过后会移出档案并保留历史，请输入原因：`)
  if (!reason) return
  await api.post('/delete-request', { table_name:'medical_assets', record_id:item.id, record_desc:`${item.asset_number} ${item.name}`, reason:reason })
  alert('删除申请已提交，等待管理员审批')
}
async function save(){
  if (form.value.id) await api.put(`/assets/medical/${form.value.id}`, form.value)
  else await api.post('/assets/medical', form.value)
  showForm.value=false; form.value={id:null,asset_number:'',name:'',model:'',department:'',keeper:'',use_years:null,expiry_date:''}; load()
}
function statusClass(s){ return {in_use:'green',idle:'amber',scrapped:'red'}[s]||'gray' }
function statusText(s){ return {in_use:'在用',idle:'闲置',scrapped:'已报废'}[s]||s }
function formatDate(d){ if(!d) return '—'; return d.substring(0,10) }
function daysLeft(d){
  if (!d) return null
  const today = new Date()
  today.setHours(0,0,0,0)
  const target = new Date(d.substring(0,10))
  return Math.ceil((target - today) / 86400000)
}
onMounted(async () => { load(); const res = await api.get('/departments'); deptList.value = res.data })
</script>
<style scoped>
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.badge{padding:2px 8px;border-radius:4px;font-size:12px}
.green{background:#dcfce7;color:#16a34a}.amber{background:#fef3c7;color:#d97706}.red{background:#fee2e2;color:#dc2626}.gray{background:#f1f5f9;color:#64748b}
.expiring-row{background:#fef2f2}
.btn-primary{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.btn-outline{background:#fff;border:1px solid #e2e8f0;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:12px;padding:24px;width:420px}
.modal h3{margin-bottom:16px}
.form-row{margin-bottom:12px}
.form-row label{display:block;font-size:13px;color:#64748b;margin-bottom:4px}
.form-row input{width:100%;height:36px;border:1px solid #e2e8f0;border-radius:6px;padding:0 10px}
</style>
