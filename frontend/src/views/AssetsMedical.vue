<template>
  <div>
    <PageHeading title="医疗设备档案" description="管理医疗设备档案，及时跟进校准与使用期限。"
      ><div style="display: flex; gap: 8px; align-items: center">
        <ImportExportButtons module="medical" />
        <button v-if="canWriteAssets" class="btn-primary" @click="openForm">+ 新增设备</button>
      </div></PageHeading
    >
    <div class="filter-bar">
      <input
        aria-label="搜索编号/名称/保管人"
        v-model="filter.keyword"
        placeholder="搜索编号/名称/保管人"
      />
      <select aria-label="筛选部门" v-model="filter.department">
        <option value="">全部科室</option>
        <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
      </select>
      <select aria-label="筛选状态" v-model="filter.status">
        <option value="">全部状态</option>
        <option value="in_use">在用</option>
        <option value="idle">闲置</option>
        <option value="scrapped">已报废</option>
      </select>
    </div>
    <section class="calibration-notice">
      <div>
        <h3>校准到期提醒</h3>
        <p>
          30天内到期 {{ calibrationCounts.upcoming }} 台，已逾期 {{ calibrationCounts.overdue }} 台
        </p>
      </div>
      <ExpiryEmailDialog v-if="canSendEmail" reminder-type="calibration" />
    </section>
    <TableFrame title="医疗设备台账" :count="filteredList.length"
      ><table>
        <thead>
          <tr>
            <th>资产编号</th>
            <th>设备名称</th>
            <th>型号</th>
            <th>科室</th>
            <th>保管人</th>
            <th>校准时间</th>
            <th>校准到期时间</th>
            <th>校准剩余天数</th>
            <th>使用年限</th>
            <th>设备到期时间</th>
            <th>剩余天数</th>
            <th>状态</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredList" :key="item.id" :class="{ 'expiring-row': isDue(item) }">
            <td>{{ item.asset_number }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.model || '—' }}</td>
            <td>{{ item.department || '—' }}</td>
            <td>{{ item.keeper || '—' }}</td>
            <td class="date-cell">{{ formatDate(item.calibration_date) }}</td>
            <td class="date-cell">{{ formatDate(item.calibration_expiry) }}</td>
            <td>
              <span v-if="daysLeft(item.calibration_expiry) === null">—</span
              ><span
                v-else
                class="badge"
                :class="daysLeft(item.calibration_expiry) <= 30 ? 'red' : 'green'"
                >{{
                  daysLeft(item.calibration_expiry) < 0
                    ? '已逾期' + Math.abs(daysLeft(item.calibration_expiry)) + '天'
                    : daysLeft(item.calibration_expiry) + '天'
                }}</span
              >
            </td>
            <td>{{ item.use_years != null ? item.use_years + ' 年' : '—' }}</td>
            <td>{{ formatDate(item.expiry_date) }}</td>
            <td>
              <span v-if="daysLeft(item.expiry_date) === null" style="color: #94a3b8">—</span>
              <span v-else-if="daysLeft(item.expiry_date) < 0" class="badge red">已过期</span>
              <span v-else-if="daysLeft(item.expiry_date) <= 30" class="badge red"
                >{{ daysLeft(item.expiry_date) }}天</span
              >
              <span v-else class="badge green">{{ daysLeft(item.expiry_date) }}天</span>
            </td>
            <td>
              <span class="badge" :class="statusClass(item.status)">{{
                statusText(item.status)
              }}</span>
            </td>
            <td>
              <button
                type="button"
                class="row-action"
                v-if="canWriteAssets"
                @click="edit(item)"
                style="color: #2563eb; cursor: pointer; margin-right: 10px"
              >
                编辑</button
              ><button
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
        <h3>{{ form.id ? '编辑医疗设备' : '新增医疗设备' }}</h3>
        <div class="form-row" v-if="form.id">
          <label>资产编号</label><input v-model="form.asset_number" disabled />
        </div>
        <div class="form-row"><label>设备名称</label><input v-model="form.name" /></div>
        <div class="form-row"><label>型号</label><input v-model="form.model" /></div>
        <div class="form-row">
          <label>科室</label>
          <select v-model="form.department">
            <option value="">-- 请选择 --</option>
            <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-row"><label>保管人</label><input v-model="form.keeper" /></div>
        <div class="form-row">
          <label>使用年限（年）</label
          ><input
            type="number"
            step="0.5"
            min="0"
            v-model.number="form.use_years"
            placeholder="如：5"
          />
        </div>
        <div class="form-row">
          <label>设备到期时间</label><input type="date" v-model="form.expiry_date" />
        </div>
        <div class="form-row">
          <label for="calibration-date">校准时间</label
          ><input id="calibration-date" type="date" v-model="form.calibration_date" />
        </div>
        <div class="form-row">
          <label for="calibration-expiry">校准到期时间</label
          ><input
            id="calibration-expiry"
            type="date"
            v-model="form.calibration_expiry"
            :min="form.calibration_date || undefined"
          />
        </div>
        <p v-if="formError" role="alert" style="color: #c83535">{{ formError }}</p>
        <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px">
          <button class="btn-outline" @click="showForm = false">取消</button>
          <button class="btn-primary" :disabled="saving" @click="save">
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </div>
    <DeleteRequestDialog :target="deleteTarget" @close="deleteTarget = null" />
  </div>
</template>
<script setup>
import PageHeading from '../components/PageHeading.vue'
import TableFrame from '../components/TableFrame.vue'
import { usePermissions } from '../usePermissions'
import { currentUser } from '../userState'
const { canWriteAssets } = usePermissions()
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import DeleteRequestDialog from '../components/DeleteRequestDialog.vue'
const deleteTarget = ref(null)
import ImportExportButtons from '../components/ImportExportButtons.vue'
import ExpiryEmailDialog from '../components/ExpiryEmailDialog.vue'
import { daysUntil } from '../medicalDates'
const list = ref([]),
  showForm = ref(false),
  deptList = ref([])
const filter = ref({ keyword: '', department: '', status: '' })
const filteredList = computed(() => {
  return list.value.filter((item) => {
    if (filter.value.department && item.department !== filter.value.department) return false
    if (filter.value.status && item.status !== filter.value.status) return false
    if (filter.value.keyword) {
      const kw = filter.value.keyword.toLowerCase()
      const text =
        `${item.asset_number || ''} ${item.name || ''} ${item.keeper || ''}`.toLowerCase()
      if (!text.includes(kw)) return false
    }
    return true
  })
})
const emptyForm = () => ({
  id: null,
  asset_number: '',
  name: '',
  model: '',
  department: '',
  keeper: '',
  use_years: null,
  expiry_date: '',
  calibration_date: '',
  calibration_expiry: '',
})
const form = ref(emptyForm()),
  formError = ref(''),
  saving = ref(false)
const calibrationCounts = computed(() => {
  const result = { upcoming: 0, overdue: 0 }
  for (const item of list.value) {
    if (['scrapped', 'archived'].includes(item.status)) continue
    const days = daysUntil(item.calibration_expiry)
    if (days !== null && days <= 30) {
      if (days < 0) result.overdue++
      else result.upcoming++
    }
  }
  return result
})
const canSendEmail = computed(
  () =>
    canWriteAssets.value &&
    (currentUser.value.role === 'super_admin' || currentUser.value.data_scope === 'all'),
)
function openForm() {
  form.value = emptyForm()
  formError.value = ''
  showForm.value = true
}
async function load() {
  const res = await api.get('/assets/medical')
  list.value = res.data
}
function edit(item) {
  form.value = { ...emptyForm(), ...item }
  formError.value = ''
  showForm.value = true
}
function askDelete(item) {
  deleteTarget.value = {
    table_name: 'medical_assets',
    record_id: item.id,
    record_desc: `${item.asset_number} ${item.name}`,
  }
}
async function save() {
  if (saving.value) return
  formError.value = ''
  const payload = { ...form.value }
  for (const key of ['purchase_date', 'expiry_date', 'calibration_date', 'calibration_expiry'])
    payload[key] = payload[key] || null
  if (
    payload.calibration_date &&
    payload.calibration_expiry &&
    payload.calibration_expiry < payload.calibration_date
  ) {
    formError.value = '校准到期时间不能早于校准时间'
    return
  }
  saving.value = true
  try {
    if (form.value.id) await api.put(`/assets/medical/${form.value.id}`, payload)
    else await api.post('/assets/medical', payload)
    showForm.value = false
    form.value = emptyForm()
    await load()
  } catch (error) {
    const detail = error.response?.data?.detail
    formError.value =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg).join('；')
          : '保存失败，请重试'
  } finally {
    saving.value = false
  }
}
function statusClass(s) {
  return { in_use: 'green', idle: 'amber', scrapped: 'red' }[s] || 'gray'
}
function statusText(s) {
  return { in_use: '在用', idle: '闲置', scrapped: '已报废' }[s] || s
}
function formatDate(d) {
  if (!d) return '—'
  return d.substring(0, 10)
}
function daysLeft(d) {
  return daysUntil(d)
}
function isDue(item) {
  return (
    !['scrapped', 'archived'].includes(item.status) &&
    [item.expiry_date, item.calibration_expiry].some(
      (value) => daysLeft(value) !== null && daysLeft(value) <= 30,
    )
  )
}
onMounted(async () => {
  load()
  const res = await api.get('/departments')
  deptList.value = res.data
})
</script>
<style scoped>
.calibration-notice {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #d97706;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.calibration-notice h3 {
  font-size: 15px;
}
.calibration-notice p {
  font-size: 13px;
  color: #64748b;
  margin-top: 6px;
}
.date-cell {
  white-space: nowrap;
}
.expiring-row {
  background: #fef2f2;
}
</style>
