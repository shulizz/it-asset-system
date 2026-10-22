<template>
  <div>
    <PageHeading title="设备申请" description="提交设备领用、调拨或报废申请，跟踪处理进度。"
      ><div>
        <button class="btn-primary" @click="showForm = true">+ 新建设备申请</button>
      </div></PageHeading
    >
    <TableFrame title="申请记录" :count="list.length"
      ><table>
        <thead>
          <tr>
            <th>申请号</th>
            <th>申请类型</th>
            <th>申请内容</th>
            <th>数量</th>
            <th>使用人</th>
            <th>部门</th>
            <th>状态</th>
            <th>提交时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list" :key="item.key">
            <td>{{ item.request_no }}</td>
            <td>
              <span class="badge" :class="typeClass(item.type)">{{ typeText(item.type) }}</span>
            </td>
            <td>{{ item.content }}</td>
            <td>{{ item.quantity ?? 1 }}</td>
            <td>{{ item.user_name || '—' }}</td>
            <td>{{ item.department || '—' }}</td>
            <td>
              <span class="badge" :class="statusClass(item.status)">{{
                statusText(item.status)
              }}</span>
            </td>
            <td>{{ item.created_at || '—' }}</td>
          </tr>
        </tbody>
      </table></TableFrame
    >

    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>新建设备申请</h3>
        <div class="form-row">
          <label>申请类型</label>
          <select v-model="form.type" @change="onTypeChange">
            <option value="scrap">申请报废设备</option>
          </select>
        </div>
        <div class="form-row">
          <label>资产类型</label>
          <select v-model="form.assetType" @change="loadAssets">
            <option value="">-- 请选择 --</option>
            <option value="it">IT 设备</option>
            <option value="phone">手机设备</option>
            <option v-if="canViewFire" value="fire">消防设备</option>
            <option v-if="canViewMedical" value="medical">医疗设备</option>
          </select>
        </div>
        <div class="form-row">
          <label>所属部门</label>
          <select v-model="form.deptFilter" @change="loadAssets">
            <option value="">-- 全部部门 --</option>
            <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-row">
          <label>选择设备</label>
          <select v-model="form.assetId" @change="onAssetSelect">
            <option :value="null">-- 请选择 --</option>
            <option v-for="a in assetList" :value="a.id">
              {{ a.asset_number }} {{ a.name || a.brand_model }}（{{ a.department || '无部门' }}）
            </option>
          </select>
        </div>
        <div class="form-row" v-if="form.assetType === 'phone'">
          <label>本次数量（台）</label
          ><input
            aria-label="本次数量（台）"
            type="number"
            min="1"
            step="1"
            :max="assetList.find((a) => a.id === form.assetId)?.quantity || 1"
            v-model.number="form.quantity"
          />
          <span>现有 {{ assetList.find((a) => a.id === form.assetId)?.quantity || 1 }} 台</span>
        </div>
        <div class="form-row">
          <label>申请说明</label
          ><textarea v-model="form.content" rows="3" placeholder="说明需要什么设备/用途"></textarea>
        </div>
        <div class="form-row"><label>使用人</label><input v-model="form.user_name" /></div>
        <div class="form-row">
          <label>部门</label>
          <select v-model="form.department">
            <option value="">-- 请选择 --</option>
            <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px">
          <button class="btn-outline" @click="showForm = false">取消</button>
          <button class="btn-primary" @click="save">提交申请</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { hasFireAccess } from '../fireAccess'
const canViewFire = computed(() => hasFireAccess(currentUser.value))
import { hasMedicalAccess } from '../medicalAccess'
const canViewMedical = computed(() => hasMedicalAccess(currentUser.value))
import { currentUser } from '../userState'
import PageHeading from '../components/PageHeading.vue'
import TableFrame from '../components/TableFrame.vue'
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import { applicationRows } from '../applicationRows'
const list = ref([]),
  showForm = ref(false),
  deptList = ref([])
const form = ref({
  type: 'scrap',
  assetType: '',
  deptFilter: '',
  quantity: 1,
  assetId: null,
  content: '',
  user_name: '',
  department: '',
})
const assetList = ref([])
async function loadAssets() {
  form.value.assetId = null
  form.value.quantity = 1
  if (!form.value.assetType) {
    assetList.value = []
    return
  }
  const map = {
    fire: '/assets/fire',
    it: '/assets/it',
    phone: '/assets/phone',
    medical: '/assets/medical',
  }
  const res = await api.get(map[form.value.assetType])
  let list = res.data.filter((a) => ['idle', 'in_use'].includes(a.status))
  if (form.value.deptFilter) list = list.filter((a) => a.department === form.value.deptFilter)
  assetList.value = list
}
function onTypeChange() {
  form.value.assetType = ''
  form.value.quantity = 1
  form.value.assetId = null
  assetList.value = []
}
function onAssetSelect() {
  form.value.quantity = 1
  const a = assetList.value.find((x) => x.id === form.value.assetId)
  if (a) form.value.content = `${a.asset_number} ${a.name || a.brand_model}`
}
async function load() {
  // 从删除审批表借用，用类型区分
  const res = await api.get('/delete-request')
  const scraps = await api.get('/scrap')
  list.value = applicationRows(res.data, scraps.data)
}
async function save() {
  if (!form.value.content) {
    alert('请填写申请说明')
    return
  }
  try {
    if (form.value.type === 'scrap') {
      if (!form.value.assetId) {
        alert('请选择要报废的设备')
        return
      }
      await api.post('/scrap', {
        request_number: 'SC-' + Date.now(),
        asset_desc: form.value.content,
        asset_type: form.value.assetType || 'it',
        asset_id: form.value.assetId,
        quantity: form.value.assetType === 'phone' ? form.value.quantity : 1,
        applicant: '部门主管',
        department: form.value.department,
        reason: form.value.content,
      })
      alert('报废申请已提交')
    } else {
      await api.post('/delete-request', {
        table_name: 'apply_requests',
        record_id: 0,
        record_desc: form.value.content,
        reason: form.value.content,
        application_type: form.value.type,
        target_user: form.value.user_name,
        target_department_id:
          deptList.value.find((d) => d.name === form.value.department)?.id || null,
        asset_type: form.value.assetType,
        asset_id: form.value.assetId,
        quantity: form.value.assetType === 'phone' ? form.value.quantity : 1,
        applicant: '部门主管',
      })
    }
  } catch (e) {
    alert(
      '提交失败: ' +
        (typeof e.response?.data?.detail === 'string'
          ? e.response.data.detail
          : JSON.stringify(e.response?.data || e.message)),
    )
    return
  }
  showForm.value = false
  form.value = {
    type: 'scrap',
    assetType: '',
    deptFilter: '',
    quantity: 1,
    assetId: null,
    content: '',
    user_name: '',
    department: '',
  }
  load()
}
function typeClass(t) {
  return { checkout: 'blue', new_asset: 'green', transfer: 'amber', scrap: 'red' }[t] || 'gray'
}
function typeText(t) {
  return (
    { checkout: '领用申请', new_asset: '新增申请', transfer: '调拨申请', scrap: '报废申请' }[t] || t
  )
}
function statusClass(s) {
  return { pending: 'amber', approved: 'green', rejected: 'red' }[s] || 'gray'
}
function statusText(s) {
  return { pending: '待审批', approved: '已通过', rejected: '已驳回' }[s] || s
}
onMounted(async () => {
  load()
  const res = await api.get('/departments')
  deptList.value = res.data
})
</script>
