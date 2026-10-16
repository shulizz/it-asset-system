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
  const due=[]
  if(limit<=0)return due
  for(const item of assets){
    if(item.status==='scrapped' || item.status==='archived')continue
    const days=daysUntil(item[field])
    if(days===null || days>30)continue
    if(limit===Infinity){due.push({...item,_days:days});continue}
    let position=due.findIndex(existing=>existing._days>days)
    if(position<0)position=due.length
    if(position<limit){due.splice(position,0,{...item,_days:days});if(due.length>limit)due.pop()}
  }
  return limit===Infinity ? due.sort((a,b)=>a._days-b._days) : due
}
