<template>
  <Teleport to="body">
    <div v-if="target" class="modal-mask" @click.self="close" @keydown.esc="close">
      <section class="modal delete-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title">
        <h3 id="delete-dialog-title">申请删除</h3>
        <p class="description">{{ target.record_desc }}</p>
        <template v-if="!submitted">
          <p class="hint">审批通过后会移出档案并保留历史记录。提交申请不会立即删除。</p>
          <form @submit.prevent="submit">
            <div class="form-group"><label for="delete-reason">删除原因</label><textarea id="delete-reason" ref="reasonInput" v-model="reason" rows="3" required maxlength="1000" placeholder="请说明为什么需要删除这条记录" :disabled="sending"></textarea></div>
            <p v-if="error" class="error" role="alert">{{ error }}</p>
            <div class="actions"><button type="button" class="btn btn-outline" :disabled="sending" @click="close">取消</button><button class="btn btn-primary" :disabled="sending || !reason.trim()">{{ sending ? '提交中…' : '提交申请' }}</button></div>
          </form>
        </template>
        <template v-else><p class="success" role="status">删除申请已提交，等待管理员审批。</p><div class="actions"><button class="btn btn-primary" @click="close">完成</button></div></template>
      </section>
    </div>
  </Teleport>
</template>
<script setup>
import { ref, watch, nextTick } from 'vue'
import api from '../api'
const props = defineProps({ target: Object })
const emit = defineEmits(['close', 'submitted'])
const reason = ref(''), error = ref(''), sending = ref(false), submitted = ref(false), reasonInput = ref(null)
let previousFocus
watch(() => props.target, async target => { if (target) { previousFocus = document.activeElement; reason.value = ''; error.value = ''; submitted.value = false; await nextTick(); reasonInput.value?.focus() } })
function close() { if (!sending.value) { emit('close'); previousFocus?.focus() } }
async function submit() {
  if (sending.value || !reason.value.trim()) return
  sending.value = true; error.value = ''
  try { await api.post('/delete-request', {...props.target, reason: reason.value.trim()}); submitted.value = true; emit('submitted') }
  catch (e) { error.value = typeof e.response?.data?.detail === 'string' ? e.response.data.detail : '提交失败，请检查网络后重试' }
  finally { sending.value = false }
}
</script>
<style scoped>
.delete-dialog h3 { margin-bottom:12px; }.description { font-weight:600; overflow-wrap:anywhere; }.hint { font-size:13px; color:#64748b; line-height:1.7; margin:12px 0 18px; }.actions { display:flex; justify-content:flex-end; gap:10px; margin-top:16px; }.error { color:#c83535; }.success { color:#16834a; margin:18px 0; }
</style>
