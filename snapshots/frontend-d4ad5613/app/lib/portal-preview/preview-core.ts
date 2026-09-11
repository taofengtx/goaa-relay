/**
 * preview-core.ts — isolated three-portal candidate preview domain model.
 *
 * Golden-version protection: this module is NEW and self-contained. It does
 * not import, require, or modify any existing page/component/lib/route.
 * It only powers the /portal-preview/* candidate routes.
 *
 * Boundaries honored here:
 *   - License approval decides Agent identity; the $99/month Agent
 *     subscription decides paid-feature access. They never replace each
 *     other and paying never bypasses license review.
 *   - AI produces review SUGGESTIONS only. Photo data is never treated as
 *     official license validity; conflicts, missing materials, high risk or
 *     an unverified official database force manual review or hold state.
 *   - All names, licenses, photos, accounts and e-mails are fictional.
 *   - Browser localStorage only holds simulated state / file metadata.
 *   - Activation links are a short-lived, single-use, signed-token INTERFACE
 *     design only. No real tokens, e-mails, usernames, passwords or rewards
 *     are generated.
 *   - No checkout, no charge, no Stripe change.
 *   - Third-party secrets are only reserved as server-side env var names.
 */

export type PortalId = 'customer' | 'agent' | 'admin'

/* Customer rail (preview) — shows where each item lives today. */
export interface CustomerNavItem {
  id: string
  label: string
  icon: string
  new?: boolean
  kicker?: string
  divider?: boolean
}

export const previewCustomerNav: CustomerNavItem[] = [
  { id: 'chat', label: 'Chat', icon: '💬', kicker: 'existing golden view' },
  { id: 'matters', label: 'Matters', icon: '🗂️', kicker: 'existing golden view' },
  { id: 'skills', label: 'Skills Marketplace', icon: '🧰' },
  { id: 'licensed', label: 'Get Licensed', icon: '📜', new: true, divider: true },
  { id: 'earning', label: 'Earning Opportunities', icon: '💡', new: true },
]

export type ApplyStatus =
  | 'draft'
  | 'submitted'
  | 'ai_review'
  | 'supplement_required'
  | 'approved'
  | 'rejected'
  | 'suspended'
  | 'expired'

export const APPLY_STATUS_LABELS: Record<ApplyStatus, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  ai_review: 'AI Review',
  supplement_required: 'Supplement Required',
  approved: 'Approved',
  rejected: 'Rejected',
  suspended: 'Suspended',
  expired: 'Expired',
}

export type DocKind = 'front' | 'back' | 'supplement'
export type DocQuality = 'good' | 'blurry' | 'unreadable'

export interface DocMeta {
  docId: string
  kind: DocKind
  filename: string
  sizeBytes: number
  mimeType: string
  quality: DocQuality
  addedAt: string
}

export interface LicenseDraft {
  localId: string
  category: string
  licenseNumber: string
  issuer: string
  expiresAt: string
  docs: DocMeta[]
}

export interface ApplicantDetails {
  fullName: string
  phone: string
  address: string
  email: string
}

export interface AiSuggestion {
  reviewId: string
  reviewedAt: string
  ocr: { fullName: string; licenseNumbers: string[]; categories: string[]; issuers: string[]; expiries: string[] }
  checks: { nameConsistent: boolean; numberConsistent: boolean; issuerConsistent: boolean; expiryValid: boolean }
  imageQuality: DocQuality | 'mixed'
  missingMaterials: string[]
  officialDb: { status: 'reserved_not_queried' | 'reserved_hold'; note: string }
  riskLevel: 'low' | 'medium' | 'high'
  flags: string[]
  recommendation: 'approve' | 'supplement' | 'manual_review'
}

export interface ActivationDesign {
  username: string
  /** Interface design only: raw token NEVER rendered in production. */
  activationToken?: string
  tokenExpiresAt: string
  tokenUsed: boolean
  passwordStatus: 'none' | 'set_via_activation'
  activatedAt?: string
}

export interface Application {
  id: string
  applicant: ApplicantDetails
  licenses: LicenseDraft[]
  status: ApplyStatus
  createdAt: string
  updatedAt: string
  submittedAt?: string
  decidedAt?: string
  decidedBy?: string
  /** Customer-visible message chosen by an admin/system action. The
   *  customer reads the RESULT only; internal AI flags/risk stay in
   *  aiSuggestions and are not rendered on the customer page. */
  customerMessage?: string
  logs: Array<{ at: string; actor: 'applicant' | 'admin' | 'system'; action: string; note?: string }>
  aiSuggestions: AiSuggestion[]
  activation?: ActivationDesign
  subscriptionIndependenceNote: string
}

/* ---------------------------------------------------------------- */
/* Pure state transitions (mirrors the demo only; no real side effects) */
/* ---------------------------------------------------------------- */

export function createApplication(applicant: ApplicantDetails, licenses: Omit<LicenseDraft, 'docs'>[]): Application {
  return {
    id: `ap_${Math.floor(Math.random() * 1e6)}`,
    applicant,
    licenses: licenses.map((l) => ({ ...l, docs: [] })),
    status: 'draft',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    logs: [{ at: new Date().toISOString(), actor: 'applicant', action: 'draft_created' }],
    aiSuggestions: [],
    subscriptionIndependenceNote: 'License approval decides Agent identity; the $99/month subscription decides paid feature access. Neither replaces the other.',
  }
}

export function validateApplication(app: Application): string[] {
  const errors: string[] = []
  if (!app.applicant.fullName.trim()) errors.push('Full name is required.')
  if (!app.applicant.phone.trim()) errors.push('Phone is required.')
  if (!app.applicant.address.trim()) errors.push('Address is required.')
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(app.applicant.email)) errors.push('A valid e-mail is required.')
  if (app.licenses.length === 0) errors.push('At least one professional license is required.')
  for (const lic of app.licenses) {
    if (!lic.licenseNumber.trim()) errors.push(`License number missing for ${lic.category}.`)
    if (!lic.issuer.trim()) errors.push(`Issuing state/agency missing for ${lic.category}.`)
    if (!lic.expiresAt) errors.push(`Expiry date missing for ${lic.category}.`)
    if (lic.docs.filter((d) => d.kind === 'front').length === 0) errors.push(`Front photo missing for ${lic.category}.`)
  }
  return errors
}

/** Driver-license rule: a standard driver license is ID only. CDL counts. */
export function isProfessionalCategory(category: string): boolean {
  return category !== 'standard_drivers_license'
}

export function submitApplication(app: Application, now = new Date().toISOString()): { ok: boolean; app: Application; errors?: string[] } {
  if (app.status !== 'draft' && app.status !== 'submitted') {
    return { ok: false, app, errors: [`Applications in state ${app.status} cannot be submitted again by the applicant.`] }
  }
  const errors = validateApplication(app)
  if (errors.length) return { ok: false, app, errors }
  const next: Application = { ...app, status: 'submitted', updatedAt: now, submittedAt: now }
  next.logs = [...app.logs, { at: now, actor: 'applicant', action: 'submitted' }]
  return { ok: true, app: next }
}

/** Simulated AI review — suggestions only; never auto-approves. */
export function runSimulatedReview(app: Application, opts: { quality?: DocQuality; ocrName?: string; ocrNumber?: string } = {}, now = new Date().toISOString()): Application {
  const numbers = app.licenses.map((l) => l.licenseNumber)
  const expiries = app.licenses.map((l) => l.expiresAt)
  const today = now.slice(0, 10)
  const allExpiryValid = expiries.every((e) => e >= today)
  const quality = opts.quality ?? 'good'
  const nameOk = !opts.ocrName || opts.ocrName === app.applicant.fullName
  const numbersOk = !opts.ocrNumber || numbers.includes(opts.ocrNumber)
  const flags: string[] = []
  if (!nameOk) flags.push('ocr_name_mismatch')
  if (!numbersOk) flags.push('ocr_number_mismatch')
  if (quality === 'blurry') flags.push('blurry_front')
  if (quality === 'unreadable') flags.push('unreadable_image')
  if (flags.length === 0 && !allExpiryValid) flags.push('expired_license_detected')
  const missing = quality === 'unreadable' ? ['readable photo of every license'] : quality === 'blurry' ? ['clear front photo'] : []
  const riskLevel: 'low' | 'medium' | 'high' = flags.length >= 2 || !nameOk || !numbersOk ? 'high' : flags.length === 1 ? 'medium' : 'low'
  const recommendation = flags.length >= 2 || !nameOk || !numbersOk
    ? 'manual_review'
    : quality === 'good' && allExpiryValid && flags.length === 0
      ? 'approve'
      : 'supplement'
  const suggestion: AiSuggestion = {
    reviewId: `rv_${Date.now()}`,
    reviewedAt: now,
    ocr: {
      fullName: opts.ocrName ?? app.applicant.fullName,
      licenseNumbers: opts.ocrNumber ? numbers.map((n) => (n === opts.ocrNumber ? opts.ocrNumber! : n)) : numbers,
      categories: app.licenses.map((l) => l.category),
      issuers: app.licenses.map((l) => l.issuer),
      expiries,
    },
    checks: { nameConsistent: nameOk, numberConsistent: numbersOk, issuerConsistent: true, expiryValid: allExpiryValid },
    imageQuality: quality,
    missingMaterials: missing,
    officialDb: { status: 'reserved_not_queried', note: 'Official database verification is reserved. Photo data is never treated as official license validity.' },
    riskLevel,
    flags,
    recommendation,
  }
  const next: Application = { ...app, status: 'ai_review', updatedAt: now, aiSuggestions: [suggestion, ...app.aiSuggestions] }
  next.logs = [...app.logs, { at: now, actor: 'system', action: 'ai_review_done', note: `Simulated AI suggestion: ${recommendation}.` }]
  return next
}

export type AdminAction = 'approve' | 'supplement' | 'reject'

/** Admin decisions require a note; client cannot change conclusions. */
export function adminDecide(app: Application, action: AdminAction, note: string, now = new Date().toISOString()): { ok: boolean; app: Application; error?: string } {
  if (app.status !== 'ai_review') return { ok: false, app, error: 'Only an AI-reviewed application can be decided.' }
  if (!note.trim()) return { ok: false, app, error: 'A decision note is required.' }
  const latest = app.aiSuggestions[0]
  const requiresManual = latest && latest.recommendation === 'manual_review'
  if (requiresManual && action === 'approve') {
    // High-risk suggestions must not be auto-approved by a one-click approve.
    return { ok: false, app, error: 'Conflict or high risk detected — this application requires manual review before an approval.' }
  }
  const status: ApplyStatus = action === 'approve' ? 'approved' : action === 'supplement' ? 'supplement_required' : 'rejected'
  const next: Application = { ...app, status, updatedAt: now, decidedAt: now, decidedBy: 'goaa_admin_demo' }
  next.logs = [...app.logs, { at: now, actor: 'admin', action: `decision_${action}`, note }]
  return { ok: true, app: next }
}

export function resubmitAfterSupplement(app: Application, now = new Date().toISOString()): { ok: boolean; app: Application; error?: string } {
  if (app.status !== 'supplement_required') return { ok: false, app, error: 'Only a supplement-required application can resubmit.' }
  const next: Application = { ...app, status: 'submitted', updatedAt: now }
  next.logs = [...app.logs, { at: now, actor: 'applicant', action: 'resubmitted_after_supplement' }]
  return { ok: true, app: next }
}

export function addDocMeta(app: Application, licenseLocalId: string, doc: Omit<DocMeta, 'docId' | 'addedAt'>): Application {
  return {
    ...app,
    licenses: app.licenses.map((l) => (l.localId === licenseLocalId ? { ...l, docs: [...l.docs, { ...doc, docId: `doc_${Date.now()}`, addedAt: new Date().toISOString() }] } : l)),
  }
}

export function provisionActivation(app: Application, now = new Date().toISOString()): { ok: boolean; app: Application; error?: string } {
  if (app.status !== 'approved') return { ok: false, app, error: 'Provisioning only happens after approval.' }
  if (app.activation && app.activation.tokenUsed) return { ok: false, app, error: 'Already activated.' }
  const expires = new Date(new Date(now).getTime() + 30 * 60000).toISOString()
  const activation: ActivationDesign = {
    username: app.applicant.email.split('@')[0].toLowerCase().replace(/[^a-z0-9]/g, '.'),
    activationToken: `preview_tok_${Date.now()}`,
    tokenExpiresAt: expires,
    tokenUsed: false,
    passwordStatus: 'none',
  }
  const next: Application = { ...app, activation }
  next.logs = [...app.logs, { at: now, actor: 'system', action: 'provisioning_sent', note: `Username ${activation.username} and one-time activation link sent (simulated). No password created or e-mailed.` }]
  return { ok: true, app: next }
}

export function activateApplication(app: Application, now = new Date().toISOString()): { ok: boolean; app: Application; error?: string } {
  if (!app.activation || app.activation.tokenUsed) return { ok: false, app, error: 'No pending activation link.' }
  if (app.activation.tokenExpiresAt < now) return { ok: false, app, error: 'Activation link expired.' }
  const next: Application = {
    ...app,
    activation: { ...app.activation, tokenUsed: true, passwordStatus: 'set_via_activation', activatedAt: now },
  }
  next.logs = [...app.logs, { at: now, actor: 'applicant', action: 'activated', note: 'Account activated through the one-time link; password set by the user. No password stored or displayed.' }]
  return { ok: true, app: next }
}

export function setLicenseLifecycle(app: Application, status: 'suspended' | 'expired', reason: string, now = new Date().toISOString()): Application {
  const next: Application = { ...app, status, updatedAt: now, decidedBy: 'goaa_admin_demo' }
  next.logs = [...app.logs, { at: now, actor: 'admin', action: `lifecycle_${status}`, note: reason }]
  return next
}

/* ---------------------------------------------------------------- */
/* Agent gate — approval and $99 subscription are independent states.  */
/* ---------------------------------------------------------------- */

export interface AgentGateInput {
  status?: ApplyStatus
  activated?: boolean
  anyLicenseValid?: boolean
}

export function canOpenAgentPreview(gate: AgentGateInput): { allowed: boolean; reason: string } {
  if (!gate.status || gate.status === 'draft' || gate.status === 'submitted' || gate.status === 'ai_review' || gate.status === 'supplement_required' || gate.status === 'rejected') {
    return { allowed: false, reason: 'License review is not approved yet. Agent Preview opens only after approval and activation.' }
  }
  if (gate.status === 'suspended') return { allowed: false, reason: 'License suspended. Agent access is paused.' }
  if (gate.status === 'expired') return { allowed: false, reason: 'License expired. Renewal is required before agent access returns.' }
  if (!gate.activated) return { allowed: false, reason: 'Approved but not activated yet. Use the one-time activation link to set your password first.' }
  if (!gate.anyLicenseValid) return { allowed: false, reason: 'None of the licenses are currently valid.' }
  return { allowed: true, reason: 'License approved, account activated, licenses valid. Agent Preview is open. The $99/month subscription only gates paid features — it never grants identity.' }
}

export const AGENT_SUB_STATUSES = ['none', 'trial', 'active', 'paused', 'canceled'] as const
export type AgentSubStatus = (typeof AGENT_SUB_STATUSES)[number]

/* ---------------------------------------------------------------- */
/* Referral reward rule — membership only, never insurance revenue.    */
/* ---------------------------------------------------------------- */

export type RewardBase = 'goaa_membership' | 'allowed_non_insurance_service' | 'insurance_premium' | 'insurance_commission'

export function referralEligible(base: RewardBase): { eligible: boolean; reason: string } {
  if (base === 'insurance_premium' || base === 'insurance_commission') {
    return { eligible: false, reason: '20% rewards never apply to insurance premiums, insurance commissions or insurance-closing percentages.' }
  }
  if (base === 'goaa_membership') return { eligible: true, reason: '20% of the GOAA membership fee (or explicitly allowed non-insurance service revenue) may be rewarded.' }
  return { eligible: true, reason: 'Allowed only when the revenue base is a non-insurance service explicitly permitted by policy.' }
}

export const REFERRAL_RATE = 0.2

/* ---------------------------------------------------------------- */
/* Third-party adapters — interface + needs_account only.             */
/* ---------------------------------------------------------------- */

export type AdapterKind = 'api' | 'sso' | 'webhook'

export interface AdapterSpec {
  id: string
  provider: string
  purpose: string
  kind: AdapterKind
  status: 'needs_account' | 'sandbox_configured' | 'live_connected'
  serverSecretEnv: string
  contract: string[]
  notes: string[]
}

export const PREVIEW_ADAPTERS: AdapterSpec[] = [
  { id: 'pipedream', provider: 'Pipedream', purpose: 'AI butler skill connections (Pipedream Connect)', kind: 'api', status: 'needs_account', serverSecretEnv: 'PIPEDREAM_CLIENT_SECRET', contract: ['POST /skills/run', 'POST /skills/webhook/complete'], notes: ['GOAA keeps catalog, review and pricing.'] },
  { id: 'webce', provider: 'WebCE', purpose: 'License training courses (reserved partner/SSO)', kind: 'sso', status: 'needs_account', serverSecretEnv: 'WEBCE_PARTNER_KEY', contract: ['GET /webce/catalog', 'SSO enrollment jump'], notes: ['Course completion webhook reserved.'] },
  { id: 'nipr', provider: 'NIPR', purpose: 'Insurance license verification', kind: 'api', status: 'needs_account', serverSecretEnv: 'NIPR_API_TOKEN', contract: ['GET /nipr/license'], notes: ['Official check reserved; photos never equal official validity.'] },
  { id: 'arello', provider: 'ARELLO', purpose: 'Real estate license verification', kind: 'api', status: 'needs_account', serverSecretEnv: 'ARELLO_API_TOKEN', contract: ['GET /arello/license'], notes: ['Reserved.'] },
  { id: 'certemy', provider: 'Certemy', purpose: 'Cross-occupation credential management (candidate)', kind: 'api', status: 'needs_account', serverSecretEnv: 'CERTEMY_API_KEY', contract: ['GET /certemy/credentials'], notes: ['Candidate only.'] },
  { id: 'firstpromoter', provider: 'FirstPromoter', purpose: 'GOAA membership referral rewards', kind: 'api', status: 'needs_account', serverSecretEnv: 'FIRSTPROMOTER_API_KEY', contract: ['POST /referral/track', 'POST /referral/reverse'], notes: ['20% membership rule only.'] },
]

/* ---------------------------------------------------------------- */
/* Admin RBAC matrix (preview)                                        */
/* ---------------------------------------------------------------- */

export type AdminRole = 'review' | 'content' | 'finance' | 'system' | 'support'

export const ADMIN_ROLE_LABELS: Record<AdminRole, string> = {
  review: 'Review Admin',
  content: 'Content Admin',
  finance: 'Finance Admin',
  system: 'System Admin',
  support: 'Support Admin',
}

export const ADMIN_ROLE_CAN: Record<AdminRole, string[]> = {
  review: ['applications', 'ai review results', 'manual review', 'license lifecycle', 'agent access'],
  content: ['skills catalog', 'courses catalog', 'earning opportunities'],
  finance: ['referral rewards', 'subscriptions', 'payout preview'],
  system: ['third-party status', 'webhook deliveries', 'audit logs'],
  support: ['users and roles view', 'account status'],
}

export const ADMIN_ROLE_DENY: Record<AdminRole, string[]> = {
  review: ['finance', 'system secrets', 'content publishing'],
  content: ['finance', 'system secrets', 'manual review'],
  finance: ['credential documents', 'system secrets'],
  system: ['manual review decisions'],
  support: ['finance writes', 'secret values', 'role changes'],
}

export function roleCan(role: AdminRole, action: string): boolean {
  if (ADMIN_ROLE_DENY[role].some((d) => d && (action.includes(d) || d.includes(action)))) return false
  return ADMIN_ROLE_CAN[role].some((c) => action.includes(c) || c.includes(action)) || action === 'overview'
}
