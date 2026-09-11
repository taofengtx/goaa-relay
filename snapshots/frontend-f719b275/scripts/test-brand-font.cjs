#!/usr/bin/env node
// Round C1.3 — brand layer in Outfit on BOTH surfaces; body text keeps the golden stack.
// Static, offline: reads source files only.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ROOT = path.resolve(__dirname, '..')
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8')
let passed = 0
const test = (n, f) => { f(); passed++; console.log(`PASS ${n}`) }

const tokens = read('app/styles/goaa-tokens.css')
const compat = read('app/styles/goaa-pp-compat.css')
const globals = read('app/globals.css')
const lastRule = (css) => css.slice(css.lastIndexOf('*/') + 2)

test('display = Outfit stack, body = the golden planning stack', () => {
  assert.ok(tokens.includes('--goaa-font-display: var(--goaa-font);'))
  const body = tokens.match(/--goaa-font-body: ([^;]+);/)
  assert.ok(body, 'body token')
  assert.ok(globals.includes(`font-family:${body[1].replace(/, /g, ',').replace(/'/g, '"')}`), 'body token equals globals.css body stack')
  assert.ok(tokens.includes('.goaa-portal { background: var(--goaa-bg); color: var(--goaa-text); font-family: var(--goaa-font-body);'))
})
test('golden brand layer: brand, rail, kicker, section titles use the display font', () => {
  const rule = lastRule(tokens)
  for (const sel of ['.goaa-brand,', '.workspace-new,', '.workspace-nav-label,', '.workspace-nav-item,', '.workspace-nav-tag,', '.workspace-kicker,', '.workspace-section-head h2,', '.workspace-plan-head h3,', '.butler-view-heading h2 {']) assert.ok(rule.includes(sel), sel)
  assert.ok(rule.trim().endsWith('{ font-family: var(--goaa-font-display); }'))
})
test('golden body text is NOT switched (chat, composer, plan text, footer)', () => {
  const rule = lastRule(tokens)
  for (const sel of ['.chat-bubble', 'textarea', '.workspace-plan-summary', '.workspace-plan-item', '.goaa-footer', 'body']) assert.ok(!rule.includes(sel), sel)
})
test('portal brand layer, placed after the font:inherit resets', () => {
  const rule = lastRule(tokens)
  for (const sel of ['.goaa-portal .goaa-brand-text', '.goaa-portal .goaa-h1', '.goaa-portal .goaa-h2', '.goaa-portal .goaa-rail-item', '.goaa-portal .goaa-btn']) assert.ok(rule.includes(sel), sel)
  assert.ok(tokens.lastIndexOf('.goaa-portal .goaa-btn {') < tokens.lastIndexOf('.goaa-portal .goaa-btn,'), 'display rule after .goaa-btn reset')
  const pp = compat.slice(compat.lastIndexOf('*/') + 2)
  assert.ok(pp.includes('.goaa-portal .pp-btn') && pp.includes('font-family: var(--goaa-font-display)'))
  assert.ok(compat.indexOf('.goaa-portal .pp-btn {') < compat.lastIndexOf('.goaa-portal .pp-btn,'), 'after .pp-btn reset')
})
test('golden source files untouched by this change', () => {
  assert.ok(!/Outfit/.test(globals), 'globals.css does not name Outfit')
  assert.ok(!/Outfit/.test(read('app/components/butler-workspace.css')))
})
console.log(`\nALL ${passed} BRAND FONT TESTS PASSED`)
