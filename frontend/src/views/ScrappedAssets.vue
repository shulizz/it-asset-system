<template>
  <div>
    <h2 style="margin-bottom:16px">报废设备</h2>
    <div class="stats" style="margin-bottom:20px">
      <div class="card"><div class="num" style="color:#dc2626">{{ list.length }}</div><div class="label">报废设备总数</div></div>
      <div class="card"><div class="num" style="color:#2563eb">{{ byType.it }}</div><div class="label">IT设备</div></div>
      <div class="card"><div class="num" style="color:#7c3aed">{{ byType.phone }}</div><div class="label">手机</div></div>
      <div class="card"><div class="num" style="color:#16a34a">{{ byType.medical }}</div><div class="label">医疗</div></div>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>资产编号</th><th>名称</th><th>类型</th><th>原部门</th><th>状态</th></tr></thead>
        <tbody>
          <tr v-for="item in list" :key="item.key">
            <td>{{ item.asset_number || item.number }}</td>
            <td>{{ item.name || item.brand_model }}</td>
            <td><span class="badge" :class="typeClass(item.type)">{{ item.type }}</span></td>
            <td>{{ item.department || '—' }}</td>
            <td><span class="badge red">已报废</span></td>
          </tr>
          <tr v-if="list.length === 0"><td colspan="5" style="text-align:center;color:#94a3b8;padding:30px">暂无报废设备</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
const list = ref([])
const byType = ref({ it:0, phone:0, medical:0 })
onMounted(async () => {
  const [it, phone, medical] = await Promise.all([
    api.get('/assets/it'), api.get('/assets/phone'), api.get('/assets/medical')
  ])
  const sc = [
    ...it.data.filter(x => x.status === 'scrapped').map(x => ({...x, type:'IT设备'})),
    ...phone.data.filter(x => x.status === 'scrapped').map(x => ({...x, type:'手机'})),
    ...medical.data.filter(x => x.status === 'scrapped').map(x => ({...x, type:'医疗'})),
  ]
  list.value = sc.map((x,i) => ({...x, key:i}))
  byType.value = {
    it: it.data.filter(x => x.status === 'scrapped').length,
    phone: phone.data.filter(x => x.status === 'scrapped').length,
    medical: medical.data.filter(x => x.status === 'scrapped').length,
  }
})
function typeClass(t){ return {'IT设备':'blue','手机':'purple','医疗':'green'}[t]||'gray' }
</script>
<style scoped>
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.card{background:#fff;border-radius:10px;padding:20px;border:1px solid #e2e8f0}
.num{font-size:28px;font-weight:700}
.label{font-size:12px;color:#94a3b8;margin-top:4px}
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.badge{padding:2px 8px;border-radius:4px;font-size:12px}
.blue{background:#dbeafe;color:#2563eb}.purple{background:#ede9fe;color:#7c3aed}.green{background:#dcfce7;color:#16a34a}.red{background:#fee2e2;color:#dc2626}
</style>
