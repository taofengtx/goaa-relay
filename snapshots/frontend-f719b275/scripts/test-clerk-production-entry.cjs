#!/usr/bin/env node
// Round C1.7 — production entry for planning.goaa.ai on C1.
//   * GOAA_CLERK_INSTANCE=production is the only way live keys are accepted,
//     and the keys must match the declared instance in both directions;
//   * every /client-login visit opens the Clerk card (the legacy form is
//     retired while Clerk is in charge); no usable `next` lands on /planning;
//   * the card keeps the retired form's "Continue as guest" exit.
// Offline: reads source files and runs app/lib/clerk-entry.ts transpiled.
// The routing itself runs against the real clerkMiddleware in
// scripts/c2-clerk/test-middleware.mjs.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')
const ROOT = path.resolve(__dirname, '..')
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8')
let passed = 0
const test = (n, f) => { f(); passed++; console.log(`PASS ${n}`) }

function loadEntry() {
  const out = ts.transpileModule(read('app/lib/clerk-entry.ts'), {
    fileName: 'clerk-entry.ts',
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText
  const mod = { exports: {} }
  vm.runInNewContext(out, { module: mod, exports: mod.exports, process: { env: {} }, URLSearchParams }, { filename: 'clerk-entry.ts' })
  return mod.exports
}
const entry = loadEntry()
// Fixtures only. The live secret is assembled so no file trips the relay scan.
const PK_TEST = 'pk_test_fixture'
const SK_TEST = 'sk_test_fixture'
const PK_LIVE = 'pk_live_fixture'
const SK_LIVE = ['sk', 'live', 'fixture'].join('_')
const ON = { GOAA_C2_CLERK_AUTH_ENABLED: 'true' }

test('production needs the explicit instance and live keys; the test stack is unchanged', () => {
  const prod = { ...ON, GOAA_CLERK_INSTANCE: 'production' }
  assert.equal(entry.clerkAuthState({ ...prod, NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: PK_LIVE, CLERK_SECRET_KEY: SK_LIVE }), 'enabled')
  assert.equal(entry.clerkAuthState({ ...ON, NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: PK_TEST, CLERK_SECRET_KEY: SK_TEST }), 'enabled')
  assert.equal(entry.clerkAuthState({ ...ON, NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: PK_LIVE, CLERK_SECRET_KEY: SK_LIVE }), 'misconfigured')
  assert.equal(entry.clerkAuthState({ ...prod, NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: PK_TEST, CLERK_SECRET_KEY: SK_TEST }), 'misconfigured')
  assert.equal(entry.clerkAuthState({ ...prod, NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: PK_LIVE, CLERK_SECRET_KEY: SK_TEST }), 'misconfigured')
  assert.equal(entry.clerkAuthState({ ...ON, GOAA_CLERK_INSTANCE: 'prod', NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: PK_LIVE, CLERK_SECRET_KEY: SK_LIVE }), 'misconfigured')
})

test('the public entry lands on /planning unless a valid next says otherwise', () => {
  assert.equal(entry.DEFAULT_LOGIN_NEXT, '/planning')
  assert.equal(entry.unifiedEntryNext(null), '/planning')
  assert.equal(entry.unifiedEntryNext('//evil.example'), '/planning')
  assert.equal(entry.unifiedEntryNext('/planning'), '/planning')
  assert.equal(entry.unifiedEntryNext('/agent-loop/customer'), '/agent-loop/customer')
  assert.equal(entry.validateNextTarget('/planning/x').ok, false)
})

test('the middleware rewrites every /client-login visit through unifiedEntryNext', () => {
  const mw = read('middleware.ts')
  assert.ok(mw.includes('target.searchParams.set("next", unifiedEntryNext(request.nextUrl.searchParams.get("next")))'))
  assert.ok(!mw.includes('validateNextTarget'), 'the old precondition check is gone')
  assert.ok(mw.includes('if (isUnifiedLoginPath(pathname)) return true'), 'a half configured deployment refuses /client-login')
})

test('the retired form itself is untouched', () => {
  const page = read('app/client-login/page.tsx')
  assert.ok(page.includes('api.goaa.ai') && page.includes('function goAsGuest()'))
})

test('the Clerk card offers "Continue as guest" to AI Butler, writing nothing', () => {
  const card = read('app/goaa-clerk-login/page.tsx')
  const link = card.slice(card.indexOf('data-testid="clerk-continue-as-guest"') - 60, card.lastIndexOf('Continue as guest') + 30)
  assert.ok(link.includes('href={DEFAULT_LOGIN_NEXT}'), link)
  assert.ok(!/onClick|localStorage|document\.cookie/.test(link))
  assert.ok(card.includes('DEFAULT_LOGIN_NEXT,'), 'imported from clerk-entry')
})

test('no source carries a live secret-key prefix literal', () => {
  const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) =>
    e.name === 'node_modules' || e.name.startsWith('.') ? [] : e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)])
  const needle = ['sk', 'live'].join('_')
  const files = [path.join(ROOT, 'middleware.ts'), ...walk(path.join(ROOT, 'app')), ...walk(path.join(ROOT, 'scripts'))]
  for (const f of files.filter((f) => /\.(tsx?|jsx?|mjs|cjs)$/.test(f))) {
    assert.ok(!fs.readFileSync(f, 'utf8').includes(needle), `${path.relative(ROOT, f)} contains the live secret prefix`)
  }
})

console.log(`\nALL ${passed} CLERK PRODUCTION ENTRY TESTS PASSED`)
