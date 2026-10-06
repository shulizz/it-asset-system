<template>
  <div>
    <h2 style="margin-bottom:20px">报表统计 <button class="btn-export" @click="exportCSV">导出Excel</button></h2>
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
import { ref, onMounted } from 'vue'
import * as XLSX from 'xlsx'
import api from '../api'
const total = ref({ it:0, phone:0, medical:0, number:0, wechat:0 })
const status = ref({ inUse:0, idle:0, scrapped:0 })
const deptCount = ref(0)
const deptStats = ref([])
const idleList = ref([])
async function exportCSV(){
  const [it, phone, medical, numbers] = await Promise.all([
    api.get('/assets/it'), api.get('/assets/phone'),
    api.get('/assets/medical'), api.get('/assets/numbers')
  ])
  const wb = XLSX.utils.book_new()

  const itData = it.data.map(i => ({
    '资产编号': i.asset_number, '设备名称': i.name, '使用人': i.user_name||'',
    '部门': i.department||'', '状态': statusText(i.status), '采购日期': i.purchase_date||''
  }))
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(itData), 'IT设备')

  const phData = phone.data.map(i => ({
    '资产编号': i.asset_number, '品牌型号': i.brand_model, '使用人': i.user_name||'',
    '部门': i.department||'', '状态': statusText(i.status)
  }))
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(phData), '手机设备')

  const medData = medical.data.map(i => ({
    '资产编号': i.asset_number, '设备名称': i.name, '型号': i.model||'',
    '科室': i.department||'', '保管人': i.keeper||'', '状态': statusText(i.status)
  }))
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(medData), '医疗设备')

  const numData = numbers.data.map(i => ({
    '号码': i.number, '运营商': i.carrier||'', '类型': cardText(i.card_type),
    '套餐': i.plan||'', '部门': i.department||'', '使用人': i.user_name||'', '状态': numStatusText(i.status)
  }))
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(numData), '电话号码')

  const deptData = deptStats.value.map(d => ({
    '部门': d.name, 'IT设备': d.it, '手机': d.phone, '医疗设备': d.medical, '电话号码': d.number
  }))
  const wcData = (wc.data||[]).filter(x=>x.wx_account).map(i => ({
    '微信账号': i.wx_account, '实名人': i.real_name||'', '使用人': i.user_name||'', '用途': i.purpose||'', '状态': i.status==='in_use'?'使用中':'停用'
  }))
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(wcData), '微信账号')
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(deptData), '部门统计')

  XLSX.writeFile(wb, `资产报表_${new Date().toISOString().slice(0,10)}.xlsx`)
}
function statusText(s){ return {in_use:'在用',idle:'闲置',scrapped:'已报废'}[s]||s }
function cardText(t){ return {main:'主卡',sub:'副卡',landline:'座机'}[t]||t }
function numStatusText(s){ return {in_use:'在用',idle:'闲置',cancelled:'注销',unused:'不再使用'}[s]||s }
onMounted(async () => {
  const [it, phone, medical, numbers, depts, wc] = await Promise.all([
    api.get('/assets/it'), api.get('/assets/phone'), api.get('/assets/medical'),
    api.get('/assets/numbers'), api.get('/departments'), api.get('/wechat')
  ])
  total.value = { it: it.data.length, phone: phone.data.length, medical: medical.data.length, number: numbers.data.length, wechat: wc.data.filter(x=>x.wx_account).length }
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

