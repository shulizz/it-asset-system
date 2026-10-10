<template>
  <div class="app">
    <button v-if="mobileNavOpen" class="nav-overlay" aria-label="关闭导航" @click="mobileNavOpen = false"></button>
    <aside id="app-navigation" class="sidebar" :class="{ open: mobileNavOpen }">
      <div class="logo">
        <div class="logo-icon">资产</div>
        <div class="logo-text">固定资产管理系统</div>
      </div>
      <nav aria-label="主导航" @click="mobileNavOpen = false">
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
        <router-link v-if="perms.includes('departments') && (user.role === 'super_admin' || user.data_scope === 'all')" to="/departments" class="nav-item"><span class="nav-dot"></span>部门管理</router-link>
        <router-link v-if="perms.includes('users')" to="/users" class="nav-item"><span class="nav-dot"></span>用户权限</router-link>
        <router-link v-if="perms.includes('logs') && (user.role === 'super_admin' || user.data_scope === 'all')" to="/logs" class="nav-item"><span class="nav-dot"></span>操作日志</router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="avatar">{{ user.name?.[0] || 'A' }}</div>
          <div>
            <div class="user-name">{{ user.name }}</div>
            <div class="user-role">{{ roleText }}</div>
          </div>
        </div>
        <button @click="logout" class="logout">退出</button>
      </div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <div class="topbar-location">
          <button class="menu-toggle" aria-label="打开导航" aria-controls="app-navigation" :aria-expanded="mobileNavOpen" @click="mobileNavOpen = !mobileNavOpen">☰</button>
          <span class="workspace-label">资产管理</span><span class="breadcrumb-divider">/</span><strong>{{ pageTitle }}</strong>
        </div>
        <div class="topbar-account"><span class="scope-label">{{ scopeText }}</span><span class="topbar-avatar">{{ user.name?.[0] || '用' }}</span><span>{{ user.name || '用户' }}</span></div>
      </header>
      <main class="main"><router-view /></main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, onUnmounted } from 'vue'
import api from '../api'

const mobileNavOpen = ref(false)
const route = useRoute()
const pageNames = { dashboard: '工作台', 'assets-it': 'IT 设备档案', 'assets-phone': '手机设备档案', 'assets-medical': '医疗设备档案', 'phone-numbers': '电话号码', transfer: '设备流转', scrap: '报废管理', reports: '报表统计', apply: '设备申请', idle: '空闲设备', scrapped: '报废设备', 'delete-approval': '审批中心', departments: '部门管理', users: '用户权限', logs: '操作日志', wechat: '微信账号' }
const pageTitle = computed(() => pageNames[route.path.split('/')[1]] || '工作台')
const scopeText = computed(() => user.value.role === 'super_admin' || user.value.data_scope === 'all' ? '全部部门' : (user.value.department || '当前权限范围'))

let refreshTimer
async function refreshUser() {
  try { const { data } = await api.get('/auth/me'); user.value = data; localStorage.setItem('user', JSON.stringify(data)) } catch (e) { if (e.response?.status === 401) logout() }
}
onMounted(() => { refreshUser(); refreshTimer = setInterval(refreshUser, 15000) })
onUnmounted(() => clearInterval(refreshTimer))
import { useRouter, useRoute } from 'vue-router'

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
.app { display:flex; height:100dvh; background:var(--canvas); }
.sidebar { width:224px; flex-shrink:0; background:#14243b; color:#c0ccdd; display:flex; flex-direction:column; }
.logo { min-height:76px; padding:18px 16px; display:flex; align-items:center; gap:10px; border-bottom:1px solid #ffffff12; }
.logo-icon { width:36px; height:36px; flex-shrink:0; border-radius:8px; background:#3478f6; display:grid; place-items:center; font-weight:700; font-size:12px; color:white; }
.logo-text { font-size:14px; font-weight:600; color:white; line-height:1.5; }
nav { flex:1; padding:12px 8px; overflow-y:auto; }
.nav-group-title { padding:18px 14px 7px; font-size:11px; color:#8ea1bb; }
.nav-item { display:flex; align-items:center; gap:11px; padding:10px 14px; min-height:39px; font-size:13px; color:#b5c4d8; text-decoration:none; border-radius:6px; margin:2px 0; }
.nav-dot { width:6px; height:6px; border:1px solid #8094af; border-radius:2px; flex-shrink:0; }
.nav-item:hover { background:#ffffff0b; color:#fff; }
.nav-item.router-link-active { background:#2865db; color:white; }
.nav-item.router-link-active .nav-dot { background:white; border-color:white; }
.sidebar-footer { padding:16px; border-top:1px solid #ffffff12; display:flex; align-items:center; justify-content:space-between; gap:8px; }
.user-info { display:flex; align-items:center; gap:9px; min-width:0; }
.avatar { width:32px; height:32px; border-radius:8px; background:#30445f; display:grid; place-items:center; color:#fff; font-size:13px; }
.user-name { font-size:13px; color:#eef4ff; }
.user-role { font-size:11px; color:#8ea1bb; margin-top:3px; }
.logout { border:0; background:transparent; cursor:pointer; color:#b5c4d8; font-size:12px; padding:6px; }
.logout:hover { color:#fff; }
.workspace { flex:1; min-width:0; display:flex; flex-direction:column; }
.topbar { height:60px; flex-shrink:0; background:white; border-bottom:1px solid var(--line); display:flex; align-items:center; justify-content:space-between; gap:12px; padding:0 28px; }
.topbar-location,.topbar-account { display:flex; align-items:center; gap:12px; font-size:13px; }
.workspace-label { color:#728198; }.breadcrumb-divider { color:#bdc7d5; }.topbar-location strong { font-weight:600; }
.scope-label { color:#64748b; border-right:1px solid var(--line); padding-right:16px; margin-right:4px; font-size:12px; }
.topbar-avatar { width:28px; height:28px; background:#eaf1ff; color:#2865db; border-radius:50%; display:grid; place-items:center; font-size:12px; }
.main { flex:1; min-height:0; overflow:auto; padding:24px 28px; }
.menu-toggle { display:none; border:1px solid var(--line); background:white; padding:5px 9px; border-radius:5px; cursor:pointer; font-size:17px; }
.nav-overlay { display:none; }
@media(max-width:900px) { .sidebar { width:200px; }.main { padding:20px; }.topbar { padding:0 20px; }.scope-label { display:none; } }
@media(max-width:680px) { .sidebar { position:fixed; inset:0 auto 0 0; width:224px; z-index:120; transform:translateX(-100%); transition:transform .18s; }.sidebar.open { transform:translateX(0); }.nav-overlay { display:block; position:fixed; inset:0; background:#14243b66; border:0; z-index:110; }.menu-toggle { display:block; }.workspace-label,.breadcrumb-divider { display:none; }.topbar { padding:0 16px; height:56px; }.main { padding:16px; }.topbar-account { gap:6px; } }
@media(prefers-reduced-motion:reduce) { .sidebar { transition:none; } }
</style>






