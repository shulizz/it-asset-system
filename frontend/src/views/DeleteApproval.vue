<template>
  <div>
    <PageHeading title="审批" description="集中处理设备申请、删除申请与报废审批。"></PageHeading>

    <TableFrame title="设备申请" :count="applyList.length"
      ><table>
        <thead>
          <tr>
            <th>申请时间</th>
            <th>类型</th>
            <th>申请内容</th>
            <th>设备</th>
            <th>本次数量</th>
            <th>使用人</th>
            <th>部门</th>
            <th>状态</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in applyList" :key="'a' + item.id">
            <td>{{ item.created_at }}</td>
            <td>
              <span class="badge" :class="applyTypeClass(item.applyType)">{{
                applyTypeText(item.applyType)
              }}</span>
            </td>
            <td>{{ item.record_desc }}</td>
            <td>{{ item.applyAsset || '—' }}</td>
            <td>{{ item.quantity ?? 1 }}</td>
            <td>{{ item.applyUser }}</td>
            <td>{{ item.applyDept }}</td>
            <td>
              <span class="badge" :class="statusClass(item.status)">{{
                statusText(item.status)
              }}</span>
            </td>
            <td>
              <template v-if="item.status === 'pending'">
                <button
                  type="button"
                  class="row-action"
                  @click="approveApply(item)"
                  style="color: #16a34a; cursor: pointer; margin-right: 10px"
                >
                  通过
                </button>
                <button
                  type="button"
                  class="row-action"
                  @click="rejectApply(item)"
                  style="color: #dc2626; cursor: pointer"
                >
                  驳回
                </button>
              </template>
              <span v-else style="color: #94a3b8">已处理</span>
            </td>
          </tr>
        </tbody>
      </table></TableFrame
    >

    <TableFrame title="删除申请" :count="deleteList.length"
      ><table>
        <thead>
          <tr>
            <th>申请时间</th>
            <th>删除内容</th>
            <th>原因</th>
            <th>状态</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in deleteList" :key="'d' + item.id">
            <td>{{ item.created_at }}</td>
            <td>{{ item.record_desc }}</td>
            <td>{{ item.reason }}</td>
            <td>
              <span class="badge" :class="statusClass(item.status)">{{
                statusText(item.status)
              }}</span>
            </td>
            <td>
              <template v-if="item.status === 'pending'">
                <button
                  type="button"
                  class="row-action"
                  @click="approveDel(item)"
                  style="color: #16a34a; cursor: pointer; margin-right: 10px"
                >
                  通过
                </button>
                <button
                  type="button"
                  class="row-action"
                  @click="rejectDel(item)"
                  style="color: #dc2626; cursor: pointer"
                >
                  驳回
                </button>
              </template>
              <span v-else style="color: #94a3b8">{{ item.approver }}</span>
            </td>
          </tr>
        </tbody>
      </table></TableFrame
    >

    <TableFrame title="报废审批" :count="scrapList.length"
      ><table>
        <thead>
          <tr>
            <th>申请号</th>
            <th>设备</th>
            <th>本次数量</th>
            <th>申请人</th>
            <th>原因</th>
            <th>状态</th>
            <th class="actions-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in scrapList" :key="'s' + item.id">
            <td>{{ item.request_number }}</td>
            <td>{{ item.asset_desc }}</td>
            <td>{{ item.quantity ?? 1 }}</td>
            <td>{{ item.applicant || '—' }}</td>
            <td>{{ item.reason || '—' }}</td>
            <td>
              <span class="badge" :class="scrapStatusClass(item.status)">{{
                scrapStatusText(item.status)
              }}</span>
            </td>
            <td>
              <template v-if="item.status === 'pending_approval'">
                <button
                  type="button"
                  class="row-action"
                  @click="approveScrap(item)"
                  style="color: #16a34a; cursor: pointer; margin-right: 10px"
                >
                  通过
                </button>
                <button
                  type="button"
                  class="row-action"
                  @click="rejectScrap(item)"
                  style="color: #dc2626; cursor: pointer"
                >
                  驳回
                </button>
              </template>
              <span v-else style="color: #94a3b8">已处理</span>
            </td>
          </tr>
        </tbody>
      </table></TableFrame
    >
  </div>
</template>
<script setup>
import PageHeading from '../components/PageHeading.vue'
import TableFrame from '../components/TableFrame.vue'
import { ref, onMounted } from 'vue'
import api from '../api'
const deleteList = ref([])
const scrapList = ref([])
const applyList = ref([])

async function load() {
  const [d, s] = await Promise.all([api.get('/delete-request'), api.get('/scrap')])
  // 分离申请和删除
  applyList.value = d.data
    .filter((r) => r.table_name === 'apply_requests')
    .map((r) => {
      return {
        ...r,
        applyType: r.application_type || '旧申请待核对',
        applyUser: r.target_user || r.applicant || '',
        applyDept: r.department || '',
        applyAsset: r.asset_type || '',
      }
    })
  deleteList.value = d.data.filter((r) => r.table_name !== 'apply_requests')
  scrapList.value = s.data
}
async function decide(path) {
  try {
    await api.put(path)
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '审批失败，请刷新后重试')
  }
}
async function approveDel(item) {
  await decide(`/delete-request/${item.id}/approve`)
}
async function rejectDel(item) {
  await decide(`/delete-request/${item.id}/reject`)
}
async function approveScrap(item) {
  await decide(`/scrap/${item.id}/approve`)
}
async function rejectScrap(item) {
  await decide(`/scrap/${item.id}/reject`)
}
async function approveApply(item) {
  await decide(`/delete-request/${item.id}/approve`)
}
async function rejectApply(item) {
  await decide(`/delete-request/${item.id}/reject`)
}

function statusClass(s) {
  return { pending: 'amber', approved: 'green', rejected: 'red' }[s] || 'gray'
}
function statusText(s) {
  return { pending: '待审批', approved: '已通过', rejected: '已驳回' }[s] || s
}
function applyTypeClass(t) {
  return { checkout: 'blue', new_asset: 'green', transfer: 'amber', scrap: 'red' }[t] || 'gray'
}
function applyTypeText(t) {
  return (
    { checkout: '领用申请', new_asset: '新增申请', transfer: '调拨申请', scrap: '报废申请' }[t] || t
  )
}
function scrapStatusClass(s) {
  return (
    { pending_approval: 'amber', approved: 'green', disposed: 'gray', archived: 'gray' }[s] ||
    'gray'
  )
}
function scrapStatusText(s) {
  return (
    { pending_approval: '待审批', approved: '已批准', disposed: '已处置', archived: '已归档' }[s] ||
    s
  )
}
onMounted(load)
</script>
