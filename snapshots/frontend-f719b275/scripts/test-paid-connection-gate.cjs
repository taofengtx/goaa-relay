#!/usr/bin/env node
// Launch switch for the $39.90 connection (Tao, 2026-09-11): closed at launch,
// "coming soon" + 30-minute booking instead; reopened later by env, no rebuild.
// Offline: transpiles the real files; no browser, no network, no payment.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')
const ROOT = path.resolve(__dirname, '..')
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8')
const tx = (src, name) => ts.transpileModule(src, { fileName: name, compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: false } }).outputText
const jsx = { jsx: (type, props) => ({ type, props }), jsxs: (type, props) => ({ type, props }), Fragment: 'Fragment' }
function load(file, modules, env = {}) {
  const exp = {}
  vm.runInNewContext(tx(read(file), path.basename(file)), { exports: exp, module: { exports: exp }, process: { env }, console,
    require: (id) => { assert.ok(id in modules, `unexpected import ${id} in ${file}`); return modules[id] } })
  return exp
}
const walk = (n, pred, out = []) => { if (!n || typeof n !== 'object') return out; if (Array.isArray(n)) { n.forEach((c) => walk(c, pred, out)); return out } if (pred(n)) out.push(n); walk(n.props && n.props.children, pred, out); return out }
let passed = 0
const test = (n, f) => { f(); passed++; console.log(`PASS ${n}`) }

const lib = load('app/lib/paid-connection.ts', {})
const libFor = (env) => { const l = load('app/lib/paid-connection.ts', {}, env); return l }

test('switch: only GOAA_PAID_CONNECTION=open opens; unset and anything else stay closed', () => {
  assert.equal(lib.PAID_CONNECTION_SWITCH, 'GOAA_PAID_CONNECTION')
  assert.equal(lib.paidConnectionOpen({}), false)
  assert.equal(lib.paidConnectionOpen({ GOAA_PAID_CONNECTION: 'open' }), true)
  assert.equal(lib.paidConnectionOpen({ GOAA_PAID_CONNECTION: ' OPEN ' }), true)
  for (const v of ['', 'true', '1', 'yes', 'opened', 'closed']) assert.equal(lib.paidConnectionOpen({ GOAA_PAID_CONNECTION: v }), false, v)
  assert.ok(!read('app/lib/paid-connection.ts').includes('NEXT_PUBLIC_'), 'runtime server switch, never inlined at build')
})
test('root layout stamps <html data-goaa-paid> from the runtime switch', () => {
  const l = read('app/layout.tsx')
  assert.ok(l.includes('import { paidConnectionOpen } from "./lib/paid-connection"'))
  assert.ok(l.includes('<html lang="en" data-goaa-paid={paidConnectionOpen() ? "open" : "closed"}>'))
  assert.ok(/^export const dynamic = ["']force-dynamic["']$/m.test(l), 'layout stays dynamic so the stamp is per request')
})
test('CSS: closed twin hidden by default; closed hides open-only and shows the twin', () => {
  const css = read('app/styles/goaa-tokens.css')
  assert.ok(css.includes('.goaa-paid-closed { display: none; }'))
  assert.ok(css.includes('html[data-goaa-paid="closed"] .goaa-paid-open-only { display: none !important; }'))
  assert.ok(css.includes('html[data-goaa-paid="closed"] .goaa-paid-closed { display: block; }'))
})
test('handoff card: paid button + fee copy are open-only; closed twin links to the booking', () => {
  const card = load('app/components/ProfessionalHandoffCard.tsx', { 'react/jsx-runtime': jsx }).default
  assert.ok(read('app/components/ProfessionalHandoffCard.tsx').includes(`const BOOKING_URL = '${lib.BOOKING_URL}'`), 'card booking URL matches lib')
  for (const lang of ['en', 'zh']) {
    const tree = card({ lang, facts: {}, onConnect() {}, onContinue() {} })
    const paid = walk(tree, (n) => n.type === 'button' && /\bhandoff-primary\b/.test(n.props.className))
    assert.equal(paid.length, 1); assert.ok(paid[0].props.className.includes('goaa-paid-open-only'))
    const support = walk(tree, (n) => n.type === 'p' && /\bhandoff-support\b/.test(n.props.className))
    assert.ok(support[0].props.className.includes('goaa-paid-open-only'))
    const twin = walk(tree, (n) => n.props && n.props.className === 'goaa-paid-closed')
    assert.equal(twin.length, 1)
    const a = walk(twin[0], (n) => n.type === 'a')[0]
    assert.equal(a.props.href, lib.BOOKING_URL); assert.equal(a.props.target, '_blank'); assert.equal(a.props.rel, 'noopener noreferrer')
    const text = JSON.stringify(twin[0])
    assert.ok(lang === 'en' ? text.includes('opening soon') && text.includes('never charges') : text.includes('即将开放') && text.includes('不会触发平台扣款'))
    assert.ok(!text.includes('$39.90'), 'closed copy does not sell the fee')
    assert.equal(walk(tree, (n) => n.type === 'button' && n.props.className === 'handoff-secondary').length, 1, 'Continue with AI stays')
  }
})
test('top bar and matter connect: paid entry is open-only; matter has a booking twin', () => {
  assert.ok(read('app/components/ProfessionalConnectBar.tsx').includes('className="goaa-professional-connect goaa-paid-open-only"'))
  const m = read('app/components/MatterProfessionalConnect.tsx')
  assert.ok(m.includes('className="goaa-paid-closed" data-testid="matter-paid-closed"'))
  assert.ok(m.includes('<div className="goaa-paid-open-only" style={{ marginTop: 10, border'))
  assert.ok(m.includes("import { BOOKING_URL } from '../lib/paid-connection'"))
})
test('/connect-pass: closed renders a notice and never mounts the checkout page; open passes through', () => {
  const mods = (env) => ({ 'react/jsx-runtime': jsx, '../lib/paid-connection': libFor(env) })
  const closed = load('app/connect-pass/layout.tsx', mods({}), {}).default({ children: 'CHECKOUT' })
  assert.ok(!JSON.stringify(closed).includes('CHECKOUT'), 'children not rendered')
  assert.equal(closed.props['data-testid'], 'connect-pass-closed')
  const links = walk(closed, (n) => n.type === 'a').map((n) => n.props.href)
  assert.deepEqual(links, [lib.BOOKING_URL, '/planning'])
  const open = load('app/connect-pass/layout.tsx', mods({ GOAA_PAID_CONNECTION: 'open' }), { GOAA_PAID_CONNECTION: 'open' }).default({ children: 'CHECKOUT' })
  assert.ok(JSON.stringify(open).includes('CHECKOUT'))
  assert.ok(/^export const dynamic = ["']force-dynamic["']$/m.test(read('app/connect-pass/layout.tsx')))
})
test('the checkout page and the protected purchase handlers are untouched', () => {
  const page = read('app/connect-pass/page.tsx')
  assert.ok(!page.includes('paid-connection'), 'page.tsx not edited')
  assert.ok(!read('app/components/ChatComponent.tsx').includes('paid-connection'), 'ChatComponent purchase path not edited')
})
console.log(`\nALL ${passed} PAID CONNECTION GATE TESTS PASSED`)
