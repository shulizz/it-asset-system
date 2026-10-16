export function daysUntil(value, today = new Date()) {
  if (!value) return null
  const match = String(value).slice(0, 10).match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!match) return null
  const [, year, month, day] = match.map(Number)
  const target = new Date(Date.UTC(year, month - 1, day))
  if (target.getUTCFullYear() !== year || target.getUTCMonth() !== month - 1 || target.getUTCDate() !== day) return null
  return Math.round((target.getTime() - Date.UTC(today.getFullYear(), today.getMonth(), today.getDate())) / 86400000)
}

export function dueMedical(assets, field, limit = Infinity) {
  return assets.filter(item => !['scrapped', 'archived'].includes(item.status))
    .map(item => ({...item, _days: daysUntil(item[field])}))
    .filter(item => item._days !== null && item._days <= 30)
    .sort((a, b) => a._days - b._days).slice(0, limit)
}
