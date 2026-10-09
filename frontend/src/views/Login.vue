<template>
  <div class="login-wrap">
    <section class="login-intro"><span class="intro-mark">资产</span><h2>让每一项资产<br>都有清晰的去向。</h2><p>统一资产档案、设备流转与审批记录，<br>让日常管理更有条理。</p><div class="intro-capabilities"><span>资产档案</span><span>流转审批</span><span>报表统计</span></div></section>
    <div class="login-box">
      <h1>固定资产管理系统</h1>
      <p>登录账号，进入资产管理工作台</p>
      <div class="form-group">
        <label for="login-username">账号</label>
        <input id="login-username" v-model="username" autocomplete="username" placeholder="请输入账号">
      </div>
      <div class="form-group">
        <label for="login-password">密码</label>
        <input id="login-password" v-model="password" autocomplete="current-password" type="password" placeholder="请输入密码" @keyup.enter="login">
      </div>
      <label class="remember">
        <input type="checkbox" v-model="remember"> 记住账号
      </label>
      <button class="btn-login" @click="login">登录工作台</button>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <p style="text-align:center;margin-top:16px"><a @click="showSettings=true" style="color:#94a3b8;font-size:12px;cursor:pointer">服务器设置</a></p>
    </div>

    <div v-if="showSettings" class="modal-mask" @click="showSettings=false">
      <div class="modal" @click.stop>
        <h3 style="margin-bottom:16px">服务器设置</h3>
        <div class="form-group">
          <label>服务器地址</label>
          <input v-model="serverURL" placeholder="如：http://192.168.4.106:8000">
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end">
          <button class="btn-outline" @click="showSettings=false">取消</button>
          <button class="btn-primary" @click="saveServer">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { setServerURL } from '../api'

const router = useRouter()
const username = ref(localStorage.getItem('remember_username') || '')
localStorage.removeItem('remember_password')
const password = ref('')
const remember = ref(!!localStorage.getItem('remember_username'))
const error = ref('')
const showSettings = ref(false)
const serverURL = ref(localStorage.getItem('server_url') || 'https://promptly-equation-cinch.ngrok-free.dev')

function saveServer() {
  setServerURL(serverURL.value.replace(/\/+$/, ''))
  showSettings.value = false
  error.value = ''
}

async function login() {
  error.value = ''
  try {
    const res = await api.post('/auth/login', { username: username.value, password: password.value })
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    if (remember.value) {
      localStorage.setItem('remember_username', username.value)
      localStorage.removeItem('remember_password')
    } else {
      localStorage.removeItem('remember_username')
      localStorage.removeItem('remember_password')
    }
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  }
}
</script>

<style scoped>
.login-intro { width:440px; padding:30px 48px 30px 0; color:#fff; }.intro-mark { display:grid; place-items:center; width:48px; height:48px; border-radius:10px; background:#3478f6; font-weight:700; margin-bottom:44px; }.login-intro h2 { font-size:34px; line-height:1.55; font-weight:600; letter-spacing:1px; }.login-intro p { font-size:14px; line-height:1.9; color:#aabbd2; margin-top:20px; }.intro-capabilities { display:flex; gap:20px; margin-top:40px; font-size:12px; color:#c5d2e3; }

.login-wrap { min-height: 100dvh; padding:32px 24px; display: flex; align-items: center; justify-content: center; background: #14243b; }
.login-box { background: #fff; padding: 40px; border-radius: 12px; width: 400px; max-width:100%; box-shadow: 0 20px 60px rgba(0,0,0,.3); }
.login-box h1 { font-size: 20px; text-align: center; margin-bottom: 4px; }
.login-box p { text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 28px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; color: #64748b; margin-bottom: 6px; }
.form-group input { width: 100%; height: 40px; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; }
.form-group input:focus { outline: none; border-color: #2563eb; }
.remember { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #64748b; margin-bottom: 16px; cursor: pointer; }
.btn-login { width: 100%; height: 42px; background: #2865db; color: #fff; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; }
.btn-login:hover { background: #1e51b8; }
.login-box p.error { margin-bottom:0; color: #ef4444; font-size: 13px; text-align: center; margin-top: 12px; }
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; border-radius: 12px; padding: 24px; width: 400px; }
.btn-outline { background: #fff; border: 1px solid #e2e8f0; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
.btn-primary { background: #2563eb; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
@media(max-width:850px) { .login-intro { width:340px; padding-right:32px; }.login-intro h2 { font-size:28px; } }
@media(max-width:680px) { .login-intro { display:none; }.login-box { padding:32px 24px; }.login-wrap { padding:20px; } }
</style>





