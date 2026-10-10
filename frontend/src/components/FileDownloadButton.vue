<template>
  <button type="button" :class="buttonClass" :disabled="loading" @click="prepare">{{ loading ? '生成中…' : label }}</button>
  <Teleport to="body">
    <div v-if="visible" class="modal-mask" @click.self="close">
      <section class="modal download-dialog" role="dialog" aria-modal="true" aria-labelledby="download-title">
        <h3 id="download-title">{{ error ? '下载失败' : '文件已生成' }}</h3>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <template v-else><p class="file-name">{{ savedName }}</p><p class="hint">如果没有自动下载，请点击下方按钮保存。部分应用内浏览器需要从菜单选择“在浏览器中打开”。</p><a class="btn btn-primary" :href="url" :download="savedName" target="_blank" rel="noopener">保存文件</a></template>
        <div class="actions"><button class="btn btn-outline" @click="close">关闭</button></div>
      </section>
    </div>
  </Teleport>
</template>
<script setup>
import { ref, onUnmounted } from 'vue'
import api from '../api'
const props = defineProps({ endpoint: {type:String,required:true}, filename:{type:String,required:true}, label:{type:String,default:'导出'}, buttonClass:{type:String,default:'btn btn-outline'} })
const loading=ref(false),visible=ref(false),error=ref(''),url=ref(''),savedName=ref('')
const pendingURLs = new Map()
function releaseAfterDownload(objectURL) { if(!objectURL || pendingURLs.has(objectURL)) return; const timer=setTimeout(()=>{URL.revokeObjectURL(objectURL);pendingURLs.delete(objectURL)},60000);pendingURLs.set(objectURL,timer) }
function close() { visible.value=false; releaseAfterDownload(url.value); url.value='' }
async function prepare() {
  if(loading.value) return
  releaseAfterDownload(url.value);url.value='';loading.value=true;error.value=''
  try {
    const res=await api.get(props.endpoint,{responseType:'blob'})
    const disposition=res.headers?.['content-disposition'] || ''
    const encoded=disposition.match(/filename\*=UTF-8''([^;]+)/i), plain=disposition.match(/filename="?([^";]+)"?/i)
    savedName.value=props.filename
    try { savedName.value=encoded ? decodeURIComponent(encoded[1]) : (plain?.[1] || props.filename) } catch {}
    savedName.value=savedName.value.replace(/[\\/\r\n]/g,'_')
    url.value=URL.createObjectURL(res.data)
    const anchor=document.createElement('a');anchor.href=url.value;anchor.download=savedName.value;document.body.appendChild(anchor);anchor.click();anchor.remove()
  } catch(e) {
    let detail=e.response?.data?.detail
    if(e.response?.data instanceof Blob) { try {detail=JSON.parse(await e.response.data.text()).detail} catch{} }
    error.value=typeof detail==='string'?detail:'下载失败，请检查网络及导出权限后重试'
  } finally { loading.value=false;visible.value=true }
}
onUnmounted(()=>{releaseAfterDownload(url.value)})
</script>
<style scoped>
.download-dialog h3 { margin-bottom:16px; }.file-name { overflow-wrap:anywhere; font-weight:600; }.hint { font-size:13px; color:#64748b; line-height:1.7; margin:12px 0 18px; }.actions { display:flex; justify-content:flex-end; margin-top:16px; }.error { color:#c83535; }
</style>
