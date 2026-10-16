// The print document is isolated from the application layout and uses no remote resources.
export const scrapStatusText = (status) =>
  ({
    pending_approval: '待审批',
    approved: '已批准',
    rejected: '已驳回',
    disposed: '已处置',
    archived: '已归档',
  })[status] ||
  status ||
  ''

const escape = (value) =>
  String(value ?? '').replace(
    /[&<>"']/g,
    (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char],
  )
const typeText = (type) =>
  ({ it: 'IT设备', phone: '手机设备', medical: '医疗设备', number: '电话号码' })[type] || ''

export function buildScrapPrintDocument(record, extra = {}) {
  const item = record || {}
  const field = (value) => `<span class="value">${escape(value)}</span>`
  const approval = record
    ? `系统审批：${escape(scrapStatusText(item.status))}　审批人：${escape(item.auditor || '—')}　审批日期：${escape(item.approve_date || '—')}`
    : '系统审批：________________　审批人：________________　审批日期：________________'
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>固定资产报废申请单</title><style>
    @page { size: A5 portrait; margin: 8mm; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: white; color: #111; }
    body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 11px; line-height: 1.5; }
    .sheet { width: 132mm; margin: 0 auto; }
    h1 { margin: 0 0 4mm; text-align: center; font-size: 21px; letter-spacing: 2px; }
    .meta { display: flex; justify-content: space-between; gap: 3mm; margin-bottom: 2mm; min-height: 6mm; }
    .meta span { overflow-wrap: anywhere; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { border: 1px solid #222; padding: 2mm; vertical-align: middle; overflow-wrap: anywhere; font-weight: normal; }
    th { text-align: center; background: #f5f5f5; }
    .value { white-space: pre-wrap; }
    .reason { height: 23mm; vertical-align: top; }
    .opinion { height: 21mm; vertical-align: top; }
    .signature { display: block; text-align: right; margin-top: 7mm; white-space: pre; }
    .system { padding: 2mm 0; border-bottom: 1px solid #222; overflow-wrap: anywhere; font-size: 10px; }
    .foot { margin: 2mm 0 0; color: #444; font-size: 9px; }
    @media screen { body { padding: 8mm; background: #edf1f5; } .sheet { background: white; padding: 8mm; width: 148mm; min-height: 210mm; box-shadow: 0 2px 12px #0001; } }
    @media print { .sheet { margin: 0; } tr { break-inside: avoid; } h1 { break-after: avoid; } }
  </style></head><body><main class="sheet">
    <h1>固定资产报废申请单</h1>
    <div class="meta"><span>单位：${field(extra.organization)}</span><span>申请日期：${field(item.submit_date)}</span></div>
    <table aria-label="固定资产报废申请单">
      <colgroup><col style="width:20%"><col style="width:30%"><col style="width:20%"><col style="width:30%"></colgroup>
      <tbody>
        <tr><th>申请编号</th><td colspan="3">${field(item.request_number)}</td></tr>
        <tr><th>申请部门</th><td>${field(item.department)}</td><th>申请人</th><td>${field(item.applicant)}</td></tr>
        <tr><th>设备名称及编号</th><td colspan="3">${field(item.asset_desc)}</td></tr>
        <tr><th>设备类型</th><td>${field(typeText(item.asset_type))}</td><th>规格型号</th><td>${field(extra.model)}</td></tr>
        <tr><th>购置日期</th><td>${field(extra.purchaseDate)}</td><th>原值（元）</th><td>${field(extra.originalValue)}</td></tr>
        <tr><th>保管 / 使用人</th><td>${field(extra.custodian)}</td><th>数量</th><td>${field(extra.quantity)}</td></tr>
        <tr><th>报废原因</th><td colspan="3" class="reason">${field(record ? item.reason : extra.reason)}</td></tr>
        <tr><th>技术鉴定意见</th><td colspan="3" class="opinion"><span class="signature">鉴定人：____________　日期：____________</span></td></tr>
        <tr><th>部门意见</th><td colspan="3" class="opinion"><span class="signature">负责人：____________　日期：____________</span></td></tr>
        <tr><th>审批意见</th><td colspan="3" class="opinion"><span class="signature">审批人：____________　日期：____________</span></td></tr>
        <tr><th>备注</th><td colspan="3">${field(extra.notes || item.notes)}</td></tr>
      </tbody>
    </table>
    <div class="system">${approval}</div>
    <p class="foot">纸质签字用于留档；系统报废状态以线上审批记录为准。</p>
  </main></body></html>`
}
