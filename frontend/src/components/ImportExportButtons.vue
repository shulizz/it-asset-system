<template>
  <div style="display:flex;gap:8px">
    <FileDownloadButton v-if="canImport" :endpoint="`/ie/${module}/template`" :filename="`${moduleName}_导入模板.xlsx`" label="下载模板" button-class="btn btn-outline" />
    <FileDownloadButton v-if="canExport" :endpoint="`/ie/${module}/export`" :filename="`${moduleName}.xlsx`" button-class="btn btn-outline" />
    <button v-if="canImport" class="ie-btn primary" @click="$refs.fileInput.click()">导入</button>
    <input ref="fileInput" type="file" accept=".xlsx" style="display:none" @change="onImport">
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import FileDownloadButton from './FileDownloadButton.vue'

const props = defineProps({ module: { type: String, required: true } })
const moduleName = computed(() => ({it:'IT设备',phone:'手机设备',medical:'医疗设备',number:'电话号码',wechat:'微信账号',department:'部门'}[props.module] || '资产表格'))
const fileInput = ref(null)
const currentUser = ref({ permissions: [] })
const modulePermission = computed(() => props.module === 'department' ? 'departments' : props.module === 'wechat' ? 'wechat' : 'assets')
const canUseModule = computed(() => currentUser.value.permissions?.includes(modulePermission.value) && (!['wechat', 'department'].includes(props.module) || currentUser.value.role === 'super_admin' || currentUser.value.data_scope === 'all'))
const canExport = computed(() => canUseModule.value && currentUser.value.permissions?.includes('export'))
const canImport = computed(() => canUseModule.value && currentUser.value.permissions?.includes('import') && ((currentUser.value.data_scope === 'all') || !['wechat', 'department'].includes(props.module)) && (props.module !== 'wechat' || currentUser.value.permissions?.includes('wechat_secret')))
onMounted(async () => {
  try { currentUser.value = (await api.get('/auth/me')).data } catch {}
})

async function onImport(e) {
  const file = e.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await api.post(`/ie/${props.module}/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    alert(res.data.message || '导入完成')
    if (res.data.errors && res.data.errors.length) {
      console.log('导入错误:', res.data.errors)
    }
    window.location.reload()
  } catch (err) {
    alert('导入失败: ' + (err.response?.data?.detail || err.message))
  }
  e.target.value = ''
}
</script>

<style scoped>
.ie-btn {
  padding: 7px 14px;
  border: 1px solid #cbd5e1;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #475569;
}
.ie-btn:hover { background: #f1f5f9; }
.ie-btn.primary { background: #2563eb; color: #fff; border-color: #2563eb; }
.ie-btn.primary:hover { background: #1d4ed8; }
</style>
