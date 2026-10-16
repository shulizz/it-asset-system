<template>
  <div>
    <PageHeading title="微信账号管理" description="维护账号资料及使用归属，敏感信息按权限展示。"
      ><div style="display: flex; gap: 8px; align-items: center">
        <ImportExportButtons module="wechat" />
        <button class="btn-primary" @click="openAdd">+ 新增账号</button>
      </div></PageHeading
    >
    <TableFrame title="账号列表" :count="list.length"
      ><table>
        <thead>
          <tr>
            <th>微信账号</th>
            <th>微信密码</th>
            <th>实名人</th>
            <th>使用人</th>
            <th>用途</th>
            <th>状态</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list" :key="item.id">
            <td>{{ item.wx_account }}</td>
            <td>
              <span v-if="item.password_error" style="color: #b45309">{{
                item.password_error
              }}</span
              ><span v-else>{{ item.wx_password }}</span>
            </td>
            <td>{{ item.real_name }}</td>
            <td>{{ item.user_name }}</td>
            <td>{{ item.purpose }}</td>
            <td>
              <span class="badge" :class="item.status === 'in_use' ? 'green' : 'gray'">{{
                item.status === 'in_use' ? '使用中' : '停用'
              }}</span>
            </td>
            <td>
              <button class="btn-outline" @click="edit(item)">编辑</button>
              <button class="btn-outline" style="color: #ef4444" @click="remove(item)">删除</button>
            </td>
          </tr>
        </tbody>
      </table></TableFrame
    >
    <div v-if="showForm" class="modal-mask" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ form.id ? '编辑账号' : '新增账号' }}</h3>
        <div class="form-row"><label>微信账号</label><input v-model="form.wx_account" /></div>
        <div class="form-row"><label>微信密码</label><input v-model="form.wx_password" /></div>
        <div class="form-row"><label>实名人</label><input v-model="form.real_name" /></div>
        <div class="form-row"><label>使用人</label><input v-model="form.user_name" /></div>
        <div class="form-row"><label>用途</label><input v-model="form.purpose" /></div>
        <div class="form-row">
          <label>状态</label>
          <select v-model="form.status">
            <option value="in_use">使用中</option>
            <option value="stopped">停用</option>
          </select>
        </div>
        <div style="text-align: right">
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
const list = ref([])
const showForm = ref(false)
const form = ref({
  id: null,
  wx_account: '',
  wx_password: '',
  real_name: '',
  user_name: '',
  purpose: '',
  status: 'in_use',
})
async function load() {
  list.value = ((await api.get('/wechat')).data || []).filter((x) => x.wx_account)
}
function openAdd() {
  form.value = {
    id: null,
    wx_account: '',
    wx_password: '',
    real_name: '',
    user_name: '',
    purpose: '',
    status: 'in_use',
  }
  showForm.value = true
}
function edit(item) {
  Object.assign(form.value, item)
  showForm.value = true
}
async function save() {
  if (form.value.id) await api.put(`/wechat/${form.value.id}`, form.value)
  else await api.post('/wechat', form.value)
  showForm.value = false
  load()
}
async function remove(item) {
  if (!confirm('确定删除 ' + item.wx_account + '?')) return
  await api.delete('/wechat/' + item.id)
  load()
}
onMounted(load)
</script>
