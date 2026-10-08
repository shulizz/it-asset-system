<template>
  <div style="display:flex;gap:8px">
    <button class="ie-btn" @click="downloadTemplate" title="下载Excel导入模板">下载模板</button>
    <button class="ie-btn" @click="exportFile">导出</button>
    <button class="ie-btn primary" @click="$refs.fileInput.click()">导入</button>
    <input ref="fileInput" type="file" accept=".xlsx" style="display:none" @change="onImport">
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'
import { getBaseURL } from '../api'

defineProps({ module: { type: String, required: true } })
const fileInput = ref(null)

function authHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function exportFile() {
  const token = localStorage.getItem('token')
  const base = getBaseURL()
  fetch(`${base}/ie/${module}/export`, { headers: authHeaders() })
    .then(r => r.blob())
    .then(blob => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = ''
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    })
    .catch(() => alert('导出失败'))
}

function downloadTemplate() {
  const base = getBaseURL()
  fetch(`${base}/ie/${module}/template`, { headers: authHeaders() })
    .then(r => r.blob())
    .then(blob => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = ''
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    })
}

async function onImport(e) {
  const file = e.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await api.post(`/ie/${module}/import`, formData, {
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
