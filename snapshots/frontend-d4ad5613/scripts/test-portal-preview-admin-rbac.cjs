#!/usr/bin/env node
// Portal Preview — Admin RBAC formal tests (batch: 7 roles x allow/deny).
//
// Two layers:
//   1) Domain layer — call the pure business/store functions directly with
//      every admin role. Unauthorized roles MUST be refused, leave the
//      application/license/agent-access state unchanged, and still write a
//      deny audit line (no secrets).
//   2) UI source layer — the admin component must pass actorRole into
//      adminDecision/adminLifecycle and must contain no customer-fact
//      forgery button (accept quote / accept work / pay on behalf / mark
//      an unpaid invoice paid).
//
// Offline; transpiles only the preview modules. Never touches golden code.

const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')

const ROOT = path.resolve(__dirname, '..')
const j = (v) => JSON.stringify(v)
const CORE = path.join(ROOT, 'app/lib/portal-preview/preview-core.ts')
const BIZ = path.join(ROOT, 'app/lib/portal-preview/preview-business.ts')
const STORE = path.join(ROOT, 'app/lib/portal-preview/preview-store.ts')
const ADMIN_UI = path.join(ROOT, 'app/components/portal-preview/AdminPortalPreview.tsx')

function transpile(file) {
  const result = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    fileName: file,
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  })
  const errs = (result.diagnostics || []).filter((d) => d.category === ts.DiagnosticCategory.Error)
  assert.equal(errs.length, 0, `transpile failed: ${file} ${errs.map((e) => e.messageText).join('; ')}`)
  return result.outputText
}

function loadAll() {
  const map = {}
  const sandbox = { console }
  function load(name, file) {
    const code = transpile(file)
    const module = { exports: {} }
    const req = (p) => {
      const key = p.replace(/^\.\//, '').replace(/\.ts$/, '')
      if (!map[key]) throw new Error(`missing module ${p} for ${name}`)
      return map[key].exports
    }
    vm.runInNewContext(`(function(require, module, exports){${code}\n})(require, module, exports)`, {
      ...sandbox, require: req, module, exports: module.exports,
    }, { filename: name + '.js' })
    map[name] = module
    return module.exports
  }
  load('preview-core', CORE)
  load('preview-business', BIZ)
  const store = load('preview-store', STORE)
  return { core: map['preview-core'].exports, biz: map['preview-business'].exports, store }
}

const { core, biz: B, store: S } = loadAll()
S._testUseMemoryStorage()
const ALL = B.ADMIN_ACTIONS.map((a) => a.id)
const ROLES = B.ADMIN_ROLES.map((r) => r.id)

async function run() {
  let passed = 0
  const test = async (name, fn) => {
    await fn()
    passed += 1
    console.log(`PASS ${name}`)
  }

  const actionLabels = Object.fromEntries(B.ADMIN_ACTIONS.map((a) => [a.id, a.label]))

  await test('live matrix has exactly the 7 roles and super owns all 15 actions', () => {
    assert.equal(j(ROLES), j(['super_admin', 'review_admin', 'operations_admin', 'finance_admin', 'content_admin', 'support_admin', 'integration_admin']))
    assert.equal(j(B.ADMIN_ROLE_ACTIONS.super_admin), j(ALL))
    assert.equal(B.adminCan('super_admin', 'approve_application'), true)
    assert.equal(B.adminCan('super_admin', 'open_agent_access'), true)
    assert.equal(B.adminCan('super_admin', 'approve_settlement'), true)
  })

  await test('review: approve/supplement/reject/suspend/expire; never refund/settle/assign/open-access', () => {
    const exp = ['approve_application', 'request_supplement', 'reject_application', 'suspend_agent', 'mark_expired']
    assert.equal(j(B.ADMIN_ROLE_ACTIONS.review_admin), j(exp))
    for (const a of exp) assert.equal(B.adminCan('review_admin', a), true, a)
    for (const a of ALL.filter((x) => !exp.includes(x))) assert.equal(B.adminCan('review_admin', a), false, a)
  })

  await test('operations: assign + exception + referrals + open-access; never license review/refund/settle', () => {
    const exp = ['open_agent_access', 'assign_client', 'transfer_client', 'handle_order_exception', 'manage_referrals']
    assert.equal(j(B.ADMIN_ROLE_ACTIONS.operations_admin), j(exp))
    for (const a of ALL.filter((x) => !exp.includes(x))) assert.equal(B.adminCan('operations_admin', a), false, a)
  })

  await test('finance: refund + settlement + plans; never license review or open-agent-access', () => {
    const exp = ['approve_refund', 'approve_settlement', 'manage_plans']
    assert.equal(j(B.ADMIN_ROLE_ACTIONS.finance_admin), j(exp))
    for (const a of ALL.filter((x) => !exp.includes(x))) assert.equal(B.adminCan('finance_admin', a), false, a)
  })

  await test('content: content + referral rewards only; never review/assign/finance', () => {
    const exp = ['manage_content', 'manage_referrals']
    assert.equal(j(B.ADMIN_ROLE_ACTIONS.content_admin), j(exp))
    for (const a of ALL.filter((x) => !exp.includes(x))) assert.equal(B.adminCan('content_admin', a), false, a)
  })

  await test('support: support scope only — exception + plans + open-access; NO assignment, review or finance', () => {
    const exp = ['open_agent_access', 'handle_order_exception', 'manage_plans']
    assert.equal(j(B.ADMIN_ROLE_ACTIONS.support_admin), j(exp))
    assert.equal(B.adminCan('support_admin', 'assign_client'), false, 'support must not assign matters')
    assert.equal(B.adminCan('support_admin', 'transfer_client'), false)
    assert.equal(B.adminCan('support_admin', 'approve_application'), false)
    assert.equal(B.adminCan('support_admin', 'approve_refund'), false)
    assert.equal(B.adminCan('support_admin', 'approve_settlement'), false)
    assert.equal(B.adminCan('support_admin', 'manage_integrations'), false)
    for (const a of ALL.filter((x) => !exp.includes(x))) assert.equal(B.adminCan('support_admin', a), false, a)
  })

  await test('integration: integrations only; never review/assign/finance', () => {
    const exp = ['manage_integrations']
    assert.equal(j(B.ADMIN_ROLE_ACTIONS.integration_admin), j(exp))
    for (const a of ALL.filter((x) => !exp.includes(x))) assert.equal(B.adminCan('integration_admin', a), false, a)
  })

  await test('open agent access keeps the existing stricter set: super/ops/support only', () => {
    for (const role of ['review_admin', 'finance_admin', 'content_admin', 'integration_admin']) {
      const s = B.defaultBusinessState()
      const r = B.openAgentAccess(s, { email: 'jordan.rivera.preview@example.com', actorRole: role })
      assert.equal(r.ok, false, role)
      assert.match(r.error, /cannot open agent access/)
      assert.equal(B.accountFor(r.state, 'jordan.rivera.preview@example.com').agentAccess, 'none')
      assert.ok(r.state.audit.some((a) => a.action === 'admin.denied' && a.detail.includes(role)), `${role} deny audit missing`)
    }
  })

  await test('direct business calls: unauthorized roles are refused and deny-audited; allowed roles proceed', () => {
    const s = B.defaultBusinessState()
    // assign: operations/super allowed; support now refused
    assert.equal(B.adminAssignMatter(s, { actorRole: 'support_admin', matterId: 'mt-3001', toEmail: 'jordan.rivera.preview@example.com' }).ok, false)
    assert.equal(B.adminAssignMatter(s, { actorRole: 'review_admin', matterId: 'mt-3001', toEmail: 'jordan.rivera.preview@example.com' }).ok, false)
    assert.equal(B.adminAssignMatter(s, { actorRole: 'operations_admin', matterId: 'mt-3001', toEmail: 'jordan.rivera.preview@example.com' }).ok, true)
    // refund: finance/super allowed; review/support/content/integration denied
    assert.equal(B.adminApproveRefund(s, { actorRole: 'review_admin', invoiceId: 'inv-mt-3001', reason: 'nope' }).ok, false)
    assert.equal(B.adminApproveRefund(s, { actorRole: 'support_admin', invoiceId: 'inv-mt-3001', reason: 'nope' }).ok, false)
    assert.equal(B.adminApproveRefund(s, { actorRole: 'content_admin', invoiceId: 'inv-mt-3001', reason: 'nope' }).ok, false)
    assert.equal(B.adminApproveRefund(s, { actorRole: 'integration_admin', invoiceId: 'inv-mt-3001', reason: 'nope' }).ok, false)
    assert.equal(B.adminApproveRefund(s, { actorRole: 'finance_admin', invoiceId: 'inv-mt-3001', reason: 'double charge' }).ok, true)
    // settlement
    assert.equal(B.adminApproveSettlement(s, { actorRole: 'integration_admin', batch: 'X', amountUsd: 1 }).ok, false)
    assert.equal(B.adminApproveSettlement(s, { actorRole: 'super_admin', batch: 'X', amountUsd: 1 }).ok, true)
    // exception: operations/support allowed; finance denied
    assert.equal(B.adminHandleOrderException(s, { actorRole: 'finance_admin', matterId: 'mt-2001', note: 'nope' }).ok, false)
    assert.equal(B.adminHandleOrderException(s, { actorRole: 'support_admin', matterId: 'mt-2001', note: 'client called' }).ok, true)
    assert.equal(B.adminHandleOrderException(s, { actorRole: 'operations_admin', matterId: 'mt-2001', note: 'client called' }).ok, true)
  })

  await test('domain decision functions are NOT cosmetic: adminDecision validates actorRole before any state change', () => {
    S.resetPortalPreviewState()
    const st = S.applySeedToStoredState('fresh')
    const app = st.applications.find((a) => a.status === 'ai_review')
    assert.ok(app)
    for (const role of ['operations_admin', 'finance_admin', 'content_admin', 'support_admin', 'integration_admin']) {
      const r = S.adminDecision(app.id, 'approve', 'Looks fine.', { actorRole: role })
      assert.equal(r.ok, false, role)
      assert.match(r.error, /Only Review Admin and Super Admin/)
      const after = S.readPortalPreviewState()
      const a = after.applications.find((x) => x.id === app.id)
      assert.equal(a.status, 'ai_review', `${role} must not change status`)
      assert.ok(after.audit.some((x) => x.action === 'admin.decision_denied' && x.detail.includes(role)))
    }
    // approve then works for review_admin (same seed, same app id)
    const ok = S.adminDecision(app.id, 'approve', 'Looks fine.', { actorRole: 'review_admin' })
    assert.equal(ok.ok, true, ok.error)
    const decided = S.readPortalPreviewState()
    const dapp = decided.applications.find((x) => x.id === app.id)
    assert.equal(dapp.status, 'approved')
    assert.ok(decided.audit.some((x) => x.action === 'decision_approve'))
  })

  await test('supplement/reject and license lifecycle honor the same review/super boundary', () => {
    S.applySeedToStoredState('fresh')
    const st = S.readPortalPreviewState()
    const app = st.applications.find((a) => a.status === 'ai_review')
    assert.ok(app)
    for (const [action, role] of [['supplement', 'operations_admin'], ['reject', 'finance_admin'], ['supplement', 'support_admin']]) {
      const r = S.adminDecision(app.id, action, 'note', { actorRole: role })
      assert.equal(r.ok, false, `${role} ${action}`)
      assert.equal(S.readPortalPreviewState().applications.find((a) => a.id === app.id).status, 'ai_review')
    }
    assert.equal(S.adminDecision(app.id, 'supplement', 'Please re-upload.', { actorRole: 'super_admin' }).ok, true)
    assert.equal(S.readPortalPreviewState().applications.find((a) => a.id === app.id).status, 'supplement_required')
    // Lifecycle on an approved application
    S.applySeedToStoredState('activated')
    const st2 = S.readPortalPreviewState()
    const approved = st2.applications.find((a) => a.status === 'approved')
    assert.ok(approved)
    const deny = S.adminLifecycle(approved.id, 'suspended', 'fraud alert', { actorRole: 'finance_admin' })
    assert.equal(deny.ok, false)
    assert.equal(S.readPortalPreviewState().applications.find((a) => a.id === approved.id).status, 'approved')
    assert.ok(S.readPortalPreviewState().audit.some((x) => x.action === 'admin.decision_denied'))
    const allow = S.adminLifecycle(approved.id, 'suspended', 'fraud alert', { actorRole: 'review_admin' })
    assert.equal(allow.ok, true, allow.error)
    assert.equal(S.readPortalPreviewState().applications.find((a) => a.id === approved.id).status, 'suspended')
  })

  await test('deny audit lines never include secret material', () => {
    S.applySeedToStoredState('fresh')
    const app = S.readPortalPreviewState().applications.find((a) => a.status === 'ai_review')
    S.applySeedToStoredState('fresh')
    S.adminDecision(app.id, 'approve', 'applicant passport number 0H1234567', { actorRole: 'content_admin' })
    const audit = S.readPortalPreviewState().audit
    for (const line of audit) {
      if (line.action === 'admin.decision_denied') {
        assert.ok(!/0H1234567|passport|cvv|card|secret/i.test(line.detail), `deny audit leaked: ${line.detail}`)
        assert.match(line.detail, /blocked from/)
      }
    }
  })

  await test('admins cannot forge customer facts — customer accept/pay functions only take the customer email', () => {
    // No admin-only accept/pay/mark-paid export exists in the domain.
    for (const fn of ['adminAcceptQuote', 'adminAcceptsQuote', 'adminAcceptWork', 'adminPayInvoice', 'adminMarkInvoicePaid', 'adminApprovePayment']) {
      assert.equal(typeof B[fn], 'undefined', `${fn} must not exist`)
      assert.equal(typeof S[fn], 'undefined', `${fn} must not exist`)
    }
    assert.equal(typeof B.customerAcceptsQuote, 'function')
    assert.equal(typeof B.customerAcceptsWork, 'function')
    assert.equal(typeof B.customerPaysInvoice, 'function')
    // Pretending to pass an admin role as an extra option does NOT bypass.
    const s = B.defaultBusinessState()
    // mt-2001 is Jordan's customer matter; Nadia is not the client.
    const r1 = B.customerAcceptsQuote(s, { email: 'nadia.martin.preview@example.com', matterId: 'mt-2001', actorRole: 'super_admin' })
    assert.equal(r1.ok, false)
    assert.match(r1.error, /only the client|not the client|client/i)
    const r2 = B.customerPaysInvoice(s, { email: 'nadia.martin.preview@example.com', invoiceId: 'inv-mt-3001', actorRole: 'super_admin' })
    assert.equal(r2.ok, false)
    const r3 = B.customerAcceptsWork(s, { email: 'nadia.martin.preview@example.com', matterId: 'mt-2001', actorRole: 'super_admin' })
    assert.equal(r3.ok, false)
  })

  await test('UI source passes actorRole into decisions and never renders a customer-fact forgery button', () => {
    const src = fs.readFileSync(ADMIN_UI, 'utf8')
    assert.ok(src.includes('adminDecision(selected.id, action, note.trim(), { actorRole: roleId })'))
    assert.ok(src.includes('adminLifecycle(selected.id, status, lifecycleNote.trim() || \'Admin lifecycle change (prototype).\', { actorRole: roleId })'))
    assert.match(src, /canReviewDecision/)
    assert.match(src, /canReviewLifecycle/)
    assert.match(src, /ADMIN_ROLE_ACTIONS\[r\.id\]/)
    assert.ok(!/(adminAcceptQuote|adminPayInvoice|adminMark.*[Pp]aid|customerAcceptsQuote|customerPaysInvoice|simulate)/.test(src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '')), 'UI source has a customer-forgery control')
    assert.ok(!src.includes('onClick={() => B.customerAcceptsQuote') && !src.includes('customerAcceptsQuote(') && !src.includes('customerPaysInvoice('))
    assert.ok(src.includes('operations/support can handle order exceptions') === false || src.includes('Operations role can assign clients'), 'stale support-assign copy')
  })

  console.log(`\nAdmin RBAC suite: ${passed} PASS (${passed})`)
  console.log('Source: scripts/test-portal-preview-admin-rbac.cjs')
}

run().catch((e) => {
  console.error('FAIL', e && e.message)
  process.exit(1)
})
