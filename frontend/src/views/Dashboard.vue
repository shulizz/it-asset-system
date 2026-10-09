<template>
  <div class="dashboard">
    <div class="dashboard-heading"><div><h2>工作台</h2><p>查看资产状态，及时处理流转与审批事项。</p></div><span class="today">{{ new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }) }}</span></div>
    <div class="stats">
      <div class="card"><div class="num">{{ stats.total }}</div><div class="label">设备总数</div></div>
      <div class="card"><div class="num" style="color:#16a34a">{{ stats.inUse }}</div><div class="label">在用</div></div>
      <div class="card"><div class="num" style="color:#d97706">{{ stats.idle }}</div><div class="label">闲置</div></div>
      <div class="card"><div class="num" style="color:#ef4444">{{ pendingCount }}</div><div class="label">待审批</div></div>
    </div>

    <div class="activity-grid">
      <div class="panel">
        <h3 style="margin-bottom:12px">待办事项</h3>
        <div v-if="pendingList.length === 0" style="color:#94a3b8;padding:20px 0;text-align:center">暂无待审批任务</div>
        <div v-else>
          <div v-for="item in pendingList" :key="item.id" class="todo-item">
            <div>
              <div style="font-size:13px;font-weight:500">{{ item.record_desc }}</div>
              <div style="font-size:12px;color:#94a3b8;margin-top:2px">原因：{{ item.reason }}</div>
            </div>
            <router-link to="/delete-approval" style="color:#2563eb;font-size:12px;white-space:nowrap">去审批 →</router-link>
          </div>
        </div>
      </div>

      <div class="panel">
        <h3 style="margin-bottom:12px">最近流转记录</h3>
        <div v-if="transferList.length === 0" style="color:#94a3b8;padding:20px 0;text-align:center">暂无流转记录</div>
        <div v-else>
          <div v-for="item in transferList" :key="item.id" class="todo-item">
            <div>
              <div style="font-size:13px">{{ item.asset_desc }}</div>
              <div style="font-size:12px;color:#94a3b8;margin-top:2px">{{ typeText(item.type) }} · {{ item.created_at }}</div>
            </div>
            <span class="badge" :class="typeBadge(item.type)">{{ typeText(item.type) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="canSeeMedical" class="panel" style="margin-bottom:20px;border-left:4px solid #ef4444">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:12px">
        <h3 style="color:#dc2626">医疗设备到期提醒（30天内）</h3>
        <button class="btn btn-outline" @click="sendEmail" :disabled="sending" style="font-size:12px;padding:6px 12px">
          {{ sending ? '发送中...' : '发送提醒邮件' }}
        </button>
      </div>
      <div v-if="expiringList.length === 0" style="color:#94a3b8;padding:12px 0;text-align:center">近期无设备到期</div>
      <div v-else>
        <div v-for="item in expiringList" :key="item.id" class="todo-item">
          <div>
            <div style="font-size:13px;font-weight:500">{{ item.asset_number }} {{ item.name }}（{{ item.department || '未分配科室' }}）</div>
            <div style="font-size:12px;color:#94a3b8;margin-top:2px">到期日：{{ (item.expiry_date||'').substring(0,10) }} · 保管人：{{ item.keeper || '—' }}</div>
          </div>
          <span class="badge" :class="item._days < 0 ? 'red' : 'amber'">
            {{ item._days < 0 ? '已过期' : '剩余' + item._days + '天' }}
          </span>
        </div>
      </div>
    </div>

    <div class="panel">
      <h3 style="margin-bottom:12px">各模块摘要</h3>
      <div class="module-grid">
        <div class="mini-stat"><div class="num-sm">{{ phoneCount }}</div><div class="label-sm">手机设备</div></div>
        <div class="mini-stat"><div class="num-sm">{{ medicalCount }}</div><div class="label-sm">医疗设备</div></div>
        <div class="mini-stat"><div class="num-sm">{{ numberCount }}</div><div class="label-sm">电话号码</div></div>
        <div class="mini-stat"><div class="num-sm">{{ deptCount }}</div><div class="label-sm">部门数</div></div>
        <div class="mini-stat"><div class="num-sm">{{ wechatCount }}</div><div class="label-sm">微信账号</div></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'

const user = computed(() => JSON.parse(localStorage.getItem('user') || '{}'))
const perms = computed(() => user.value.permissions || [])
const canSeeMedical = computed(() => perms.value.includes('assets'))

const stats = ref({ total: 0, inUse: 0, idle: 0 })
const pendingList = ref([])
const transferList = ref([])
const phoneCount = ref(0)
const medicalCount = ref(0)
const numberCount = ref(0)
const deptCount = ref(0)
const wechatCount = ref(0)
const pendingCount = ref(0)
const expiringList = ref([])
const sending = ref(false)

async function sendEmail() {
  sending.value = true
  try {
    const r = await api.post('/assets/medical/send-expiry-email?days=30')
    alert(r.data.message)
  } catch(e) {
    alert('发送失败: ' + (e.response?.data?.detail || e.message))
  }
  sending.value = false
}

async function safeGet(url) {
  try { const r = await api.get(url); return r.data || [] } catch(e) { return [] }
}

onMounted(async () => {
  const it = await safeGet('/assets/it')
  const ph = await safeGet('/assets/phone')
  const med = await safeGet('/assets/medical')
  const del = await safeGet('/delete-request')
  const tr = await safeGet('/transfer')
  const num = await safeGet('/assets/numbers')
  const dept = await safeGet('/departments')
  const scrap = await safeGet('/scrap')
  const wc = await safeGet('/wechat')

  // 全部资产类型纳入统计：IT设备、手机、医疗、电话号码、微信
  const allAssets = [...it, ...ph, ...med, ...num, ...wc]
  stats.value.total = allAssets.length
  stats.value.inUse = allAssets.filter(i => i.status === 'in_use').length
  stats.value.idle = allAssets.filter(i => i.status === 'idle').length

  pendingList.value = del.filter(d => d.status === 'pending').slice(0, 5)
  pendingCount.value = del.filter(d => d.status === 'pending').length
  const scrapPending = scrap.filter(s => s.status === 'pending_approval')
  pendingCount.value += scrapPending.length
  scrapPending.slice(0, 5).forEach(s => {
    pendingList.value.push({ id: 'scrap_' + s.id, record_desc: '报废申请：' + s.asset_desc, reason: s.reason || '', type: 'scrap' })
  })

  transferList.value = tr.slice(0, 5)
  phoneCount.value = ph.length
  medicalCount.value = med.length
  numberCount.value = num.length
  deptCount.value = dept.length
  wechatCount.value = wc.length

  // 医疗设备到期提醒：30天内到期或已过期
  const today = new Date(); today.setHours(0,0,0,0)
  expiringList.value = med
    .filter(m => m.expiry_date && m.status !== 'scrapped')
    .map(m => {
      const d = new Date(m.expiry_date.substring(0,10))
      return { ...m, _days: Math.ceil((d - today) / 86400000) }
    })
    .filter(m => m._days <= 30)
    .sort((a, b) => a._days - b._days)
    .slice(0, 10)

  // 登录弹窗提醒：有到期设备且用户有医疗设备权限时自动弹窗
  if (canSeeMedical.value && expiringList.value.length > 0) {
    const over = expiringList.value.filter(e => e._days < 0).length
    const soon = expiringList.value.length - over
    let msg = `⚠️ 医疗设备到期提醒\n\n`
    if (over > 0) msg += `已过期设备：${over} 台\n`
    if (soon > 0) msg += `30天内到期：${soon} 台\n\n`
    msg += '详细信息请查看下方「医疗设备到期提醒」面板。'
    setTimeout(() => alert(msg), 500)
  }
})

function typeText(t){ return {checkout:'领用',return:'归还',transfer:'调拨',offboard:'离职回收',scrap:'报废'}[t]||t }
function typeBadge(t){ return {checkout:'green',return:'blue',transfer:'amber',offboard:'red',scrap:'red'}[t]||'gray' }
</script>

<style scoped>
.dashboard-heading { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:22px; }.dashboard-heading h2 { font-size:22px; font-weight:650; }.dashboard-heading p { color:#728198; font-size:13px; margin-top:7px; }.today { color:#64748b; font-size:12px; white-space:nowrap; }
.stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin-bottom:20px; }
.card { position:relative; background:#fff; border-radius:8px; padding:20px 22px; border:1px solid var(--line); display:flex; flex-direction:column-reverse; gap:12px; }.card:first-child { border-left:3px solid #3478f6; }.card:nth-child(2) { border-left:3px solid #16a34a; }.card:nth-child(3) { border-left:3px solid #d97706; }.card:nth-child(4) { border-left:3px solid #ef4444; }
.num { font-size:30px; font-weight:650; line-height:1; font-variant-numeric:tabular-nums; color:#253751; }.label { font-size:13px; color:#64748b; }
.activity-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:20px; }
.panel { background:#fff; border-radius:8px; padding:20px; border:1px solid var(--line); min-width:0; }.panel h3 { font-size:15px; font-weight:600; }.todo-item { display:flex; justify-content:space-between; gap:12px; align-items:center; padding:12px 0; border-bottom:1px solid #edf1f6; }.todo-item:last-child { border-bottom:none; }.todo-item>div { min-width:0; overflow-wrap:anywhere; }
.module-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:12px; }.mini-stat { background:#f5f8fc; border:1px solid #edf1f6; border-radius:6px; padding:16px; text-align:left; }.num-sm { font-size:23px; font-weight:650; color:#253751; font-variant-numeric:tabular-nums; }.label-sm { font-size:12px; color:#64748b; margin-top:6px; }
.badge { padding:3px 8px; border-radius:4px; font-size:12px; white-space:nowrap; }.green { background:#e8f6ee; color:#16834a; }.blue { background:#eaf1ff; color:#2865db; }.amber { background:#fff4df; color:#a76a13; }.red { background:#ffeded; color:#ce3e3e; }.gray { background:#f1f5f9; color:#64748b; }
@media(max-width:1000px) { .module-grid { grid-template-columns:repeat(3,minmax(0,1fr)); } }
@media(max-width:760px) { .stats { grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }.activity-grid { grid-template-columns:1fr; }.dashboard-heading { align-items:flex-start; }.today { display:none; }.card { padding:16px; }.module-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.panel { padding:16px; } }
</style>

