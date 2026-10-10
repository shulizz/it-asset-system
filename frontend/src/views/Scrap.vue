<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>报废管理</h2>
      <button class="btn-primary" @click="showForm = true">+ 发起报废申请</button>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>申请号</th><th>设备</th><th>申请人</th><th>部门</th><th>原因</th><th>状态</th><th>提交日期</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in list" :key="item.id">
            <td>{{ item.request_number }}</td><td>{{ item.asset_desc }}</td><td>{{ item.applicant || '—' }}</td>
            <td>{{ item.department || '—' }}</td><td>{{ item.reason || '—' }}</td>
            <td><span class="badge" :class="statusClass(item.status)">{{ statusText(item.status) }}</span></td>
            <td>{{ item.submit_date || '—' }}</td>
            <td>
              <button type="button" class="delete-action" v-if="canWriteAssets" @click="askDelete(item)" style="color:#ef4444;cursor:pointer">申请删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>发起报废申请</h3>
        <div class="form-row"><label>设备类型</label>
          <select v-model="form.assetType" @change="onTypeChange">
            <option value="">-- 请选择 --</option>
            <option value="it">IT设备</option>
            <option value="phone">手机设备</option>
            <option value="medical">医疗设备</option>
            <option value="number">电话号码</option>
          </select>
        </div>
        <div class="form-row"><label>选择设备</label>
          <select v-model="form.assetId" @change="onAssetSelect">
            <option value="">-- 请先选择设备类型 --</option>
            <option v-for="a in assetOptions" :value="a.id">{{ a.asset_number || a.number }} {{ a.name || a.brand_model || '' }}</option>
          </select>
        </div>
        <div class="form-row"><label>申请人</label><input v-model="form.applicant"></div>
        <div class="form-row"><label>部门</label>
          <select v-model="form.department">
            <option value="">-- 请选择 --</option>
            <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-row"><label>报废原因</label><input v-model="form.reason"></div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
          <button class="btn-outline" @click="showForm = false">取消</button>
          <button class="btn-primary" @click="save">提交</button>
        </div>
      </div>
    </div>
  <DeleteRequestDialog :target="deleteTarget" @close="deleteTarget = null" />
  </div>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import DeleteRequestDialog from '../components/DeleteRequestDialog.vue'
const deleteTarget = ref(null)
const canWriteAssets = computed(() => (JSON.parse(localStorage.getItem('user') || '{}').permissions || []).includes('assets_write'))
const list = ref([]), showForm = ref(false)
const deptList = ref([]), assetOptions = ref([])
const form = ref({ assetType:'', assetId:null, asset_desc:'', applicant:'', department:'', reason:'' })
async function load(){ const res = await api.get('/scrap'); list.value = res.data }
async function onTypeChange(){
  assetOptions.value = []
  if (!form.value.assetType) return
  const map = { it:'/assets/it', phone:'/assets/phone', medical:'/assets/medical', number:'/assets/numbers' }
  const res = await api.get(map[form.value.assetType])
  assetOptions.value = res.data
}
function onAssetSelect(){
  const a = assetOptions.value.find(x => x.id === form.value.assetId)
  if (a) {
    form.value.asset_desc = `${a.asset_number || a.number} ${a.name || a.brand_model || ''}`
    form.value.department = a.department || ''
  }
}
async function save(){
  if (!form.value.assetId) { alert('请选择设备'); return }
  await api.post('/scrap', {
    request_number: 'SC-' + Date.now(),
    asset_desc: form.value.asset_desc,
    asset_type: form.value.assetType,
    asset_id: form.value.assetId,
    applicant: form.value.applicant,
    department: form.value.department,
    reason: form.value.reason
  })
  showForm.value = false
  form.value = { assetType:'', assetId:null, asset_desc:'', applicant:'', department:'', reason:'' }
  load()
}
function askDelete(item) { deleteTarget.value = { table_name: 'scrap_requests', record_id: item.id, record_desc: item.request_number } }
function reject(item){ alert('驳回功能待开发') }
function statusClass(s){ return {pending_approval:'amber',approved:'green',disposed:'gray',archived:'gray'}[s]||'gray' }
function statusText(s){ return {pending_approval:'待审批',approved:'已批准',disposed:'已处置',archived:'已归档'}[s]||s }
onMounted(async () => { load(); const res = await api.get('/departments'); deptList.value = res.data })
</script>
<style scoped>
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.badge{padding:2px 8px;border-radius:4px;font-size:12px}
.blue{background:#dbeafe;color:#2563eb}.amber{background:#fef3c7;color:#d97706}.green{background:#dcfce7;color:#16a34a}.gray{background:#f1f5f9;color:#64748b}.red{background:#fee2e2;color:#dc2626}
.btn-primary{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.btn-outline{background:#fff;border:1px solid #e2e8f0;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:12px;padding:24px;width:420px}
.modal h3{margin-bottom:16px}
.form-row{margin-bottom:12px}
.form-row label{display:block;font-size:13px;color:#64748b;margin-bottom:4px}
.form-row input, .form-row select{width:100%;height:36px;border:1px solid #e2e8f0;border-radius:6px;padding:0 10px}
</style>
