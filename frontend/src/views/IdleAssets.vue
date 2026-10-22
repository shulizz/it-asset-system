<template>
  <div>
    <PageHeading title="空闲设备" description="查看可调配的闲置资产，安排后续使用。"></PageHeading>
    <div class="stats" style="margin-bottom: 20px">
      <div class="card">
        <div class="num">{{ totalQuantity(list) }}</div>
        <div class="label">空闲总数</div>
      </div>
      <div class="card">
        <div class="num" style="color: #2563eb">{{ byType.it }}</div>
        <div class="label">IT设备</div>
      </div>
      <div class="card">
        <div class="num" style="color: #7c3aed">{{ byType.phone }}</div>
        <div class="label">手机</div>
      </div>
      <div v-if="canViewMedical" class="card">
        <div class="num" style="color: #16a34a">{{ byType.medical }}</div>
        <div class="label">医疗</div>
      </div>
      <div class="card">
        <div class="num" style="color: #d97706">{{ byType.number }}</div>
        <div class="label">电话号码</div>
      </div>
      <div class="card">
        <div class="num" style="color: #db2777">{{ byType.wechat }}</div>
        <div class="label">微信账号</div>
      </div>
    </div>
    <TableFrame title="空闲资产列表" :count="list.length"
      ><table>
        <thead>
          <tr>
            <th>资产编号/号码</th>
            <th>名称/说明</th>
            <th>数量</th>
            <th>类型</th>
            <th>当前部门</th>
            <th>状态</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list" :key="item.key">
            <td>{{ item.asset_number || item.number || item.wx_account }}</td>
            <td>{{ item.name || item.brand_model || item.keeper || item.wx_account || '—' }}</td>
            <td>{{ assetQuantity(item) }}</td>
            <td>
              <span class="badge" :class="typeClass(item.type)">{{ item.type }}</span>
            </td>
            <td>{{ item.department || '—' }}</td>
            <td><span class="badge amber">空闲</span></td>
            <td>
              <button
                type="button"
                class="row-action"
                @click="goTransfer(item)"
                style="color: #2563eb; cursor: pointer"
              >
                去领用
              </button>
            </td>
          </tr>
        </tbody>
      </table></TableFrame
    >
  </div>
</template>
<script setup>
import { assetQuantity, totalQuantity } from '../assetQuantity'
import { hasMedicalAccess } from '../medicalAccess'
const canViewMedical = computed(() => hasMedicalAccess(currentUser.value))
import { currentUser } from '../userState'
import PageHeading from '../components/PageHeading.vue'
import TableFrame from '../components/TableFrame.vue'
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
const router = useRouter()
const list = ref([])
const byType = ref({ it: 0, phone: 0, medical: 0, number: 0, wechat: 0 })
onMounted(async () => {
  const [it, phone, medical, numbers, wechat] = await Promise.all([
    api.get('/assets/it').catch(() => ({ data: [] })),
    api.get('/assets/phone').catch(() => ({ data: [] })),
    canViewMedical.value
      ? api.get('/assets/medical').catch(() => ({ data: [] }))
      : Promise.resolve({ data: [] }),
    api.get('/assets/numbers').catch(() => ({ data: [] })),
    api.get('/wechat').catch(() => ({ data: [] })),
  ])
  const idle = [
    ...it.data.filter((x) => x.status === 'idle').map((x) => ({ ...x, type: 'IT设备' })),
    ...phone.data.filter((x) => x.status === 'idle').map((x) => ({ ...x, type: '手机' })),
    ...medical.data.filter((x) => x.status === 'idle').map((x) => ({ ...x, type: '医疗' })),
    ...numbers.data.filter((x) => x.status === 'idle').map((x) => ({ ...x, type: '电话号码' })),
    ...wechat.data.filter((x) => x.status === 'idle').map((x) => ({ ...x, type: '微信账号' })),
  ]
  list.value = idle.map((x, i) => ({ ...x, key: i }))
  byType.value = {
    it: it.data.filter((x) => x.status === 'idle').length,
    phone: totalQuantity(phone.data.filter((x) => x.status === 'idle')),
    medical: medical.data.filter((x) => x.status === 'idle').length,
    number: numbers.data.filter((x) => x.status === 'idle').length,
    wechat: wechat.data.filter((x) => x.status === 'idle').length,
  }
})
function goTransfer(item) {
  router.push('/transfer')
}
function typeClass(t) {
  return (
    { IT设备: 'blue', 手机: 'purple', 医疗: 'green', 电话号码: 'amber', 微信账号: 'pink' }[t] ||
    'gray'
  )
}
</script>
<style scoped>
.pink {
  background: #fce7f3;
  color: #db2777;
}
</style>
