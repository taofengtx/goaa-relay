#!/usr/bin/env node
// Round C1 — customer growth pages: English only, no payment actions, correct links.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ROOT = path.resolve(__dirname, '..')
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8')
const CJK = /[\u3400-\u9fff]/
const PAY = /\b(checkout|pay now|payout|withdraw|buy now|subscribe)\b/i
let passed = 0
const test = (n, f) => { f(); passed++; console.log(`PASS ${n}`) }

const pages = {
  skills: read('app/agent-loop/customer/skills/page.tsx'),
  licensed: read('app/agent-loop/customer/get-licensed/page.tsx'),
  earning: read('app/agent-loop/customer/earning/page.tsx'),
}

test('all three pages are English-only and carry no payment actions', () => {
  for (const [k, s] of Object.entries(pages)) { assert.ok(!CJK.test(s), `${k} CJK`); assert.ok(!PAY.test(s), `${k} payment action`) }
})
test('each page requires a session and mounts the customer portal with the right rail item', () => {
  for (const [k, s] of Object.entries(pages)) {
    assert.ok(s.includes("if (!session) redirect('/agent-loop/login?next=/agent-loop/customer/"), `${k} guard`)
    assert.ok(s.includes('portal="customer"'), `${k} portal`)
  }
  assert.ok(pages.skills.includes('activeId="skills"')); assert.ok(pages.licensed.includes('activeId="licensed"')); assert.ok(pages.earning.includes('activeId="earning"'))
})
test('Skills: partner pending notice, Use this skill seeds the chat', () => {
  assert.ok(pages.skills.includes('data-testid="skills-partner-pending"'))
  // /planning reads ?prompt= (app/planning/page.tsx); ?q= was silently dropped.
  assert.ok(pages.skills.includes('/planning?prompt='))
  assert.ok(!pages.skills.includes('/planning?q='))
})
test('Get Licensed: Learn first disabled, Apply now -> /agent-loop/apply', () => {
  assert.ok(pages.licensed.includes('disabled>Coming soon'))
  assert.ok(pages.licensed.includes('href="/agent-loop/apply"'))
})
test('Earning: membership-fee-only rule stated; referral disabled; agent path links to Get Licensed', () => {
  assert.ok(pages.earning.includes('membership fees only'))
  assert.ok(pages.earning.includes('never to insurance premiums or commissions'))
  assert.ok(pages.earning.includes('disabled>Coming soon'))
  assert.ok(pages.earning.includes('href="/agent-loop/customer/get-licensed"'))
})
test('agent/admin placeholder routes exist so the rails never 404', () => {
  for (const p of ['agent/opportunities', 'agent/orders', 'agent/knowledge', 'agent/my-ai', 'admin/applications', 'admin/content', 'admin/finance', 'admin/system', 'admin/support']) assert.ok(fs.existsSync(path.join(ROOT, `app/agent-loop/${p}/page.tsx`)), p)
})
console.log(`\nALL ${passed} GROWTH PAGE TESTS PASSED`)
