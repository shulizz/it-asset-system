<template>
  <div>
    <PageHeading title="部门管理" description="维护组织部门与负责人，查看资产归属。"
      ><div style="display: flex; gap: 8px; align-items: center">
        <ImportExportButtons module="department" />
        <button class="btn-primary" @click="openForm">+ 新增部门</button>
      </div></PageHeading
    >
    <TableFrame title="部门列表" :count="list.length"
      ><table>
        <thead>
          <tr>
            <th>部门名称</th>
            <th>负责人</th>
            <th>备注</th>
            <th>设备数</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list" :key="item.id">
            <td>{{ item.name }}</td>
            <td>{{ item.manager || '—' }}</td>
            <td>{{ item.note || '—' }}</td>
            <td>{{ countMap[item.name] || 0 }}</td>
            <td>
              <button
                type="button"
                class="row-action"
                @click="edit(item)"
                style="color: #2563eb; cursor: pointer; margin-right: 10px"
              >
                编辑</button
              ><button
                type="button"
                class="row-action"
                @click="askDelete(item)"
                style="color: #ef4444; cursor: pointer"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table></TableFrame
    >
    <div v-if="showForm" class="modal-mask" @click="showForm = false">
      <div class="modal" @click.stop>
        <h3>{{ form.id ? '编辑部门' : '新增部门' }}</h3>
        <div class="form-row"><label>部门名称</label><input v-model="form.name" /></div>
        <div class="form-row"><label>负责人</label><input v-model="form.manager" /></div>
        <div class="form-row"><label>备注</label><input v-model="form.note" /></div>
        <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px">
          <button class="btn-outline" @click="showForm = false">取消</button>
          <button class="btn-primary" @click="save">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import PageHeading from '../components/PageHeading.vue'
import TableFrame from '../components/TableFrame.vue'
import { ref, onMounted } from 'vue'
import api from '../api'
import ImportExportButtons from '../components/ImportExportButtons.vue'
const list = ref([]),
  showForm = ref(false),
  countMap = ref({})
const form = ref({ id: null, name: '', manager: '', note: '' })
async function load() {
  const res = await api.get('/departments')
  list.value = res.data
  const [it, phone, medical, numbers] = await Promise.all([
    api.get('/assets/it'),
    api.get('/assets/phone'),
    api.get('/assets/medical'),
    api.get('/assets/numbers'),
  ])
  const map = {}
  ;[...it.data, ...phone.data, ...medical.data, ...numbers.data].forEach((a) => {
    if (a.department) map[a.department] = (map[a.department] || 0) + 1
  })
  countMap.value = map
}
function openForm() {
  form.value = { id: null, name: '', manager: '', note: '' }
  showForm.value = true
}
function edit(item) {
  Object.assign(form.value, item)
  showForm.value = true
}
async function askDelete(item) {
  if (!confirm(`确定删除部门"${item.name}"？有关联用户、资产或历史记录的部门需要保留。`)) return
  try {
    await api.delete(`/departments/${item.id}`)
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}
async function save() {
  try {
    if (form.value.id) await api.put(`/departments/${form.value.id}`, form.value)
    else await api.post('/departments', form.value)
    showForm.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  }
}
onMounted(load)
</script>
