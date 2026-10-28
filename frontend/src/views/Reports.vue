<template>
  <div>
    <PageHeading title="报表统计" description="查看资产数量、使用状态及部门分布。"
      ><FileDownloadButton
        v-if="canExport"
        endpoint="/reports/export"
        filename="资产报表.xlsx"
        label="导出Excel"
        button-class="btn btn-primary"
    /></PageHeading>
    <p v-if="loadError" style="color: #b45309">{{ loadError }}</p>
    <section class="group-report" aria-labelledby="group-report-title">
      <header class="group-report-heading">
        <div>
          <h3 id="group-report-title">医院 / 网络部统计</h3>
          <p>
            {{
              groupSummary?.scope === 'department'
                ? '当前仅统计你有权查看的部门。'
                : '按部门归属汇总各模块数量。'
            }}
          </p>
        </div>
        <span class="group-scope">手机按实际台数</span>
      </header>
      <p v-if="groupError" class="group-error" role="alert">{{ groupError }}</p>
      <p v-else-if="!groupSummary" class="group-note">正在加载分组统计…</p>
      <template v-else>
        <div class="group-panels">
          <article
            v-for="group in groupSummary.groups"
            :key="group.key"
            class="group-panel"
            :class="group.key"
            :aria-label="group.name + '模块统计'"
          >
            <header>
              <h4>{{ group.name }}</h4>
              <p>
                {{
                  group.key === 'hospital'
                    ? groupSummary.hospital_departments.join('、')
                    : '除医院范围外的其余部门'
                }}
              </p>
            </header>
            <dl>
              <div v-for="module in visibleGroupModules" :key="module.key">
                <dt>{{ module.label }}</dt>
                <dd>{{ group.counts[module.key] }}</dd>
              </div>
            </dl>
            <section class="group-scrap" :aria-label="group.name + '报废分类统计'">
              <h5>已报废（不计入合计）</h5>
              <dl>
                <div>
                  <dt>主机报废</dt>
                  <dd>{{ group.it_scrapped?.hosts ?? 0 }}</dd>
                </div>
                <div>
                  <dt>显示器报废</dt>
                  <dd>{{ group.it_scrapped?.monitors ?? 0 }}</dd>
                </div>
                <div>
                  <dt>其他 IT 报废</dt>
                  <dd>{{ group.it_scrapped?.other ?? 0 }}</dd>
                </div>
                <div
                  v-for="module in visibleGroupModules.filter((m) => m.key !== 'it')"
                  :key="module.key"
                >
                  <dt>{{ module.label }}报废</dt>
                  <dd>{{ group.scrapped?.[module.key] ?? 0 }}</dd>
                </div>
              </dl>
            </section>
          </article>
        </div>
        <p class="group-note">
          上方合计不含已报废、已移出档案设备；报废数量单独列出。医疗、消防按查看权限显示。
        </p>
        <p v-if="hasUnassigned" class="group-note">
          未分配部门（未计入两组）：{{ unassignedText }}
        </p>
        <p
          v-if="
            groupSummary.unassigned_it_scrapped &&
            Object.values(groupSummary.unassigned_it_scrapped).some((n) => n > 0)
          "
          class="group-note"
        >
          未分配部门的报废 IT：主机 {{ groupSummary.unassigned_it_scrapped.hosts }} 台，显示器
          {{ groupSummary.unassigned_it_scrapped.monitors }} 台，其他
          {{ groupSummary.unassigned_it_scrapped.other }} 台。
        </p>
        <p
          v-if="groupSummary.wechat_count !== null && hasWeChatRead(currentUser)"
          class="group-note"
        >
          微信账号尚无部门归属，暂不分组；可查看账号共 {{ groupSummary.wechat_count }} 个。
        </p>
      </template>
    </section>
    <div class="stats">
      <div v-if="canViewFire" class="card">
        <div class="num">{{ total.fire || 0 }}</div>
        <div class="label">消防设备</div>
      </div>
      <div class="card">
        <div class="num">{{ total.it }}</div>
        <div class="label">IT设备</div>
      </div>
      <div class="card">
        <div class="num">{{ total.phone }}</div>
        <div class="label">手机</div>
      </div>
      <div v-if="canViewMedical" class="card">
        <div class="num">{{ total.medical }}</div>
        <div class="label">医疗设备</div>
      </div>
      <div class="card">
        <div class="num">{{ total.number }}</div>
        <div class="label">电话号码</div>
      </div>
      <div class="card">
        <div class="num">{{ total.wechat }}</div>
        <div class="label">微信账号</div>
      </div>
    </div>
    <p class="group-note">
      状态统计包含可查看的设备、电话号码和微信账号；手机按台数，注销及停用不计入在用、闲置。
    </p>
    <div class="stats" style="margin-top: 16px">
      <div class="card">
        <div class="num" style="color: #16a34a">{{ status.inUse }}</div>
        <div class="label">在用</div>
      </div>
      <div class="card">
        <div class="num" style="color: #d97706">{{ status.idle }}</div>
        <div class="label">闲置</div>
      </div>
      <div class="card">
        <div class="num" style="color: #dc2626">{{ status.scrapped }}</div>
        <div class="label">已报废（单独统计）</div>
        <p v-if="groupSummary?.it_scrapped_totals" class="group-note">
          主机 {{ groupSummary.it_scrapped_totals.hosts }} 台 · 显示器
          {{ groupSummary.it_scrapped_totals.monitors }} 台
        </p>
      </div>
      <div class="card">
        <div class="num">{{ deptCount }}</div>
        <div class="label">部门数</div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 20px">
      <TableFrame title="部门资产分布" :count="deptStats.length"
        ><table>
          <thead>
            <tr>
              <th v-if="canViewFire">消防设备</th>
              <th>部门</th>
              <th>IT设备</th>
              <th>手机</th>
              <th v-if="canViewMedical">医疗</th>
              <th>电话</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in deptStats" :key="d.name">
              <td v-if="canViewFire">{{ d.fire }}</td>
              <td>{{ d.name }}</td>
              <td>{{ d.it }}</td>
              <td>{{ d.phone }}</td>
              <td v-if="canViewMedical">{{ d.medical }}</td>
              <td>{{ d.number }}</td>
            </tr>
          </tbody>
        </table></TableFrame
      >
      <TableFrame title="闲置设备明细" :count="idleList.length"
        ><table>
          <thead>
            <tr>
              <th>编号</th>
              <th>名称</th>
              <th>数量</th>
              <th>类型</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in idleList" :key="item.key">
              <td>{{ item.asset_number || item.number || item.wx_account }}</td>
              <td>{{ item.name || item.brand_model || item.wx_account || item.carrier || '—' }}</td>
              <td>{{ assetQuantity(item) }}</td>
              <td>{{ item.type }}</td>
            </tr>
          </tbody>
        </table></TableFrame
      >
    </div>
  </div>
</template>
<script setup>
import { hasFireAccess } from '../fireAccess'
const canViewFire = computed(() => hasFireAccess(currentUser.value))
import { assetQuantity, totalQuantity } from '../assetQuantity'
import { hasMedicalAccess } from '../medicalAccess'
import { hasWeChatRead } from '../wechatAccess'
const canViewMedical = computed(() => hasMedicalAccess(currentUser.value))
import PageHeading from '../components/PageHeading.vue'
import TableFrame from '../components/TableFrame.vue'
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import { currentUser, refreshCurrentUser } from '../userState'
import FileDownloadButton from '../components/FileDownloadButton.vue'
const canExport = computed(() => (currentUser.value.permissions || []).includes('export'))
const loadError = ref('')
const total = ref({ it: 0, phone: 0, medical: 0, number: 0, wechat: 0 })
const status = ref({ inUse: 0, idle: 0, scrapped: 0 })
const deptCount = ref(0)
const deptStats = ref([])
const idleList = ref([])
const retainedAssets = (rows) =>
  rows.filter((item) => !['scrapped', 'archived'].includes(item.status))
const groupSummary = ref(null),
  groupError = ref('')
const visibleGroupModules = computed(() =>
  (groupSummary.value?.modules || []).filter(
    (module) =>
      (module.key !== 'medical' || canViewMedical.value) &&
      (module.key !== 'fire' || canViewFire.value),
  ),
)
const hasUnassigned = computed(() =>
  visibleGroupModules.value.some((module) => groupSummary.value.unassigned[module.key] > 0),
)
const unassignedText = computed(() =>
  visibleGroupModules.value
    .filter((module) => groupSummary.value.unassigned[module.key] > 0)
    .map((module) => `${module.label} ${groupSummary.value.unassigned[module.key]}`)
    .join('，'),
)

async function loadGroups() {
  try {
    groupSummary.value = (await api.get('/reports/group-summary')).data
    groupError.value = ''
  } catch {
    groupError.value = '医院 / 网络部统计加载失败，请刷新重试'
  }
}

function statusText(s) {
  return { in_use: '在用', idle: '闲置', scrapped: '已报废' }[s] || s
}
function cardText(t) {
  return { main: '主卡', sub: '副卡', landline: '座机' }[t] || t
}
function numStatusText(s) {
  return { in_use: '在用', idle: '闲置', cancelled: '注销', unused: '不再使用' }[s] || s
}
onMounted(async () => {
  try {
    await refreshCurrentUser()
  } catch {
    loadError.value = '无法读取用户权限，请重新登录'
    groupError.value = '无法读取用户权限，请重新登录后查看分组统计'
    return
  }
  const errors = []
  async function fetchModule(path, label) {
    try {
      return await api.get(path)
    } catch {
      errors.push(label)
      return { data: [] }
    }
  }
  const canWechat = hasWeChatRead(currentUser.value)
  const [it, phone, medical, numbers, depts, wc, fire] = await Promise.all([
    fetchModule('/assets/it', 'IT设备'),
    fetchModule('/assets/phone', '手机'),
    canViewMedical.value
      ? fetchModule('/assets/medical', '医疗设备')
      : Promise.resolve({ data: [] }),
    fetchModule('/assets/numbers', '电话号码'),
    fetchModule('/departments', '部门'),
    canWechat ? fetchModule('/wechat', '微信账号') : Promise.resolve({ data: [] }),
    canViewFire.value ? fetchModule('/assets/fire', '消防设备') : Promise.resolve({ data: [] }),
    loadGroups(),
  ])
  if (errors.length) loadError.value = `${errors.join('、')}加载失败，相关统计不完整，请刷新重试`
  total.value = {
    it: retainedAssets(it.data).length,
    phone: totalQuantity(retainedAssets(phone.data)),
    fire: retainedAssets(fire.data).length,
    medical: retainedAssets(medical.data).length,
    number: retainedAssets(numbers.data).length,
    wechat: canWechat ? retainedAssets(wc.data).filter((x) => x.wx_account).length : '无权限',
  }
  deptCount.value = depts.data.length

  const all = [
    ...fire.data.map((x) => ({ ...x, type: '消防设备' })),
    ...it.data.map((x) => ({ ...x, type: 'IT设备' })),
    ...phone.data.map((x) => ({ ...x, type: '手机' })),
    ...medical.data.map((x) => ({ ...x, type: '医疗' })),
    ...numbers.data.map((x) => ({ ...x, type: '电话号码' })),
    ...wc.data.filter((x) => x.wx_account).map((x) => ({ ...x, type: '微信账号' })),
  ]
  status.value.inUse = totalQuantity(all.filter((x) => x.status === 'in_use'))
  status.value.idle = totalQuantity(all.filter((x) => x.status === 'idle'))
  status.value.scrapped = totalQuantity(all.filter((x) => x.status === 'scrapped'))
  idleList.value = all.filter((x) => x.status === 'idle').map((x, i) => ({ ...x, key: i }))

  deptStats.value = depts.data.map((d) => ({
    name: d.name,
    fire: retainedAssets(fire.data).filter((x) => x.department === d.name).length,
    it: retainedAssets(it.data).filter((x) => x.department === d.name).length,
    phone: totalQuantity(retainedAssets(phone.data).filter((x) => x.department === d.name)),
    medical: retainedAssets(medical.data).filter((x) => x.department === d.name).length,
    number: retainedAssets(numbers.data).filter((x) => x.department === d.name).length,
  }))
})
</script>
<style scoped>
.group-report {
  margin-bottom: 24px;
}
.group-report-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 8px 0 14px;
}
.group-report-heading h3 {
  font-size: 16px;
  margin: 0 0 5px;
}
.group-report-heading p,
.group-note {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.7;
}
.group-scope {
  font-size: 12px;
  color: var(--muted);
  white-space: nowrap;
}
.group-panels {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.group-panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
}
.group-panel header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
  border-left: 4px solid #2563eb;
}
.group-panel.network header {
  border-left-color: #168374;
}
.group-panel h4 {
  margin: 0 0 5px;
  font-size: 18px;
}
.group-panel header p {
  margin: 0;
  font-size: 12px;
  color: var(--muted);
}
.group-panel dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px 12px;
  padding: 20px;
  margin: 0;
}
.group-panel dt {
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 6px;
}
.group-panel dd {
  font-size: 26px;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
  margin: 0;
}
.group-scrap {
  border-top: 1px solid var(--line);
  background: #fffaf6;
}
.group-scrap h5 {
  font-size: 12px;
  font-weight: 600;
  color: #9a451c;
  padding: 14px 20px 0;
  margin: 0;
}
.group-scrap dl {
  padding-top: 12px;
}
.group-scrap dd {
  font-size: 22px;
  color: #9a451c;
}
.group-note {
  margin: 10px 0 0;
}
.group-error {
  color: #b42318;
  padding: 12px 0;
}
@media (max-width: 760px) {
  .group-panels {
    grid-template-columns: 1fr;
  }
  .group-report-heading {
    align-items: flex-start;
  }
  .group-panel dl {
    padding: 16px;
  }
}
.btn-export {
  margin-left: 12px;
  background: #16a34a;
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  vertical-align: middle;
}
.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  font-weight: 600;
}
</style>
