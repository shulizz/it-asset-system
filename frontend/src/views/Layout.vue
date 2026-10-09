<template>
  <div class="app">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-icon">资产</div>
        <div class="logo-text">固定资产管理系统</div>
      </div>
      <nav>
        <router-link to="/dashboard" class="nav-item">
          <span class="nav-dot"></span>工作台
        </router-link>
        <template v-if="perms.includes('assets') || perms.includes('assets_write') || perms.includes('import') || perms.includes('export')">
          <div class="nav-group-title">资产档案</div>
          <router-link to="/assets-it" class="nav-item"><span class="nav-dot"></span>IT 设备</router-link>
          <router-link to="/assets-phone" class="nav-item"><span class="nav-dot"></span>手机设备</router-link>
          <router-link to="/assets-medical" class="nav-item"><span class="nav-dot"></span>医疗设备</router-link>
          <router-link to="/phone-numbers" class="nav-item"><span class="nav-dot"></span>电话号码</router-link>
        </template>
        <router-link v-if="perms.includes('wechat') && (user.role === 'super_admin' || user.data_scope === 'all')" to="/wechat" class="nav-item"><span class="nav-dot"></span>微信账号</router-link>
        <template v-if="perms.includes('transfer') || perms.includes('scrap')">
          <div class="nav-group-title">流转与处置</div>
          <router-link v-if="perms.includes('transfer')" to="/transfer" class="nav-item"><span class="nav-dot"></span>设备流转</router-link>
          <router-link v-if="perms.includes('scrap')" to="/scrap" class="nav-item"><span class="nav-dot"></span>报废管理</router-link>
        </template>
        <div class="nav-group-title">日常</div>
        <router-link v-if="perms.includes('reports')" to="/reports" class="nav-item"><span class="nav-dot"></span>报表统计</router-link>
        <router-link v-if="perms.includes('apply')" to="/apply" class="nav-item"><span class="nav-dot"></span>设备申请</router-link>
        <router-link v-if="perms.includes('idle')" to="/idle" class="nav-item"><span class="nav-dot"></span>空闲设备</router-link>
        <router-link v-if="perms.includes('scrapped')" to="/scrapped" class="nav-item"><span class="nav-dot"></span>报废设备</router-link>
        <router-link v-if="perms.includes('approval')" to="/delete-approval" class="nav-item"><span class="nav-dot"></span>审批中心</router-link>
        <router-link v-if="perms.includes('departments')" to="/departments" class="nav-item"><span class="nav-dot"></span>部门管理</router-link>
        <router-link v-if="perms.includes('users')" to="/users" class="nav-item"><span class="nav-dot"></span>用户权限</router-link>
        <router-link v-if="perms.includes('roles')" to="/roles" class="nav-item"><span class="nav-dot"></span>角色权限</router-link>
        <router-link v-if="perms.includes('logs')" to="/logs" class="nav-item"><span class="nav-dot"></span>操作日志</router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="avatar">{{ user.name?.[0] || 'A' }}</div>
          <div>
            <div class="user-name">{{ user.name }}</div>
            <div class="user-role">{{ roleText }}</div>
          </div>
        </div>
        <a @click="logout" class="logout">退出</a>
      </div>
    </aside>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, onUnmounted } from 'vue'
import api from '../api'

const CURRENT_VERSION = '1.0.0'

let refreshTimer
async function refreshUser() {
  try { const { data } = await api.get('/auth/me'); user.value = data; localStorage.setItem('user', JSON.stringify(data)) } catch (e) { if (e.response?.status === 401) logout() }
}
onMounted(() => { refreshUser(); refreshTimer = setInterval(refreshUser, 15000) })
onUnmounted(() => clearInterval(refreshTimer))
import { useRouter } from 'vue-router'

const router = useRouter()
const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const role = computed(() => user.value.role || '')
const perms = computed(() => user.value.permissions || [])
const roleText = computed(() => role.value === 'super_admin' ? '超级管理员' : role.value)

function logout() {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.app { display: flex; height: 100vh; background: #f0f4f8; }
.sidebar { width: 230px; background: linear-gradient(180deg, #0f2c3f 0%, #0a1f2e 100%); color: #cbd5e1; display: flex; flex-direction: column; }
.logo { padding: 20px 18px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid rgba(255,255,255,.06); }
.logo-icon { width: 38px; height: 38px; background: linear-gradient(135deg, #0d9488, #14b8a6); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; color: #fff; box-shadow: 0 2px 8px rgba(13,148,136,.4); }
.logo-text { font-size: 14px; font-weight: 600; color: #fff; line-height: 1.3; }
nav { flex: 1; padding: 12px 0; overflow-y: auto; }
.nav-group-title { padding: 14px 20px 4px; font-size: 11px; color: #4a6a7a; letter-spacing: .5px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 9px 20px; font-size: 13.5px; color: #8aa5b5; text-decoration: none; transition: all .15s; border-left: 3px solid transparent; margin: 1px 8px; border-radius: 0 8px 8px 0; }
.nav-dot { width: 6px; height: 6px; border-radius: 50%; background: #4a6a7a; transition: all .15s; }
.nav-item:hover { background: rgba(255,255,255,.04); color: #e2e8f0; }
.nav-item.router-link-active { background: linear-gradient(90deg, rgba(13,148,136,.25), rgba(13,148,136,.05)); color: #2dd4bf; border-left-color: #14b8a6; }
.nav-item.router-link-active .nav-dot { background: #14b8a6; box-shadow: 0 0 6px #14b8a6; }
.sidebar-footer { padding: 14px 16px; border-top: 1px solid rgba(255,255,255,.06); display: flex; align-items: center; justify-content: space-between; }
.user-info { display: flex; align-items: center; gap: 8px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: #3b82f6; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px; font-weight: 600; }
.user-name { font-size: 13px; color: #e2e8f0; }
.user-role { font-size: 11px; color: #64748b; }
.logout { cursor: pointer; color: #64748b; font-size: 13px; }
.logout:hover { color: #ef4444; }
.main { flex: 1; overflow-y: auto; padding: 24px 28px; }
</style>






