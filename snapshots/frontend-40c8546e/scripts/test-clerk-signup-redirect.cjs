#!/usr/bin/env node
// Round C1.4 — the sign-up branch of the Clerk card must land on the same
// validated `next` as the sign-in branch (T3: new accounts landed on "/").
// Static, offline: reads source files only.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ROOT = path.resolve(__dirname, '..')
const src = fs.readFileSync(path.join(ROOT, 'app/goaa-clerk-login/page.tsx'), 'utf8')
let passed = 0
const test = (n, f) => { f(); passed++; console.log(`PASS ${n}`) }

test('both branches of the combined card use the validated next', () => {
  assert.ok(src.includes('const next = safeNextTarget(raw)'))
  assert.ok(src.includes('withSignUp'))
  for (const prop of ['forceRedirectUrl', 'fallbackRedirectUrl', 'signUpForceRedirectUrl', 'signUpFallbackRedirectUrl']) {
    assert.ok(new RegExp(`\\b${prop}=\\{next\\}`).test(src), prop)
  }
})
test('no redirect prop takes anything but the validated next', () => {
  const props = [...src.matchAll(/\b(\w*RedirectUrl)=\{([^}]+)\}/g)]
  assert.equal(props.length, 4)
  for (const [, name, value] of props) assert.equal(value, 'next', name)
})
console.log(`\nALL ${passed} CLERK SIGN-UP REDIRECT TESTS PASSED`)
