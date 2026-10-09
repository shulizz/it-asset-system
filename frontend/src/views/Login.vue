<template>
  <div class="login-wrap">
    <div class="login-box">
      <h1>固定资产管理系统</h1>
      <p>固定资产管理系统</p>
      <div class="form-group">
        <label>账号</label>
        <input v-model="username" placeholder="请输入账号">
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="请输入密码" @keyup.enter="login">
      </div>
      <label class="remember">
        <input type="checkbox" v-model="remember"> 记住账号密码
      </label>
      <button class="btn-login" @click="login">登 录</button>
      <p v-if="error" class="error">{{ error }}</p>
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
.login-wrap { height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #0f2c3f, #0a1f2e); }
.login-box { background: #fff; padding: 40px; border-radius: 12px; width: 380px; box-shadow: 0 20px 60px rgba(0,0,0,.3); }
.login-box h1 { font-size: 20px; text-align: center; margin-bottom: 4px; }
.login-box p { text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 28px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; color: #64748b; margin-bottom: 6px; }
.form-group input { width: 100%; height: 40px; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; }
.form-group input:focus { outline: none; border-color: #2563eb; }
.remember { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #64748b; margin-bottom: 16px; cursor: pointer; }
.btn-login { width: 100%; height: 42px; background: #0d9488; color: #fff; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; }
.btn-login:hover { background: #0f766e; }
.error { color: #ef4444; font-size: 13px; text-align: center; margin-top: 12px; }
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; border-radius: 12px; padding: 24px; width: 400px; }
.btn-outline { background: #fff; border: 1px solid #e2e8f0; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
.btn-primary { background: #2563eb; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
</style>





