<template>
  <div class="app">
    <button
      v-if="mobileNavOpen"
      class="nav-overlay"
      aria-label="关闭导航"
      @click="mobileNavOpen = false"
    ></button>
    <aside
      id="app-navigation"
      class="sidebar"
      :class="{ open: mobileNavOpen }"
      @keydown.esc="mobileNavOpen = false"
    >
      <div class="logo">
        <div class="logo-icon"><AppIcon name="asset" /></div>
        <div class="logo-text"><strong>固定资产管理系统</strong><span>资产与设备工作台</span></div>
      </div>
      <nav aria-label="主导航" @click="mobileNavOpen = false">
        <router-link to="/dashboard" class="nav-item">
          <AppIcon name="dashboard" />工作台
        </router-link>
        <template
          v-if="
            perms.includes('assets') ||
            perms.includes('assets_write') ||
            perms.includes('import') ||
            perms.includes('export')
          "
        >
          <div class="nav-group-title">资产档案</div>
          <router-link to="/assets-it" class="nav-item"><AppIcon name="it" />IT 设备</router-link>
          <router-link to="/assets-phone" class="nav-item"
            ><AppIcon name="phone" />手机设备</router-link
          >
          <router-link to="/assets-medical" class="nav-item"
            ><AppIcon name="medical" />医疗设备</router-link
          >
          <router-link to="/phone-numbers" class="nav-item"
            ><AppIcon name="number" />电话号码</router-link
          >
        </template>
        <router-link
          v-if="
            perms.includes('wechat') && (user.role === 'super_admin' || user.data_scope === 'all')
          "
          to="/wechat"
          class="nav-item"
          ><AppIcon name="wechat" />微信账号</router-link
        >
        <template v-if="perms.includes('transfer') || perms.includes('scrap')">
          <div class="nav-group-title">流转与处置</div>
          <router-link v-if="perms.includes('transfer')" to="/transfer" class="nav-item"
            ><AppIcon name="transfer" />设备流转</router-link
          >
          <router-link v-if="perms.includes('scrap')" to="/scrap" class="nav-item"
            ><AppIcon name="scrap" />报废管理</router-link
          >
        </template>
        <div
          v-if="['reports', 'apply', 'idle', 'scrapped', 'approval'].some((p) => perms.includes(p))"
          class="nav-group-title"
        >
          业务协作
        </div>
        <router-link v-if="perms.includes('reports')" to="/reports" class="nav-item"
          ><AppIcon name="reports" />报表统计</router-link
        >
        <router-link v-if="perms.includes('apply')" to="/apply" class="nav-item"
          ><AppIcon name="apply" />设备申请</router-link
        >
        <router-link v-if="perms.includes('idle')" to="/idle" class="nav-item"
          ><AppIcon name="idle" />空闲设备</router-link
        >
        <router-link v-if="perms.includes('scrapped')" to="/scrapped" class="nav-item"
          ><AppIcon name="scrap" />报废设备</router-link
        >
        <router-link v-if="perms.includes('approval')" to="/delete-approval" class="nav-item"
          ><AppIcon name="approval" />审批中心</router-link
        >
        <div
          v-if="['departments', 'users', 'logs'].some((p) => perms.includes(p))"
          class="nav-group-title"
        >
          系统管理
        </div>
        <router-link
          v-if="
            perms.includes('departments') &&
            (user.role === 'super_admin' || user.data_scope === 'all')
          "
          to="/departments"
          class="nav-item"
          ><AppIcon name="departments" />部门管理</router-link
        >
        <router-link v-if="perms.includes('users')" to="/users" class="nav-item"
          ><AppIcon name="users" />用户权限</router-link
        >
        <router-link
          v-if="
            perms.includes('logs') && (user.role === 'super_admin' || user.data_scope === 'all')
          "
          to="/logs"
          class="nav-item"
          ><AppIcon name="logs" />操作日志</router-link
        >
      </nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="avatar">{{ user.name?.[0] || 'A' }}</div>
          <div>
            <div class="user-name">{{ user.name }}</div>
            <div class="user-role">{{ roleText }}</div>
          </div>
        </div>
        <button @click="logout" class="logout" title="退出登录">
          <AppIcon name="logout" /><span>退出</span>
        </button>
      </div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <div class="topbar-location">
          <button
            class="menu-toggle"
            aria-label="打开导航"
            aria-controls="app-navigation"
            :aria-expanded="mobileNavOpen"
            @click="mobileNavOpen = !mobileNavOpen"
          >
            <AppIcon name="menu" />
          </button>
          <span class="workspace-label">资产管理</span><span class="breadcrumb-divider">/</span
          ><strong>{{ pageTitle }}</strong>
        </div>
        <div class="topbar-account">
          <span class="scope-label">{{ scopeText }}</span
          ><span class="topbar-avatar">{{ user.name?.[0] || '用' }}</span
          ><span>{{ user.name || '用户' }}</span>
        </div>
      </header>
      <main class="main"><router-view /></main>
    </div>
  </div>
</template>

<script setup>
import AppIcon from '../components/AppIcon.vue'
import { computed, onMounted, ref, onUnmounted } from 'vue'
import { currentUser, refreshCurrentUser, clearSession } from '../userState'

const mobileNavOpen = ref(false)
const route = useRoute()
const pageNames = {
  dashboard: '工作台',
  'assets-it': 'IT 设备档案',
  'assets-phone': '手机设备档案',
  'assets-medical': '医疗设备档案',
  'phone-numbers': '电话号码',
  transfer: '设备流转',
  scrap: '报废管理',
  reports: '报表统计',
  apply: '设备申请',
  idle: '空闲设备',
  scrapped: '报废设备',
  'delete-approval': '审批中心',
  departments: '部门管理',
  users: '用户权限',
  logs: '操作日志',
  wechat: '微信账号',
}
const pageTitle = computed(() => pageNames[route.path.split('/')[1]] || '工作台')
const scopeText = computed(() =>
  user.value.role === 'super_admin' || user.value.data_scope === 'all'
    ? '全部部门'
    : user.value.department || '当前权限范围',
)

let refreshTimer
let refreshing = false,
  refreshController
async function refreshUser() {
  if (refreshing) return
  refreshing = true
  refreshController = new AbortController()
  try {
    await refreshCurrentUser(refreshController.signal)
  } catch (e) {
    if (e.response?.status === 401) logout()
  } finally {
    refreshing = false
  }
}
function refreshVisibleUser() {
  if (!document.hidden) refreshUser()
}
onMounted(() => {
  refreshUser()
  refreshTimer = setInterval(refreshVisibleUser, 15000)
  document.addEventListener('visibilitychange', refreshVisibleUser)
})
onUnmounted(() => {
  clearInterval(refreshTimer)
  document.removeEventListener('visibilitychange', refreshVisibleUser)
  refreshController?.abort()
})
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const user = currentUser
const role = computed(() => user.value.role || '')
const perms = computed(() => user.value.permissions || [])
const roleText = computed(() => (role.value === 'super_admin' ? '超级管理员' : role.value))

function logout() {
  clearSession()
  router.push('/login')
}
</script>

<style scoped>
.app {
  display: flex;
  height: 100dvh;
  background: var(--canvas);
}
.sidebar {
  width: 232px;
  flex-shrink: 0;
  background: #122d40;
  color: #b5c9d7;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #18374c;
}
.logo {
  min-height: 88px;
  padding: 22px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #ffffff0d;
}
.logo-icon {
  width: 37px;
  height: 39px;
  border-radius: 10px;
  background: #2d6ee8;
  color: white;
  display: grid;
  place-items: center;
}
.logo-icon .app-icon {
  width: 23px;
  height: 23px;
}
.logo-text strong {
  display: block;
  color: #f6faff;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
}
.logo-text span {
  display: block;
  color: #7f9aaf;
  font-size: 10px;
  margin-top: 5px;
  letter-spacing: 1px;
}
nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px 12px 20px;
  scrollbar-width: thin;
  scrollbar-color: #3a5365 transparent;
}
.nav-group-title {
  padding: 20px 14px 7px;
  font-size: 10px;
  font-weight: 500;
  color: #7e9aaf;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  min-height: 40px;
  font-size: 12px;
  color: #b6cad9;
  text-decoration: none;
  border-radius: 7px;
  margin: 3px 0;
  position: relative;
}
.nav-item .app-icon {
  width: 17px;
  height: 17px;
  opacity: 0.8;
}
.nav-item:hover {
  background: #ffffff09;
  color: white;
}
.nav-item.router-link-active {
  background: #3168df;
  color: white;
  box-shadow: 0 3px 10px #07192d1f;
}
.nav-item.router-link-active .app-icon {
  opacity: 1;
}
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #ffffff0d;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: #0f293b;
}
.user-info {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: 0;
}
.avatar {
  width: 33px;
  height: 33px;
  flex-shrink: 0;
  border-radius: 9px;
  background: #29495e;
  color: #dcebf5;
  display: grid;
  place-items: center;
  font-size: 13px;
}
.user-name {
  font-size: 12px;
  color: #edf6fc;
  max-width: 105px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-role {
  font-size: 10px;
  color: #7d9bb0;
  margin-top: 3px;
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.logout {
  border: 0;
  background: transparent;
  cursor: pointer;
  display: flex;
  gap: 5px;
  align-items: center;
  color: #8ca8bc;
  font-size: 11px;
  padding: 6px 2px;
}
.logout .app-icon {
  width: 15px;
  height: 15px;
}
.logout:hover {
  color: white;
}
.workspace {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.topbar {
  height: 64px;
  flex-shrink: 0;
  background: white;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 28px;
}
.topbar-location,
.topbar-account {
  display: flex;
  align-items: center;
  gap: 13px;
  font-size: 12px;
}
.workspace-label {
  color: #7b8d9e;
}
.breadcrumb-divider {
  color: #c8d3df;
}
.topbar-location strong {
  font-weight: 550;
  color: #334d63;
}
.scope-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #637d92;
  font-size: 11px;
  margin-right: 10px;
}
.scope-label .app-icon {
  width: 14px;
  height: 14px;
  color: #7e94a5;
}
.topbar-avatar {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  background: #eaf0fc;
  color: #3168df;
  border-radius: 50%;
  font-size: 12px;
}
.topbar-account > span:last-child {
  color: #526b7f;
  font-size: 12px;
}
.main {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 26px 28px 36px;
  scrollbar-gutter: stable;
}
.main > div {
  max-width: 1680px;
  margin-inline: auto;
}
.menu-toggle {
  display: none;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--line);
  background: white;
  padding: 7px;
  border-radius: 7px;
  color: #3e596e;
  cursor: pointer;
}
.nav-overlay {
  display: none;
}
@media (max-width: 1080px) {
  .sidebar {
    width: 210px;
  }
  .logo {
    padding-inline: 16px;
    gap: 9px;
  }
  .logo-text strong {
    font-size: 12px;
  }
  .main {
    padding: 22px;
  }
  .topbar {
    padding-inline: 22px;
  }
}
@media (max-width: 760px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: 232px;
    z-index: 120;
    transform: translateX(-100%);
    visibility: hidden;
    transition:
      transform 0.18s,
      visibility 0.18s;
  }
  .sidebar.open {
    transform: translateX(0);
    visibility: visible;
  }
  .nav-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: #0c233b66;
    border: 0;
    z-index: 110;
    backdrop-filter: blur(2px);
  }
  .menu-toggle {
    display: flex;
  }
  .workspace-label,
  .breadcrumb-divider,
  .scope-label {
    display: none;
  }
  .topbar {
    padding-inline: 16px;
    height: 58px;
  }
  .main {
    padding: 20px 16px 28px;
    scrollbar-gutter: auto;
  }
  .topbar-account {
    gap: 8px;
  }
  .topbar-location {
    gap: 10px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .sidebar {
    transition: none;
  }
}
</style>
