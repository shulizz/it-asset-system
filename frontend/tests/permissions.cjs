const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const vue = require('vue')
const { parse } = require('vue/compiler-sfc')
const root = path.join(__dirname, '..', 'src')

async function main() {
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
  store.setCurrentUser({ permissions: ['assets', 'assets_write'], data_scope: 'all' })
  const dashboard = {
    ...vue,
    ...store,
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
  pending.shift()({ data: { permissions: ['assets'] } })
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
