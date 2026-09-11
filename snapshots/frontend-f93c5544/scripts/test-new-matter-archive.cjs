#!/usr/bin/env node
// Round 14/15: "+ New" archives the current planning chat as a numbered matter
// (goaa_personal_agent_matter_history_v1) and starts a fresh conversation.
// Round 15 adds the auto-sync rules: no matter before a session id exists,
// a matter_local_<firstUserHash> row upgrades to matter_<sessionId> on first
// session appearance (number + createdAt kept), numbers are minted only for
// genuinely new rows, archive and sync share one persistence path, and
// duplicate pre-fix rows are cleaned up once.
// Coverage:
//   - user messages present  -> archiveCurrentWorkspace() creates a matter,
//     writes it to history, and clears CURRENT_MATTER_KEY immediately.
//   - no user message        -> returns null, history untouched.
//   - restored matter        -> archive updates that same matter (createdAt
//     kept, updatedAt refreshed, no duplicate row).
//   - numbering              -> missing numbers backfilled once in createdAt
//     order (1..N), next new matter gets max+1 (#8 after 7 backfilled).
//   - ensureMatterNumbers idempotent (second call changes nothing).
//   - sync without session   -> bridge never archives a sessionless chat; an
//     existing same-conversation CURRENT row may still be updated in place.
//   - session first seen     -> local row upgraded to session row, old local
//     removed, number + createdAt preserved.
//   - repeated syncs         -> exactly one row, number never re-minted.
//   - one-time dedupe        -> local row dropped when a session row shares
//     its firstUser hash; lone locals kept; later reads unchanged.
//   - contiguous numbering   -> sequential conversations are 1,2 with no skip.
//   - ChatComponent source   -> workspace-new button routes through
//     handleNewMatter in butler mode and that handler has no new-topic
//     login redirect; resetHome (non-butler) keeps its original shape.
// Offline only: transpiled lib + vm sandbox with a fake window/localStorage.

const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')

const ROOT = path.resolve(__dirname, '..')
const LIB_PATH = path.join(ROOT, 'app/lib/personal-agent-matter.ts')

const LEGACY = 'goaa_planning_workspace_v1'
const CURRENT = 'goaa_personal_agent_current_matter_v1'
const HISTORY = 'goaa_personal_agent_matter_history_v1'

const userThread = [
  { role: 'user', content: '我想规划保险保障' },
  { role: 'assistant', content: '好的，先了解您的家庭情况。' },
  { role: 'user', content: '家里有两个孩子，预算一年三万。' },
]

const baseMatter = (over = {}) => ({
  schemaVersion: 1, id: 'matter_s_old', title: '旧事项', status: 'active',
  source: 'planning_workspace', createdAt: '2026-08-01T00:00:00.000Z',
  updatedAt: '2026-08-01T00:00:00.000Z', sessionId: 's_old', intent: null,
  subIntent: null, stage: '', knownFacts: {}, thread: [{ role: 'user', content: '旧内容' }],
  blueprint: [], ...over,
})

function createStorage(seed = {}) {
  const store = new Map(Object.entries(seed))
  return {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => { store.set(k, String(v)) },
    removeItem: (k) => { store.delete(k) },
    keys: () => [...store.keys()],
  }
}

const libCode = (() => {
  const result = ts.transpileModule(fs.readFileSync(LIB_PATH, 'utf8'), {
    fileName: LIB_PATH, compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  })
  assert.equal((result.diagnostics || []).filter((d) => d.category === ts.DiagnosticCategory.Error).length, 0)
  return result.outputText
})()

// Mirror of lib stableMatterId for fixtures: matter_local_<abs(hash(firstUser))>.
function localHashId(firstUser) {
  let hash = 0
  for (let i = 0; i < firstUser.length; i += 1) hash = ((hash << 5) - hash + firstUser.charCodeAt(i)) | 0
  return `matter_local_${Math.abs(hash)}`
}

function loadLib(ls) {
  const sandbox = { module: { exports: {} }, exports: {}, window: { localStorage: ls }, console }
  vm.runInNewContext(libCode, sandbox, { filename: 'personal-agent-matter.js' })
  return sandbox.exports
}

async function run() {
  let passed = 0
  const test = async (name, fn) => { await fn(); passed += 1; console.log(`PASS ${name}`) }

  await test('user messages present: archive writes a numbered matter, updates the row and clears CURRENT immediately', () => {
    const ls = createStorage({
      [LEGACY]: JSON.stringify({ thread: userThread, sessionId: 's1', displayTitle: '保险保障规划' }),
      [HISTORY]: JSON.stringify([baseMatter({ id: 'matter_s1', sessionId: 's1', createdAt: '2026-08-10T00:00:00.000Z', number: 4 })]),
      [CURRENT]: JSON.stringify(baseMatter({ id: 'matter_s1', sessionId: 's1', createdAt: '2026-08-10T00:00:00.000Z', number: 4 })),
    })
    const lib = loadLib(ls)

    const matter = lib.archiveCurrentWorkspace()
    assert.ok(matter, 'archive returned a matter')
    assert.equal(matter.id, 'matter_s1', 'same session => same stable id')
    assert.equal(matter.number, 4, 'existing matter number preserved (no renumber)')
    const history = lib.readMatterHistory()
    assert.equal(history.length, 1, 'no duplicate row')
    assert.equal(history[0].id, 'matter_s1')
    assert.equal(history[0].createdAt, '2026-08-10T00:00:00.000Z', 'createdAt kept on update')
    assert.ok(Date.parse(history[0].updatedAt) >= Date.parse('2026-09-07T00:00:00.000Z'), 'updatedAt refreshed')
    assert.equal(history[0].thread.length, 3, 'thread updated to the latest chat')
    assert.equal(history[0].title, '保险保障规划', 'title = displayTitle')
    assert.equal(ls.getItem(CURRENT), null, 'CURRENT_MATTER_KEY removed right after archive')
    assert.ok(ls.keys().includes(HISTORY))
  })

  await test('no user message: archive returns null and history is untouched', () => {
    const ls = createStorage({
      [LEGACY]: JSON.stringify({ thread: [], displayTitle: 'GOAA Plan' }),
      [HISTORY]: JSON.stringify([baseMatter({ number: 1 })]),
      [CURRENT]: JSON.stringify(baseMatter({ number: 1 })),
    })
    const lib = loadLib(ls)

    assert.equal(lib.archiveCurrentWorkspace(), null, 'empty thread archives nothing')
    assert.equal(lib.readMatterHistory().length, 1, 'history unchanged')
  })

  await test('restored matter: archiving updates the same row instead of creating a new one', () => {
    const ls = createStorage({
      [LEGACY]: JSON.stringify({ thread: userThread, sessionId: 's_old', displayTitle: '旧事项' }),
      [HISTORY]: JSON.stringify([baseMatter({ number: 2, updatedAt: '2026-08-01T00:00:00.000Z' })]),
      [CURRENT]: JSON.stringify(baseMatter({ number: 2, updatedAt: '2026-08-01T00:00:00.000Z' })),
    })
    const lib = loadLib(ls)

    const matter = lib.archiveCurrentWorkspace()
    const history = lib.readMatterHistory()
    assert.ok(matter, 'archive returned the updated matter')
    assert.equal(history.length, 1, 'update in place, no new row')
    assert.equal(history[0].id, 'matter_s_old')
    assert.equal(history[0].createdAt, '2026-08-01T00:00:00.000Z', 'createdAt kept')
    assert.ok(Date.parse(history[0].updatedAt) > Date.parse('2026-08-01T00:00:00.000Z'), 'updatedAt refreshed')
    assert.equal(history[0].number, 2, 'number unchanged on update')
    assert.equal(ls.getItem(CURRENT), null, 'CURRENT cleared after archiving an update too')
  })

  await test('numbering: backfill 7 unnumbered matters 1..7 once, next archive is #8', () => {
    const older = []
    for (let i = 0; i < 7; i += 1) {
      older.push(baseMatter({
        id: `matter_local_${i}`, sessionId: '', title: `本地事项${i + 1}`,
        createdAt: new Date(Date.UTC(2026, 7, 1 + i)).toISOString(),
        updatedAt: new Date(Date.UTC(2026, 7, 1 + i)).toISOString(),
      }))
    }
    const ls = createStorage({
      [HISTORY]: JSON.stringify(older),
      [LEGACY]: JSON.stringify({ thread: userThread, sessionId: 'new_s', displayTitle: '保险保障规划' }),
    })
    const lib = loadLib(ls)

    const ensured1 = lib.ensureMatterNumbers(lib.readMatterHistory())
    assert.equal(ensured1.length, 7)
    const numbers1 = ensured1.map((m) => m.number).sort((a, b) => a - b)
    assert.equal(JSON.stringify(numbers1), JSON.stringify([1, 2, 3, 4, 5, 6, 7]), 'backfilled in order once')
    assert.equal(ensured1.find((m) => m.id === 'matter_local_0').number, 1, 'oldest unnumbered matter gets #1')

    const matter = lib.archiveCurrentWorkspace()
    assert.equal(matter.number, 8, 'next new matter gets #8 after backfill')
    const history = lib.readMatterHistory()
    assert.equal(history.filter((m) => m.id === 'matter_new_s').length, 1)
    assert.equal(history.find((m) => m.id === 'matter_new_s').number, 8)
    assert.equal(history.find((m) => m.id === 'matter_local_0').number, 1, 'existing numbers unchanged')
  })

  await test('ensureMatterNumbers second call changes nothing (never renumbers)', () => {
    const ls = createStorage({
      [HISTORY]: JSON.stringify([baseMatter({ number: 7 }), baseMatter({ id: 'm2', number: 3 })]),
    })
    const lib = loadLib(ls)

    const before = lib.readMatterHistory().map((m) => m.number)
    const after = lib.ensureMatterNumbers(lib.readMatterHistory()).map((m) => m.number)
    assert.equal(JSON.stringify(after), JSON.stringify(before), 'idempotent, no renumber')
    assert.equal(JSON.stringify([...after].sort()), JSON.stringify([3, 7]))
  })

  await test('sync without session creates nothing; same-conversation CURRENT is still updated', () => {
    const ls = createStorage({
      [LEGACY]: JSON.stringify({ thread: [{ role: 'user', content: 'AAA' }] }),
    })
    const lib = loadLib(ls)
    assert.equal(lib.syncLegacyWorkspaceToCurrentMatter(), null, 'no session => no new matter from bridge sync')
    assert.equal(lib.readMatterHistory().length, 0, 'history untouched')
    assert.equal(ls.getItem(CURRENT), null, 'CURRENT untouched')

    const ls2 = createStorage({
      [HISTORY]: JSON.stringify([baseMatter({ id: localHashId('AAA'), number: 2, sessionId: '', createdAt: '2026-08-01T00:00:00.000Z', thread: [{ role: 'user', content: 'AAA' }] })]),
      [CURRENT]: JSON.stringify(baseMatter({ id: localHashId('AAA'), number: 2, sessionId: '', createdAt: '2026-08-01T00:00:00.000Z', thread: [{ role: 'user', content: 'AAA' }] })),
      [LEGACY]: JSON.stringify({ thread: [{ role: 'user', content: 'AAA' }, { role: 'assistant', content: '答' }] }),
    })
    const lib2 = loadLib(ls2)
    const matter = lib2.syncLegacyWorkspaceToCurrentMatter()
    assert.ok(matter, 'same-conversation CURRENT may still be updated')
    const h = lib2.readMatterHistory()
    assert.equal(h.length, 1, 'no new row for a sessionless update')
    assert.equal(h[0].id, localHashId('AAA'))
    assert.equal(h[0].number, 2, 'number preserved on sessionless update')
    assert.equal(h[0].createdAt, '2026-08-01T00:00:00.000Z', 'createdAt preserved on sessionless update')
    assert.equal(h[0].thread.length, 2, 'thread updated')
    assert.equal(matter.number, 2, 'CURRENT written with the stored row')
  })

  await test('session first appearance upgrades matter_local_ to matter_<sessionId> keeping number+createdAt', () => {
    const ls = createStorage({
      [LEGACY]: JSON.stringify({ thread: userThread }),
    })
    const first = loadLib(ls)
    // Simulate the pre-Round-15 guest archive: no session, archive allowed -> local row.
    const local = first.archiveCurrentWorkspace()
    assert.ok(local && local.id.startsWith('matter_local_'), 'archive created the local row')
    const localCreated = local.createdAt
    assert.equal(ls.getItem(CURRENT), null, 'archive clears CURRENT')
    assert.equal(first.readMatterHistory().length, 1)

    // Session id arrives on the next sync of the same conversation.
    ls.setItem(LEGACY, JSON.stringify({ thread: userThread, sessionId: 's_up' }))
    const lib = loadLib(ls)
    const upgraded = lib.syncLegacyWorkspaceToCurrentMatter()
    const history = lib.readMatterHistory()
    assert.ok(upgraded, 'sync upgraded the local row to the session row')
    assert.equal(history.length, 1, 'old local row removed')
    assert.equal(history[0].id, 'matter_s_up', 'row id upgraded to session id')
    assert.equal(history[0].sessionId, 's_up')
    assert.equal(history[0].number, local.number, 'number kept through the upgrade')
    assert.equal(history[0].createdAt, localCreated, 'createdAt kept through the upgrade')
    assert.equal(history[0].thread.length, userThread.length, 'latest thread stored')
    assert.equal(JSON.parse(ls.getItem(CURRENT)).number, local.number, 'CURRENT written with the upgraded stored row')
  })

  await test('repeated bridge syncs are stable: one row, number never re-minted', () => {
    const ls = createStorage({
      [LEGACY]: JSON.stringify({ thread: userThread, sessionId: 's_rep' }),
    })
    const lib = loadLib(ls)
    lib.archiveCurrentWorkspace()
    let numbers = []
    for (let i = 0; i < 3; i += 1) {
      const synced = lib.syncLegacyWorkspaceToCurrentMatter()
      assert.ok(synced, `sync ${i} returned the row`)
      const h = lib.readMatterHistory()
      assert.equal(h.length, 1, `sync ${i}: still exactly one row`)
      numbers.push(h[0].number)
    }
    assert.equal(JSON.stringify(numbers), JSON.stringify([1, 1, 1]), 'number stays 1 across repeated syncs')
  })

  await test('one-time dedupe: local row dropped when a session row shares its firstUser hash; lone locals kept', () => {
    const localA = baseMatter({ id: localHashId('AAA'), number: 1, sessionId: '', thread: [{ role: 'user', content: 'AAA' }], createdAt: '2026-07-01T00:00:00.000Z' })
    const sessionA = baseMatter({ id: 'matter_sss', number: 2, sessionId: 'sss', thread: [{ role: 'user', content: 'AAA' }, { role: 'assistant', content: '答' }], createdAt: '2026-08-01T00:00:00.000Z' })
    const localB = baseMatter({ id: localHashId('BBB'), number: 3, sessionId: '', thread: [{ role: 'user', content: 'BBB' }], createdAt: '2026-08-05T00:00:00.000Z' })
    const ls = createStorage({
      [HISTORY]: JSON.stringify([localA, sessionA, localB]),
    })
    const lib = loadLib(ls)

    const firstRead = lib.readMatterHistory()
    assert.equal(firstRead.length, 2, 'duplicate localA cleaned on first read')
    assert.ok(!firstRead.some((m) => m.id === localHashId('AAA')), 'localA removed')
    assert.ok(firstRead.some((m) => m.id === 'matter_sss'), 'session row kept')
    assert.ok(firstRead.some((m) => m.id === localHashId('BBB')), 'lone local row without session kept')
    assert.equal(ls.getItem('goaa_personal_agent_matter_dedupe_v1'), '1', 'dedupe flag set after cleanup')
    const secondRead = lib.readMatterHistory()
    assert.equal(JSON.stringify(secondRead.map((m) => m.id).sort()), JSON.stringify(['matter_sss', localHashId('BBB')].sort()), 'later reads unchanged')
    const persisted = JSON.parse(ls.getItem(HISTORY))
    assert.equal(persisted.length, 2, 'cleanup persisted to history storage')
  })

  await test('two sequential conversations number contiguously (1,2) with no skip from sessionless ticks', () => {
    const ls = createStorage({})
    const lib = loadLib(ls)
    assert.equal(lib.syncLegacyWorkspaceToCurrentMatter(), null, 'empty workspace sync is null')
    assert.equal(lib.readMatterHistory().length, 0)

    ls.setItem(LEGACY, JSON.stringify({ thread: [{ role: 'user', content: 'AAA' }] }))
    assert.equal(lib.syncLegacyWorkspaceToCurrentMatter(), null, 'sessionless first message creates nothing')
    assert.equal(lib.readMatterHistory().length, 0)

    ls.setItem(LEGACY, JSON.stringify({ thread: [{ role: 'user', content: 'AAA' }, { role: 'assistant', content: '答1' }, { role: 'user', content: '追问1' }], sessionId: 's1' }))
    assert.equal(lib.syncLegacyWorkspaceToCurrentMatter().number, 1, 'first session row gets #1')
    ls.setItem(LEGACY, JSON.stringify({ thread: [{ role: 'user', content: 'AAA' }, { role: 'assistant', content: '答1' }, { role: 'user', content: '追问1' }, { role: 'assistant', content: '答2' }], sessionId: 's1' }))
    assert.equal(lib.syncLegacyWorkspaceToCurrentMatter().number, 1, 'same conversation keeps #1')
    assert.equal(lib.readMatterHistory().length, 1)

    ls.setItem(LEGACY, JSON.stringify({ thread: [{ role: 'user', content: 'BBB' }, { role: 'assistant', content: '答' }], sessionId: 's2' }))
    assert.equal(lib.syncLegacyWorkspaceToCurrentMatter().number, 2, 'second conversation gets #2')
    const nums = lib.readMatterHistory().map((m) => m.number).sort((a, b) => a - b)
    assert.equal(JSON.stringify(nums), JSON.stringify([1, 2]), 'numbers contiguous, no gaps')
  })

  await test('ChatComponent: + New routes through handleNewMatter in butler mode; no new-topic redirect inside', () => {
    const src = fs.readFileSync(path.join(ROOT, 'app/components/ChatComponent.tsx'), 'utf8')
    assert.ok(src.includes('onClick={butlerMode ? handleNewMatter : resetHome}'), 'workspace-new uses handleNewMatter in butler mode')
    const handler = src.slice(src.indexOf('function handleNewMatter'), src.indexOf('function resetHome'))
    assert.ok(handler.includes('archiveCurrentWorkspace()'), 'handler archives first')
    assert.ok(handler.includes('removeItem(WORKSPACE_STORAGE_KEY)'), 'handler clears the saved workspace')
    assert.ok(handler.includes("setDisplayTitle('GOAA Plan')"), 'handler resets display title')
    assert.ok(handler.includes('setThread([])'), 'handler clears the thread')
    assert.ok(!handler.includes('sendToLogin'), 'no login redirect in butler + New')
    const reset = src.slice(src.indexOf('function resetHome'))
    assert.ok(reset.includes("sendToLogin('new-topic')"), 'non-butler resetHome keeps its original login branch')
  })

  await test('ButlerMattersView card title shows #number only for matter rows', () => {
    const src = fs.readFileSync(path.join(ROOT, 'app/components/ButlerMattersView.tsx'), 'utf8')
    assert.ok(src.includes('`#${row.matter.number} ${row.title}`'), 'matter card heading prefixed with #number')
    assert.ok(src.includes("row.matter && typeof row.matter.number === 'number'"), 'prefix only when matter row carries a number')
  })

  if (passed === 0) throw new Error('no tests ran')
  console.log(`\nOK ${passed}/${passed} new-matter-archive tests passed.`)
}

run().catch((err) => { console.error(err); process.exit(1) })
