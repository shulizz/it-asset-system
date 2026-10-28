const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const vue = require('vue')
const { parse } = require('vue/compiler-sfc')
const root = path.join(__dirname, '..', 'src')

async function main() {
  const { hasFireAccess } = await import(
    'data:text/javascript;base64,' +
      Buffer.from(fs.readFileSync(path.join(root, 'fireAccess.js'), 'utf8')).toString('base64')
  )
  assert.equal(
    hasFireAccess({ role: '消防管理员', data_scope: 'all', permissions: ['fire'] }),
    true,
  )
  assert.equal(hasFireAccess({ role: '消防管理员', data_scope: 'all', permissions: [] }), false)
  assert.equal(
    hasFireAccess({ role: '消防管理员', data_scope: 'department', permissions: ['fire'] }),
    false,
  )
  const { hasMedicalAccess } = await import(
    'data:text/javascript;base64,' +
      Buffer.from(fs.readFileSync(path.join(root, 'medicalAccess.js'), 'utf8')).toString('base64')
  )
  assert.equal(hasMedicalAccess({ role: 'super_admin' }), true)
  assert.equal(hasMedicalAccess({ role: '管理员', department: '商务通', department_id: 1 }), false)
  assert.equal(
    hasMedicalAccess({ department: '护理部', department_id: 2, medical_access: true }),
    true,
  )
  assert.equal(
    hasMedicalAccess({ department: '医院', department_id: 3, medical_access: true }),
    true,
  )
  assert.equal(
    hasMedicalAccess({ department: '改名后的医院', department_id: 3, medical_access: true }),
    true,
  )
  assert.equal(
    hasMedicalAccess({ department: '医院', department_id: 3, medical_access: false }),
    false,
  )
  assert.equal(hasMedicalAccess({ department: '医院' }), false)
  const storage = new Map([['token', 'first-session']])
  const localStorage = {
    getItem: (key) => storage.get(key) || null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: (key) => storage.delete(key),
  }
  const pending = []
  const context = {
    ...vue,
    localStorage,
    api: { get: () => new Promise((resolve) => pending.push(resolve)) },
    Promise,
  }
  vm.createContext(context)
  const source = fs
    .readFileSync(path.join(root, 'userState.js'), 'utf8')
    .replace(/^import .*$/gm, '')
    .replace(/^export /gm, '')
  vm.runInContext(
    source + '\nglobalThis.store={currentUser,setCurrentUser,clearSession,refreshCurrentUser}',
    context,
  )
  const store = context.store
  store.setCurrentUser({
    role: 'super_admin',
    permissions: ['assets', 'assets_write'],
    data_scope: 'all',
  })
  const dashboard = {
    ...vue,
    ...store,
    hasMedicalAccess,
    localStorage,
    onMounted: () => {},
    api: {},
    dueMedical: () => [],
  }
  vm.createContext(dashboard)
  const script = parse(
    fs.readFileSync(path.join(root, 'views/Dashboard.vue'), 'utf8'),
  ).descriptor.scriptSetup.content.replace(/^import .*$/gm, '')
  vm.runInContext(script + '\nglobalThis.view={canSeeMedical,canSendEmail}', dashboard)
  assert.equal(dashboard.view.canSendEmail.value, true)
  store.setCurrentUser({ permissions: [], data_scope: 'department' })
  assert.equal(
    dashboard.view.canSendEmail.value,
    false,
    'Revocation must update the open dashboard',
  )
  assert.equal(dashboard.view.canSeeMedical.value, false)
  const a = store.refreshCurrentUser(),
    b = store.refreshCurrentUser()
  assert.equal(pending.length, 1, 'Concurrent consumers must share one request')
  pending.shift()({ data: { role: 'super_admin', permissions: ['assets'] } })
  await Promise.all([a, b])
  assert.equal(dashboard.view.canSeeMedical.value, true)
  const stale = store.refreshCurrentUser()
  store.clearSession()
  pending.shift()({ data: { permissions: ['assets_write'], data_scope: 'all' } })
  await stale
  assert.equal(
    dashboard.view.canSeeMedical.value,
    false,
    'Late response must not restore a logged-out user',
  )
  assert.equal(localStorage.getItem('user'), null)
  console.log('Shared permissions checks passed: live revocation, deduplication, logout race')
}
main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
