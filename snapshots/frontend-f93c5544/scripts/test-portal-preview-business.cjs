#!/usr/bin/env node
// Portal Preview (isolated) — phase 2 business-loop domain tests.
//
// Covers the unified single-account model, admin-only grants, self-service
// activation without plaintext password storage, the full agent order loop,
// matter ownership/visibility isolation, $99 subscription pause boundaries,
// and admin RBAC matrices (license decisions vs finance vs operations vs
// content vs support vs integration). Offline; never touches golden code.

const assert = require('node:assert/strict')

// Cross-VM arrays carry a different realm prototype, so compare shapes as
// JSON instead of deepStrictEqual on arrays/objects from the sandbox lib.
const j = (v) => JSON.stringify(v)
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')

const ROOT = path.resolve(__dirname, '..')
const LIB_PATH = path.join(ROOT, 'app/lib/portal-preview/preview-business.ts')

const libCode = (() => {
  const result = ts.transpileModule(fs.readFileSync(LIB_PATH, 'utf8'), {
    fileName: LIB_PATH,
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  })
  assert.equal(
    (result.diagnostics || []).filter((d) => d.category === ts.DiagnosticCategory.Error).length,
    0,
    'preview-business transpiles clean',
  )
  return result.outputText
})()

function loadLib() {
  const sandbox = { console }
  sandbox.module = { exports: {} }
  sandbox.exports = sandbox.module.exports
  vm.runInNewContext(libCode, sandbox, { filename: 'preview-business.js' })
  return sandbox.exports
}

const JORDAN = 'jordan.rivera.preview@example.com'
const NADIA = 'nadia.martin.preview@example.com'

async function run() {
  let passed = 0
  const test = async (name, fn) => {
    await fn()
    passed += 1
    console.log(`PASS ${name}`)
  }
  const L = loadLib()

  const okState = (r) => {
    assert.equal(r.ok, true, r.error || 'expected ok')
    return r.state
  }

  await test('everyone starts as customer; duplicate registration is refused', () => {
    const s = L.defaultBusinessState()
    const acc0 = L.accountFor(s, JORDAN)
    assert.equal(j(acc0.roles), j(['customer']))
    assert.equal(acc0.agentAccess, 'none')
    const dup = L.registerAccount(s, { email: JORDAN, displayName: 'Jordan Again' })
    assert.equal(dup.ok, false)
    assert.ok(/already exists/.test(dup.error))
    const fresh = okState(L.registerAccount(s, { email: 'new.demo@example.com', displayName: 'New Demo' }))
    assert.equal(j(L.accountFor(fresh, 'new.demo@example.com').roles), j(['customer']))
  })

  await test('only an admin role with open_agent_access can grant access', () => {
    const s = L.defaultBusinessState()
    assert.equal(L.openAgentAccess(s, { email: JORDAN, actorRole: 'review_admin' }).ok, false)
    assert.equal(L.openAgentAccess(s, { email: JORDAN, actorRole: 'finance_admin' }).ok, false)
    const ops = okState(L.openAgentAccess(s, { email: JORDAN, actorRole: 'operations_admin' }))
    assert.equal(L.accountFor(ops, JORDAN).agentAccess, 'granted')
    const second = L.openAgentAccess(ops, { email: JORDAN, actorRole: 'super_admin' })
    assert.equal(second.ok, false)
  })

  await test('activation is self-service: password is never generated or stored', () => {
    const granted = okState(L.openAgentAccess(L.defaultBusinessState(), { email: JORDAN, actorRole: 'super_admin' }))
    const before = L.setPasswordAndActivate(granted, { email: JORDAN, password: '' })
    assert.equal(before.ok, false)
    const after = okState(L.setPasswordAndActivate(granted, { email: JORDAN, password: 'hunter2demo' }))
    const acc = L.accountFor(after, JORDAN)
    assert.equal(j(acc.roles), j(['customer', 'agent']))
    assert.equal(acc.agentAccess, 'activated')
    assert.equal(acc.agentUsername, 'jordan.rivera.preview')
    assert.ok(acc.passwordSetAt)
    assert.equal(L.agentDeniedReason(after, JORDAN), null)
    assert.ok(!JSON.stringify(after).includes('hunter2demo'), 'plaintext password must never be stored')
    const again = L.setPasswordAndActivate(after, { email: JORDAN, password: 'newpass1' })
    assert.equal(again.ok, false)
  })

  await test('agent gate copy reasons distinguish not-granted vs not-activated', () => {
    const fresh = L.defaultBusinessState()
    assert.match(L.agentDeniedReason(fresh, JORDAN), /has not been granted/)
    const granted = okState(L.openAgentAccess(fresh, { email: JORDAN, actorRole: 'super_admin' }))
    assert.match(L.agentDeniedReason(granted, JORDAN), /not activated/)
    const activated = okState(L.setPasswordAndActivate(granted, { email: JORDAN, password: 'pw12345' }))
    assert.equal(L.agentDeniedReason(activated, JORDAN), null)
  })

  await test('matter visibility is strictly per assigned agent account', () => {
    const s = L.seedBusinessState('activated')
    const jordanIds = L.mattersVisibleToAgent(s, JORDAN).map((m) => m.id).sort()
    assert.equal(j(jordanIds), j(['mt-2001', 'mt-2002', 'mt-2003']))
    const nadiaIds = L.mattersVisibleToAgent(s, NADIA).map((m) => m.id)
    assert.equal(j(nadiaIds), j(['mt-3001']))
    assert.ok(!L.visibleMatter(s, JORDAN, 'mt-3001'))
  })

  await test('agent cannot open matters assigned to another agent', () => {
    const s = L.seedBusinessState('activated')
    const r = L.agentUploadDeliverable(s, { email: JORDAN, matterId: 'mt-3001', filename: 'steal.pdf', mimeType: 'application/pdf', sizeBytes: 1 })
    assert.equal(r.ok, false)
    assert.match(r.error, /own account/)
  })

  await test('full order loop advances through every stage and stays auditable', () => {
    let s = L.seedBusinessState('activated')
    const CLIENT = 'eleanor.frost.demo@example.com'
    s = okState(L.registerAccount(s, { email: CLIENT, displayName: 'Eleanor Frost' }))
    const accept = okState(L.agentAcceptOpportunity(s, { email: JORDAN, opportunityId: 'opp-1002' }))
    s = accept
    const matter = s.matters.find((m) => m.clientEmail === CLIENT)
    assert.ok(matter)
    assert.equal(matter.stage, 'accepted')
    // Invoice cannot be issued before acceptance.
    assert.equal(L.agentIssueInvoice(s, { email: JORDAN, matterId: matter.id }).ok, false)
    s = okState(L.agentPrepareEstimate(s, { email: JORDAN, matterId: matter.id, amountUsd: 180 }))
    assert.equal(s.matters.find((m) => m.id === matter.id).stage, 'estimate_prepared')
    s = okState(L.agentSendQuote(s, { email: JORDAN, matterId: matter.id }))
    assert.equal(s.matters.find((m) => m.id === matter.id).stage, 'quote_awaiting_accept')
    // Only the client account can accept the quote (agent must not).
    assert.equal(L.customerAcceptsQuote(s, { email: JORDAN, matterId: matter.id }).ok, false)
    s = okState(L.customerAcceptsQuote(s, { email: CLIENT, matterId: matter.id }))
    assert.equal(s.matters.find((m) => m.id === matter.id).stage, 'in_progress')
    s = okState(L.agentUploadDeliverable(s, { email: JORDAN, matterId: matter.id, filename: 'cleaning-report.pdf', mimeType: 'application/pdf', sizeBytes: 2048 }))
    assert.equal(s.matters.find((m) => m.id === matter.id).stage, 'deliverables_uploaded')
    s = okState(L.agentRequestWorkAcceptance(s, { email: JORDAN, matterId: matter.id }))
    s = okState(L.customerAcceptsWork(s, { email: CLIENT, matterId: matter.id }))
    assert.equal(s.matters.find((m) => m.id === matter.id).stage, 'work_accepted')
    s = okState(L.agentIssueInvoice(s, { email: JORDAN, matterId: matter.id }))
    const invoice = s.invoices.find((i) => i.matterId === matter.id)
    assert.ok(invoice)
    assert.equal(invoice.status, 'issued')
    assert.equal(s.matters.find((m) => m.id === matter.id).stage, 'invoice_issued')
    // Cannot complete before paid.
    assert.equal(L.agentCompleteOrder(s, { email: JORDAN, matterId: matter.id }).ok, false)
    // Agent cannot pay; only the client can.
    assert.equal(L.customerPaysInvoice(s, { email: JORDAN, invoiceId: invoice.id }).ok, false)
    s = okState(L.customerPaysInvoice(s, { email: CLIENT, invoiceId: invoice.id }))
    assert.equal(s.invoices.find((i) => i.id === invoice.id).status, 'paid')
    assert.equal(s.matters.find((m) => m.id === matter.id).stage, 'paid')
    assert.ok(s.payments.some((p) => p.invoiceId === invoice.id))
    s = okState(L.agentCompleteOrder(s, { email: JORDAN, matterId: matter.id }))
    assert.equal(s.matters.find((m) => m.id === matter.id).stage, 'completed')
    const log = s.matters.find((m) => m.id === matter.id).audit.map((a) => a.action)
    for (const expected of ['opportunity.accepted', 'estimate.prepared', 'quote.sent', 'quote.accepted', 'deliverable.uploaded', 'work.awaiting_accept', 'work.accepted', 'invoice.issued', 'payment.received', 'order.completed']) {
      assert.ok(log.includes(expected), `audit missing ${expected}`)
    }
  })

  await test('subscription pause limits only paid features, never license state', () => {
    const activated = L.seedBusinessState('paused')
    const acc = L.accountFor(activated, JORDAN)
    assert.equal(j(acc.roles), j(['customer', 'agent']))
    assert.equal(acc.agentAccess, 'activated')
    assert.equal(acc.subscription.status, 'paused')
    assert.equal(L.agentDeniedReason(activated, JORDAN), null, 'pause must not lock an approved+activated agent')
    assert.equal(L.paidFeatureOpen(activated, JORDAN, 'ai_assistant'), false)
    assert.equal(L.paidFeatureOpen(activated, JORDAN, 'payments_earnings'), false)
    // Core order work stays possible while paused (explicit in-progress
    // matter; picking a later-stage matter would be the wrong fixture).
    const mt = activated.matters.find((m) => m.id === 'mt-2001')
    assert.ok(mt, 'fixture mt-2001 must exist')
    assert.equal(mt.stage, 'in_progress')
    const r = L.agentUploadDeliverable(activated, { email: JORDAN, matterId: 'mt-2001', filename: 'still-works.pdf', mimeType: 'application/pdf', sizeBytes: 100 })
    assert.equal(r.ok, true, r.error)
    // The same upload on an invoice_issued matter must still be rejected.
    const bad = L.agentUploadDeliverable(activated, { email: JORDAN, matterId: 'mt-2002', filename: 'late.pdf', mimeType: 'application/pdf', sizeBytes: 100 })
    assert.equal(bad.ok, false)
    assert.match(bad.error, /Stage invoice_issued does not allow/)
    assert.ok(activated.audit.some((a) => a.action === 'subscription.paused' && /license state unchanged/.test(a.detail)))
  })

  await test('admin RBAC: review can decide licenses but never finance or open access', () => {
    assert.equal(L.adminCan('review_admin', 'approve_application'), true)
    assert.equal(L.adminCan('review_admin', 'request_supplement'), true)
    assert.equal(L.adminCan('review_admin', 'reject_application'), true)
    assert.equal(L.adminCan('review_admin', 'suspend_agent'), true)
    assert.equal(L.adminCan('review_admin', 'mark_expired'), true)
    assert.equal(L.adminCan('review_admin', 'open_agent_access'), false)
    assert.equal(L.adminCan('review_admin', 'approve_refund'), false)
    assert.equal(L.adminCan('review_admin', 'approve_settlement'), false)
  })

  await test('admin RBAC: finance can refund/settle but never approve licenses', () => {
    assert.equal(L.adminCan('finance_admin', 'approve_refund'), true)
    assert.equal(L.adminCan('finance_admin', 'approve_settlement'), true)
    assert.equal(L.adminCan('finance_admin', 'approve_application'), false)
    const s = L.defaultBusinessState()
    assert.equal(L.adminApproveRefund(s, { actorRole: 'finance_admin', invoiceId: 'inv-mt-3001', reason: 'double charge' }).ok, true)
    assert.equal(L.adminApproveSettlement(s, { actorRole: 'finance_admin', batch: 'BATCH-0912', amountUsd: 2000 }).ok, true)
    assert.equal(L.adminApproveRefund(s, { actorRole: 'review_admin', invoiceId: 'inv-mt-3001', reason: 'nope' }).ok, false)
  })

  await test('admin RBAC: operations handles assignments/exceptions; content, support, integration stay in lane', () => {
    const s = L.defaultBusinessState()
    assert.equal(L.adminAssignMatter(s, { actorRole: 'operations_admin', matterId: 'mt-3001', toEmail: JORDAN }).ok, true)
    assert.equal(L.adminHandleOrderException(s, { actorRole: 'operations_admin', matterId: 'mt-2001', note: 'rescheduled by client' }).ok, true)
    assert.equal(L.adminAssignMatter(s, { actorRole: 'review_admin', matterId: 'mt-2001', toEmail: NADIA }).ok, false)
    assert.equal(L.adminHandleOrderException(s, { actorRole: 'finance_admin', matterId: 'mt-2001', note: 'nope' }).ok, false)
    assert.equal(L.adminCan('content_admin', 'manage_content'), true)
    assert.equal(L.adminCan('content_admin', 'manage_referrals'), true)
    assert.equal(L.adminCan('content_admin', 'approve_application'), false)
    assert.equal(L.adminCan('support_admin', 'handle_order_exception'), true)
    assert.equal(L.adminCan('integration_admin', 'manage_integrations'), true)
    assert.equal(L.adminCan('integration_admin', 'approve_settlement'), false)
    assert.equal(L.adminCan('super_admin', 'manage_integrations'), true)
  })

  await test('paused subscriptions never alter application or license fields', () => {
    const fresh = L.seedBusinessState('activated')
    const paused = L.seedBusinessState('paused')
    for (const key of ['agentUsername', 'activatedAt', 'passwordSetAt']) {
      assert.equal(L.accountFor(paused, JORDAN)[key], L.accountFor(fresh, JORDAN)[key])
    }
    assert.equal(j(L.accountFor(paused, JORDAN).roles), j(['customer', 'agent']))
  })

  console.log(`\nAll portal-preview business assertions passed (${passed})`)
  process.exitCode = 0
}

run().catch((e) => {
  console.error(e)
  process.exitCode = 1
})
