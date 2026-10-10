import { createRouter, createWebHashHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Layout from '../views/Layout.vue'
import Dashboard from '../views/Dashboard.vue'
import AssetsIT from '../views/AssetsIT.vue'
import AssetsPhone from '../views/AssetsPhone.vue'
import AssetsMedical from '../views/AssetsMedical.vue'
import PhoneNumbers from '../views/PhoneNumbers.vue'
import Transfer from '../views/Transfer.vue'
import Scrap from '../views/Scrap.vue'
import Reports from '../views/Reports.vue'
import Users from '../views/Users.vue'
import Logs from '../views/Logs.vue'
import Departments from '../views/Departments.vue'
import DeleteApproval from '../views/DeleteApproval.vue'
import IdleAssets from '../views/IdleAssets.vue'
import ScrappedAssets from '../views/ScrappedAssets.vue'
import Apply from '../views/Apply.vue'
import WeChat from '../views/WeChat.vue'

const routes = [
  { path: '/login', component: Login },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: Dashboard },
      { path: 'assets-it', component: AssetsIT },
      { path: 'assets-phone', component: AssetsPhone },
      { path: 'assets-medical', component: AssetsMedical },
      { path: 'phone-numbers', component: PhoneNumbers },
      { path: 'transfer', component: Transfer },
      { path: 'scrap', component: Scrap },
      { path: 'delete-approval', component: DeleteApproval },
      { path: 'idle', component: IdleAssets },
      { path: 'scrapped', component: ScrappedAssets },
      { path: 'apply', component: Apply },
      { path: 'wechat', component: WeChat },
      { path: 'reports', component: Reports },
      { path: 'users', component: Users },
      { path: 'roles', redirect: '/users' },
      { path: 'departments', component: Departments },
      { path: 'logs', component: Logs }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) next('/login')
  else next()
})

export default router

