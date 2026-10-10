<template>
  <button class="btn btn-outline" @click="open">发送提醒邮件</button>
  <Teleport to="body">
    <div v-if="visible" class="modal-mask" @click.self="close">
      <section class="modal" role="dialog" aria-modal="true" aria-labelledby="expiry-mail-title">
        <h3 id="expiry-mail-title">选择提醒邮件收件人</h3>
        <p class="hint">发送医疗设备30天内到期及已过期的提醒。邮箱来自“用户权限”中保存的用户资料。</p>
        <p v-if="loading">正在加载收件人…</p>
        <template v-else>
          <p v-if="!configured" class="warning">服务器尚未配置发件邮箱和SMTP授权码，完成配置后才能发送。</p>
          <p v-if="!recipients.length" class="hint">暂无可选用户，请先在“用户权限”中为启用的用户填写邮箱。</p>
          <div class="recipient-list"><label v-for="user in recipients" :key="user.id" class="recipient"><input type="checkbox" v-model="selected" :value="user.id" :disabled="sending"><span>{{ user.name }}<small>{{ user.email }}</small></span></label></div>
        </template>
        <p v-if="message" :class="success ? 'success' : 'error'" role="status">{{ message }}</p>
        <div class="actions"><button class="btn btn-outline" :disabled="sending" @click="close">关闭</button><button class="btn btn-primary" :disabled="loading || sending || !configured || !selected.length || success" @click="send">{{ sending ? '发送中…' : '发送给所选用户' }}</button></div>
      </section>
    </div>
  </Teleport>
</template>
<script setup>
import { ref } from 'vue'
import api from '../api'
const visible=ref(false),loading=ref(false),sending=ref(false),configured=ref(false),success=ref(false),recipients=ref([]),selected=ref([]),message=ref('')
function close(){if(!sending.value)visible.value=false}
async function open(){
  visible.value=true;loading.value=true;message.value='';selected.value=[];recipients.value=[];configured.value=false;success.value=false
  try{ const {data}=await api.get('/assets/medical/notice-recipients');recipients.value=data.users;configured.value=data.smtp_configured }
  catch(e){ message.value=typeof e.response?.data?.detail==='string'?e.response.data.detail:'收件人加载失败，请重试' }
  finally{loading.value=false}
}
async function send(){
  if(sending.value || !configured.value || !selected.value.length || success.value)return
  sending.value=true;message.value=''
  try{const {data}=await api.post('/assets/medical/send-expiry-email?days=30',{recipient_user_ids:selected.value});success.value=data.success===true;message.value=data.message}
  catch(e){message.value=typeof e.response?.data?.detail==='string'?e.response.data.detail:'发送失败，请重试'}
  finally{sending.value=false}
}
</script>
<style scoped>
.hint { color:#64748b; font-size:13px; line-height:1.7; margin:12px 0; }.recipient-list { max-height:280px; overflow:auto; margin:16px 0; }.recipient { display:flex; gap:12px; align-items:center; border-bottom:1px solid #e2e8f1; padding:12px 0; }.recipient small { display:block; color:#64748b; margin-top:4px; overflow-wrap:anywhere; }.warning { padding:12px; background:#fff4df; color:#915f18; font-size:13px; line-height:1.6; }.actions { display:flex; justify-content:flex-end; gap:10px; margin-top:18px; }.error { color:#c83535; }.success { color:#16834a; }
</style>
