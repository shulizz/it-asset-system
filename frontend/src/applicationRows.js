export function applicationRows(requests, scraps) {
  return [
    ...requests.filter(r => r.table_name === 'apply_requests').map(r => ({
      key: `apply-${r.id}`, request_no: `AP-${r.id}`, type: r.application_type || '设备申请',
      content: r.record_desc, user_name: r.target_user || r.applicant,
      department: r.department || '', status: r.status, created_at: r.created_at
    })),
    ...scraps.map(r => ({
      key: `scrap-${r.id}`, request_no: r.request_number, type: 'scrap',
      content: r.asset_desc, user_name: r.applicant, department: r.department,
      status: r.status === 'pending_approval' ? 'pending' : r.status, created_at: r.submit_date
    }))
  ].sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
}
