<template>
  <div>
    <h2 style="margin-bottom:20px">审批</h2>

    <h3 style="margin:16px 0 8px;color:#334155">设备申请</h3>
    <div class="panel" style="margin-bottom:24px">
      <table>
        <thead><tr><th>申请时间</th><th>类型</th><th>申请内容</th><th>设备</th><th>使用人</th><th>部门</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in applyList" :key="'a'+item.id">
            <td>{{ item.created_at }}</td>
            <td><span class="badge" :class="applyTypeClass(item.applyType)">{{ applyTypeText(item.applyType) }}</span></td>
            <td>{{ item.record_desc }}</td>
            <td>{{ item.applyAsset || '—' }}</td>
            <td>{{ item.applyUser }}</td>
            <td>{{ item.applyDept }}</td>
            <td><span class="badge" :class="statusClass(item.status)">{{ statusText(item.status) }}</span></td>
            <td>
              <template v-if="item.status === 'pending'">
                <a @click="approveApply(item)" style="color:#16a34a;cursor:pointer;margin-right:10px">通过</a>
                <a @click="rejectApply(item)" style="color:#dc2626;cursor:pointer">驳回</a>
              </template>
              <span v-else style="color:#94a3b8">已处理</span>
            </td>
          </tr>
          <tr v-if="applyList.length === 0"><td colspan="8" style="text-align:center;color:#94a3b8;padding:20px">暂无设备申请</td></tr>
        </tbody>
      </table>
    </div>

    <h3 style="margin:16px 0 8px;color:#334155">删除申请</h3>
    <div class="panel" style="margin-bottom:24px">
      <table>
        <thead><tr><th>申请时间</th><th>删除内容</th><th>原因</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in deleteList" :key="'d'+item.id">
            <td>{{ item.created_at }}</td>
            <td>{{ item.record_desc }}</td>
            <td>{{ item.reason }}</td>
            <td><span class="badge" :class="statusClass(item.status)">{{ statusText(item.status) }}</span></td>
            <td>
              <template v-if="item.status === 'pending'">
                <a @click="approveDel(item)" style="color:#16a34a;cursor:pointer;margin-right:10px">通过</a>
                <a @click="rejectDel(item)" style="color:#dc2626;cursor:pointer">驳回</a>
              </template>
              <span v-else style="color:#94a3b8">{{ item.approver }}</span>
            </td>
          </tr>
          <tr v-if="deleteList.length === 0"><td colspan="5" style="text-align:center;color:#94a3b8;padding:20px">暂无删除申请</td></tr>
        </tbody>
      </table>
    </div>

    <h3 style="margin:16px 0 8px;color:#334155">报废申请</h3>
    <div class="panel">
      <table>
        <thead><tr><th>申请号</th><th>设备</th><th>申请人</th><th>原因</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in scrapList" :key="'s'+item.id">
            <td>{{ item.request_number }}</td>
            <td>{{ item.asset_desc }}</td>
            <td>{{ item.applicant || '—' }}</td>
            <td>{{ item.reason || '—' }}</td>
            <td><span class="badge" :class="scrapStatusClass(item.status)">{{ scrapStatusText(item.status) }}</span></td>
            <td>
              <template v-if="item.status === 'pending_approval'">
                <a @click="approveScrap(item)" style="color:#16a34a;cursor:pointer;margin-right:10px">通过</a>
                <a @click="rejectScrap(item)" style="color:#dc2626;cursor:pointer">驳回</a>
              </template>
              <span v-else style="color:#94a3b8">已处理</span>
            </td>
          </tr>
          <tr v-if="scrapList.length === 0"><td colspan="6" style="text-align:center;color:#94a3b8;padding:20px">暂无报废申请</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
const deleteList = ref([])
const scrapList = ref([])
const applyList = ref([])

async function load(){
  const [d, s] = await Promise.all([api.get('/delete-request'), api.get('/scrap')])
  // 分离申请和删除
  applyList.value = d.data.filter(r => r.table_name === 'apply_requests').map(r => {
    const parts = (r.reason || '||||').split('|')
    return { ...r, applyType: parts[0]||'', applyUser: parts[1]||'', applyDept: parts[2]||'', applyAsset: parts[3]||'' }
  })
  deleteList.value = d.data.filter(r => r.table_name !== 'apply_requests')
  scrapList.value = s.data
}
async function approveDel(item){ await api.put(`/delete-request/${item.id}/approve`); load() }
async function rejectDel(item){ await api.put(`/delete-request/${item.id}/reject`); load() }
async function approveScrap(item){ await api.put(`/scrap/${item.id}/approve`); load() }
async function rejectScrap(item){ await api.put(`/scrap/${item.id}/reject`); load() }
async function approveApply(item){ await api.put(`/delete-request/${item.id}/approve`); load() }
async function rejectApply(item){ await api.put(`/delete-request/${item.id}/reject`); load() }

function statusClass(s){ return {pending:'amber',approved:'green',rejected:'red'}[s]||'gray' }
function statusText(s){ return {pending:'待审批',approved:'已通过',rejected:'已驳回'}[s]||s }
function applyTypeClass(t){ return {checkout:'blue',new_asset:'green',transfer:'amber',scrap:'red'}[t]||'gray' }
function applyTypeText(t){ return {checkout:'领用申请',new_asset:'新增申请',transfer:'调拨申请',scrap:'报废申请'}[t]||t }
function scrapStatusClass(s){ return {pending_approval:'amber',approved:'green',disposed:'gray',archived:'gray'}[s]||'gray' }
function scrapStatusText(s){ return {pending_approval:'待审批',approved:'已批准',disposed:'已处置',archived:'已归档'}[s]||s }
onMounted(load)
</script>
<style scoped>
.panel{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}
.badge{padding:2px 8px;border-radius:4px;font-size:12px}
.amber{background:#fef3c7;color:#d97706}.green{background:#dcfce7;color:#16a34a}.red{background:#fee2e2;color:#dc2626}.gray{background:#f1f5f9;color:#64748b}.blue{background:#dbeafe;color:#2563eb}
</style>
