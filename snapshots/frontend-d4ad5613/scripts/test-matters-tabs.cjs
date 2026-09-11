#!/usr/bin/env node
// Round 16: Butler Matters view becomes a five-tab filter
// (All / In Conversation / Organizing / Connecting / Completed).
// Category rules (blueprint first for matter rows, order stage for rows
// with an order):
//   - Rows with an order follow the order stage: anything not confirmed
//     completed is Connecting; stage completed is Completed.
//   - Matter-only rows follow the first non-completed blueprint step:
//     01 -> conversation; 02/03 -> organizing; 04/05 -> connecting;
//     empty blueprint -> conversation; fully completed blueprint counts as
//     05 (connecting); a completed matter without an order is Completed.
// The four categories partition all rows: their counts always sum to All.
// Coverage:
//   - sample rows stop at every blueprint step (01..05, all done, empty).
//   - completed matter without an order -> Completed (new branch).
//   - order rows: estimate/processing/delivered/completed + pure rows.
//   - linked order id that cannot be resolved -> Connecting / Order sync pending.
//   - every row falls into exactly one category and 4 categories sum to All.
//   - badge texts, tab labels, buttons, headings are all English.
//   - neither the view component nor the lib contains CJK.
// Offline only: transpiled lib + vm sandbox; static source checks.

const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')

const ROOT = path.resolve(__dirname, '..')
const LIB_PATH = path.join(ROOT, 'app/lib/butler-matter-view.ts')
const VIEW_PATH = path.join(ROOT, 'app/components/ButlerMattersView.tsx')
const CJK = /[\u3400-\u9fff]/

const now = '2026-09-07T00:00:00.000Z'
const baseMatter = (over = {}) => {
  const { bp, ...rest } = over
  return {
    schemaVersion: 1, id: 'm1', title: 'Sample matter', status: 'active',
    source: 'planning_workspace', createdAt: now, updatedAt: now,
    sessionId: '', intent: null, subIntent: null, stage: '', knownFacts: {},
    thread: [{ role: 'user', content: 'sample' }], blueprint: bp || [], ...rest,
  }
}
const step = (id, status = 'active') => ({ id, title: `Step ${id}`, status })
const done = (id) => step(id, 'completed')
const order = (id, stage) => ({ id, serviceTitle: `Service ${id}`, amount: 100, stage, updatedAt: now })
const bp = (list) => ({ blueprint: list })

const libCode = (() => {
  const result = ts.transpileModule(fs.readFileSync(LIB_PATH, 'utf8'), {
    fileName: LIB_PATH, compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  })
  assert.equal((result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error).length, 0)
  return result.outputText
})()

function loadLib() {
  const sandbox = { module: { exports: {} }, exports: {}, console }
  vm.runInNewContext(libCode, sandbox, { filename: 'butler-matter-view.js' })
  return sandbox.exports
}

async function run() {
  let passed = 0
  const test = async (name, fn) => { await fn(); passed += 1; console.log(`PASS ${name}`) }

  const matters = [
    baseMatter({ id: 'm01', bp: [done(1), step(2)] }), // first non-completed = 02 -> organizing
    baseMatter({ id: 'm02', bp: [step(1)] }), // 01 -> conversation
    baseMatter({ id: 'm03', bp: [done(1), done(2), step(3)] }), // 03 -> organizing
    baseMatter({ id: 'm04', bp: [done(1), done(2), done(3), step(4)] }), // 04 -> connecting
    baseMatter({ id: 'm05', bp: [done(1), done(2), done(3), done(4), step(5)] }), // 05 -> connecting
    baseMatter({ id: 'm06', bp: [done(1), done(2), done(3), done(4), done(5)] }), // all done -> connecting (05)
    baseMatter({ id: 'm07', bp: [] }), // empty -> conversation
    baseMatter({ id: 'm08', status: 'completed', bp: [done(1), done(2), done(3), done(4), done(5)] }), // completed matter -> completed
    baseMatter({ id: 'm09', knownFacts: { service_order_id: 'ord_proc' }, bp: [done(1), done(2), step(3)] }), // order overrides blueprint
    baseMatter({ id: 'm10', knownFacts: { service_order_id: 'ord_done' }, bp: [done(1), done(2), step(3)] }), // completed order
    baseMatter({ id: 'm11', knownFacts: { service_order_id: 'ord_missing' }, bp: [step(1)] }), // unresolved link
  ]
  const orders = [
    order('ord_proc', 'processing'),
    order('ord_done', 'completed'),
    order('ord_est', 'estimate'), // pure order row
    order('ord_del', 'delivered'), // pure order row
  ]
  const lib = loadLib()
  const rows = lib.buildButlerMatterRows(matters, orders)

  await test('every row lands in exactly one of the four categories; counts sum to All', () => {
    assert.equal(rows.length, matters.length + 2, 'all matter rows + 2 pure order rows')
    const counts = { conversation: 0, organizing: 0, connecting: 0, completed: 0 }
    for (const row of rows) {
      assert.ok(['conversation', 'organizing', 'connecting', 'completed'].includes(row.category), `row ${row.id} has one category`)
      counts[row.category] += 1
    }
    assert.equal(counts.conversation + counts.organizing + counts.connecting + counts.completed, rows.length, 'four categories sum to All')
    assert.deepEqual(counts, { conversation: 2, organizing: 2, connecting: 7, completed: 2 }, 'expected counts for the fixed sample')
  })

  await test('blueprint stops map to categories (01 conv / 02-03 org / 04-05 conn / all done conn / empty conv)', () => {
    const byId = Object.fromEntries(rows.map(row => [row.id, row]))
    assert.equal(byId.m01.category, 'organizing')
    assert.equal(byId.m02.category, 'conversation')
    assert.equal(byId.m03.category, 'organizing')
    assert.equal(byId.m04.category, 'connecting')
    assert.equal(byId.m05.category, 'connecting')
    assert.equal(byId.m06.category, 'connecting', 'fully completed blueprint counts as step 05')
    assert.equal(byId.m07.category, 'conversation', 'empty blueprint stays in conversation')
    assert.equal(byId.m08.category, 'completed', 'completed matter without order is Completed')
  })

  await test('order stage rules: non-completed stages are Connecting; completed order is Completed; unresolved link is Connecting', () => {
    const byId = Object.fromEntries(rows.map(row => [row.id, row]))
    assert.equal(byId.m09.category, 'connecting', 'processing order overrides blueprint step 03')
    assert.equal(byId.m09.status, 'Service in progress')
    assert.equal(byId.m10.category, 'completed', 'completed order lands in Completed')
    assert.equal(byId.m10.status, 'Completed')
    assert.equal(byId.m11.category, 'connecting', 'unresolved service_order_id stays Connecting')
    assert.equal(byId.m11.status, 'Order sync pending')
    assert.equal(byId['order:ord_est'].category, 'connecting')
    assert.equal(byId['order:ord_est'].status, 'Quote pending')
    assert.equal(byId['order:ord_del'].category, 'connecting')
    assert.equal(byId['order:ord_del'].status, 'Delivered, awaiting review')
  })

  await test('matter-only badge text is the English category label; group derives from category', () => {
    const byId = Object.fromEntries(rows.map(row => [row.id, row]))
    assert.equal(byId.m02.status, 'In conversation')
    assert.equal(byId.m01.status, 'Organizing')
    assert.equal(byId.m04.status, 'Connecting')
    assert.equal(byId.m08.status, 'Completed')
    assert.equal(byId.m08.group, 'completed')
    assert.equal(byId.m04.group, 'active')
    assert.equal(byId.m10.group, 'completed', 'group = completed for completed category')
  })

  await test('ButlerMattersView renders five tabs with counts, All defaults, and category filter', () => {
    const src = fs.readFileSync(VIEW_PATH, 'utf8')
    for (const label of ['All', 'In Conversation', 'Organizing', 'Connecting', 'Completed']) assert.ok(src.includes(`'${label}'`) || src.includes(`"${label}"`), `tab label ${label} present`)
    assert.ok(src.includes("useState<MatterFilter>('all')"), 'default filter is All')
    assert.ok(src.includes("const visible = filter === 'all' ? rows : rows.filter(item => item.category === filter)"), 'visible filters by category when not All')
    assert.ok(src.includes('counts[row.category] += 1'), 'counts derived from the same rows')
    assert.ok(src.includes('aria-pressed={filter === tab.key}'), 'tabs toggle aria-pressed')
    assert.ok(!CJK.test(src), 'view component contains no CJK')
  })

  await test('card buttons, headings, notices, meta and empty states are English', () => {
    const src = fs.readFileSync(VIEW_PATH, 'utf8')
    for (const text of [
      'MY MATTERS', '>Matters</h2>', 'Check progress, continue the conversation, or review',
      'Refresh', 'Continue with Butler', 'View details', 'View results', 'View invoice',
      'Local planning record', 'Professional service order',
      'Showing local planning records.', 'Sign in', 'No completed matters yet', 'No matters in this stage',
    ]) assert.ok(src.includes(text), `expected text present: ${text}`)
    for (const gone of ['进行中', '已完成', '管家整理中', '查看进度', '查看结果与交付', '继续与管家沟通', '本机规划记录', '专业服务订单', '查看进展', '刷新']) assert.ok(!src.includes(gone), `old Chinese copy removed: ${gone}`)
  })

  await test('lib contains no CJK and keeps row fields for the card', () => {
    const src = fs.readFileSync(LIB_PATH, 'utf8')
    assert.ok(!CJK.test(src), 'lib contains no CJK')
    assert.ok(src.includes('category'), 'row exposes category')
    assert.ok(src.includes("linkedOrderId: 'connecting'") || src.includes("'connecting'"), 'unresolved link category present')
  })

  if (passed === 0) throw new Error('no tests ran')
  console.log(`\nOK ${passed}/${passed} matters-tabs tests passed.`)
}

run().catch(err => { console.error(err); process.exit(1) })
