<template>
  <div>
    <h2 style="margin-bottom:20px">设备申请</h2>
    <div class="panel">
      <div style="margin-bottom:20px">
        <button class="btn-primary" @click="showForm = true">+ 新建设备申请</button>
      </div>
      <table>
        <thead><tr><th>申请号</th><th>申请类型</th><th>申请内容</th><th>使用人</th><th>部门</th><th>状态</th><th>提交时间</th></tr></thead>
        <tbody>
          <tr v-for="item in list" :key="item.id">
            <td>{{ item.request_no }}</td>
            <td><span class="badge" :class="typeClass(item.type)">{{ typeText(item.type) }}</span></td>
            <td>{{ item.content }}</td>
            <td>{{ item.user_name || '—' }}</td>
            <td>{{ item.department || '—' }}</td>
            <td><span class="badge" :class="statusClass(item.status)">{{ statusText(item.status) }}</span></td>
            <td>{{ item.created_at || '—' }}</td>
          </tr>
          <tr v-if="list.length === 0"><td colspan="7" style="text-align:center;color:#94a3b8;padding:30px">暂无申请记录</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>新建设备申请</h3>
        <div class="form-row"><label>申请类型</label>
          <select v-model="form.type" @change="onTypeChange">
            <option value="scrap">申请报废设备</option>
          </select>
        </div>
        <div class="form-row"><label>资产类型</label>
          <select v-model="form.assetType" @change="loadAssets">
            <option value="">-- 请选择 --</option>
            <option value="it">IT 设备</option>
            <option value="phone">手机设备</option>
            <option value="medical">医疗设备</option>
          </select>
        </div>
        <div class="form-row"><label>所属部门</label>
          <select v-model="form.deptFilter" @change="loadAssets">
            <option value="">-- 全部部门 --</option>
            <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-row"><label>选择设备</label>
          <select v-model="form.assetId" @change="onAssetSelect">
            <option :value="null">-- 请选择 --</option>
            <option v-for="a in assetList" :value="a.id">{{ a.asset_number }} {{ a.name || a.brand_model }}（{{ a.department || '无部门' }}）</option>
          </select>
        </div>
        <div class="form-row"><label>申请说明</label><textarea v-model="form.content" rows="3" placeholder="说明需要什么设备/用途"></textarea></div>
        <div class="form-row"><label>使用人</label><input v-model="form.user_name"></div>
        <div class="form-row"><label>部门</label>
          <select v-model="form.department">
            <option value="">-- 请选择 --</option>
            <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
          <button class="btn-outline" @click="showForm = false">取消</button>
          <button class="btn-primary" @click="save">提交申请</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
const list = ref([]), showForm = ref(false), deptList = ref([])
const form = ref({ type:'checkout', assetType:'', deptFilter:'', assetId:null, content:'', user_name:'', department:'' })
const assetList = ref([])
async function loadAssets(){
  if (!form.value.assetType) { assetList.value = []; return }
  const map = { it:'/assets/it', phone:'/assets/phone', medical:'/assets/medical' }
  const res = await api.get(map[form.value.assetType])
  let list = res.data
  if (form.value.deptFilter) list = list.filter(a => a.department === form.value.deptFilter)
  assetList.value = list
}
function onTypeChange(){ form.value.assetType=''; form.value.assetId=null; assetList.value=[] }
function onAssetSelect(){
  const a = assetList.value.find(x => x.id === form.value.assetId)
  if (a) form.value.content = `${a.asset_number} ${a.name || a.brand_model}`
}
async function load(){
  // 从删除审批表借用，用类型区分
  const res = await api.get('/delete-request')
  list.value = res.data.filter(r => r.table_name === 'apply_requests')
}
async function save(){
  if (!form.value.content) { alert('请填写申请说明'); return }
  try {
  if (form.value.type === 'scrap') {
    if (!form.value.assetId) { alert('请选择要报废的设备'); return }
    await api.post('/scrap', {
      request_number: 'SC-' + Date.now(),
      asset_desc: form.value.content,
      asset_type: form.value.assetType || 'it',
      asset_id: form.value.assetId,
      applicant: '部门主管',
      department: form.value.department,
      reason: form.value.content
    })
    alert('报废申请已提交')
  } else {
    await api.post('/delete-request', {
      table_name: 'apply_requests',
      record_id: 0,
      record_desc: form.value.content,
      reason: `${form.value.type}|${form.value.user_name}|${form.value.department}|${form.value.assetType||''}|${form.value.assetId||0}`,
      applicant: '部门主管'
    })
  }
  } catch(e) { alert('提交失败: ' + (typeof e.response?.data?.detail === 'string' ? e.response.data.detail : JSON.stringify(e.response?.data || e.message))); return }
  showForm.value = false
  form.value = { type:'checkout', assetType:'', deptFilter:'', assetId:null, content:'', user_name:'', department:'' }
  load()
}
function typeClass(t){ return {checkout:'blue',new_asset:'green',transfer:'amber',scrap:'red'}[t]||'gray' }
function typeText(t){ return {checkout:'领用申请',new_asset:'新增申请',transfer:'调拨申请',scrap:'报废申请'}[t]||t }
function statusClass(s){ return {pending:'amber',approved:'green',rejected:'red'}[s]||'gray' }
function statusText(s){ return {pending:'待审批',approved:'已通过',rejected:'已驳回'}[s]||s }
onMounted(async () => { load(); const res = await api.get('/departments'); deptList.value = res.data })
</script>
<style scoped>
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.badge{padding:2px 8px;border-radius:4px;font-size:12px}
.blue{background:#dbeafe;color:#2563eb}.green{background:#dcfce7;color:#16a34a}.amber{background:#fef3c7;color:#d97706}.red{background:#fee2e2;color:#dc2626}.gray{background:#f1f5f9;color:#64748b}
.btn-primary{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.btn-outline{background:#fff;border:1px solid #e2e8f0;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:12px;padding:24px;width:420px}
.modal h3{margin-bottom:16px}
.form-row{margin-bottom:12px}
.form-row label{display:block;font-size:13px;color:#64748b;margin-bottom:4px}
.form-row input,.form-row select,.form-row textarea{width:100%;border:1px solid #e2e8f0;border-radius:6px;padding:0 10px;box-sizing:border-box}
.form-row textarea{padding:8px 10px}
</style>





