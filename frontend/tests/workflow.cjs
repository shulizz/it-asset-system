const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const { parse } = require('vue/compiler-sfc')
const root = path.join(__dirname, '..', 'src')

function component(file, context, bindings) {
  const descriptor = parse(fs.readFileSync(path.join(root, file), 'utf8')).descriptor
  const code = descriptor.scriptSetup.content.replace(/^import .*$/gm, '')
  const mounted = []
  context = {...context, ref: value => ({value}), computed: fn => ({get value(){return fn()}}), onMounted: fn => mounted.push(fn)}
  vm.createContext(context)
  vm.runInContext(code + `\nglobalThis.state = {${bindings.join(',')}}`, context)
  return {state: context.state, mounted, context}
}

async function main() {
  const rowsModule = await import('data:text/javascript;base64,' + Buffer.from(fs.readFileSync(path.join(root,'applicationRows.js'),'utf8')).toString('base64'))
  const rows = rowsModule.applicationRows([{id:1,table_name:'apply_requests',application_type:'checkout',target_user:'接收人',record_desc:'电脑',created_at:'2026-10-09',department:'甲部门'}],
    [{id:1,request_number:'SC-1',asset_desc:'报废电脑',applicant:'申请人',department:'甲部门',status:'pending_approval',submit_date:'2026-10-08'}])
  assert.equal(new Set(rows.map(row=>row.key)).size,2)
  assert.equal(rows[0].user_name,'接收人')
  assert.equal(rows[1].request_no,'SC-1')
  assert.equal(rows[1].status,'pending')
  assert.equal(rows[1].content,'报废电脑')

  const calls=[], downloads=[]
  const report = component('views/Reports.vue', {
    api: {get: async (url, options) => {
      calls.push(url)
      if(url==='/auth/me') return {data:{permissions:['reports','export'],data_scope:'department'}}
      if(url==='/reports/export') {assert.equal(options.responseType,'blob');return {data: new Blob(['xlsx'])}}
      if(url==='/departments') return {data:[{name:'甲部门'}]}
      return {data:[{asset_number:'IT-1',department:'甲部门',status:'idle'}]}
    }}, URL: {createObjectURL:()=> 'blob:report', revokeObjectURL:()=>{}},
    document: {createElement:()=>({click(){downloads.push(this.download)}})},
    setTimeout: fn=>fn(), alert: message=>{throw Error(message)}
  }, ['total','canExport','deptStats','exportCSV'])
  await report.mounted[0]()
  assert.equal(report.state.total.value.it,1)
  assert.equal(report.state.total.value.wechat,'无权限')
  assert.equal(calls.includes('/wechat'),false)
  assert.equal(report.state.canExport.value,true)
  await report.state.exportCSV()
  assert.equal(downloads.length,1)

  const partial=component('views/Reports.vue', {api:{get:async url=>{
    if(url==='/auth/me') return {data:{permissions:['reports','wechat'],data_scope:'all'}}
    if(url==='/wechat') throw Error('暂时失败')
    if(url==='/departments') return {data:[]}
    return {data:[{status:'idle'}]}
  }}, alert:()=>{}}, ['total','canExport','loadError'])
  await partial.mounted[0]()
  assert.equal(partial.state.total.value.it,1)
  assert.match(partial.state.loadError.value,/微信账号/)
  assert.equal(partial.state.canExport.value,false)

  for(const permissions of [['export'],['assets','export'],['assets','import']]) {
    const buttons=component('components/ImportExportButtons.vue', {
      defineProps:()=>({module:'it'}),api:{get:async()=>({data:{permissions,data_scope:'department'}})}
    }, ['canImport','canExport'])
    await buttons.mounted[0]()
    assert.equal(buttons.state.canExport.value,permissions.includes('assets')&&permissions.includes('export'))
    assert.equal(buttons.state.canImport.value,permissions.includes('assets')&&permissions.includes('import'))
  }
  console.log('Frontend logic checks passed: application mapping, report loading/export, partial failure, permission controls')
}
main().catch(error=>{console.error(error);process.exitCode=1})
