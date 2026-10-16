const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const { parse } = require('vue/compiler-sfc')
const root = path.join(__dirname, '..', 'src')

function component(file, context, bindings) {
  const code = parse(
    fs.readFileSync(path.join(root, file), 'utf8'),
  ).descriptor.scriptSetup.content.replace(/^import .*$/gm, '')
  const mounted = [],
    unmounted = []
  Object.assign(context, {
    ref: (value) => ({ value }),
    computed: (fn) => ({
      get value() {
        return fn()
      },
    }),
    onMounted: (fn) => mounted.push(fn),
    onUnmounted: (fn) => unmounted.push(fn),
  })
  context.currentUser = { value: { permissions: [] } }
  context.refreshCurrentUser = (signal) => context.api.get('/auth/me', { signal })
  context.clearSession = () => {}
  vm.createContext(context)
  vm.runInContext(code + `\nglobalThis.state={${bindings}}`, context)
  return { state: context.state, mounted, unmounted }
}

async function main() {
  const { daysUntil, dueMedical } = await import(
    'data:text/javascript;base64,' +
      Buffer.from(fs.readFileSync(path.join(root, 'medicalDates.js'), 'utf8')).toString('base64')
  )
  const today = new Date()
  const assets = Array.from({ length: 5000 }, (_, id) => {
    const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() + (id % 100) - 50)
    return {
      id,
      status: ['in_use', 'idle', 'archived', 'scrapped'][id % 4],
      calibration_expiry:
        id % 17 === 0
          ? 'invalid'
          : `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`,
    }
  })
  const reference = assets
    .filter((a) => !['scrapped', 'archived'].includes(a.status))
    .map((a) => ({ ...a, _days: daysUntil(a.calibration_expiry) }))
    .filter((a) => a._days !== null && a._days <= 30)
    .sort((a, b) => a._days - b._days)
  for (const limit of [0, 1, 10, Infinity])
    assert.deepEqual(dueMedical(assets, 'calibration_expiry', limit), reference.slice(0, limit))
  assert.ok(assets.every((a) => !('_days' in a)))

  const pending = [],
    calls = []
  const fixtures = {
    '/assets/it': [{ status: 'in_use' }],
    '/assets/phone': [{ status: 'idle' }],
    '/assets/medical': assets,
    '/delete-request': Array.from({ length: 7 }, (_, id) => ({ id, status: 'pending' })),
    '/scrap': Array.from({ length: 8 }, (_, id) => ({ id, status: 'pending_approval' })),
  }
  const dashboard = component(
    'views/Dashboard.vue',
    {
      api: {
        get: (url) => {
          calls.push(url)
          return new Promise((resolve, reject) =>
            pending.push(() =>
              url === '/wechat'
                ? reject(Error('simulated failure'))
                : resolve({ data: fixtures[url] || [] }),
            ),
          )
        },
      },
      localStorage: { getItem: () => '{"permissions":[]}' },
      dueMedical,
      setTimeout: () => {},
    },
    'stats,pendingList,pendingCount,calibrationList,expiringList',
  )
  const loading = dashboard.mounted[0]()
  assert.equal(calls.length, 9, 'All dashboard requests must start before waiting for any response')
  pending.forEach((resolve) => resolve())
  await loading
  assert.equal(dashboard.state.stats.value.total, 5002)
  assert.equal(dashboard.state.pendingCount.value, 15)
  assert.equal(dashboard.state.pendingList.value.length, 10)
  assert.deepEqual(
    JSON.parse(JSON.stringify(dashboard.state.calibrationList.value)),
    reference.slice(0, 10),
  )

  let finish,
    requests = 0,
    tick,
    visible,
    removed = false,
    cleared = false,
    signal
  const document = {
    hidden: false,
    addEventListener: (_, fn) => (visible = fn),
    removeEventListener: (_, fn) => (removed = fn === visible),
  }
  const layout = component(
    'views/Layout.vue',
    {
      api: {
        get: (_, options) => {
          requests++
          signal = options.signal
          return new Promise((resolve) => (finish = () => resolve({ data: { permissions: [] } })))
        },
      },
      document,
      AbortController,
      localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
      useRoute: () => ({ path: '/dashboard' }),
      useRouter: () => ({ push: () => {} }),
      setInterval: (fn) => {
        tick = fn
        return 1
      },
      clearInterval: () => (cleared = true),
    },
    'refreshUser',
  )
  layout.mounted[0]()
  tick()
  visible()
  assert.equal(requests, 1, 'Slow auth requests must not overlap')
  finish()
  await new Promise((resolve) => setImmediate(resolve))
  document.hidden = true
  tick()
  visible()
  assert.equal(requests, 1)
  document.hidden = false
  visible()
  assert.equal(requests, 2)
  layout.unmounted[0]()
  assert.ok(signal.aborted && removed && cleared)
  finish()
  console.log(
    'Performance regression checks passed: bounded medical lists, parallel dashboard with partial failure, auth polling overlap/visibility/cleanup',
  )
}
main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
