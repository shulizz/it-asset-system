<template>
  <div>
    <PageHeading title="报废管理" description="提交报废申请，查看审核进度与处理结果。"
      ><div class="scrap-heading-actions">
        <button class="btn-outline" @click="openPrint(null)">打印空白报废单</button
        ><button class="btn-primary" @click="showForm = true">+ 发起报废申请</button>
      </div></PageHeading
    >
    <TableFrame title="报废申请" :count="list.length"
      ><table>
        <thead>
          <tr>
            <th>申请号</th>
            <th>设备</th>
            <th>申请人</th>
            <th>部门</th>
            <th>原因</th>
            <th>状态</th>
            <th>提交日期</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list" :key="item.id">
            <td>{{ item.request_number }}</td>
            <td>{{ item.asset_desc }}</td>
            <td>{{ item.applicant || '—' }}</td>
            <td>{{ item.department || '—' }}</td>
            <td>{{ item.reason || '—' }}</td>
            <td>
              <span class="badge" :class="statusClass(item.status)">{{
                statusText(item.status)
              }}</span>
            </td>
            <td>{{ item.submit_date || '—' }}</td>
            <td>
              <button type="button" class="row-action print-record-action" @click="openPrint(item)">
                打印报废单
              </button>
              <button
                type="button"
                class="delete-action"
                v-if="canWriteAssets"
                @click="askDelete(item)"
                style="color: #ef4444; cursor: pointer"
              >
                申请删除
              </button>
            </td>
          </tr>
        </tbody>
      </table></TableFrame
    >
    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>发起报废申请</h3>
        <div class="form-row">
          <label>设备类型</label>
          <select v-model="form.assetType" @change="onTypeChange">
            <option value="">-- 请选择 --</option>
            <option value="it">IT设备</option>
            <option value="phone">手机设备</option>
            <option value="medical">医疗设备</option>
            <option value="number">电话号码</option>
          </select>
        </div>
        <div class="form-row">
          <label>选择设备</label>
          <select v-model="form.assetId" @change="onAssetSelect">
            <option value="">-- 请先选择设备类型 --</option>
            <option v-for="a in assetOptions" :value="a.id">
              {{ a.asset_number || a.number }} {{ a.name || a.brand_model || '' }}
            </option>
          </select>
        </div>
        <div class="form-row"><label>申请人</label><input v-model="form.applicant" /></div>
        <div class="form-row">
          <label>部门</label>
          <select v-model="form.department">
            <option value="">-- 请选择 --</option>
            <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-row"><label>报废原因</label><input v-model="form.reason" /></div>
        <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px">
          <button class="btn-outline" @click="showForm = false">取消</button>
          <button class="btn-primary" @click="save">提交</button>
        </div>
      </div>
    </div>
    <DeleteRequestDialog :target="deleteTarget" @close="deleteTarget = null" />
    <ScrapPrintDialog v-if="showPrint" :record="printRecord" @close="showPrint = false" />
  </div>
</template>
<script setup>
import PageHeading from '../components/PageHeading.vue'
import TableFrame from '../components/TableFrame.vue'
import ScrapPrintDialog from '../components/ScrapPrintDialog.vue'
import { scrapStatusText } from '../scrapPrint'
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import { currentUser } from '../userState'
import DeleteRequestDialog from '../components/DeleteRequestDialog.vue'
const deleteTarget = ref(null)
const showPrint = ref(false),
  printRecord = ref(null)
function openPrint(item) {
  printRecord.value = item
  showPrint.value = true
}
const canWriteAssets = computed(() =>
  (currentUser.value.permissions || []).includes('assets_write'),
)
const list = ref([]),
  showForm = ref(false)
const deptList = ref([]),
  assetOptions = ref([])
const form = ref({
  assetType: '',
  assetId: null,
  asset_desc: '',
  applicant: '',
  department: '',
  reason: '',
})
async function load() {
  const res = await api.get('/scrap')
  list.value = res.data
}
async function onTypeChange() {
  assetOptions.value = []
  if (!form.value.assetType) return
  const map = {
    it: '/assets/it',
    phone: '/assets/phone',
    medical: '/assets/medical',
    number: '/assets/numbers',
  }
  const res = await api.get(map[form.value.assetType])
  assetOptions.value = res.data
}
function onAssetSelect() {
  const a = assetOptions.value.find((x) => x.id === form.value.assetId)
  if (a) {
    form.value.asset_desc = `${a.asset_number || a.number} ${a.name || a.brand_model || ''}`
    form.value.department = a.department || ''
  }
}
async function save() {
  if (!form.value.assetId) {
    alert('请选择设备')
    return
  }
  await api.post('/scrap', {
    request_number: 'SC-' + Date.now(),
    asset_desc: form.value.asset_desc,
    asset_type: form.value.assetType,
    asset_id: form.value.assetId,
    applicant: form.value.applicant,
    department: form.value.department,
    reason: form.value.reason,
  })
  showForm.value = false
  form.value = {
    assetType: '',
    assetId: null,
    asset_desc: '',
    applicant: '',
    department: '',
    reason: '',
  }
  load()
}
function askDelete(item) {
  deleteTarget.value = {
    table_name: 'scrap_requests',
    record_id: item.id,
    record_desc: item.request_number,
  }
}
function reject(item) {
  alert('驳回功能待开发')
}
function statusClass(s) {
  return (
    {
      pending_approval: 'amber',
      approved: 'green',
      rejected: 'red',
      disposed: 'gray',
      archived: 'gray',
    }[s] || 'gray'
  )
}
function statusText(s) {
  return scrapStatusText(s)
}
onMounted(async () => {
  load()
  const res = await api.get('/departments')
  deptList.value = res.data
})
</script>
<style scoped>
.print-record-action {
  margin-right: 10px;
}
.scrap-heading-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
