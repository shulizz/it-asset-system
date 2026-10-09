<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>设备流转</h2>
      <button class="btn-primary" @click="openForm">+ 登记流转</button>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>工单号</th><th>类型</th><th>设备</th><th>经手人</th><th>对方</th><th>原部门</th><th>目标部门</th><th>原使用人</th><th>新使用人</th><th>日期</th><th>备注</th></tr></thead>
        <tbody>
          <tr v-for="item in list" :key="item.id">
            <td>{{ item.transfer_number }}</td>
            <td><span class="badge" :class="typeClass(item.type)">{{ typeText(item.type) }}</span></td>
            <td>{{ item.asset_desc }}</td><td>{{ item.operator }}</td><td>{{ item.counterparty || '—' }}</td>
            <td>{{ item.department || '—' }}</td><td>{{ item.new_dept || '—' }}</td><td>{{ item.old_user || '—' }}</td><td>{{ item.new_user || '—' }}</td><td>{{ item.transfer_date || '—' }}</td><td>{{ item.notes || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>登记流转</h3>
        <div class="form-row"><label>流转类型</label>
          <select v-model="form.type" @change="onTypeChange">
            <option value="checkout">领用（发给员工）</option>
            <option value="return">归还（员工还回）</option>
            <option value="transfer">部门调拨</option>
            <option value="offboard">离职回收</option>
          </select>
        </div>
        <div class="form-row"><label>资产类型</label>
          <select v-model="form.assetType" @change="loadAssets">
            <option value="it">IT 设备</option>
            <option value="phone">手机设备</option>
            <option value="medical">医疗设备</option>
          </select>
        </div>
        <div class="form-row"><label>选择设备</label>
          <select v-model="form.assetId" @change="onAssetSelect">
            <option :value="null">-- 请选择 --</option>
            <option v-for="a in assets" :value="a.id">{{ a.asset_number }} {{ a.name || a.brand_model || a.number }}</option>
          </select>
        </div>
        <div v-if="selectedAsset" class="asset-info">
          <span>当前使用人：{{ selectedAsset.user_name || selectedAsset.keeper || '无' }}</span>
          <span>当前部门：{{ selectedAsset.department || '无' }}</span>
        </div>
        <div class="form-row"><label>{{ typeLabel }}</label>
          <input v-model="form.counterparty" :placeholder="typePlaceholder">
        </div>
        <div class="form-row" v-if="form.type !== 'return' && form.type !== 'offboard'"><label>部门</label>
          <select v-model="form.department">
            <option value="">-- 请选择部门 --</option>
            <option v-for="d in departments" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-row"><label>备注</label><input v-model="form.notes"></div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
          <button class="btn-outline" @click="showForm = false">取消</button>
          <button class="btn-primary" @click="save">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
const list = ref([]), showForm = ref(false), assets = ref([]), selectedAsset = ref(null), departments = ref([])
const form = ref({ type:'checkout', assetType:'it', assetId:null, counterparty:'', department:'', notes:'' })

const typeLabel = computed(() => ({
  checkout: '领用员工姓名', return: '归还员工姓名', transfer: '新使用人', offboard: '离职员工姓名'
}[form.value.type]))
const typePlaceholder = computed(() => ({
  checkout: '如：张工', return: '如：张工', transfer: '如：李工', offboard: '如：王姐'
}[form.value.type]))

async function load(){ const res = await api.get('/transfer'); list.value = res.data }
async function openForm(){
  form.value = { type:'checkout', assetType:'it', assetId:null, counterparty:'', department:'', notes:'' }
  selectedAsset.value = null
  showForm.value = true
  loadAssets()
}
function onTypeChange(){ selectedAsset.value = null; loadAssets() }

async function loadAssets(){
  const map = { it:'/assets/it', phone:'/assets/phone', medical:'/assets/medical', number:'/assets/numbers' }
  const res = await api.get(map[form.value.assetType])
  // 按流转类型过滤可选设备
  if (form.value.type === 'checkout') {
    // 领用只能选闲置的
    assets.value = res.data.filter(a => a.status === 'idle')
  } else if (form.value.type === 'return' || form.value.type === 'offboard') {
    // 归还/离职回收只能选用在用的
    assets.value = res.data.filter(a => a.status === 'in_use')
  } else {
    // 调拨只能选用在用的
    assets.value = res.data.filter(a => a.status === 'in_use')
  }
  selectedAsset.value = null
}
function onAssetSelect(){
  selectedAsset.value = assets.value.find(a => a.id === form.value.assetId)
  if (selectedAsset.value && selectedAsset.value.department) {
    form.value.department = selectedAsset.value.department
  }
}

async function save(){
  if (!form.value.assetId) { alert('请选择设备'); return }
  const asset = selectedAsset.value
  const assetDesc = `${asset.asset_number} ${asset.name || asset.brand_model || asset.number}`
  await api.post('/transfer', {
    transfer_number: 'TR-' + Date.now(),
    type: form.value.type,
    asset_desc: assetDesc,
    counterparty: form.value.counterparty,
    department: form.value.department,
    notes: form.value.notes,
    asset_type: form.value.assetType,
    asset_id: form.value.assetId,
    new_user: form.value.type === 'return' || form.value.type === 'offboard' ? '' : form.value.counterparty,
    new_dept: form.value.department
  })
  showForm.value = false
  load()
}
function typeClass(t){ return {checkout:'blue',return:'amber',transfer:'purple',offboard:'red',scrap:'red'}[t]||'gray' }
function typeText(t){ return {checkout:'领用',return:'归还',transfer:'调拨',offboard:'离职回收',scrap:'报废'}[t]||t }
onMounted(async () => { load(); const res = await api.get('/departments'); departments.value = res.data })
</script>
<style scoped>
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.badge{padding:2px 8px;border-radius:4px;font-size:12px}
.blue{background:#dbeafe;color:#2563eb}.amber{background:#fef3c7;color:#d97706}.purple{background:#ede9fe;color:#7c3aed}.red{background:#fee2e2;color:#dc2626}.gray{background:#f1f5f9;color:#64748b}
.btn-primary{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.btn-outline{background:#fff;border:1px solid #e2e8f0;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:12px;padding:24px;width:440px;max-height:90vh;overflow-y:auto}
.modal h3{margin-bottom:16px}
.form-row{margin-bottom:12px}
.form-row label{display:block;font-size:13px;color:#64748b;margin-bottom:4px}
.form-row input,.form-row select{width:100%;height:36px;border:1px solid #e2e8f0;border-radius:6px;padding:0 10px}
.asset-info{background:#f0f9ff;border-radius:6px;padding:8px 12px;margin-bottom:12px;font-size:13px;color:#2563eb;display:flex;gap:16px}
</style>
