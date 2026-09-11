#!/usr/bin/env node
// Portal Preview (isolated) — domain model tests for the three-portal
// candidate. The lib under test is NEW (app/lib/portal-preview/preview-core.ts)
// and never imports or edits golden code. All coverage is offline.
//
// Key boundaries asserted here:
//   - License review -> approval -> activation gates the Agent preview;
//     the $99/month subscription never grants or replaces identity.
//   - AI produces suggestions only; conflicts/high risk block one-click
//     approval; official-database checks stay reserved.
//   - Photos are simulated metadata; nothing is uploaded.
//   - Referral rewards: 20% on GOAA membership / allowed non-insurance
//     service revenue only; insurance premiums/commissions never qualify.
//   - Adapters reserve server-side env secret names; no real secret value
//     appears in source.

const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')

const ROOT = path.resolve(__dirname, '..')
const LIB_PATH = path.join(ROOT, 'app/lib/portal-preview/preview-core.ts')

const libCode = (() => {
  const result = ts.transpileModule(fs.readFileSync(LIB_PATH, 'utf8'), {
    fileName: LIB_PATH,
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  })
  assert.equal(
    (result.diagnostics || []).filter((d) => d.category === ts.DiagnosticCategory.Error).length,
    0,
    'portal-preview core transpiles clean',
  )
  return result.outputText
})()

function loadLib() {
  const sandbox = { console }
  sandbox.module = { exports: {} }
  sandbox.exports = sandbox.module.exports
  vm.runInNewContext(libCode, sandbox, { filename: 'preview-core.js' })
  return sandbox.exports
}

async function run() {
  let passed = 0
  const test = async (name, fn) => {
    await fn()
    passed += 1
    console.log(`PASS ${name}`)
  }
  const L = loadLib()

  const baseApplicant = { fullName: 'Jordan Rivera', phone: '(555) 010-2233', address: '880 Previs Lane, Austin, TX 78701', email: 'jordan.rivera.preview@example.com' }
  const baseLicenses = [
    { localId: 'lic-1', category: 'insurance', licenseNumber: '0H1234567', issuer: 'CA', expiresAt: '2028-06-30' },
    { localId: 'lic-2', category: 'real_estate', licenseNumber: 'RE-009911', issuer: 'NY', expiresAt: '2029-03-31' },
  ]

  const makeApp = () => {
    let app = L.createApplication(baseApplicant, baseLicenses)
    for (const lic of app.licenses) {
      app = L.addDocMeta(app, lic.localId, { kind: 'front', filename: `${lic.category}-front.jpg`, sizeBytes: 180000, mimeType: 'image/jpeg', quality: 'good' })
    }
    return app
  }

  await test('draft application validation rejects missing identity and licenses', () => {
    const app = L.createApplication({ fullName: '', phone: '', address: '', email: 'not-an-email' }, [])
    const errors = L.validateApplication(app)
    assert.ok(errors.some((e) => e.includes('Full name')))
    assert.ok(errors.some((e) => e.includes('professional license')))
  })

  await test('front photo metadata is required before submit', () => {
    const app = L.createApplication(baseApplicant, baseLicenses)
    const res = L.submitApplication(app)
    assert.equal(res.ok, false)
    assert.ok((res.errors ?? []).some((e) => e.includes('Front photo')))
  })

  await test('good photos + valid expiries produce an approve suggestion only', () => {
    const app = L.runSimulatedReview(makeApp(), { quality: 'good' })
    assert.equal(app.status, 'ai_review')
    assert.equal(app.aiSuggestions[0].recommendation, 'approve')
    assert.equal(app.aiSuggestions[0].riskLevel, 'low')
    assert.equal(app.aiSuggestions[0].officialDb.status, 'reserved_not_queried')
  })

  await test('blurry photos suggest supplement, never auto-approval', () => {
    const app = L.runSimulatedReview(makeApp(), { quality: 'blurry' })
    assert.equal(app.aiSuggestions[0].recommendation, 'supplement')
    assert.ok(app.aiSuggestions[0].flags.includes('blurry_front'))
  })

  await test('name conflict forces manual review suggestion', () => {
    const app = L.runSimulatedReview(makeApp(), { quality: 'good', ocrName: 'Someone Else' })
    assert.equal(app.aiSuggestions[0].recommendation, 'manual_review')
    assert.equal(app.aiSuggestions[0].riskLevel, 'high')
  })

  await test('admin approve path works only after ai_review and requires a note', () => {
    let app = makeApp()
    let res = L.adminDecide(app, 'approve', '')
    assert.equal(res.ok, false)
    app = L.runSimulatedReview(app, { quality: 'good' })
    res = L.adminDecide(app, 'approve', 'Verified by demo admin.')
    assert.equal(res.ok, true)
    assert.equal(res.app.status, 'approved')
    assert.ok(res.app.decidedAt)
  })

  await test('client decision buttons cannot change a rejected application', () => {
    let app = makeApp()
    app = L.runSimulatedReview(app, { quality: 'good' })
    app = L.adminDecide(app, 'reject', 'Fictional mismatch policy.', '2026-09-08T10:00:00Z').app
    const res = L.adminDecide(app, 'approve', 'Try to force approval.')
    assert.equal(res.ok, false)
    assert.equal(res.app.status, 'rejected')
  })

  await test('high-risk manual_review blocks one-click approval but allows supplement/reject', () => {
    let app = L.runSimulatedReview(makeApp(), { quality: 'good', ocrName: 'Morgan Hale' })
    let res = L.adminDecide(app, 'approve', 'One click.')
    assert.equal(res.ok, false)
    res = L.adminDecide(app, 'supplement', 'Photo shows another person name.')
    assert.equal(res.ok, true)
    assert.equal(res.app.status, 'supplement_required')
  })

  await test('supplement resubmission returns to review, then approval completes the flow', () => {
    let app = makeApp()
    app = L.runSimulatedReview(app, { quality: 'blurry' })
    app = L.adminDecide(app, 'supplement', 'Blurry front photo.', '2026-09-08T10:00:00Z').app
    let res = L.submitApplication(app)
    assert.equal(res.ok, false) // resubmit path must use the dedicated helper
    res = L.resubmitAfterSupplement(app)
    assert.equal(res.ok, true)
    app = L.runSimulatedReview(res.app, { quality: 'good' })
    app = L.adminDecide(app, 'approve', 'Clear photos now.', '2026-09-08T10:30:00Z').app
    assert.equal(app.status, 'approved')
  })

  await test('provisioning only after approval; activation token is one-time and expires', () => {
    let app = makeApp()
    let res = L.provisionActivation(app)
    assert.equal(res.ok, false)
    app = L.runSimulatedReview(app, { quality: 'good' })
    app = L.adminDecide(app, 'approve', 'Ok.', '2026-09-08T10:00:00Z').app
    res = L.provisionActivation(app)
    assert.equal(res.ok, true)
    assert.equal(res.app.activation.passwordStatus, 'none')
    assert.equal(res.app.activation.tokenUsed, false)
    let act = L.activateApplication(res.app, '2026-09-08T10:25:00Z')
    assert.equal(act.ok, true)
    assert.equal(act.app.activation.tokenUsed, true)
    // second use blocked
    const second = L.activateApplication(act.app, '2026-09-08T10:26:00Z')
    assert.equal(second.ok, false)
    // expiry path
    let app2 = L.runSimulatedReview(makeApp(), { quality: 'good' })
    app2 = L.adminDecide(app2, 'approve', 'Ok.', '2026-09-01T00:00:00Z').app
    app2 = L.provisionActivation(app2, '2026-09-01T00:05:00Z').app
    const late = L.activateApplication(app2, '2026-09-08T10:26:00Z')
    assert.equal(late.ok, false)
    assert.ok(late.error.includes('expired'))
  })

  await test('license lifecycle can suspend or expire an approved agent', () => {
    let app = makeApp()
    app = L.runSimulatedReview(app, { quality: 'good' })
    app = L.adminDecide(app, 'approve', 'Ok.', '2026-09-08T10:00:00Z').app
    const suspended = L.setLicenseLifecycle(app, 'suspended', 'Official check returned a hold.')
    assert.equal(suspended.status, 'suspended')
    const expired = L.setLicenseLifecycle(app, 'expired', 'Renewal not completed.')
    assert.equal(expired.status, 'expired')
  })

  await test('agent preview gate: subscription never opens an unapproved agent', () => {
    const pending = L.canOpenAgentPreview({ status: 'ai_review', activated: false, anyLicenseValid: true })
    assert.equal(pending.allowed, false)
    const approvedNotActivated = L.canOpenAgentPreview({ status: 'approved', activated: false, anyLicenseValid: true })
    assert.equal(approvedNotActivated.allowed, false)
    assert.ok(approvedNotActivated.reason.includes('activation'))
    const approvedNoLicense = L.canOpenAgentPreview({ status: 'approved', activated: true, anyLicenseValid: false })
    assert.equal(approvedNoLicense.allowed, false)
    const suspended = L.canOpenAgentPreview({ status: 'suspended', activated: true, anyLicenseValid: true })
    assert.equal(suspended.allowed, false)
    const expired = L.canOpenAgentPreview({ status: 'expired', activated: true, anyLicenseValid: true })
    assert.equal(expired.allowed, false)
  })

  await test('agent preview gate opens only for approved + activated + valid license', () => {
    const open = L.canOpenAgentPreview({ status: 'approved', activated: true, anyLicenseValid: true })
    assert.equal(open.allowed, true)
  })

  await test('referral reward: 20% membership rule, insurance never eligible', () => {
    assert.equal(L.REFERRAL_RATE, 0.2)
    assert.equal(L.referralEligible('goaa_membership').eligible, true)
    assert.equal(L.referralEligible('insurance_premium').eligible, false)
    assert.equal(L.referralEligible('insurance_commission').eligible, false)
    assert.equal(L.referralEligible('allowed_non_insurance_service').eligible, true)
  })

  await test('standard driver license is ID, never a professional category', () => {
    assert.equal(L.isProfessionalCategory('standard_drivers_license'), false)
    assert.equal(L.isProfessionalCategory('cdl'), true)
    assert.equal(L.isProfessionalCategory('insurance'), true)
  })

  await test('customer rail order shows divider before Get Licensed and Earning Opportunities', () => {
    const ids = L.previewCustomerNav.map((i) => i.id)
    assert.equal(JSON.stringify(ids), JSON.stringify(['chat', 'matters', 'skills', 'licensed', 'earning']))
    assert.equal(L.previewCustomerNav[3].divider, true)
    assert.equal(L.previewCustomerNav[3].new, true)
    assert.equal(L.previewCustomerNav[4].new, true)
  })

  await test('adapter catalog reserves server env names only, no real secrets', () => {
    const code = fs.readFileSync(LIB_PATH, 'utf8')
    assert.ok(!/(sk|key|secret|token)[_-][A-Za-z0-9]{20,}/i.test(code), 'no secret-looking literal in source')
    for (const a of L.PREVIEW_ADAPTERS) {
      assert.ok(/^[A-Z][A-Z0-9_]{3,}$/.test(a.serverSecretEnv), `env name reserved: ${a.serverSecretEnv}`)
      assert.ok(a.status.includes('needs_account') || a.status.includes('configured'), 'no live credentials claimed')
      assert.ok(['api', 'sso', 'webhook'].includes(a.kind), `adapter kind valid: ${a.id}`)
    }
    assert.equal(L.PREVIEW_ADAPTERS.length, 6)
  })

  await test('admin role matrix denies across sections and allows overview', () => {
    assert.equal(L.roleCan('review', 'applications'), true)
    assert.equal(L.roleCan('review', 'finance'), false)
    assert.equal(L.roleCan('support', 'finance'), false)
    assert.equal(L.roleCan('finance', 'system secrets'), false)
    assert.equal(L.roleCan('content', 'referral'), false)
    assert.equal(L.roleCan('system', 'overview'), true)
    assert.equal(L.roleCan('review', 'overview'), true)
  })

  console.log(`\nAll portal-preview core assertions passed (${passed})`)
}

run().catch((err) => {
  console.error('FAIL', err)
  process.exit(1)
})
