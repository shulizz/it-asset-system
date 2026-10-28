<template>
  <div>
    <PageHeading title="修改密码" description="先验证当前密码，再设置新的账户密码。" />
    <section class="password-panel" aria-labelledby="password-section-title">
      <div class="password-account">
        <AppIcon name="shield" />
        <div>
          <strong>{{ currentUser.username }}</strong>
          <p>修改成功后，所有设备上的旧登录均会失效。</p>
        </div>
      </div>
      <ol class="password-steps">
        <li :class="{ active: !verified }">1. 验证当前密码</li>
        <li :class="{ active: verified }">2. 设置新密码</li>
      </ol>
      <form v-if="!verified" @submit.prevent="verify">
        <h3 id="password-section-title">验证当前密码</h3>
        <div class="form-row">
          <label for="account-current-password">当前密码</label
          ><input
            id="account-current-password"
            v-model="currentPassword"
            type="password"
            autocomplete="current-password"
            maxlength="72"
            required
            :disabled="busy"
          />
        </div>
        <p v-if="error" class="password-error" role="alert">{{ error }}</p>
        <button class="btn-primary" type="submit" :disabled="busy">
          {{ busy ? '正在验证…' : '验证并继续' }}
        </button>
      </form>
      <form v-else @submit.prevent="save">
        <h3 id="password-section-title">设置新密码</h3>
        <p class="password-verified" role="status">当前密码已验证，请填写新密码。</p>
        <div class="form-row">
          <label for="account-new-password">新密码</label
          ><input
            id="account-new-password"
            ref="newPasswordInput"
            v-model="newPassword"
            type="password"
            autocomplete="new-password"
            minlength="10"
            maxlength="72"
            required
            :disabled="busy"
          />
          <p class="password-hint">至少10个字符，最多72个UTF-8字节；不能与当前密码相同。</p>
        </div>
        <div class="form-row">
          <label for="account-confirm-password">确认新密码</label
          ><input
            id="account-confirm-password"
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            minlength="10"
            maxlength="72"
            required
            :disabled="busy"
          />
        </div>
        <p v-if="error" class="password-error" role="alert">{{ error }}</p>
        <div class="password-actions">
          <button class="btn-outline" type="button" :disabled="busy" @click="back">重新验证</button
          ><button class="btn-primary" type="submit" :disabled="busy">
            {{ busy ? '正在保存…' : '保存新密码' }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>
<script setup>
import { nextTick, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeading from '../components/PageHeading.vue'
import AppIcon from '../components/AppIcon.vue'
import api from '../api'
import { currentUser, clearSession, captureSession } from '../userState'
const router = useRouter()
const currentPassword = ref(''),
  newPassword = ref(''),
  confirmPassword = ref('')
const verified = ref(false),
  busy = ref(false),
  error = ref(''),
  newPasswordInput = ref(null)
function clearPasswords() {
  currentPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
}
let mounted = true
onBeforeUnmount(() => {
  mounted = false
  clearPasswords()
})
function back() {
  verified.value = false
  clearPasswords()
  error.value = ''
}
function showError(e) {
  error.value =
    typeof e.response?.data?.detail === 'string'
      ? e.response.data.detail
      : '操作失败，请检查网络后重试'
  if (e.response?.status === 401) {
    clearPasswords()
    clearSession()
    router.replace('/login')
  }
  if (e.response?.status === 409) {
    verified.value = false
    clearPasswords()
  }
}
async function verify() {
  if (busy.value) return
  const sameSession = captureSession()
  error.value = ''
  busy.value = true
  try {
    await api.post('/auth/password/verify', { current_password: currentPassword.value })
    if (!mounted || !sameSession()) return
    verified.value = true
    busy.value = false
    await nextTick()
    newPasswordInput.value?.focus()
  } catch (e) {
    if (mounted && sameSession()) showError(e)
  } finally {
    busy.value = false
  }
}
async function save() {
  if (busy.value) return
  const sameSession = captureSession()
  error.value = ''
  if (newPassword.value !== confirmPassword.value) {
    error.value = '两次填写的新密码不一致'
    return
  }
  if (
    Array.from(newPassword.value).length < 10 ||
    new TextEncoder().encode(newPassword.value).length > 72
  ) {
    error.value = '新密码至少10个字符，最多72个UTF-8字节'
    return
  }
  if (newPassword.value === currentPassword.value) {
    error.value = '新密码不能与当前密码相同'
    return
  }
  busy.value = true
  try {
    await api.post('/auth/password/change', {
      current_password: currentPassword.value,
      new_password: newPassword.value,
      confirm_password: confirmPassword.value,
    })
    if (!mounted || !sameSession()) return
    clearPasswords()
    clearSession()
    await router.replace({ path: '/login', query: { passwordChanged: '1' } })
  } catch (e) {
    if (mounted && sameSession()) showError(e)
  } finally {
    busy.value = false
  }
}
</script>
<style scoped>
.password-panel {
  max-width: 560px;
  padding: 28px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
}
.password-account {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding-bottom: 22px;
  border-bottom: 1px solid var(--line);
}
.password-account > .app-icon {
  color: var(--primary);
  width: 26px;
  height: 26px;
}
.password-account p,
.password-hint {
  margin-top: 6px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.7;
}
.password-steps {
  display: flex;
  gap: 22px;
  list-style: none;
  margin: 24px 0;
  color: var(--muted);
  font-size: 12px;
}
.password-steps .active {
  color: var(--primary);
  font-weight: 600;
}
.password-panel h3 {
  margin-bottom: 20px;
}
.password-panel input {
  width: 100%;
}
.password-error {
  margin-bottom: 16px;
  color: #b42318;
}
.password-verified {
  margin-bottom: 20px;
  color: #087f72;
}
.password-actions {
  display: flex;
  gap: 10px;
}
@media (max-width: 600px) {
  .password-panel {
    padding: 20px;
  }
  .password-steps {
    gap: 14px;
  }
  .password-actions > button {
    flex: 1;
  }
}
</style>
