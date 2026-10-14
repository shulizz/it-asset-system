<template>
  <div v-if="allowed" class="user-import-buttons">
    <FileDownloadButton endpoint="/user-import/template" filename="新增用户_导入模板.xlsx" label="下载用户模板" />
    <button type="button" class="btn btn-outline" :disabled="uploading" @click="fileInput.click()">{{ uploading ? '导入中…' : '导入用户' }}</button>
    <input ref="fileInput" type="file" accept=".xlsx" hidden @change="importUsers">
  </div>
  <Teleport to="body">
    <div v-if="visible" class="modal-mask" @click.self="visible=false">
      <section class="modal" role="dialog" aria-modal="true" aria-labelledby="user-import-title">
        <h3 id="user-import-title">用户导入结果</h3>
        <p :class="success ? 'success' : 'error'" role="status">{{ message }}</p>
        <ul v-if="errors.length" class="import-errors"><li v-for="error in errors" :key="error.row">第{{ error.row }}行：{{ error.message }}</li></ul>
        <p v-if="!success" class="hint">检查模板后重新导入。已有账号不会被覆盖，角色名称不决定权限。</p>
        <div class="actions"><button class="btn btn-primary" @click="visible=false">知道了</button></div>
      </section>
    </div>
  </Teleport>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import FileDownloadButton from './FileDownloadButton.vue'
const emit=defineEmits(['imported'])
const fileInput=ref(null),uploading=ref(false),visible=ref(false),success=ref(false),message=ref(''),errors=ref([])
const allowed=ref(false)
onMounted(async()=>{try{allowed.value=(await api.get('/auth/me')).data.role==='super_admin'}catch{}})
async function importUsers(event){
  const file=event.target.files?.[0]
  if(!file || uploading.value)return
  errors.value=[];success.value=false;message.value='';uploading.value=true
  try{
    if(!file.name.toLowerCase().endsWith('.xlsx'))throw Error('请上传.xlsx用户模板')
    if(file.size>10*1024*1024)throw Error('导入文件不能超过10MB')
    const body=new FormData();body.append('file',file)
    const {data}=await api.post('/user-import/import',body)
    success.value=true;message.value=data.message;emit('imported')
  }catch(error){
    const detail=error.response?.data?.detail
    if(detail && typeof detail==='object' && Array.isArray(detail.errors)){message.value=detail.message;errors.value=detail.errors}
    else message.value=typeof detail==='string'?detail:(error.response ? '导入失败，请检查模板或重新登录' : error.message || '网络连接失败，请重试')
  }finally{uploading.value=false;visible.value=true;event.target.value=''}
}
</script>
<style scoped>
.user-import-buttons { display:flex; gap:8px; flex-wrap:wrap; }.success { color:#16834a; margin:16px 0; }.error { color:#c83535; margin:16px 0; }.import-errors { padding-left:20px; max-height:280px; overflow:auto; color:#c83535; font-size:13px; line-height:1.8; }.hint { color:#64748b; font-size:13px; line-height:1.7; margin:12px 0; }.actions { display:flex; justify-content:flex-end; margin-top:16px; }
</style>
