<template>
  <div>
    <h2 style="margin-bottom:16px">操作日志</h2>
    <div style="display:flex;gap:12px;margin-bottom:16px">
      <input v-model="keyword" placeholder="搜索操作人/模块/内容..." style="flex:1;height:36px;border:1px solid #e2e8f0;border-radius:6px;padding:0 10px">
      <select v-model="filterModule" style="height:36px;border:1px solid #e2e8f0;border-radius:6px;padding:0 10px">
        <option value="">全部模块</option>
        <option v-for="m in modules" :value="m">{{ m }}</option>
      </select>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>时间</th><th>操作人</th><th>模块</th><th>操作</th><th>内容</th></tr></thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.id">
            <td>{{ item.created_at }}</td><td>{{ item.user }}</td><td>{{ item.module }}</td>
            <td><span class="badge blue">{{ item.action }}</span></td><td>{{ item.detail }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
const list = ref([])
const keyword = ref('')
const filterModule = ref('')
onMounted(async () => { const res = await api.get('/logs'); list.value = res.data })
const modules = computed(() => [...new Set(list.value.map(i => i.module))])
const filtered = computed(() => list.value.filter(i => {
  if (filterModule.value && i.module !== filterModule.value) return false
  if (keyword.value) {
    const k = keyword.value.toLowerCase()
    return (i.user||'').toLowerCase().includes(k) || (i.detail||'').toLowerCase().includes(k) || (i.action||'').toLowerCase().includes(k)
  }
  return true
}))
</script>
<style scoped>
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.badge{padding:2px 8px;border-radius:4px;font-size:12px}
.blue{background:#dbeafe;color:#2563eb}
</style>
