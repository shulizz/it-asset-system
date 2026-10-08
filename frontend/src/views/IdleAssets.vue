<template>
  <div>
    <h2 style="margin-bottom:16px">空闲设备</h2>
    <div class="stats" style="margin-bottom:20px">
      <div class="card"><div class="num">{{ list.length }}</div><div class="label">空闲总数</div></div>
      <div class="card"><div class="num" style="color:#2563eb">{{ byType.it }}</div><div class="label">IT设备</div></div>
      <div class="card"><div class="num" style="color:#7c3aed">{{ byType.phone }}</div><div class="label">手机</div></div>
      <div class="card"><div class="num" style="color:#16a34a">{{ byType.medical }}</div><div class="label">医疗</div></div>
      <div class="card"><div class="num" style="color:#d97706">{{ byType.number }}</div><div class="label">电话号码</div></div>
      <div class="card"><div class="num" style="color:#db2777">{{ byType.wechat }}</div><div class="label">微信账号</div></div>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>资产编号/号码</th><th>名称/说明</th><th>类型</th><th>当前部门</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in list" :key="item.key">
            <td>{{ item.asset_number || item.number || item.wx_account }}</td>
            <td>{{ item.name || item.brand_model || item.keeper || item.wx_account || '—' }}</td>
            <td><span class="badge" :class="typeClass(item.type)">{{ item.type }}</span></td>
            <td>{{ item.department || '—' }}</td>
            <td><span class="badge amber">空闲</span></td>
            <td><a @click="goTransfer(item)" style="color:#2563eb;cursor:pointer">去领用</a></td>
          </tr>
          <tr v-if="list.length === 0"><td colspan="6" style="text-align:center;color:#94a3b8;padding:30px">当前没有空闲资源</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
const router = useRouter()
const list = ref([])
const byType = ref({ it:0, phone:0, medical:0, number:0, wechat:0 })
onMounted(async () => {
  const [it, phone, medical, numbers, wechat] = await Promise.all([
    api.get('/assets/it').catch(()=>({data:[]})),
    api.get('/assets/phone').catch(()=>({data:[]})),
    api.get('/assets/medical').catch(()=>({data:[]})),
    api.get('/assets/numbers').catch(()=>({data:[]})),
    api.get('/wechat').catch(()=>({data:[]})),
  ])
  const idle = [
    ...it.data.filter(x => x.status === 'idle').map(x => ({...x, type:'IT设备'})),
    ...phone.data.filter(x => x.status === 'idle').map(x => ({...x, type:'手机'})),
    ...medical.data.filter(x => x.status === 'idle').map(x => ({...x, type:'医疗'})),
    ...numbers.data.filter(x => x.status === 'idle').map(x => ({...x, type:'电话号码'})),
    ...wechat.data.filter(x => x.status === 'idle').map(x => ({...x, type:'微信账号'})),
  ]
  list.value = idle.map((x,i) => ({...x, key:i}))
  byType.value = {
    it: it.data.filter(x => x.status === 'idle').length,
    phone: phone.data.filter(x => x.status === 'idle').length,
    medical: medical.data.filter(x => x.status === 'idle').length,
    number: numbers.data.filter(x => x.status === 'idle').length,
    wechat: wechat.data.filter(x => x.status === 'idle').length,
  }
})
function goTransfer(item){
  router.push('/transfer')
}
function typeClass(t){ return {'IT设备':'blue','手机':'purple','医疗':'green','电话号码':'amber','微信账号':'pink'}[t]||'gray' }
</script>
<style scoped>
.stats{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}
.card{background:#fff;border-radius:10px;padding:16px;border:1px solid #e2e8f0}
.num{font-size:24px;font-weight:700}
.label{font-size:12px;color:#94a3b8;margin-top:4px}
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.badge{padding:2px 8px;border-radius:4px;font-size:12px}
.blue{background:#dbeafe;color:#2563eb}.purple{background:#ede9fe;color:#7c3aed}.green{background:#dcfce7;color:#16a34a}.amber{background:#fef3c7;color:#d97706}.pink{background:#fce7f3;color:#db2777}.gray{background:#f1f5f9;color:#64748b}
</style>
