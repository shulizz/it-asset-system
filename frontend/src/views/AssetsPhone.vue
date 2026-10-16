<template>
  <div>
    <PageHeading title="手机设备档案" description="管理手机档案、IMEI 与号码绑定信息。"
      ><div style="display: flex; gap: 8px; align-items: center">
        <ImportExportButtons module="phone" />
        <button class="btn-primary" @click="openCreateForm">+ 新增手机</button>
      </div></PageHeading
    >
    <div class="filter-bar">
      <input
        aria-label="搜索编号/型号/使用人"
        v-model="filter.keyword"
        placeholder="搜索编号/型号/使用人"
      />
      <select aria-label="筛选部门" v-model="filter.department">
        <option value="">全部部门</option>
        <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
      </select>
      <select aria-label="筛选状态" v-model="filter.status">
        <option value="">全部状态</option>
        <option value="in_use">在用</option>
        <option value="idle">闲置</option>
        <option value="scrapped">已报废</option>
      </select>
    </div>
    <TableFrame title="手机设备台账" :count="filteredList.length"
      ><table>
        <thead>
          <tr>
            <th>资产编号</th>
            <th>品牌型号</th>
            <th>使用人</th>
            <th>部门</th>
            <th>状态</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredList" :key="item.id">
            <td>{{ item.asset_number }}</td>
            <td>{{ item.brand_model }}</td>
            <td>{{ item.user_name || '—' }}</td>
            <td>{{ item.department || '—' }}</td>
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
        <h3>{{ form.id ? '编辑手机' : '新增手机' }}</h3>
        <div class="form-row" v-if="form.id">
          <label>资产编号</label><input v-model="form.asset_number" disabled />
        </div>
        <div class="form-row"><label>品牌型号</label><input v-model="form.brand_model" /></div>
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
const { canWriteAssets } = usePermissions()
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
      const text =
        `${item.asset_number || ''} ${item.brand_model || ''} ${item.user_name || ''}`.toLowerCase()
      if (!text.includes(kw)) return false
    }
    return true
  })
})
const form = ref({
  asset_number: '',
  brand_model: '',
  imei: '',
  bound_number: '',
  user_name: '',
  department: '',
})
async function load() {
  const res = await api.get('/assets/phone')
  list.value = res.data
}
function edit(item) {
  Object.assign(form.value, item)
  showForm.value = true
}
function askDelete(item) {
  deleteTarget.value = {
    table_name: 'phone_assets',
    record_id: item.id,
    record_desc: `${item.asset_number} ${item.brand_model}`,
  }
}
async function save() {
  if (form.value.id) await api.put(`/assets/phone/${form.value.id}`, form.value)
  else await api.post('/assets/phone', form.value)
  showForm.value = false
  form.value = { id: null, asset_number: '', brand_model: '', user_name: '', department: '' }
  load()
}
function statusClass(s) {
  return { in_use: 'green', idle: 'amber', scrapped: 'gray' }[s] || 'gray'
}
function statusText(s) {
  return { in_use: '在用', idle: '闲置', scrapped: '已报废' }[s] || s
}
onMounted(async () => {
  load()
  const res = await api.get('/departments')
  deptList.value = res.data
})

function openCreateForm() {
  form.value = { id: null, asset_number: '', brand_model: '', user_name: '', department: '' }
  showForm.value = true
}
</script>
