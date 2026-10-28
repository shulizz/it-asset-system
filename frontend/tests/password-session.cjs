const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const vue = require('vue')
const { parse } = require('vue/compiler-sfc')
const root = path.join(__dirname, '..', 'src')

async function scenario(phase, status, switchSession, unmount = false) {
  const storage = new Map([['token', 'token-A']])
  const localStorage = {
    getItem: (key) => storage.get(key) || null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: (key) => storage.delete(key),
  }
  const store = { ...vue, localStorage, api: {} }
  vm.createContext(store)
  vm.runInContext(
    fs
      .readFileSync(path.join(root, 'userState.js'), 'utf8')
      .replace(/^import .*$/gm, '')
      .replace(/^export /gm, '') +
      '\nglobalThis.state={currentUser,setCurrentUser,clearSession,captureSession}',
    store,
  )
  store.state.setCurrentUser({ id: 1, username: 'A' })
  let resolve, reject, dispose
  const redirects = []
  const context = {
    ...vue,
    ...store.state,
    TextEncoder,
    api: {
      post: () =>
        new Promise((yes, no) => {
          resolve = yes
          reject = no
        }),
    },
    useRouter: () => ({ replace: async (target) => redirects.push(target) }),
    onBeforeUnmount: (callback) => {
      dispose = callback
    },
  }
  vm.createContext(context)
  vm.runInContext(
    parse(
      fs.readFileSync(path.join(root, 'views/AccountPassword.vue'), 'utf8'),
    ).descriptor.scriptSetup.content.replace(/^import .*$/gm, '') +
      '\nglobalThis.view={verify,save,currentPassword,newPassword,confirmPassword,verified,error}',
    context,
  )
  const view = context.view
  view.currentPassword.value = 'old-password-123'
  view.newPassword.value = view.confirmPassword.value = 'new-password-123'
  const request = view[phase]()
  // Periodic identity refresh within the same login must not invalidate the operation.
  store.state.setCurrentUser({ id: 1, username: 'A', permissions: [] })
  if (unmount) dispose()
  if (switchSession) {
    store.state.clearSession()
    localStorage.setItem('token', 'token-B')
    store.state.setCurrentUser({ id: 2, username: 'B' })
  }
  if (status === 200) resolve({ data: {} })
  else reject({ response: { status, data: { detail: 'expired' } } })
  await request
  if (switchSession || unmount) {
    assert.equal(localStorage.getItem('token'), switchSession ? 'token-B' : 'token-A')
    assert.equal(redirects.length, 0, 'Old component must not navigate the new session')
    assert.equal(view.verified.value, false)
    assert.equal(view.error.value, '')
  } else {
    assert.equal(localStorage.getItem('token'), null, 'Own password change must log out')
    assert.equal(redirects.length, 1)
  }
}
;(async () => {
  for (const phase of ['verify', 'save']) {
    for (const status of [200, 401, 409]) {
      await scenario(phase, status, true)
      await scenario(phase, status, false, true)
    }
  }
  await scenario('save', 200, false)
  console.log('Password session checks passed: delayed success/errors, unmount, own-session logout')
})().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
