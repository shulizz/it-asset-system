<template>
  <div>
    <PageHeading title="操作日志" description="按操作人和模块查询关键业务记录。"></PageHeading>
    <div class="filter-bar">
      <input
        aria-label="搜索操作人/模块/内容..."
        v-model="keyword"
        placeholder="搜索操作人/模块/内容..."
      />
      <select aria-label="筛选模块" v-model="filterModule">
        <option value="">全部模块</option>
        <option v-for="m in modules" :value="m">{{ m }}</option>
      </select>
    </div>
    <TableFrame title="操作记录" :count="filtered.length"
      ><table>
        <thead>
          <tr>
            <th>时间</th>
            <th>操作人</th>
            <th>模块</th>
            <th class="actions-header">操作</th>
            <th>内容</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.id">
            <td>{{ item.created_at }}</td>
            <td>{{ item.user }}</td>
            <td>{{ item.module }}</td>
            <td>
              <span class="badge blue">{{ item.action }}</span>
            </td>
            <td>{{ item.detail }}</td>
          </tr>
        </tbody>
      </table></TableFrame
    >
  </div>
</template>
<script setup>
import PageHeading from '../components/PageHeading.vue'
import TableFrame from '../components/TableFrame.vue'
import { ref, computed, onMounted } from 'vue'
import api from '../api'
const list = ref([])
const keyword = ref('')
const filterModule = ref('')
onMounted(async () => {
  const res = await api.get('/logs')
  list.value = res.data
})
const modules = computed(() => [...new Set(list.value.map((i) => i.module))])
const filtered = computed(() =>
  list.value.filter((i) => {
    if (filterModule.value && i.module !== filterModule.value) return false
    if (keyword.value) {
      const k = keyword.value.toLowerCase()
      return (
        (i.user || '').toLowerCase().includes(k) ||
        (i.detail || '').toLowerCase().includes(k) ||
        (i.action || '').toLowerCase().includes(k)
      )
    }
    return true
  }),
)
</script>
