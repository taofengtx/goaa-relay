#!/usr/bin/env node
// Round C1.2 — fixes found on the signed-in C2 screenshots (2026-09-11).
// Static, offline: reads source files only. No browser, no network, no API.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ROOT = path.resolve(__dirname, '..')
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8')
let passed = 0
const test = (n, f) => { f(); passed++; console.log(`PASS ${n}`) }

const shell = read('app/components/portal/PortalShell.tsx')
const chat = read('app/components/ChatComponent.tsx')
const planning = read('app/planning/page.tsx')
const tokens = read('app/styles/goaa-tokens.css')
const compat = read('app/styles/goaa-pp-compat.css')

test('growth entry is called "Earning Paths" in both rails and on its page', () => {
  assert.ok(shell.includes("{ id: 'earning', label: 'Earning Paths', href: '/agent-loop/customer/earning', isNew: true }"))
  const r = chat.slice(chat.indexOf('<aside className="workspace-rail">'), chat.indexOf('</aside>', chat.indexOf('<aside className="workspace-rail">')))
  assert.ok(r.includes('href="/agent-loop/customer/earning">Earning Paths <span className="workspace-nav-tag">NEW</span></a>'))
  assert.ok(!r.includes('Earning Opportunities'))
  assert.ok(!shell.includes("label: 'Earning Opportunities'"))
  assert.ok(read('app/agent-loop/customer/earning/page.tsx').includes('eyebrow="Earning Paths"'))
})

test('Skills "Use this skill" uses the query key /planning actually reads', () => {
  assert.ok(planning.includes("searchParams.get('prompt')"))
  const skills = read('app/agent-loop/customer/skills/page.tsx')
  assert.ok(skills.includes('`/planning?prompt=${encodeURIComponent('))
})

test('rail "Matters" deep link is consumed by the butler workspace, then removed from the URL', () => {
  assert.ok(shell.includes("{ id: 'matters', label: 'Matters', href: '/planning?view=matters' }"))
  const i = chat.indexOf("url.searchParams.get('view') !== 'matters'")
  assert.ok(i > 0, 'ChatComponent reads ?view=matters')
  const block = chat.slice(chat.lastIndexOf('useEffect(() => {', i), chat.indexOf('}, [butlerMode])', i) + 16)
  assert.ok(block.includes("if (!butlerMode || typeof window === 'undefined') return"), 'butler mode only, SSR safe')
  assert.ok(block.includes("setViewMode('matters')"))
  assert.ok(block.includes("url.searchParams.delete('view')"))
  assert.ok(block.includes('window.history.replaceState('))
  assert.ok(!/catch\s*\{\s*\}/.test(block), 'no silent catch (rule #28)')
  // No new state hook: the effect reuses the existing viewMode state.
  assert.equal((chat.match(/const \[viewMode, setViewMode\] = useState/g) || []).length, 1)
})

test('status pills never break onto two lines', () => {
  assert.ok(/\.goaa-portal \.goaa-pill \{[^}]*white-space: nowrap;[^}]*flex-shrink: 0;/.test(tokens))
  assert.ok(compat.includes('.goaa-portal .pp-status { white-space: nowrap; flex-shrink: 0; }'))
})

test('Outfit is self-hosted: @font-face points at public/fonts, no font CDN', () => {
  const face = tokens.slice(tokens.indexOf('@font-face'), tokens.indexOf('}', tokens.indexOf('@font-face')))
  assert.ok(face.includes("font-family: 'Outfit'"))
  assert.ok(face.includes("url('/fonts/outfit/outfit-latin-wght-normal.woff2')"))
  assert.ok(face.includes('font-display: swap'))
  assert.ok(face.includes('font-weight: 100 900'))
  assert.ok(tokens.indexOf('@font-face') < tokens.indexOf(':root {'), '@font-face before tokens')
  for (const f of ['app/styles/goaa-tokens.css', 'app/styles/goaa-pp-compat.css', 'app/layout.tsx']) {
    assert.ok(!/fonts\.(googleapis|gstatic)\.com/.test(read(f)), `${f} must not call a font CDN`)
  }
  assert.ok(tokens.includes('--goaa-font: Outfit, Inter,'))
})

test('both Get Licensed entries keep their apply buttons (intentional: licensed agents apply from home)', () => {
  const panel = read('app/components/agent-loop/CustomerPanel.tsx')
  assert.ok(panel.includes('data-testid="become-an-agent" href="/agent-loop/apply"'))
  assert.ok(read('app/agent-loop/customer/get-licensed/page.tsx').includes('data-testid="apply-now" href="/agent-loop/apply"'))
})

console.log(`\nALL ${passed} ROUND C1.2 TESTS PASSED`)
