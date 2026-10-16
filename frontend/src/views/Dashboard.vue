<template>
  <div class="dashboard">
    <PageHeading title="工作台" description="掌握资产使用情况，跟进日常审批和设备到期事项。"
      ><div class="dashboard-date">
        <AppIcon name="calendar" />{{
          new Date().toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long',
          })
        }}
      </div></PageHeading
    >
    <p v-if="dataError" class="data-warning" role="status">
      部分数据未能读取，相关统计可能不完整，请刷新后重试。
    </p>
    <section class="stats" aria-label="资产概览" :aria-busy="loading">
      <div class="card">
        <div class="metric-top">
          <span class="label">资产总数</span
          ><span class="metric-icon"><AppIcon name="asset" /></span>
        </div>
        <div class="num">{{ loading ? '—' : stats.total }}</div>
        <p class="metric-note">当前权限范围内的资产</p>
      </div>
      <div class="card">
        <div class="metric-top">
          <span class="label">在用资产</span
          ><span class="metric-icon positive"><AppIcon name="check" /></span>
        </div>
        <div class="num">{{ loading ? '—' : stats.inUse }}</div>
        <p class="metric-note">
          {{
            stats.total
              ? '占资产总数的 ' + Math.round((stats.inUse / stats.total) * 100) + '%'
              : '录入资产后显示使用情况'
          }}
        </p>
      </div>
      <div class="card">
        <div class="metric-top">
          <span class="label">闲置资产</span
          ><span class="metric-icon idle"><AppIcon name="idle" /></span>
        </div>
        <div class="num">{{ loading ? '—' : stats.idle }}</div>
        <p class="metric-note">可关注的待调配资源</p>
      </div>
      <div class="card">
        <div class="metric-top">
          <span class="label">待审批事项</span
          ><span class="metric-icon pending"><AppIcon name="approval" /></span>
        </div>
        <div class="num">{{ loading ? '—' : pendingCount }}</div>
        <p class="metric-note">设备申请、删除及报废申请</p>
      </div>
    </section>
    <section class="module-overview" aria-label="各模块摘要">
      <div class="overview-title">
        <h3>档案概况</h3>
        <p>各模块数量</p>
      </div>
      <div class="module-grid">
        <div class="mini-stat">
          <AppIcon name="phone" />
          <div>
            <span class="label-sm">手机设备</span><strong>{{ phoneCount }}</strong>
          </div>
        </div>
        <div class="mini-stat">
          <AppIcon name="medical" />
          <div>
            <span class="label-sm">医疗设备</span><strong>{{ medicalCount }}</strong>
          </div>
        </div>
        <div class="mini-stat">
          <AppIcon name="number" />
          <div>
            <span class="label-sm">电话号码</span><strong>{{ numberCount }}</strong>
          </div>
        </div>
        <div class="mini-stat">
          <AppIcon name="departments" />
          <div>
            <span class="label-sm">部门</span><strong>{{ deptCount }}</strong>
          </div>
        </div>
        <div class="mini-stat">
          <AppIcon name="wechat" />
          <div>
            <span class="label-sm">微信账号</span><strong>{{ wechatCount }}</strong>
          </div>
        </div>
      </div>
    </section>
    <div class="activity-grid">
      <section class="panel activity-panel">
        <header class="panel-heading">
          <div class="section-title">
            <AppIcon name="approval" />
            <h3>待办事项</h3>
            <span class="section-count">{{ pendingCount }}</span>
          </div>
          <router-link v-if="perms.includes('approval')" to="/delete-approval" class="section-link"
            >审批中心<AppIcon name="arrow"
          /></router-link>
        </header>
        <EmptyState
          v-if="!pendingList.length"
          icon="approval"
          title="暂无待审批任务"
          description="新的待办事项会在这里显示。"
        />
        <div v-else class="activity-list">
          <div v-for="item in pendingList" :key="item.id" class="todo-item">
            <span class="activity-mark"><AppIcon name="apply" /></span>
            <div class="todo-copy">
              <div class="todo-title">{{ item.record_desc }}</div>
              <p>原因：{{ item.reason || '未填写' }}</p>
            </div>
            <router-link
              v-if="perms.includes('approval')"
              to="/delete-approval"
              class="section-link"
              >处理<AppIcon name="arrow" /></router-link
            ><span v-else class="badge amber">待审批</span>
          </div>
        </div>
      </section>
      <section class="panel activity-panel">
        <header class="panel-heading">
          <div class="section-title">
            <AppIcon name="transfer" />
            <h3>最近流转记录</h3>
          </div>
          <router-link v-if="perms.includes('transfer')" to="/transfer" class="section-link"
            >全部记录<AppIcon name="arrow"
          /></router-link>
        </header>
        <EmptyState
          v-if="!transferList.length"
          icon="transfer"
          title="暂无流转记录"
          description="领用、归还和调拨完成后会留下记录。"
        />
        <div v-else class="activity-list">
          <div v-for="item in transferList" :key="item.id" class="todo-item">
            <span class="activity-mark"><AppIcon name="transfer" /></span>
            <div class="todo-copy">
              <div class="todo-title">{{ item.asset_desc }}</div>
              <p>{{ (item.transfer_date || item.created_at || '').slice(0, 10) }}</p>
            </div>
            <span class="badge" :class="typeBadge(item.type)">{{ typeText(item.type) }}</span>
          </div>
        </div>
      </section>
    </div>
    <div v-if="canSeeMedical" class="reminder-grid">
      <section class="panel reminder-panel">
        <header class="panel-heading">
          <div>
            <div class="section-title">
              <span class="reminder-icon"><AppIcon name="clock" /></span>
              <h3>医疗设备到期提醒（30天内）</h3>
            </div>
            <p class="section-description">关注使用期限，及时安排后续处置。</p>
          </div>
          <ExpiryEmailDialog v-if="canSendEmail" />
        </header>
        <EmptyState
          v-if="!expiringList.length"
          icon="check"
          title="近期无设备到期"
          description="30天内到期或已过期的设备会在这里显示。"
        />
        <div v-else class="activity-list">
          <div v-for="item in expiringList" :key="item.id" class="todo-item">
            <div class="todo-copy">
              <div class="todo-title">
                {{ item.name }}<span class="asset-reference">{{ item.asset_number }}</span>
              </div>
              <p>
                到期日：{{ (item.expiry_date || '').slice(0, 10) }} ·
                {{ item.department || '未分配科室' }} · {{ item.keeper || '未填写保管人' }}
              </p>
            </div>
            <span class="badge" :class="item._days < 0 ? 'red' : 'amber'">{{
              item._days < 0 ? '已过期' : '剩余' + item._days + '天'
            }}</span>
          </div>
        </div>
      </section>
      <section class="panel reminder-panel">
        <header class="panel-heading">
          <div>
            <div class="section-title">
              <span class="reminder-icon calibration"><AppIcon name="medical" /></span>
              <h3>医疗设备校准到期提醒（30天内）</h3>
            </div>
            <p class="section-description">跟进校准周期，避免遗漏到期设备。</p>
          </div>
          <ExpiryEmailDialog v-if="canSendEmail" reminder-type="calibration" />
        </header>
        <EmptyState
          v-if="!calibrationList.length"
          icon="check"
          title="暂无校准到期设备"
          description="已填写校准到期时间的设备参与提醒。"
        />
        <div v-else class="activity-list">
          <div v-for="item in calibrationList" :key="item.id" class="todo-item">
            <div class="todo-copy">
              <div class="todo-title">
                {{ item.name }}<span class="asset-reference">{{ item.asset_number }}</span>
              </div>
              <p>校准到期：{{ item.calibration_expiry }} · {{ item.keeper || '未填写保管人' }}</p>
            </div>
            <span class="badge" :class="item._days < 0 ? 'red' : 'amber'">{{
              item._days < 0 ? '已逾期' + Math.abs(item._days) + '天' : '剩余' + item._days + '天'
            }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import AppIcon from '../components/AppIcon.vue'
import PageHeading from '../components/PageHeading.vue'
import EmptyState from '../components/EmptyState.vue'
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import { currentUser } from '../userState'
import { dueMedical } from '../medicalDates'
import ExpiryEmailDialog from '../components/ExpiryEmailDialog.vue'

const user = currentUser
const perms = computed(() => user.value.permissions || [])
const canSeeMedical = computed(() => perms.value.includes('assets'))
const canSendEmail = computed(
  () =>
    perms.value.includes('assets_write') &&
    (user.value.role === 'super_admin' || user.value.data_scope === 'all'),
)

const loading = ref(true)
const dataError = ref(false)
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
const calibrationList = ref([])
async function safeGet(url) {
  try {
    const r = await api.get(url)
    return r.data || []
  } catch (e) {
    if (e.response?.status !== 403) dataError.value = true
    return []
  }
}

onMounted(async () => {
  const [it, ph, med, del, tr, num, dept, scrap, wc] = await Promise.all(
    [
      '/assets/it',
      '/assets/phone',
      '/assets/medical',
      '/delete-request',
      '/transfer',
      '/assets/numbers',
      '/departments',
      '/scrap',
      '/wechat',
    ].map(safeGet),
  )
  calibrationList.value = dueMedical(med, 'calibration_expiry', 10)

  // 全部资产类型纳入统计：IT设备、手机、医疗、电话号码、微信
  const totals = { total: 0, inUse: 0, idle: 0 }
  for (const assets of [it, ph, med, num, wc]) {
    totals.total += assets.length
    for (const item of assets) {
      if (item.status === 'in_use') totals.inUse++
      else if (item.status === 'idle') totals.idle++
    }
  }
  stats.value = totals

  const pending = []
  let count = 0,
    scrapShown = 0
  for (const item of del) {
    if (item.status === 'pending') {
      count++
      if (pending.length < 5) pending.push(item)
    }
  }
  for (const item of scrap) {
    if (item.status === 'pending_approval') {
      count++
      if (scrapShown < 5) {
        pending.push({
          id: 'scrap_' + item.id,
          record_desc: '报废申请：' + item.asset_desc,
          reason: item.reason || '',
          type: 'scrap',
        })
        scrapShown++
      }
    }
  }
  pendingList.value = pending
  pendingCount.value = count

  transferList.value = tr.slice(0, 5)
  phoneCount.value = ph.length
  medicalCount.value = med.length
  numberCount.value = num.length
  deptCount.value = dept.length
  wechatCount.value = wc.length

  // 医疗设备到期提醒：30天内到期或已过期
  expiringList.value = dueMedical(med, 'expiry_date', 10)

  // 登录弹窗提醒：有到期设备且用户有医疗设备权限时自动弹窗
  if (canSeeMedical.value && expiringList.value.length > 0) {
    const over = expiringList.value.filter((e) => e._days < 0).length
    const soon = expiringList.value.length - over
    let msg = `⚠️ 医疗设备到期提醒\n\n`
    if (over > 0) msg += `已过期设备：${over} 台\n`
    if (soon > 0) msg += `30天内到期：${soon} 台\n\n`
    msg += '详细信息请查看下方「医疗设备到期提醒」面板。'
    setTimeout(() => alert(msg), 500)
  }
  loading.value = false
})

function typeText(t) {
  return (
    { checkout: '领用', return: '归还', transfer: '调拨', offboard: '离职回收', scrap: '报废' }[
      t
    ] || t
  )
}
function typeBadge(t) {
  return (
    { checkout: 'green', return: 'blue', transfer: 'amber', offboard: 'red', scrap: 'red' }[t] ||
    'gray'
  )
}
</script>

<style scoped>
.dashboard-date {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #748b9d;
}
.dashboard-date .app-icon {
  width: 16px;
  height: 16px;
}
.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}
.card {
  background: white;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 18px 20px 17px;
  min-width: 0;
}
.metric-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.label {
  font-size: 12px;
  font-weight: 500;
  color: #62798d;
}
.metric-icon {
  width: 31px;
  height: 31px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: #3168df;
  background: #edf2fe;
}
.metric-icon .app-icon {
  width: 18px;
  height: 18px;
}
.metric-icon.positive {
  color: #087f72;
  background: #eaf6f2;
}
.metric-icon.idle {
  color: #8b6ab7;
  background: #f2eef9;
}
.metric-icon.pending {
  color: #b27a27;
  background: #fdf4e7;
}
.num {
  font-size: 31px;
  font-weight: 650;
  letter-spacing: -0.5px;
  line-height: 1.25;
  font-variant-numeric: tabular-nums;
  margin-top: 10px;
  color: var(--ink);
}
.metric-note {
  font-size: 11px;
  color: #7b8fa0;
  margin-top: 7px;
}
.module-overview {
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 18px 22px;
  border: 1px solid var(--line);
  background: white;
  border-radius: 10px;
  margin-bottom: 20px;
}
.overview-title {
  flex-shrink: 0;
  padding-right: 22px;
  border-right: 1px solid var(--line);
}
.overview-title h3 {
  font-size: 13px;
  font-weight: 600;
}
.overview-title p {
  font-size: 10px;
  margin-top: 5px;
  color: #899aa9;
}
.module-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 18px;
}
.mini-stat {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.mini-stat > .app-icon {
  width: 20px;
  height: 20px;
  color: #8fa3b4;
}
.mini-stat > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.label-sm {
  font-size: 11px;
  color: #7a8c9d;
  white-space: nowrap;
}
.mini-stat strong {
  font-size: 20px;
  font-weight: 600;
  color: #304c63;
  font-variant-numeric: tabular-nums;
}
.activity-grid,
.reminder-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}
.panel {
  background: white;
  border: 1px solid var(--line);
  border-radius: 10px;
  min-width: 0;
  overflow: hidden;
}
.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 18px 20px;
  border-bottom: 1px solid #edf1f5;
  flex-wrap: wrap;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
}
.section-title > .app-icon {
  width: 18px;
  height: 18px;
  color: #7c93a6;
}
.section-title h3 {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.6;
}
.section-count {
  padding: 1px 6px;
  border-radius: 5px;
  background: #f1f5f9;
  color: #758a9c;
  font-size: 10px;
}
.section-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  text-decoration: none;
  color: var(--primary);
  white-space: nowrap;
}
.section-link .app-icon {
  width: 14px;
  height: 14px;
}
.section-link:hover {
  text-decoration: underline;
}
.activity-list {
  padding: 0 20px;
}
.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid #edf2f6;
}
.todo-item:last-child {
  border-bottom: 0;
}
.activity-mark {
  display: grid;
  place-items: center;
  width: 33px;
  height: 35px;
  border-radius: 8px;
  background: #f2f6fb;
  color: #7f96ad;
  flex-shrink: 0;
}
.activity-mark .app-icon {
  width: 17px;
  height: 17px;
}
.todo-copy {
  flex: 1;
  min-width: 0;
}
.todo-title {
  font-size: 12px;
  font-weight: 500;
  overflow-wrap: anywhere;
  line-height: 1.65;
}
.todo-copy p {
  font-size: 11px;
  color: #899bab;
  margin-top: 4px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.asset-reference {
  display: block;
  font-size: 10px;
  font-weight: 400;
  color: #8ba0b0;
  margin-top: 3px;
}
.reminder-icon {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: #fff5e7;
  color: #ba812d;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.reminder-icon .app-icon {
  width: 16px;
  height: 16px;
}
.reminder-icon.calibration {
  background: #eaf5f4;
  color: #248e83;
}
.section-description {
  font-size: 11px;
  color: #8b9cac;
  margin-top: 6px;
}
.reminder-panel .panel-heading {
  min-height: 103px;
  align-items: flex-start;
}
.reminder-panel .empty-state {
  padding-block: 28px;
}
@media (max-width: 1180px) {
  .module-overview {
    gap: 18px;
    padding-inline: 18px;
  }
  .module-grid {
    gap: 12px;
  }
  .mini-stat {
    gap: 8px;
  }
  .mini-stat > .app-icon {
    display: none;
  }
  .overview-title {
    padding-right: 16px;
  }
  .reminder-panel .panel-heading {
    min-height: 125px;
  }
}
@media (max-width: 900px) {
  .activity-grid,
  .reminder-grid {
    grid-template-columns: 1fr;
  }
  .module-overview {
    display: block;
  }
  .overview-title {
    display: none;
  }
  .mini-stat > .app-icon {
    display: block;
  }
  .reminder-panel .panel-heading {
    min-height: 0;
  }
  .card {
    padding: 16px;
  }
  .metric-note {
    font-size: 10px;
  }
}
@media (max-width: 600px) {
  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }
  .card {
    padding: 15px;
  }
  .num {
    font-size: 29px;
  }
  .metric-icon {
    width: 28px;
    height: 28px;
  }
  .metric-note {
    min-height: 16px;
    line-height: 1.5;
  }
  .module-overview {
    padding: 16px;
  }
  .module-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    row-gap: 17px;
  }
  .mini-stat {
    gap: 9px;
  }
  .mini-stat > .app-icon {
    width: 17px;
    height: 17px;
  }
  .mini-stat strong {
    font-size: 18px;
  }
  .label-sm {
    font-size: 10px;
  }
  .activity-grid,
  .reminder-grid {
    gap: 16px;
    margin-bottom: 16px;
  }
  .panel-heading {
    padding: 16px;
  }
  .activity-list {
    padding-inline: 16px;
  }
  .section-title h3 {
    font-size: 12px;
  }
  .dashboard-date {
    font-size: 11px;
  }
}
</style>
