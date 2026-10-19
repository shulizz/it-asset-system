<template>
  <div>
    <PageHeading title="电话号码管理" description="集中维护号码、套餐及设备绑定关系。"
      ><div style="display: flex; gap: 8px; align-items: center">
        <ImportExportButtons module="number" />
        <button class="btn-primary" @click="openCreateForm">+ 新增号码</button>
      </div></PageHeading
    >
    <div class="filter-bar">
      <input aria-label="搜索号码/使用人" v-model="filter.keyword" placeholder="搜索号码/使用人" />
      <select aria-label="筛选部门" v-model="filter.department">
        <option value="">全部部门</option>
        <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
      </select>
      <select aria-label="筛选状态" v-model="filter.status">
        <option value="">全部状态</option>
        <option value="in_use">在用</option>
        <option value="idle">闲置</option>
        <option value="cancelled">注销</option>
        <option value="unused">不再使用</option>
      </select>
    </div>
    <TableFrame title="号码台账" :count="filteredList.length"
      ><table>
        <thead>
          <tr>
            <th>号码</th>
            <th>运营商</th>
            <th>类型</th>
            <th>部门</th>
            <th>使用人</th>
            <th>状态</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredList" :key="item.id">
            <td>{{ item.number }}</td>
            <td>{{ item.carrier || '—' }}</td>
            <td>
              <span class="badge" :class="typeClass(item.card_type)">{{
                typeText(item.card_type)
              }}</span>
            </td>
            <td>{{ item.department || '—' }}</td>
            <td>{{ item.user_name || '—' }}</td>
            <td>
              <span class="badge" :class="statusClass(item.status)">{{
                statusText(item.status)
              }}</span>
            </td>
            <td>
              <button
                type="button"
                class="row-action"
                v-if="canEditAsset(item)"
                @click="edit(item)"
                style="color: #2563eb; cursor: pointer; margin-right: 10px"
              >
                编辑</button
              ><button
                type="button"
                class="delete-action"
                v-if="canEditAsset(item)"
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
        <h3>{{ form.id ? '编辑电话号码' : '新增电话号码' }}</h3>
        <div class="form-row">
          <label>号码</label><input v-model="form.number" maxlength="11" />
        </div>
        <div class="form-row">
          <label>运营商</label>
          <select v-model="form.carrier">
            <option value="">请选择</option>
            <option>中国移动</option>
            <option>中国联通</option>
            <option>中国电信</option>
          </select>
        </div>
        <div class="form-row">
          <label>类型</label>
          <select v-model="form.card_type">
            <option value="">请选择</option>
            <option value="main">主卡</option>
            <option value="sub">副卡</option>
            <option value="landline">座机</option>
          </select>
        </div>

        <div class="form-row">
          <label>部门</label>
          <select v-model="form.department">
            <option v-if="canWriteAllDepartments" value="">-- 请选择 --</option>
            <option v-for="d in deptList.filter(canUseDepartment)" :value="d.name">
              {{ d.name }}
            </option>
          </select>
        </div>
        <div class="form-row"><label>使用人</label><input v-model="form.user_name" /></div>
        <div class="form-row">
          <label>状态</label>
          <select v-model="form.status">
            <option value="in_use">在用</option>
            <option value="idle">闲置</option>
            <option value="cancelled">注销</option>
            <option value="unused">不再使用</option>
          </select>
        </div>
        <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px">
          <button class="btn-outline" @click="showForm = false">取消</button>
          <button class="btn-primary" @click="save">保存</button>
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
const {
  canWriteAssets,
  canEditAsset,
  canUseDepartment,
  canWriteAllDepartments,
  defaultAssetDepartment,
} = usePermissions()
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import DeleteRequestDialog from '../components/DeleteRequestDialog.vue'
const deleteTarget = ref(null)
import ImportExportButtons from '../components/ImportExportButtons.vue'
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
      const text = `${item.number || ''} ${item.user_name || ''}`.toLowerCase()
      if (!text.includes(kw)) return false
    }
    return true
  })
})
const form = ref({
  id: null,
  number: '',
  carrier: '',
  card_type: '',
  department: defaultAssetDepartment(),
  user_name: '',
  status: 'in_use',
})
async function load() {
  const res = await api.get('/assets/numbers')
  list.value = res.data
}
function edit(item) {
  Object.assign(form.value, item)
  showForm.value = true
}
function askDelete(item) {
  deleteTarget.value = { table_name: 'phone_numbers', record_id: item.id, record_desc: item.number }
}
async function save() {
  if (form.value.id) await api.put(`/assets/numbers/${form.value.id}`, form.value)
  else await api.post('/assets/numbers', form.value)
  showForm.value = false
  form.value = {
    id: null,
    number: '',
    carrier: '',
    card_type: '',
    department: defaultAssetDepartment(),
    user_name: '',
    status: 'in_use',
  }
  load()
}
function typeClass(t) {
  return { main: 'blue', sub: 'purple', landline: 'gray' }[t] || 'gray'
}
function typeText(t) {
  return { main: '主卡', sub: '副卡', landline: '座机' }[t] || t
}
function statusClass(s) {
  return { in_use: 'green', idle: 'amber', cancelled: 'red', unused: 'gray' }[s] || 'gray'
}
function statusText(s) {
  return { in_use: '在用', idle: '闲置', cancelled: '注销', unused: '不再使用' }[s] || s
}
onMounted(async () => {
  load()
  const res = await api.get('/departments')
  deptList.value = res.data
})

function openCreateForm() {
  form.value = {
    id: null,
    number: '',
    carrier: '',
    card_type: '',
    department: defaultAssetDepartment(),
    user_name: '',
    status: 'in_use',
  }
  showForm.value = true
}
</script>
