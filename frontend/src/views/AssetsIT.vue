<template>
  <div>
    <PageHeading title="IT 设备档案" description="统一管理设备台账、使用归属与采购信息。"
      ><div style="display: flex; gap: 8px; align-items: center">
        <ImportExportButtons module="it" />
        <button class="btn-primary" @click="openCreateForm">+ 新增设备</button>
      </div></PageHeading
    >

    <div class="filter-bar">
      <input
        aria-label="搜索编号/名称/使用人"
        v-model="filter.keyword"
        placeholder="搜索编号/名称/使用人"
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

    <TableFrame title="IT 设备台账" :count="filteredList.length"
      ><table>
        <thead>
          <tr>
            <th>资产编号</th>
            <th>设备名称</th>
            <th>型号</th>
            <th>使用人</th>
            <th>部门</th>
            <th>状态</th>
            <th>备注</th>
            <th>采购日期</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredList" :key="item.id">
            <td>{{ item.asset_number }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.model || '—' }}</td>
            <td>{{ item.user_name || '—' }}</td>
            <td>{{ item.department || '—' }}</td>
            <td>
              <span class="badge" :class="statusClass(item.status)">{{
                statusText(item.status)
              }}</span>
            </td>
            <td>{{ item.notes || '—' }}</td>
            <td>{{ item.purchase_date || '—' }}</td>
            <td>
              <button
                type="button"
                class="row-action"
                v-if="canWriteAssets"
                @click="edit(item)"
                style="color: #2563eb; cursor: pointer; margin-right: 10px"
              >
                编辑
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

    <!-- 新增弹窗 -->
    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>{{ form.id ? '编辑 IT 设备' : '新增 IT 设备' }}</h3>
        <div class="form-row" v-if="form.id">
          <label>资产编号</label><input v-model="form.asset_number" disabled />
        </div>
        <div class="form-row">
          <label>设备名称</label
          ><select v-model="form.name">
            <option value="">-- 请选择 --</option>
            <option>打印机</option>
            <option>服务器</option>
            <option>路由器</option>
            <option>主机</option>
            <option>显示器</option>
            <option>交换机</option>
          </select>
        </div>
        <div class="form-row" v-if="['打印机', '服务器', '路由器', '交换机'].includes(form.name)">
          <label>型号</label><input v-model="form.model" />
        </div>
        <div class="form-row" v-if="['服务器', '路由器', '交换机'].includes(form.name)">
          <label>备注</label><input v-model="form.notes" />
        </div>
        <div class="form-row"><label>使用人</label><input v-model="form.user_name" /></div>
        <div class="form-row">
          <label>部门</label>
          <select v-model="form.department">
            <option value="">-- 请选择 --</option>
            <option v-for="d in deptList" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-row">
          <label>采购日期</label><input type="date" v-model="form.purchase_date" />
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

const list = ref([])
const deptList = ref([])
const filter = ref({ keyword: '', department: '', status: '' })
const filteredList = computed(() => {
  return list.value.filter((item) => {
    if (filter.value.department && item.department !== filter.value.department) return false
    if (filter.value.status && item.status !== filter.value.status) return false
    if (filter.value.keyword) {
      const kw = filter.value.keyword.toLowerCase()
      const text =
        `${item.asset_number || ''} ${item.name || ''} ${item.user_name || ''}`.toLowerCase()
      if (!text.includes(kw)) return false
    }
    return true
  })
})
const showForm = ref(false)
const form = ref({
  asset_number: '',
  name: '',
  model: '',
  notes: '',
  user_name: '',
  department: '',
  purchase_date: '',
})

async function load() {
  const res = await api.get('/assets/it')
  list.value = res.data
}

function edit(item) {
  Object.assign(form.value, item)
  showForm.value = true
}

function askDelete(item) {
  deleteTarget.value = {
    table_name: 'it_assets',
    record_id: item.id,
    record_desc: `${item.asset_number} ${item.name}`,
  }
}

async function save() {
  const data = { ...form.value }
  if (!data.purchase_date) data.purchase_date = null
  if (data.id) {
    await api.put(`/assets/it/${data.id}`, data)
  } else {
    await api.post('/assets/it', data)
  }
  showForm.value = false
  form.value = {
    id: null,
    asset_number: '',
    name: '',
    user_name: '',
    department: '',
    purchase_date: '',
  }
  load()
}

function statusClass(s) {
  return { in_use: 'green', idle: 'amber', scrapped: 'red', archived: 'gray' }[s] || 'gray'
}
function statusText(s) {
  return { in_use: '在用', idle: '闲置', scrapped: '已报废', archived: '已归档' }[s] || s
}

onMounted(async () => {
  load()
  const res = await api.get('/departments')
  deptList.value = res.data
})

function openCreateForm() {
  form.value = {
    id: null,
    asset_number: '',
    name: '',
    user_name: '',
    department: '',
    purchase_date: '',
  }
  showForm.value = true
}
</script>
