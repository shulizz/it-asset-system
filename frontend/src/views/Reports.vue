<template>
  <div>
    <h2 style="margin-bottom:20px;display:flex;gap:12px;align-items:center">报表统计 <FileDownloadButton v-if="canExport" endpoint="/reports/export" filename="资产报表.xlsx" label="导出Excel" button-class="btn btn-primary" /></h2>
    <p v-if="loadError" style="color:#b45309">{{ loadError }}</p>
    <div class="stats">
      <div class="card"><div class="num">{{ total.it }}</div><div class="label">IT设备</div></div>
      <div class="card"><div class="num">{{ total.phone }}</div><div class="label">手机</div></div>
      <div class="card"><div class="num">{{ total.medical }}</div><div class="label">医疗设备</div></div>
      <div class="card"><div class="num">{{ total.number }}</div><div class="label">电话号码</div></div>
      <div class="card"><div class="num">{{ total.wechat }}</div><div class="label">微信账号</div></div>
    </div>
    <div class="stats" style="margin-top:16px">
      <div class="card"><div class="num" style="color:#16a34a">{{ status.inUse }}</div><div class="label">在用</div></div>
      <div class="card"><div class="num" style="color:#d97706">{{ status.idle }}</div><div class="label">闲置</div></div>
      <div class="card"><div class="num" style="color:#dc2626">{{ status.scrapped }}</div><div class="label">已报废</div></div>
      <div class="card"><div class="num">{{ deptCount }}</div><div class="label">部门数</div></div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px">
      <div class="panel">
        <div class="panel-header"><h3>各部门设备分布</h3></div>
        <table>
          <thead><tr><th>部门</th><th>IT设备</th><th>手机</th><th>医疗</th><th>电话</th></tr></thead>
          <tbody>
            <tr v-for="d in deptStats" :key="d.name">
              <td>{{ d.name }}</td><td>{{ d.it }}</td><td>{{ d.phone }}</td><td>{{ d.medical }}</td><td>{{ d.number }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="panel">
        <div class="panel-header"><h3>闲置设备清单</h3></div>
        <table>
          <thead><tr><th>编号</th><th>名称</th><th>类型</th></tr></thead>
          <tbody>
            <tr v-for="item in idleList" :key="item.key">
              <td>{{ item.asset_number || item.number }}</td><td>{{ item.name || item.brand_model }}</td><td>{{ item.type }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import FileDownloadButton from '../components/FileDownloadButton.vue'
const currentUser = ref({permissions: []})
const canExport = computed(() => currentUser.value.permissions.includes('export'))
const loadError = ref('')
const total = ref({ it:0, phone:0, medical:0, number:0, wechat:0 })
const status = ref({ inUse:0, idle:0, scrapped:0 })
const deptCount = ref(0)
const deptStats = ref([])
const idleList = ref([])

function statusText(s){ return {in_use:'在用',idle:'闲置',scrapped:'已报废'}[s]||s }
function cardText(t){ return {main:'主卡',sub:'副卡',landline:'座机'}[t]||t }
function numStatusText(s){ return {in_use:'在用',idle:'闲置',cancelled:'注销',unused:'不再使用'}[s]||s }
onMounted(async () => {
  try { currentUser.value = (await api.get('/auth/me')).data }
  catch { loadError.value = '无法读取用户权限，请重新登录'; return }
  const errors = []
  async function fetchModule(path, label){
    try { return await api.get(path) }
    catch { errors.push(label); return {data: []} }
  }
  const canWechat = currentUser.value.permissions.includes('wechat') && (currentUser.value.role === 'super_admin' || currentUser.value.data_scope === 'all')
  const [it, phone, medical, numbers, depts, wc] = await Promise.all([
    fetchModule('/assets/it', 'IT设备'), fetchModule('/assets/phone', '手机'), fetchModule('/assets/medical', '医疗设备'),
    fetchModule('/assets/numbers', '电话号码'), fetchModule('/departments', '部门'),
    canWechat ? fetchModule('/wechat', '微信账号') : Promise.resolve({data: []})
  ])
  if(errors.length) loadError.value = `${errors.join('、')}加载失败，相关统计不完整，请刷新重试`
  total.value = { it: it.data.length, phone: phone.data.length, medical: medical.data.length, number: numbers.data.length, wechat: canWechat ? wc.data.filter(x=>x.wx_account).length : '无权限' }
  deptCount.value = depts.data.length

  const all = [
    ...it.data.map(x => ({...x, type:'IT设备'})),
    ...phone.data.map(x => ({...x, type:'手机'})),
    ...medical.data.map(x => ({...x, type:'医疗'})),
  ]
  status.value.inUse = all.filter(x => x.status === 'in_use').length
  status.value.idle = all.filter(x => x.status === 'idle').length
  status.value.scrapped = all.filter(x => x.status === 'scrapped').length
  idleList.value = all.filter(x => x.status === 'idle').map((x,i) => ({...x, key:i}))

  deptStats.value = depts.data.map(d => ({
    name: d.name,
    it: it.data.filter(x => x.department === d.name).length,
    phone: phone.data.filter(x => x.department === d.name).length,
    medical: medical.data.filter(x => x.department === d.name).length,
    number: numbers.data.filter(x => x.department === d.name).length,
  }))
})
</script>
<style scoped>
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}
.card{background:#fff;border-radius:10px;padding:20px;border:1px solid #e2e8f0}
.num{font-size:28px;font-weight:700}
.label{font-size:12px;color:#94a3b8;margin-top:4px}
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
.btn-export{margin-left:12px;background:#16a34a;color:#fff;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;vertical-align:middle}
.panel-header{padding:16px 20px;border-bottom:1px solid #f1f5f9;font-weight:600}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
</style>

