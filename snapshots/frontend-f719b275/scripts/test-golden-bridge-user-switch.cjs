#!/usr/bin/env node
// Round C1.5 — GoldenSessionBridge must start a business session for every
// Clerk user that signs in within one tab, including after a sign-out that
// did not remount the layout (Clerk's signOut navigates inside the app).
// Renders the real component with hook doubles; no browser, no network.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')
const ROOT = path.resolve(__dirname, '..')
const source = fs.readFileSync(path.join(ROOT, 'app/components/GoldenSessionBridge.tsx'), 'utf8')
const js = ts.transpileModule(source, { fileName: 'GoldenSessionBridge.tsx', compilerOptions: {
  module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: false,
} }).outputText

let passed = 0
const test = async (n, f) => { await f(); passed++; console.log(`PASS ${n}`) }

function harness() {
  // Minimal hook runtime: refs persist by call index, effects re-run when deps change.
  const refs = []; const effects = []; let i = 0; let e = 0
  const react = {
    useRef: (v) => { const k = i++; if (!(k in refs)) refs[k] = { current: v }; return refs[k] },
    useEffect: (fn, deps) => {
      const k = e++; const prev = effects[k]
      const changed = !prev || !deps || deps.length !== prev.deps.length || deps.some((d, j) => d !== prev.deps[j])
      if (!changed) return
      if (prev && typeof prev.cleanup === 'function') prev.cleanup()
      effects[k] = { deps, cleanup: fn() }
    },
  }
  let auth = { isLoaded: true, isSignedIn: false, userId: null }
  const calls = { start: [], credentials: [], revoke: 0 }
  const storage = () => { const m = new Map(); return { getItem: (k) => m.has(k) ? m.get(k) : null, setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) } }
  const win = { localStorage: storage(), sessionStorage: storage(), addEventListener() {}, removeEventListener() {}, dispatchEvent() {} }
  const golden = {
    startBusinessSession: async (_f, opts) => {
      calls.start.push(auth.userId); calls.credentials.push(opts.credential)
      win.localStorage.setItem('client_token', 'tok-' + auth.userId)
      return { state: 'live', session: { user_id: 'biz-' + auth.userId, role: 'customer' }, created: true }
    },
    revokeBusinessSession: async () => { calls.revoke++ },
    bootstrapBusinessSession: async () => ({}), endBusinessSession: async () => ({ status: 'ended' }),
    readGoldenCredential: (st) => st.getItem('client_token'), clearGoldenCredential: (st) => st.removeItem('client_token'), readMarker: () => null, writeMarker: () => {}, clearMarker: () => {},
    GOLDEN_SESSION_UNAVAILABLE: 'unavailable',
  }
  const modules = {
    react, 'react/jsx-runtime': { jsx: (type, props) => ({ type, props }), jsxs: (type, props) => ({ type, props }) },
    '@clerk/nextjs': { useAuth: () => auth },
    '@/app/lib/agent-loop/signout': { SIGN_OUT_FAILED_MESSAGE: 'f', SIGN_OUT_LOADING_MESSAGE: 'l', clerkSignOutOf: () => null },
    '@/app/lib/golden-session': golden,
  }
  const exp = {}
  vm.runInNewContext(js, { exports: exp, module: { exports: exp }, require: (id) => { assert.ok(id in modules, `unexpected import ${id}`); return modules[id] }, window: win, CustomEvent: class { constructor(n, o) { this.type = n; this.detail = o && o.detail } }, console })
  const el = exp.default({ clerkAuth: true })
  const render = async (next) => { auth = { ...auth, ...next }; i = 0; e = 0; el.type(); await new Promise((r) => setImmediate(r)) }
  return { render, calls }
}

;(async () => {
  await test('first sign-in starts one session', async () => {
    const h = harness()
    await h.render({ isSignedIn: true, userId: 'user_A' })
    await h.render({})
    assert.deepEqual(h.calls.start, ['user_A'])
  })
  await test('sign-out then another user in the same tab starts a new session', async () => {
    const h = harness()
    await h.render({ isSignedIn: true, userId: 'user_A' })
    await h.render({ isSignedIn: false, userId: null })
    await h.render({ isSignedIn: true, userId: 'user_B' })
    assert.deepEqual(h.calls.start, ['user_A', 'user_B'])
  })
  await test('sign-out then the SAME user again starts a new session', async () => {
    const h = harness()
    await h.render({ isSignedIn: true, userId: 'user_A' })
    await h.render({ isSignedIn: false, userId: null })
    await h.render({ isSignedIn: true, userId: 'user_A' })
    assert.deepEqual(h.calls.start, ['user_A', 'user_A'])
  })
  await test('re-renders without a user change never rotate the session', async () => {
    const h = harness()
    await h.render({ isSignedIn: true, userId: 'user_A' })
    for (let k = 0; k < 5; k++) await h.render({})
    assert.equal(h.calls.start.length, 1)
  })
  await test('a direct switch from one user to another (no signed-out render) starts for the new user', async () => {
    const h = harness()
    await h.render({ isSignedIn: true, userId: 'user_A' })
    await h.render({ isSignedIn: true, userId: 'user_B' })
    assert.deepEqual(h.calls.start, ['user_A', 'user_B'])
    assert.equal(h.calls.credentials[1], null, "user_A's stored credential must not be resumed for user_B")
  })
  console.log(`\nALL ${passed} GOLDEN BRIDGE USER-SWITCH TESTS PASSED`)
})().catch((err) => { console.error(err); process.exit(1) })
