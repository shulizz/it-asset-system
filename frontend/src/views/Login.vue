<template>
  <div class="login-wrap">
    <section class="login-intro">
      <span class="intro-mark"><AppIcon name="asset" /></span>
      <h2>让每一项资产<br />都有清晰的去向。</h2>
      <p>统一资产档案、设备流转与审批记录，<br />让日常管理更有条理。</p>
      <div class="intro-capabilities">
        <span><AppIcon name="asset" />资产档案</span><span><AppIcon name="approval" />流转审批</span
        ><span><AppIcon name="reports" />报表统计</span>
      </div>
    </section>
    <div class="login-box">
      <div class="login-brand"><AppIcon name="asset" /></div>
      <h1>固定资产管理系统</h1>
      <p>登录账号，进入资产管理工作台</p>
      <div class="form-group">
        <label for="login-username">账号</label>
        <input
          id="login-username"
          v-model="username"
          autocomplete="username"
          placeholder="请输入账号"
        />
      </div>
      <div class="form-group">
        <label for="login-password">密码</label>
        <input
          id="login-password"
          v-model="password"
          autocomplete="current-password"
          type="password"
          placeholder="请输入密码"
          @keyup.enter="login"
        />
      </div>
      <label class="remember"> <input type="checkbox" v-model="remember" /> 记住账号 </label>
      <button class="btn-login" @click="login">登录工作台</button>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <p style="text-align: center; margin-top: 16px">
        <button type="button" class="server-settings" @click="showSettings = true">
          服务器设置
        </button>
      </p>
    </div>

    <div v-if="showSettings" class="modal-mask" @click="showSettings = false">
      <div class="modal" @click.stop>
        <h3 style="margin-bottom: 16px">服务器设置</h3>
        <div class="form-group">
          <label for="server-url">服务器地址</label>
          <input id="server-url" v-model="serverURL" placeholder="如：https://slzz.cloud" />
        </div>
        <div style="display: flex; gap: 8px; justify-content: flex-end">
          <button class="btn-outline" @click="showSettings = false">取消</button>
          <button class="btn-primary" @click="saveServer">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import AppIcon from '../components/AppIcon.vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { setServerURL, getServerURL } from '../api'
import { setCurrentUser } from '../userState'

const router = useRouter()
const username = ref(localStorage.getItem('remember_username') || '')
localStorage.removeItem('remember_password')
const password = ref('')
const remember = ref(!!localStorage.getItem('remember_username'))
const error = ref('')
const showSettings = ref(false)
const serverURL = ref(getServerURL())

function saveServer() {
  setServerURL(serverURL.value.replace(/\/+$/, ''))
  showSettings.value = false
  error.value = ''
}

async function login() {
  error.value = ''
  try {
    const res = await api.post('/auth/login', {
      username: username.value,
      password: password.value,
    })
    localStorage.setItem('token', res.data.token)
    setCurrentUser(res.data.user)
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
.login-wrap {
  min-height: 100dvh;
  background: #122d40;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 80px;
  padding: 48px 32px;
}
.login-intro {
  width: 400px;
  color: white;
  padding-block: 30px;
}
.intro-mark {
  width: 49px;
  height: 52px;
  display: grid;
  place-items: center;
  background: #3168df;
  color: white;
  border-radius: 12px;
  margin-bottom: 44px;
}
.intro-mark .app-icon {
  width: 31px;
  height: 31px;
}
.login-intro h2 {
  font-size: 35px;
  font-weight: 600;
  line-height: 1.65;
  letter-spacing: 0.5px;
}
.login-intro > p {
  font-size: 13px;
  color: #90acbf;
  line-height: 2;
  margin-top: 22px;
}
.intro-capabilities {
  display: flex;
  gap: 28px;
  margin-top: 46px;
  padding-top: 24px;
  border-top: 1px solid #ffffff12;
}
.intro-capabilities span {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #afc5d4;
}
.intro-capabilities .app-icon {
  width: 17px;
  height: 17px;
  color: #7fa3bd;
}
.login-box {
  width: 400px;
  max-width: 100%;
  padding: 36px;
  background: white;
  border: 1px solid #e5edf2;
  border-radius: 14px;
  box-shadow: 0 24px 80px #061a2d33;
}
.login-brand {
  display: none;
  width: 39px;
  height: 41px;
  border-radius: 10px;
  background: #edf3ff;
  color: #3168df;
  place-items: center;
  margin-bottom: 22px;
}
.login-brand .app-icon {
  width: 24px;
  height: 24px;
}
.login-box h1 {
  font-size: 22px;
  font-weight: 650;
  color: var(--ink);
  letter-spacing: -0.3px;
}
.login-box > p {
  font-size: 12px;
  color: #8093a4;
  margin-top: 8px;
  margin-bottom: 30px;
}
.login-box .form-group {
  margin-bottom: 20px;
}
.login-box .form-group > label {
  font-size: 12px;
  margin-bottom: 8px;
  color: #536e83;
}
.login-box input:not([type='checkbox']) {
  height: 42px;
  border: 1px solid #dbe5ed;
  background: #fcfdff;
  border-radius: 7px;
  padding-inline: 12px;
}
.login-box input:focus {
  background: white;
  border-color: #90aff0;
}
.remember {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #7b90a1;
  margin: 4px 0 22px;
}
.btn-login {
  height: 42px;
  width: 100%;
  border: 1px solid #3168df;
  border-radius: 7px;
  background: #3168df;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}
.btn-login:hover {
  background: #265ccc;
}
.login-box p.error {
  background: #fff1f2;
  color: #b64855;
  border: 1px solid #f7dfe3;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.7;
  margin: 16px 0 0;
}
.server-settings {
  padding: 3px 8px;
  border: 0;
  background: transparent;
  color: #8ca0b0;
  font-size: 11px;
  cursor: pointer;
}
.server-settings:hover {
  color: var(--primary);
}
.login-box > p:last-child {
  margin-bottom: 0;
}
@media (max-width: 1000px) {
  .login-wrap {
    gap: 44px;
  }
  .login-intro {
    width: 330px;
  }
  .login-intro h2 {
    font-size: 30px;
  }
  .intro-capabilities {
    gap: 18px;
  }
  .login-box {
    width: 380px;
    padding: 32px;
  }
}
@media (max-width: 760px) {
  .login-intro {
    display: none;
  }
  .login-wrap {
    padding: 24px 18px;
    align-items: center;
    background: #f1f5f9;
  }
  .login-box {
    padding: 30px 26px;
    width: 390px;
    border-radius: 12px;
    box-shadow: 0 8px 40px #173b5610;
  }
  .login-brand {
    display: grid;
  }
  .login-box h1 {
    font-size: 21px;
  }
  .login-box > p {
    line-height: 1.8;
  }
  .login-box input:not([type='checkbox']) {
    height: 44px;
  }
  .btn-login {
    height: 44px;
  }
}
</style>
