#!/usr/bin/env node
// Round C1 — PortalShell / three-portal navigation checks (static, offline).
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ROOT = path.resolve(__dirname, '..')
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8')
const CJK = /[\u3400-\u9fff]/
let passed = 0
const test = (name, fn) => { fn(); passed++; console.log(`PASS ${name}`) }

const shell = read('app/components/portal/PortalShell.tsx')
const rail = (name) => {
  const start = shell.indexOf(`export const ${name}`)
  const end = shell.indexOf('];', start)
  return shell.slice(start, end)
}

test('customer rail hides Plan Result / Professional Execution and shows the three growth entries', () => {
  const r = rail('CUSTOMER_RAIL')
  assert.ok(!/label: 'Plan Result'/.test(r))
  assert.ok(!/label: 'Professional Execution'/.test(r))
  for (const label of ['Chat', 'Matters', 'Skills Marketplace', 'Get Licensed', 'Earning Paths']) assert.ok(r.includes(`label: '${label}'`), label)
  assert.ok(r.includes("href: '/agent-loop/customer/skills'"))
  assert.ok(r.includes("href: '/agent-loop/customer/get-licensed'"))
  assert.ok(r.includes("href: '/agent-loop/customer/earning'"))
})

test('brand text follows the portal: AI Butler / AI Agent / AI Admin', () => {
  assert.ok(shell.includes("customer: 'AI Butler'"))
  assert.ok(shell.includes("agent: 'AI Agent'"))
  assert.ok(shell.includes("admin: 'AI Admin'"))
  assert.ok(shell.includes('<span className="goaa-brand-text">{brand}</span>'))
})

test('agent and admin rails exist with their sections', () => {
  const a = rail('AGENT_RAIL'); const d = rail('ADMIN_RAIL')
  for (const l of ['Overview', 'Opportunities', 'Service Orders', 'Knowledge Base', 'My AI']) assert.ok(a.includes(`label: '${l}'`), l)
  for (const l of ['Overview', 'Applications', 'Content', 'Finance', 'System', 'Support']) assert.ok(d.includes(`label: '${l}'`), l)
})

test('PortalShell and the real agent-loop UI never import the preview stylesheet or preview libs', () => {
  const files = ['app/components/portal/PortalShell.tsx', 'app/components/portal/clerk-appearance.ts']
  const walk = (dir) => { for (const e of fs.readdirSync(path.join(ROOT, dir), { withFileTypes: true })) { const p = `${dir}/${e.name}`; if (e.isDirectory()) walk(p); else if (/\.(tsx?|css)$/.test(e.name)) files.push(p) } }
  walk('app/agent-loop'); walk('app/components/agent-loop')
  for (const f of files) {
    const s = read(f)
    assert.ok(!/(from|import)\s+['"][^'"]*portal-preview/.test(s), `${f} imports from portal-preview`)
    assert.ok(!CJK.test(s), `${f} contains CJK`)
  }
})

test('layout loads the goaa token sheets once', () => {
  const l = read('app/layout.tsx')
  assert.ok(l.includes('import "./styles/goaa-tokens.css"'))
  assert.ok(l.includes('import "./styles/goaa-pp-compat.css"'))
})

test('Clerk sign-in uses the approved auth-card appearance', () => {
  const p = read('app/goaa-clerk-login/page.tsx')
  assert.ok(p.includes('appearance={goaaClerkAppearance}'))
  assert.ok(p.includes('style={goaaClerkPageStyle}'))
  assert.ok(!p.includes('#6d5efc'))
})

test('golden customer rail: growth links present, old two entries hidden in butler mode', () => {
  const c = read('app/components/ChatComponent.tsx')
  const start = c.indexOf('<aside className="workspace-rail">'); const end = c.indexOf('</aside>', start)
  const r = c.slice(start, end)
  assert.ok(r.includes('href="/agent-loop/customer/skills"'))
  assert.ok(r.includes('href="/agent-loop/customer/get-licensed"'))
  assert.ok(r.includes('href="/agent-loop/customer/earning"'))
  assert.ok(r.includes("{!butlerMode && <button className={`workspace-nav-item ${viewMode === 'plan' ? 'active' : ''}`}"), 'Plan Result only outside butler mode')
  assert.ok(r.includes("{!butlerMode && <button className={`workspace-nav-item ${viewMode === 'execution' ? 'active' : ''}`}"), 'Professional Execution only outside butler mode')
})

test('token sheets scope to .goaa-portal, never bare .goaa (golden chat avatar uses class "goaa")', () => {
  for (const f of ['app/styles/goaa-tokens.css', 'app/styles/goaa-pp-compat.css']) {
    const css = read(f)
    assert.ok(!/\.goaa[\s{,]/.test(css), `${f} has a bare .goaa selector`)
    assert.ok(!/\.goaa\s*\{/.test(css))
  }
  assert.ok(shell.includes('className="goaa-portal"'))
})

console.log(`\nALL ${passed} PORTAL SHELL TESTS PASSED`)
