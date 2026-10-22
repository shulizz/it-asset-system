<template>
  <div>
    <PageHeading
      title="消防设备"
      description="登记消防设备、购买时间和到期时间，及时跟进设备更换。"
    >
      <div class="fire-actions">
        <ExpiryEmailDialog module="fire" />
        <ImportExportButtons module="fire" /><button class="btn-primary" @click="openForm">
          + 新增消防设备
        </button>
      </div>
    </PageHeading>
    <p class="fire-notice">已到期 {{ overdue }} 台 · 30 天内到期 {{ upcoming }} 台</p>
    <div class="filter-bar">
      <input
        aria-label="搜索消防设备"
        v-model="keyword"
        placeholder="搜索编号、消防设备、位置或部门"
      />
      <select aria-label="到期筛选" v-model="expiryFilter">
        <option value="">全部到期状态</option>
        <option value="overdue">已到期</option>
        <option value="upcoming">30天内到期</option>
      </select>
    </div>
    <p v-if="error" class="fire-error" role="alert">{{ error }}</p>
    <TableFrame title="消防设备台账" :count="filtered.length">
      <table>
        <thead>
          <tr>
            <th>资产编号</th>
            <th>消防设备</th>
            <th>位置</th>
            <th>购买时间</th>
            <th>到期时间</th>
            <th>到期状态</th>
            <th>部门</th>
            <th>状态</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.id">
            <td>{{ item.asset_number }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.location || '—' }}</td>
            <td>{{ item.purchase_date || '—' }}</td>
            <td>{{ item.expiry_date || '—' }}</td>
            <td>
              <span class="badge" :class="expiryClass(item)">{{ expiryText(item) }}</span>
            </td>
            <td>{{ item.department || '—' }}</td>
            <td>{{ statusText(item.status) }}</td>
            <td>
              <button v-if="item.status !== 'scrapped'" class="row-action" @click="edit(item)">
                编辑
              </button>
              <button class="delete-action" @click="askDelete(item)">申请删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </TableFrame>
    <div v-if="showForm" class="modal-mask" @click.self="showForm = false">
      <form class="modal" @submit.prevent="save">
        <h3>{{ form.id ? '编辑消防设备' : '新增消防设备' }}</h3>
        <div class="form-row">
          <label for="fire-name">消防设备</label
          ><input
            id="fire-name"
            v-model="form.name"
            maxlength="100"
            required
            placeholder="如：干粉灭火器"
          />
        </div>
        <div class="form-row">
          <label for="fire-purchased">购买时间</label
          ><input id="fire-purchased" type="date" v-model="form.purchase_date" />
        </div>
        <div class="form-row">
          <label for="fire-location">位置</label
          ><input
            id="fire-location"
            v-model="form.location"
            maxlength="200"
            placeholder="如：一楼大厅东侧、二楼消防通道"
          />
        </div>
        <div class="form-row">
          <label for="fire-expiry">到期时间</label
          ><input
            id="fire-expiry"
            type="date"
            v-model="form.expiry_date"
            :min="form.purchase_date || undefined"
          />
        </div>
        <div class="form-row">
          <label for="fire-dept">部门</label
          ><select id="fire-dept" v-model="form.department">
            <option value="">未分配部门</option>
            <option v-for="d in departments" :key="d.id" :value="d.name">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-row">
          <label for="fire-user">保管人</label><input id="fire-user" v-model="form.user_name" />
        </div>
        <div class="form-row">
          <label for="fire-status">状态</label
          ><select id="fire-status" v-model="form.status">
            <option value="in_use">在用</option>
            <option value="idle">闲置</option>
          </select>
        </div>
        <div class="form-row">
          <label for="fire-notes">备注</label><input id="fire-notes" v-model="form.notes" />
        </div>
        <p v-if="formError" class="fire-error" role="alert">{{ formError }}</p>
        <div class="fire-actions">
          <button type="button" class="btn-outline" @click="showForm = false">取消</button
          ><button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </form>
    </div>
    <DeleteRequestDialog :target="deleteTarget" @close="deleteTarget = null" />
  </div>
</template>
<script setup>
import { computed, ref, onMounted } from 'vue'
import api from '../api'
import { daysUntil } from '../medicalDates'
import PageHeading from '../components/PageHeading.vue'
import TableFrame from '../components/TableFrame.vue'
import ImportExportButtons from '../components/ImportExportButtons.vue'
import DeleteRequestDialog from '../components/DeleteRequestDialog.vue'
import ExpiryEmailDialog from '../components/ExpiryEmailDialog.vue'
const list = ref([]),
  departments = ref([]),
  keyword = ref(''),
  expiryFilter = ref(''),
  showForm = ref(false),
  saving = ref(false),
  error = ref(''),
  formError = ref(''),
  deleteTarget = ref(null)
const blank = () => ({
  name: '',
  location: '',
  purchase_date: '',
  expiry_date: '',
  department: '',
  user_name: '',
  status: 'in_use',
  notes: '',
})
const form = ref(blank())
const activeDue = (item) =>
  !['scrapped', 'archived'].includes(item.status) ? daysUntil(item.expiry_date) : null
const overdue = computed(
  () => list.value.filter((x) => activeDue(x) !== null && activeDue(x) < 0).length,
)
const upcoming = computed(
  () =>
    list.value.filter((x) => activeDue(x) !== null && activeDue(x) >= 0 && activeDue(x) <= 30)
      .length,
)
const filtered = computed(() =>
  list.value.filter((x) => {
    if (
      keyword.value &&
      !`${x.asset_number} ${x.name} ${x.location || ''} ${x.department || ''}`
        .toLowerCase()
        .includes(keyword.value.toLowerCase())
    )
      return false
    const days = activeDue(x)
    return (
      !expiryFilter.value ||
      (days !== null && (expiryFilter.value === 'overdue' ? days < 0 : days >= 0 && days <= 30))
    )
  }),
)
const statusText = (s) => ({ in_use: '在用', idle: '闲置', scrapped: '已报废' })[s] || s
function expiryText(item) {
  const days = activeDue(item)
  return days === null ? '—' : days < 0 ? `已到期 ${-days} 天` : `剩余 ${days} 天`
}
function expiryClass(item) {
  const days = activeDue(item)
  return days === null ? 'gray' : days < 0 ? 'red' : days <= 30 ? 'amber' : 'green'
}
function openForm() {
  form.value = blank()
  formError.value = ''
  showForm.value = true
}
function edit(item) {
  form.value = {
    ...item,
    purchase_date: item.purchase_date || '',
    expiry_date: item.expiry_date || '',
    department: item.department || '',
  }
  formError.value = ''
  showForm.value = true
}
function askDelete(item) {
  deleteTarget.value = {
    table_name: 'fire_assets',
    record_id: item.id,
    record_desc: `${item.asset_number} ${item.name}`,
  }
}
async function load() {
  try {
    list.value = (await api.get('/assets/fire')).data
    error.value = ''
  } catch (e) {
    error.value = e.response?.data?.detail || '消防设备加载失败，请刷新重试'
  }
}
async function save() {
  if (saving.value) return
  formError.value = ''
  if (
    form.value.purchase_date &&
    form.value.expiry_date &&
    form.value.expiry_date < form.value.purchase_date
  ) {
    formError.value = '到期时间不能早于购买时间'
    return
  }
  saving.value = true
  try {
    const payload = {
      ...form.value,
      purchase_date: form.value.purchase_date || null,
      expiry_date: form.value.expiry_date || null,
      department: form.value.department || null,
    }
    if (form.value.id) await api.put(`/assets/fire/${form.value.id}`, payload)
    else await api.post('/assets/fire', payload)
    showForm.value = false
    await load()
  } catch (e) {
    formError.value =
      typeof e.response?.data?.detail === 'string'
        ? e.response.data.detail
        : '保存失败，请检查设备名称和日期'
  } finally {
    saving.value = false
  }
}
onMounted(async () => {
  await Promise.all([
    load(),
    api
      .get('/departments')
      .then((r) => (departments.value = r.data))
      .catch(() => (error.value = '部门列表加载失败，请刷新重试')),
  ])
})
</script>
<style scoped>
.fire-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  flex-wrap: wrap;
}
.fire-notice {
  padding: 12px 16px;
  margin-bottom: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: var(--muted);
}
.fire-error {
  color: #b42318;
  margin: 12px 0;
}
</style>
