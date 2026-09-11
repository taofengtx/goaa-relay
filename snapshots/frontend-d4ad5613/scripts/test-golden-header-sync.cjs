#!/usr/bin/env node
// Round C1.3 — golden header must notice a business session created in the SAME tab.
// Static, offline: reads source files only.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ROOT = path.resolve(__dirname, '..')
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8')
let passed = 0
const test = (n, f) => { f(); passed++; console.log(`PASS ${n}`) }

const chat = read('app/components/ChatComponent.tsx')
const bridge = read('app/components/GoldenSessionBridge.tsx')

test('ChatComponent listens for the literal the bridge actually dispatches', () => {
  const m = bridge.match(/export const GOLDEN_SESSION_READY_EVENT = '([^']+)'/)
  assert.ok(m, 'bridge exports GOLDEN_SESSION_READY_EVENT')
  assert.equal(m[1], 'goaa:golden-session')
  assert.ok(chat.includes(`window.addEventListener('${m[1]}', syncSessionDisplay)`))
  assert.ok(chat.includes(`window.removeEventListener('${m[1]}', syncSessionDisplay)`))
})
test('listener lives in the existing session-display effect (no new state, no Clerk import)', () => {
  const start = chat.indexOf('const syncSessionDisplay = () => {')
  const end = chat.indexOf('}, [])', start)
  const block = chat.slice(start, end)
  for (const ev of ["'storage', onStorage", "'focus', syncSessionDisplay", "'pageshow', syncSessionDisplay", "'goaa:golden-session', syncSessionDisplay"]) {
    assert.ok(block.includes(`addEventListener(${ev})`), `add ${ev}`)
    assert.ok(block.includes(`removeEventListener(${ev})`), `remove ${ev}`)
  }
  assert.ok(!/from ['"]@clerk\//.test(chat), 'ChatComponent must not import Clerk')
  assert.ok(!/from ['"][^'"]*GoldenSessionBridge['"]/.test(chat), 'no import of the bridge module')
})
console.log(`\nALL ${passed} GOLDEN HEADER SYNC TESTS PASSED`)
