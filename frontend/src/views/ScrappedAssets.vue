<template>
  <div>
    <PageHeading title="报废设备" description="查阅已报废设备，保留历史资产信息。"></PageHeading>
    <div class="stats" style="margin-bottom: 20px">
      <div class="card">
        <div class="num" style="color: #dc2626">{{ list.length }}</div>
        <div class="label">报废设备总数</div>
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
    </div>
    <TableFrame title="报废资产列表" :count="list.length"
      ><table>
        <thead>
          <tr>
            <th>资产编号</th>
            <th>名称</th>
            <th>类型</th>
            <th>原部门</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in list" :key="item.key">
            <td>{{ item.asset_number || item.number }}</td>
            <td>{{ item.name || item.brand_model }}</td>
            <td>
              <span class="badge" :class="typeClass(item.type)">{{ item.type }}</span>
            </td>
            <td>{{ item.department || '—' }}</td>
            <td><span class="badge red">已报废</span></td>
          </tr>
        </tbody>
      </table></TableFrame
    >
  </div>
</template>
<script setup>
import { hasMedicalAccess } from '../medicalAccess'
const canViewMedical = computed(() => hasMedicalAccess(currentUser.value))
import { currentUser } from '../userState'
import PageHeading from '../components/PageHeading.vue'
import TableFrame from '../components/TableFrame.vue'
import { ref, onMounted, computed } from 'vue'
import api from '../api'
const list = ref([])
const byType = ref({ it: 0, phone: 0, medical: 0 })
onMounted(async () => {
  const [it, phone, medical] = await Promise.all([
    api.get('/assets/it'),
    api.get('/assets/phone'),
    canViewMedical.value ? api.get('/assets/medical') : Promise.resolve({ data: [] }),
  ])
  const sc = [
    ...it.data.filter((x) => x.status === 'scrapped').map((x) => ({ ...x, type: 'IT设备' })),
    ...phone.data.filter((x) => x.status === 'scrapped').map((x) => ({ ...x, type: '手机' })),
    ...medical.data.filter((x) => x.status === 'scrapped').map((x) => ({ ...x, type: '医疗' })),
  ]
  list.value = sc.map((x, i) => ({ ...x, key: i }))
  byType.value = {
    it: it.data.filter((x) => x.status === 'scrapped').length,
    phone: phone.data.filter((x) => x.status === 'scrapped').length,
    medical: medical.data.filter((x) => x.status === 'scrapped').length,
  }
})
function typeClass(t) {
  return { IT设备: 'blue', 手机: 'purple', 医疗: 'green' }[t] || 'gray'
}
</script>
