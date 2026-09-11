#!/usr/bin/env node
// Round C1 — LOG OUT wiring through window.__goaaGoldenSession (three outcomes).
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')
const ROOT = path.resolve(__dirname, '..')

function load(rel) {
  const src = fs.readFileSync(path.join(ROOT, rel), 'utf8')
  const out = ts.transpileModule(src, { fileName: rel, reportDiagnostics: true, compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } })
  assert.equal((out.diagnostics || []).filter((d) => d.category === ts.DiagnosticCategory.Error).length, 0)
  const exports = {}; const module = { exports }
  vm.runInNewContext(out.outputText, { exports, module, require: () => { throw new Error('no imports expected') }, console }, { filename: rel })
  return exports
}

let passed = 0
const test = async (name, fn) => { await fn(); passed++; console.log(`PASS ${name}`) }

;(async () => {
  const { decideGoldenSignOut, GOLDEN_SIGN_OUT_FAILED } = load('app/lib/golden-signout.ts')
  const bridge = (result, lastError = null) => ({ __goaaGoldenSession: { session: null, lastError, signOut: async () => result } })

  await test("'ended' -> navigate", async () => { assert.equal((await decideGoldenSignOut(bridge('ended'), '/x')).status, 'navigate') })
  await test("'not-started' -> navigate", async () => { assert.equal((await decideGoldenSignOut(bridge('not-started'), '/x')).status, 'navigate') })
  await test("'failed' -> failed with lastError, no navigation", async () => {
    const r = await decideGoldenSignOut(bridge('failed', 'revoke not confirmed'), '/x')
    assert.equal(r.status, 'failed'); assert.equal(r.message, 'revoke not confirmed')
  })
  await test("'failed' without lastError -> default message", async () => {
    const r = await decideGoldenSignOut(bridge('failed'), '/x')
    assert.equal(r.status, 'failed'); assert.equal(r.message, GOLDEN_SIGN_OUT_FAILED)
  })
  await test('signOut throws -> failed', async () => {
    const r = await decideGoldenSignOut({ __goaaGoldenSession: { session: null, lastError: null, signOut: async () => { throw new Error('boom') } } }, '/x')
    assert.equal(r.status, 'failed')
  })
  await test('bridge absent -> legacy fallback', async () => { assert.equal((await decideGoldenSignOut({}, '/x')).status, 'legacy') })
  await test('redirectUrl is passed through to the bridge', async () => {
    let seen = null
    await decideGoldenSignOut({ __goaaGoldenSession: { session: null, lastError: null, signOut: async (u) => { seen = u; return 'ended' } } }, '/planning?logged_out=1')
    assert.equal(seen, '/planning?logged_out=1')
  })
  await test("ChatComponent: 'failed' returns before clearing local state; error passed to LoginMenu", () => {
    const c = fs.readFileSync(path.join(ROOT, 'app/components/ChatComponent.tsx'), 'utf8')
    const fn = c.slice(c.indexOf('async function handleCustomerSignOut'), c.indexOf('async function submitPrompt'))
    assert.ok(fn.indexOf("outcome.status === 'failed'") < fn.indexOf('clearCustomerSession('), 'failed check precedes clear')
    assert.ok(fn.includes('setSignOutError(outcome.message)') && fn.includes('return'))
    assert.ok(c.includes('error={signOutError}'))
    const m = fs.readFileSync(path.join(ROOT, 'app/components/LoginMenu.tsx'), 'utf8')
    assert.ok(m.includes('data-testid="sign-out-error"'))
  })
  console.log(`\nALL ${passed} SIGNOUT WIRING TESTS PASSED`)
})().catch((e) => { console.error(e); process.exit(1) })
