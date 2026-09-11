#!/usr/bin/env node
// Round C1.3c — the root layout reads the Clerk switch at render time, so it must
// never be prerendered (c1-2-diag: /planning froze clerkAuth=false at build time).
// Static, offline: reads source files only.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ROOT = path.resolve(__dirname, '..')
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8')
let passed = 0
const test = (n, f) => { f(); passed++; console.log(`PASS ${n}`) }
const layout = read('app/layout.tsx')

test('root layout opts out of static prerendering', () => {
  assert.ok(/^export const dynamic = ["']force-dynamic["']$/m.test(layout))
})
test('no route re-enables static rendering underneath it', () => {
  const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)])
  for (const f of walk(path.join(ROOT, 'app')).filter((f) => /\.(tsx?|jsx?)$/.test(f))) {
    const s = fs.readFileSync(f, 'utf8')
    assert.ok(!/export const dynamic = ["']force-static["']/.test(s), `${path.relative(ROOT, f)} forces static`)
    assert.ok(!/export (async )?function generateStaticParams/.test(s), `${path.relative(ROOT, f)} generates static params`)
  }
})
test('the Clerk gate and the bridge mount are unchanged', () => {
  assert.ok(/const clerkAuth = clerkState === "enabled" && Boolean\(publishableKey\)/.test(layout))
  assert.ok(layout.includes('<GoldenSessionBridge clerkAuth={clerkAuth} />'))
  assert.ok(layout.indexOf('if (!clerkAuth) return page') < layout.indexOf('<ClerkProvider'))
  assert.ok(!layout.includes('CLERK_SECRET_KEY'))
})
test('golden entry pages stay client components (only rendering mode changes)', () => {
  for (const f of ['app/page.tsx', 'app/planning/page.tsx']) assert.ok(read(f).startsWith("'use client'"), f)
})
console.log(`\nALL ${passed} ROOT LAYOUT DYNAMIC TESTS PASSED`)
