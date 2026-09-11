/**
 * preview-business.ts — pure business-loop domain for the three-portal
 * candidate preview (phase 2).
 *
 * SCOPE
 *   One account, multiple roles. Everyone starts as a customer. After the
 *   admin approves the license application the SAME account can be granted
 *   agent access; activation (one-time link + self-set password) opens the
 *   Agent Portal. No second, unlinked account is ever created for the same
 *   person in this model.
 *
 *   The order loop is driven by REAL role boundaries — each step is only
 *   callable by the account that owns it:
 *     New Opportunity -> Agent Accepts -> Agent Estimates -> Agent Quotes
 *     -> CUSTOMER accepts or declines the quote
 *     -> In Progress -> Agent Uploads Deliverables
 *     -> CUSTOMER accepts or requests changes
 *     -> Agent Issues Invoice -> CUSTOMER pays -> Completed
 *   Customer acceptance/payment functions verify the caller's email equals
 *   matter.clientEmail; agent functions verify the agent owns the matter.
 *   No "simulate client" shortcut exists in this module or in any UI.
 *   Every transition writes an audit line (actor + action + detail), so
 *   invoices, payments and order completion remain auditable in the demo.
 *
 *   Admin console actions are guarded by role matrices. Approval /
 *   supplement / reject / suspend / expiry / agent-access opening / client
 *   assignment / refunds and settlements are ADMIN-ONLY operations in this
 *   module; the customer and agent modules expose no equivalent.
 *
 * BOUNDARIES
 *   - The $99/month subscription only gates paid features. It never
 *     replaces license review, never grants agent identity, and pausing it
 *     never touches license or application state.
 *   - Ordinary driver licenses are accepted as identity documents but are
 *     never auto-promoted to a professional agent category.
 *   - Photos, uploads, invoices, payments and referral rewards are
 *     fictional, simulated metadata only. Nothing real is created.
 */

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

export type AccountRole = 'customer' | 'agent'
export type AgentAccessState = 'none' | 'granted' | 'activated'
export type SubscriptionStatus = 'active' | 'paused'

export interface AccountRecord {
  email: string
  displayName: string
  roles: AccountRole[]
  agentAccess: AgentAccessState
  agentUsername: string | null
  activatedAt: string | null
  passwordSetAt: string | null
  subscription: { plan: 'premium-99'; status: SubscriptionStatus; pausedAt: string | null }
  createdAt: string
}

export type MatterStage =
  | 'opportunity'
  | 'accepted'
  | 'estimate_prepared'
  | 'quote_awaiting_accept'
  | 'quote_declined'
  | 'in_progress'
  | 'deliverables_uploaded'
  | 'work_awaiting_accept'
  | 'rework_requested'
  | 'work_accepted'
  | 'invoice_issued'
  | 'paid'
  | 'completed'

export const MATTER_FLOW: MatterStage[] = [
  'opportunity',
  'accepted',
  'estimate_prepared',
  'quote_awaiting_accept',
  'quote_declined',
  'in_progress',
  'deliverables_uploaded',
  'work_awaiting_accept',
  'rework_requested',
  'work_accepted',
  'invoice_issued',
  'paid',
  'completed',
]

export interface AuditItem {
  at: string
  actorRole: 'agent' | 'customer' | 'admin' | 'system'
  actorLabel: string
  action: string
  detail: string
}

export interface DeliverableMeta {
  filename: string
  mimeType: string
  sizeBytes: number
  uploadedAt: string
}

export interface Matter {
  id: string
  agentEmail: string
  clientName: string
  clientEmail: string
  title: string
  category: string
  stage: MatterStage
  quoteAmountUsd: number | null
  deliverables: DeliverableMeta[]
  exception: { note: string; at: string } | null
  createdAt: string
  updatedAt: string
  audit: AuditItem[]
}

export interface Opportunity {
  id: string
  title: string
  clientName: string
  clientEmail: string
  category: string
  feeRange: string
  status: 'open' | 'accepted'
  createdAt: string
}

export interface Invoice {
  id: string
  number: string
  matterId: string
  agentEmail: string
  amountUsd: number
  status: 'issued' | 'paid' | 'refund_requested' | 'refund_approved'
  issuedAt: string
  paidAt: string | null
  refundRequestedAt: string | null
  refundNote: string | null
}

export interface PaymentRecord {
  id: string
  invoiceId: string
  amountUsd: number
  provider: 'card'
  receivedAt: string
}

export type AdminRole =
  | 'super_admin'
  | 'review_admin'
  | 'operations_admin'
  | 'finance_admin'
  | 'content_admin'
  | 'support_admin'
  | 'integration_admin'

export const ADMIN_ROLES: { id: AdminRole; label: string }[] = [
  { id: 'super_admin', label: 'Super Admin' },
  { id: 'review_admin', label: 'Review Admin' },
  { id: 'operations_admin', label: 'Operations Admin' },
  { id: 'finance_admin', label: 'Finance Admin' },
  { id: 'content_admin', label: 'Content Admin' },
  { id: 'support_admin', label: 'Support Admin' },
  { id: 'integration_admin', label: 'Integration Admin' },
]

export type AdminActionId =
  | 'approve_application'
  | 'request_supplement'
  | 'reject_application'
  | 'suspend_agent'
  | 'mark_expired'
  | 'open_agent_access'
  | 'assign_client'
  | 'transfer_client'
  | 'handle_order_exception'
  | 'approve_refund'
  | 'approve_settlement'
  | 'manage_content'
  | 'manage_plans'
  | 'manage_referrals'
  | 'manage_integrations'

export const ADMIN_ACTIONS: { id: AdminActionId; label: string }[] = [
  { id: 'approve_application', label: 'Approve application' },
  { id: 'request_supplement', label: 'Request supplement' },
  { id: 'reject_application', label: 'Reject application' },
  { id: 'suspend_agent', label: 'Suspend agent license' },
  { id: 'mark_expired', label: 'Mark license expired' },
  { id: 'open_agent_access', label: 'Open agent access' },
  { id: 'assign_client', label: 'Assign client to agent' },
  { id: 'transfer_client', label: 'Transfer client matter' },
  { id: 'handle_order_exception', label: 'Handle order exception' },
  { id: 'approve_refund', label: 'Approve refund' },
  { id: 'approve_settlement', label: 'Approve settlement' },
  { id: 'manage_content', label: 'Manage marketplace content' },
  { id: 'manage_plans', label: 'Manage plans & subscriptions' },
  { id: 'manage_referrals', label: 'Manage referral rewards' },
  { id: 'manage_integrations', label: 'Manage AI & third-party integrations' },
]

export const ADMIN_SECTIONS: { id: string; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'users', label: 'Users & Agents' },
  { id: 'applications', label: 'Applications & Licenses' },
  { id: 'leads', label: 'Leads & Opportunities' },
  { id: 'matters', label: 'Matters & Orders' },
  { id: 'estimates', label: 'Estimates & Deliverables' },
  { id: 'invoices', label: 'Invoices & Payments' },
  { id: 'skills', label: 'Skills Marketplace' },
  { id: 'courses', label: 'Licensing Courses' },
  { id: 'earnings', label: 'Earning Opportunities' },
  { id: 'plans', label: 'Plans & Subscriptions' },
  { id: 'referrals', label: 'Referral Rewards' },
  { id: 'integrations', label: 'AI & Third-party Integrations' },
  { id: 'roles', label: 'Roles & Permissions' },
  { id: 'risk', label: 'Risk & Audit' },
]

export const ADMIN_ROLE_ACTIONS: Record<AdminRole, AdminActionId[]> = {
  super_admin: ADMIN_ACTIONS.map((a) => a.id),
  review_admin: ['approve_application', 'request_supplement', 'reject_application', 'suspend_agent', 'mark_expired'],
  operations_admin: ['open_agent_access', 'assign_client', 'transfer_client', 'handle_order_exception', 'manage_referrals'],
  finance_admin: ['approve_refund', 'approve_settlement', 'manage_plans'],
  content_admin: ['manage_content', 'manage_referrals'],
  support_admin: ['open_agent_access', 'handle_order_exception', 'manage_plans'],
  integration_admin: ['manage_integrations'],
}

export const PAID_FEATURE_KEYS = ['ai_assistant', 'payments_earnings'] as const
export type PaidFeatureKey = (typeof PAID_FEATURE_KEYS)[number]
export const PAID_FEATURE_LABELS: Record<PaidFeatureKey, string> = {
  ai_assistant: 'AI Assistant',
  payments_earnings: 'Payments & Earnings',
}

export interface BusinessState {
  version: 1
  sessionEmail: string | null
  accounts: AccountRecord[]
  opportunities: Opportunity[]
  matters: Matter[]
  invoices: Invoice[]
  payments: PaymentRecord[]
  adminRole: AdminRole
  audit: AuditItem[]
}

/* ------------------------------------------------------------------ */
/* Pure helpers                                                        */
/* ------------------------------------------------------------------ */

export function adminCan(role: AdminRole, action: AdminActionId): boolean {
  if (role === 'super_admin') return true
  return (ADMIN_ROLE_ACTIONS[role] ?? []).includes(action)
}

export function accountFor(state: BusinessState, email: string | null | undefined): AccountRecord | undefined {
  if (!email) return undefined
  return state.accounts.find((a) => a.email === email)
}

export function accountRoles(state: BusinessState, email: string | null | undefined): AccountRole[] {
  return accountFor(state, email)?.roles ?? []
}

export function sessionAccount(state: BusinessState): AccountRecord | undefined {
  return accountFor(state, state.sessionEmail)
}

export function agentIdentityOpen(account: AccountRecord | undefined): boolean {
  return Boolean(account && account.roles.includes('agent') && account.agentAccess === 'activated')
}

export function paidFeatureOpen(state: BusinessState, email: string | null | undefined, feature: PaidFeatureKey): boolean {
  const acc = accountFor(state, email)
  if (!agentIdentityOpen(acc)) return false
  return acc!.subscription.status === 'active'
}

export function mattersVisibleToAgent(state: BusinessState, email: string | null | undefined): Matter[] {
  return state.matters
    .filter((m) => m.agentEmail === email)
    .slice()
    .sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1))
}

export function visibleMatter(state: BusinessState, email: string | null | undefined, matterId: string): Matter | undefined {
  const m = state.matters.find((x) => x.id === matterId)
  if (!m || m.agentEmail !== email) return undefined
  return m
}

export function agentDeniedReason(state: BusinessState, email: string | null | undefined): string | null {
  const acc = accountFor(state, email)
  if (!acc) return 'No account is linked to this preview session.'
  if (acc.agentAccess === 'none') return 'Agent access has not been granted. An admin must open it after approval.'
  if (acc.agentAccess === 'granted') return 'Agent access is granted but not activated. Open the one-time activation link and set your password first.'
  if (!acc.roles.includes('agent')) return 'The agent role is missing from this account.'
  return null
}

export function deriveAgentUsername(displayName: string): string {
  const base = displayName.toLowerCase().replace(/[^a-z0-9]+/g, '.').replace(/^\.+|\.+$/g, '').replace(/\.{2,}/g, '.')
  return `${base}.preview`
}

/* ------------------------------------------------------------------ */
/* Result wrapper                                                      */
/* ------------------------------------------------------------------ */

export type OpResult =
  | { ok: true; state: BusinessState }
  | { ok: false; error: string; state: BusinessState }

function err(state: BusinessState, error: string): OpResult {
  return { ok: false, error, state }
}

/** Append a deny audit line (actor + blocked action, never a secret value)
 *  so allowed and refused admin actions are both observable. */
function deniedAudit(state: BusinessState, actorRole: AdminRole, action: AdminActionId): BusinessState {
  return {
    ...state,
    audit: [...state.audit, { at: new Date().toISOString(), actorRole: 'admin', actorLabel: actorRole, action: 'admin.denied', detail: `${actorRole} blocked from ${action}.` }],
  }
}

/* ------------------------------------------------------------------ */
/* Session & account actions                                           */
/* ------------------------------------------------------------------ */

export function signIn(state: BusinessState, email: string): OpResult {
  if (!accountFor(state, email)) return err(state, `No account exists for ${email}. Register first.`)
  return { ok: true, state: { ...state, sessionEmail: email } }
}

export function signOut(state: BusinessState): OpResult {
  return { ok: true, state: { ...state, sessionEmail: null } }
}

export function registerAccount(state: BusinessState, opts: { email: string; displayName: string }): OpResult {
  const email = opts.email.trim().toLowerCase()
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return err(state, 'A valid demo email is required.')
  if (!opts.displayName.trim()) return err(state, 'A display name is required.')
  if (accountFor(state, email)) return err(state, `${email} already exists. Sign in instead of creating a duplicate account.`)
  const account: AccountRecord = {
    email,
    displayName: opts.displayName.trim(),
    roles: ['customer'],
    agentAccess: 'none',
    agentUsername: null,
    activatedAt: null,
    passwordSetAt: null,
    subscription: { plan: 'premium-99', status: 'active', pausedAt: null },
    createdAt: '2026-09-08T09:00:00.000Z',
  }
  const next: BusinessState = {
    ...state,
    accounts: [...state.accounts, account],
    audit: [...state.audit, { at: '2026-09-08T09:00:00.000Z', actorRole: 'system', actorLabel: 'system', action: 'account.registered', detail: `${email} created with the customer role.` }],
  }
  return { ok: true, state: next }
}

/** ADMIN ONLY — opens agent access on an existing account. Never creates a
 *  second account. */
export function openAgentAccess(state: BusinessState, opts: { email: string; actorRole: AdminRole }): OpResult {
  if (!adminCan(opts.actorRole, 'open_agent_access')) {
    return err(deniedAudit(state, opts.actorRole, 'open_agent_access'), `${opts.actorRole} cannot open agent access. Super Admin, Operations Admin or Support Admin required.`)
  }
  const acc = accountFor(state, opts.email)
  if (!acc) return err(state, `Account ${opts.email} not found.`)
  if (acc.agentAccess !== 'none') return err(state, `${opts.email} already has agent access granted or activated.`)
  const next: BusinessState = {
    ...state,
    accounts: state.accounts.map((a) => (a.email === acc.email ? { ...acc, agentAccess: 'granted' as const } : a)),
    audit: [...state.audit, { at: '2026-09-08T12:05:00.000Z', actorRole: 'admin', actorLabel: opts.actorRole, action: 'agent_access.opened', detail: `Agent access opened on ${acc.email}; no duplicate account created.` }],
  }
  return { ok: true, state: next }
}

/** SELF-SERVICE — consumes the one-time activation link and sets the
 *  user-chosen password. No plaintext password is generated or stored;
 *  only a passwordSetAt marker is recorded. */
export function setPasswordAndActivate(state: BusinessState, opts: { email: string; password: string }): OpResult {
  const acc = accountFor(state, opts.email)
  if (!acc) return err(state, `Account ${opts.email} not found.`)
  if (acc.agentAccess !== 'granted') return err(state, 'Agent access must be opened before activation is possible.')
  if (opts.password.length < 4) return err(state, 'Password must be at least 4 characters (simulated; never stored).')
  if (acc.roles.includes('agent')) return err(state, 'This account is already activated as an agent.')
  const updated: AccountRecord = {
    ...acc,
    roles: ['customer', 'agent'],
    agentAccess: 'activated',
    agentUsername: deriveAgentUsername(acc.displayName),
    activatedAt: '2026-09-08T12:30:00.000Z',
    passwordSetAt: '2026-09-08T12:30:00.000Z',
  }
  const next: BusinessState = {
    ...state,
    accounts: state.accounts.map((a) => (a.email === acc.email ? updated : a)),
    audit: [...state.audit, { at: '2026-09-08T12:30:00.000Z', actorRole: 'system', actorLabel: acc.email, action: 'agent.activated', detail: `Agent username ${updated.agentUsername} activated on the existing customer account.` }],
  }
  return { ok: true, state: next }
}

export function setSubscriptionStatus(state: BusinessState, email: string, status: SubscriptionStatus): OpResult {
  const acc = accountFor(state, email)
  if (!acc) return err(state, `Account ${email} not found.`)
  const next: BusinessState = {
    ...state,
    accounts: state.accounts.map((a) => (a.email === acc.email ? { ...acc, subscription: { ...acc.subscription, status, pausedAt: status === 'paused' ? '2026-09-08T13:00:00.000Z' : null } } : a)),
    audit: [...state.audit, { at: '2026-09-08T13:00:00.000Z', actorRole: 'system', actorLabel: email, action: `subscription.${status}`, detail: `$99 premium subscription ${status}; license state unchanged.` }],
  }
  return { ok: true, state: next }
}

/* ------------------------------------------------------------------ */
/* Agent order loop                                                    */
/* ------------------------------------------------------------------ */

type GuardedMatter<T> = { ok: true; matter: Matter } | { ok: false; error: string }

function guardMatter(state: BusinessState, email: string | null | undefined, matterId: string, allowedStages: MatterStage[]): GuardedMatter<never> {
  const acc = accountFor(state, email)
  if (!acc) return { ok: false, error: 'No account is linked to this preview session.' }
  if (!agentIdentityOpen(acc)) return { ok: false, error: 'Agent identity is not activated for this account.' }
  const m = state.matters.find((x) => x.id === matterId)
  if (!m) return { ok: false, error: `Matter ${matterId} not found.` }
  if (m.agentEmail !== acc.email) return { ok: false, error: 'An agent can only work matters assigned to their own account.' }
  if (!allowedStages.includes(m.stage)) return { ok: false, error: `Stage ${m.stage} does not allow this action.` }
  return { ok: true, matter: m }
}

const T = (step: number): string => `2026-09-08T12:${String(step).padStart(2, '0')}:00.000Z`

function transitionMatter(state: BusinessState, email: string | null | undefined, matterId: string, allowed: MatterStage[], action: string, detail: string, apply: (m: Matter) => void, step: number): OpResult {
  const g = guardMatter(state, email, matterId, allowed)
  if (!g.ok) return err(state, g.error)
  const matter = g.matter
  const nextMatter: Matter = {
    ...matter,
    audit: [...matter.audit, { at: T(step), actorRole: 'agent', actorLabel: email ?? 'agent', action, detail }],
    updatedAt: T(step),
  }
  apply(nextMatter)
  const next = { ...state, matters: state.matters.map((x) => (x.id === matterId ? nextMatter : x)) }
  return { ok: true, state: next }
}

export function agentAcceptOpportunity(state: BusinessState, opts: { email: string | null | undefined; opportunityId: string }): OpResult {
  const acc = accountFor(state, opts.email)
  if (!acc) return err(state, 'No account is linked to this preview session.')
  if (!agentIdentityOpen(acc)) return err(state, 'Agent identity is not activated for this account.')
  const opp = state.opportunities.find((o) => o.id === opts.opportunityId && o.status === 'open')
  if (!opp) return err(state, `Open opportunity ${opts.opportunityId} not found.`)
  const matter: Matter = {
    id: `mt-${Date.now().toString(36)}`,
    agentEmail: acc.email,
    clientName: opp.clientName,
    clientEmail: opp.clientEmail,
    title: opp.title,
    category: opp.category,
    stage: 'accepted',
    quoteAmountUsd: null,
    deliverables: [],
    exception: null,
    createdAt: T(40),
    updatedAt: T(40),
    audit: [{ at: T(40), actorRole: 'agent', actorLabel: acc.email, action: 'opportunity.accepted', detail: `Accepted ${opp.id} — ${opp.title}` }],
  }
  const next: BusinessState = {
    ...state,
    opportunities: state.opportunities.map((o) => (o.id === opp.id ? { ...o, status: 'accepted' as const } : o)),
    matters: [...state.matters, matter],
  }
  return { ok: true, state: next }
}

export function agentPrepareEstimate(state: BusinessState, opts: { email: string | null | undefined; matterId: string; amountUsd: number }): OpResult {
  if (!(opts.amountUsd > 0)) return err(state, 'A positive estimate amount is required.')
  return transitionMatter(state, opts.email, opts.matterId, ['accepted', 'estimate_prepared'], 'estimate.prepared', `Estimate $${opts.amountUsd.toFixed(2)} prepared.`, (m) => {
    m.stage = 'estimate_prepared'
    m.quoteAmountUsd = opts.amountUsd
  }, 41)
}

export function agentSendQuote(state: BusinessState, opts: { email: string | null | undefined; matterId: string }): OpResult {
  return transitionMatter(state, opts.email, opts.matterId, ['estimate_prepared'], 'quote.sent', 'Quote sent to client for acceptance.', (m) => {
    m.stage = 'quote_awaiting_accept'
  }, 42)
}

/* ------------------------------------------------------------------ */
/* Customer-side order actions (real role boundary, never simulated)   */
/* An Agent/Admin UI must not expose these; only the signed-in account */
/* whose email matches matter.clientEmail can perform them.            */
/* ------------------------------------------------------------------ */

function customerGuard(state: BusinessState, email: string | null | undefined, matterId: string, from: MatterStage[]): { ok: true; matter: Matter } | { ok: false; error: string } {
  const acc = accountFor(state, email)
  if (!acc) return { ok: false, error: 'No account is linked to this preview session.' }
  if (!acc.roles.includes('customer')) return { ok: false, error: 'A customer role is required for this action.' }
  const matter = state.matters.find((m) => m.id === matterId)
  if (!matter) return { ok: false, error: `Matter ${matterId} not found.` }
  if (matter.clientEmail !== acc.email) return { ok: false, error: 'This matter belongs to another client.' }
  if (!from.includes(matter.stage)) return { ok: false, error: `Stage ${matter.stage} does not allow this action.` }
  return { ok: true, matter }
}

export function customerAcceptsQuote(state: BusinessState, opts: { email: string | null | undefined; matterId: string }): OpResult {
  const g = customerGuard(state, opts.email, opts.matterId, ['quote_awaiting_accept'])
  if (!g.ok) return err(state, g.error)
  const matter = g.matter
  const nextMatter: Matter = {
    ...matter,
    stage: 'in_progress',
    updatedAt: T(43),
    audit: [...matter.audit, { at: T(43), actorRole: 'customer', actorLabel: matter.clientEmail, action: 'quote.accepted', detail: `${matter.clientEmail} accepted the quote; work may begin.` }],
  }
  return { ok: true, state: { ...state, matters: state.matters.map((x) => (x.id === matter.id ? nextMatter : x)) } }
}

export function customerRejectsQuote(state: BusinessState, opts: { email: string | null | undefined; matterId: string }): OpResult {
  const g = customerGuard(state, opts.email, opts.matterId, ['quote_awaiting_accept'])
  if (!g.ok) return err(state, g.error)
  const matter = g.matter
  const nextMatter: Matter = {
    ...matter,
    stage: 'quote_declined',
    updatedAt: T(43),
    audit: [...matter.audit, { at: T(43), actorRole: 'customer', actorLabel: matter.clientEmail, action: 'quote.declined', detail: `${matter.clientEmail} declined the quote.` }],
  }
  return { ok: true, state: { ...state, matters: state.matters.map((x) => (x.id === matter.id ? nextMatter : x)) } }
}

export function agentUploadDeliverable(state: BusinessState, opts: { email: string | null | undefined; matterId: string; filename: string; mimeType: string; sizeBytes: number }): OpResult {
  return transitionMatter(state, opts.email, opts.matterId, ['in_progress', 'deliverables_uploaded', 'work_awaiting_accept', 'rework_requested'], 'deliverable.uploaded', `Uploaded ${opts.filename} (metadata only).`, (m) => {
    m.deliverables.push({ filename: opts.filename, mimeType: opts.mimeType, sizeBytes: opts.sizeBytes, uploadedAt: T(46) })
    m.stage = 'deliverables_uploaded'
  }, 46)
}

export function agentRequestWorkAcceptance(state: BusinessState, opts: { email: string | null | undefined; matterId: string }): OpResult {
  return transitionMatter(state, opts.email, opts.matterId, ['deliverables_uploaded'], 'work.awaiting_accept', 'Requested client acceptance of deliverables.', (m) => {
    m.stage = 'work_awaiting_accept'
  }, 47)
}

export function customerAcceptsWork(state: BusinessState, opts: { email: string | null | undefined; matterId: string }): OpResult {
  const g = customerGuard(state, opts.email, opts.matterId, ['work_awaiting_accept'])
  if (!g.ok) return err(state, g.error)
  const matter = g.matter
  const nextMatter: Matter = {
    ...matter,
    stage: 'work_accepted',
    updatedAt: T(48),
    audit: [...matter.audit, { at: T(48), actorRole: 'customer', actorLabel: matter.clientEmail, action: 'work.accepted', detail: `${matter.clientEmail} accepted the deliverables; invoicing may proceed.` }],
  }
  return { ok: true, state: { ...state, matters: state.matters.map((x) => (x.id === matter.id ? nextMatter : x)) } }
}

export function customerRequestsWorkChanges(state: BusinessState, opts: { email: string | null | undefined; matterId: string; note: string }): OpResult {
  const g = customerGuard(state, opts.email, opts.matterId, ['work_awaiting_accept', 'deliverables_uploaded'])
  if (!g.ok) return err(state, g.error)
  const matter = g.matter
  const nextMatter: Matter = {
    ...matter,
    stage: 'rework_requested',
    updatedAt: T(48),
    audit: [...matter.audit, { at: T(48), actorRole: 'customer', actorLabel: matter.clientEmail, action: 'work.revision_requested', detail: `${matter.clientEmail} requested changes: ${opts.note}` }],
  }
  return { ok: true, state: { ...state, matters: state.matters.map((x) => (x.id === matter.id ? nextMatter : x)) } }
}

export function agentIssueInvoice(state: BusinessState, opts: { email: string | null | undefined; matterId: string }): OpResult {
  const g = guardMatter(state, opts.email, opts.matterId, ['work_accepted'])
  if (!g.ok) return err(state, g.error)
  const matter = g.matter
  if (!(matter.quoteAmountUsd && matter.quoteAmountUsd > 0)) return err(state, 'A quoted amount is required before invoicing.')
  const number = `INV-2026-${String(state.invoices.length + 1).padStart(4, '0')}`
  const nextMatter: Matter = {
    ...matter,
    stage: 'invoice_issued',
    updatedAt: T(49),
    audit: [...matter.audit, { at: T(49), actorRole: 'agent', actorLabel: opts.email ?? 'agent', action: 'invoice.issued', detail: `${number} issued for $${matter.quoteAmountUsd.toFixed(2)}.` }],
  }
  const invoice: Invoice = {
    id: `inv-${matter.id}`,
    number,
    matterId: matter.id,
    agentEmail: matter.agentEmail,
    amountUsd: matter.quoteAmountUsd,
    status: 'issued',
    issuedAt: T(49),
    paidAt: null,
    refundRequestedAt: null,
    refundNote: null,
  }
  const next: BusinessState = {
    ...state,
    matters: state.matters.map((x) => (x.id === matter.id ? nextMatter : x)),
    invoices: [...state.invoices, invoice],
  }
  return { ok: true, state: next }
}

export function customerPaysInvoice(state: BusinessState, opts: { email: string | null | undefined; invoiceId: string }): OpResult {
  const acc = accountFor(state, opts.email)
  if (!acc) return err(state, 'No account is linked to this preview session.')
  if (!acc.roles.includes('customer')) return err(state, 'A customer role is required to pay an invoice.')
  const inv = state.invoices.find((i) => i.id === opts.invoiceId)
  if (!inv) return err(state, `Invoice ${opts.invoiceId} not found.`)
  const matter = state.matters.find((m) => m.id === inv.matterId)
  if (!matter || matter.clientEmail !== acc.email) return err(state, 'This invoice belongs to another client.')
  if (inv.status !== 'issued') return err(state, 'Only an issued invoice can be paid.')
  const payment: PaymentRecord = { id: `pay-${inv.id}`, invoiceId: inv.id, amountUsd: inv.amountUsd, provider: 'card', receivedAt: T(50) }
  const next: BusinessState = {
    ...state,
    invoices: state.invoices.map((i) => (i.id === inv.id ? { ...i, status: 'paid' as const, paidAt: T(50) } : i)),
    matters: state.matters.map((m) => (m.id === matter.id ? { ...m, stage: 'paid' as const, updatedAt: T(50), audit: [...m.audit, { at: T(50), actorRole: 'customer', actorLabel: matter.clientEmail, action: 'payment.received', detail: `${inv.number} paid in full by ${matter.clientEmail}.` }] } : m)),
    payments: [...state.payments, payment],
    audit: [...state.audit, { at: T(50), actorRole: 'customer', actorLabel: matter.clientEmail, action: 'payment.received', detail: `${inv.number} paid in full by ${matter.clientEmail}.` }],
  }
  return { ok: true, state: next }
}

export function agentCompleteOrder(state: BusinessState, opts: { email: string | null | undefined; matterId: string }): OpResult {
  return transitionMatter(state, opts.email, opts.matterId, ['paid'], 'order.completed', 'Order marked completed after payment.', (m) => {
    m.stage = 'completed'
  }, 51)
}

/* ------------------------------------------------------------------ */
/* Admin operations on matters, invoices, payments                     */
/* ------------------------------------------------------------------ */

export function adminAssignMatter(state: BusinessState, opts: { actorRole: AdminRole; matterId: string; toEmail: string }): OpResult {
  if (!adminCan(opts.actorRole, 'assign_client') && !adminCan(opts.actorRole, 'transfer_client')) {
    return err(deniedAudit(state, opts.actorRole, 'assign_client'), `${opts.actorRole} cannot assign clients.`)
  }
  const m = state.matters.find((x) => x.id === opts.matterId)
  if (!m) return err(state, `Matter ${opts.matterId} not found.`)
  if (!accountFor(state, opts.toEmail)) return err(state, `Agent ${opts.toEmail} not found.`)
  const nextMatter: Matter = { ...m, agentEmail: opts.toEmail, updatedAt: T(10), audit: [...m.audit, { at: T(10), actorRole: 'admin', actorLabel: opts.actorRole, action: 'client.assigned', detail: `Assigned to ${opts.toEmail}.` }] }
  const next: BusinessState = {
    ...state,
    matters: state.matters.map((x) => (x.id === m.id ? nextMatter : x)),
    audit: [...state.audit, { at: T(10), actorRole: 'admin', actorLabel: opts.actorRole, action: 'client.assigned', detail: `Matter ${m.id} assigned to ${opts.toEmail}.` }],
  }
  return { ok: true, state: next }
}

export function adminHandleOrderException(state: BusinessState, opts: { actorRole: AdminRole; matterId: string; note: string }): OpResult {
  if (!adminCan(opts.actorRole, 'handle_order_exception')) return err(deniedAudit(state, opts.actorRole, 'handle_order_exception'), `${opts.actorRole} cannot handle order exceptions.`)
  const m = state.matters.find((x) => x.id === opts.matterId)
  if (!m) return err(state, `Matter ${opts.matterId} not found.`)
  const nextMatter: Matter = { ...m, exception: { note: opts.note, at: T(15) }, updatedAt: T(15), audit: [...m.audit, { at: T(15), actorRole: 'admin', actorLabel: opts.actorRole, action: 'order.exception_handled', detail: opts.note }] }
  const next: BusinessState = {
    ...state,
    matters: state.matters.map((x) => (x.id === m.id ? nextMatter : x)),
    audit: [...state.audit, { at: T(15), actorRole: 'admin', actorLabel: opts.actorRole, action: 'order.exception_handled', detail: `Matter ${m.id} — ${opts.note}` }],
  }
  return { ok: true, state: next }
}

export function adminApproveRefund(state: BusinessState, opts: { actorRole: AdminRole; invoiceId: string; reason: string }): OpResult {
  if (!adminCan(opts.actorRole, 'approve_refund')) return err(deniedAudit(state, opts.actorRole, 'approve_refund'), `${opts.actorRole} cannot approve refunds.`)
  const inv = state.invoices.find((i) => i.id === opts.invoiceId)
  if (!inv) return err(state, `Invoice ${opts.invoiceId} not found.`)
  if (inv.status !== 'refund_requested') return err(state, 'Only a refund request can be approved.')
  const next: BusinessState = {
    ...state,
    invoices: state.invoices.map((i) => (i.id === inv.id ? { ...i, status: 'refund_approved' as const, refundNote: opts.reason } : i)),
    audit: [...state.audit, { at: T(20), actorRole: 'admin', actorLabel: opts.actorRole, action: 'refund.approved', detail: `${inv.number} refund approved — ${opts.reason}` }],
  }
  return { ok: true, state: next }
}

export function adminApproveSettlement(state: BusinessState, opts: { actorRole: AdminRole; batch: string; amountUsd: number }): OpResult {
  if (!adminCan(opts.actorRole, 'approve_settlement')) return err(deniedAudit(state, opts.actorRole, 'approve_settlement'), `${opts.actorRole} cannot approve settlements.`)
  const next: BusinessState = {
    ...state,
    audit: [...state.audit, { at: T(25), actorRole: 'admin', actorLabel: opts.actorRole, action: 'settlement.approved', detail: `${opts.batch} settlement of $${opts.amountUsd.toFixed(2)} approved.` }],
  }
  return { ok: true, state: next }
}

/* ------------------------------------------------------------------ */
/* Fixtures (all fictional)                                            */
/* ------------------------------------------------------------------ */

export type BusinessSeedKind =
  | 'fresh'
  | 'under_review'
  | 'supplement'
  | 'approved_ready'
  | 'activated'
  | 'suspended'
  | 'rejected'
  | 'paused'

const JORDAN_EMAIL = 'jordan.rivera.preview@example.com'
const NADIA_EMAIL = 'nadia.martin.preview@example.com'
const AVA_EMAIL = 'ava.nguyen.preview@example.com'
const CARLOS_EMAIL = 'carlos.perez.preview@example.com'

export const DEMO_AGENT_EMAIL = JORDAN_EMAIL

export function defaultBusinessState(): BusinessState {
  const base: BusinessState = {
    version: 1,
    sessionEmail: JORDAN_EMAIL,
    accounts: [
      {
        email: JORDAN_EMAIL,
        displayName: 'Jordan Rivera',
        roles: ['customer'],
        agentAccess: 'none',
        agentUsername: null,
        activatedAt: null,
        passwordSetAt: null,
        subscription: { plan: 'premium-99', status: 'active', pausedAt: null },
        createdAt: '2026-09-08T08:00:00.000Z',
      },
      {
        email: NADIA_EMAIL,
        displayName: 'Nadia Martin',
        roles: ['customer', 'agent'],
        agentAccess: 'activated',
        agentUsername: 'nadia.martin.preview',
        activatedAt: '2026-09-08T09:20:00.000Z',
        passwordSetAt: '2026-09-08T09:20:00.000Z',
        subscription: { plan: 'premium-99', status: 'active', pausedAt: null },
        createdAt: '2026-09-08T08:05:00.000Z',
      },
      {
        email: AVA_EMAIL,
        displayName: 'Ava Nguyen',
        roles: ['customer'],
        agentAccess: 'none',
        agentUsername: null,
        activatedAt: null,
        passwordSetAt: null,
        subscription: { plan: 'premium-99', status: 'active', pausedAt: null },
        createdAt: '2026-09-08T08:10:00.000Z',
      },
      {
        email: CARLOS_EMAIL,
        displayName: 'Carlos Perez',
        roles: ['customer', 'agent'],
        agentAccess: 'activated',
        agentUsername: 'carlos.perez.preview',
        activatedAt: '2026-09-08T09:35:00.000Z',
        passwordSetAt: '2026-09-08T09:35:00.000Z',
        subscription: { plan: 'premium-99', status: 'active', pausedAt: null },
        createdAt: '2026-09-08T08:15:00.000Z',
      },
    ],
    opportunities: [
      { id: 'opp-1001', title: 'Interior painting estimate — 3 rooms', clientName: 'Priya Raman', clientEmail: 'priya.raman.demo@example.com', category: 'Home services', feeRange: '$620–$980', status: 'open', createdAt: '2026-09-08T10:00:00.000Z' },
      { id: 'opp-1002', title: 'Weekly cleaning — senior home', clientName: 'Eleanor Frost', clientEmail: 'eleanor.frost.demo@example.com', category: 'Senior care', feeRange: '$180/week', status: 'open', createdAt: '2026-09-08T10:20:00.000Z' },
      { id: 'opp-1003', title: 'Rental inspection walkthrough', clientName: 'Sam Whitfield', clientEmail: 'sam.whitfield.demo@example.com', category: 'Real estate forms', feeRange: '$150 flat', status: 'open', createdAt: '2026-09-08T10:40:00.000Z' },
    ],
    matters: [
      {
        id: 'mt-2001',
        agentEmail: JORDAN_EMAIL,
        clientName: 'Dana Ortiz',
        clientEmail: 'dana.ortiz.demo@example.com',
        title: 'Deep clean before new tenant move-in',
        category: 'Home services',
        stage: 'in_progress',
        quoteAmountUsd: 320,
        deliverables: [],
        exception: null,
        createdAt: '2026-09-08T09:30:00.000Z',
        updatedAt: '2026-09-08T12:20:00.000Z',
        audit: [
          { at: '2026-09-08T11:00:00.000Z', actorRole: 'agent', actorLabel: JORDAN_EMAIL, action: 'opportunity.accepted', detail: 'Accepted opportunity opp-2001' },
          { at: '2026-09-08T11:10:00.000Z', actorRole: 'customer', actorLabel: 'eleanor.frost.demo@example.com', action: 'quote.accepted', detail: 'Client accepted the quote.' },
        ],
      },
      {
        id: 'mt-2002',
        agentEmail: JORDAN_EMAIL,
        clientName: 'Marcus Lee',
        clientEmail: 'marcus.lee.demo@example.com',
        title: 'Garage declutter & donation haul',
        category: 'Moving help',
        stage: 'invoice_issued',
        quoteAmountUsd: 480,
        deliverables: [{ filename: 'garage-haul-report.pdf', mimeType: 'application/pdf', sizeBytes: 51200, uploadedAt: '2026-09-08T12:30:00.000Z' }],
        exception: null,
        createdAt: '2026-09-08T09:10:00.000Z',
        updatedAt: '2026-09-08T12:40:00.000Z',
        audit: [
          { at: '2026-09-08T12:10:00.000Z', actorRole: 'customer', actorLabel: 'eleanor.frost.demo@example.com', action: 'work.accepted', detail: 'Client accepted the deliverables.' },
          { at: '2026-09-08T12:40:00.000Z', actorRole: 'agent', actorLabel: JORDAN_EMAIL, action: 'invoice.issued', detail: 'INV-2026-0001 issued for $480.00.' },
        ],
      },
      {
        id: 'mt-2003',
        agentEmail: JORDAN_EMAIL,
        clientName: 'Hana Kim',
        clientEmail: 'hana.kim.demo@example.com',
        title: 'Window washing — 12 windows',
        category: 'Home services',
        stage: 'completed',
        quoteAmountUsd: 210,
        deliverables: [{ filename: 'window-wash-complete.jpg', mimeType: 'image/jpeg', sizeBytes: 240100, uploadedAt: '2026-09-08T11:40:00.000Z' }],
        exception: null,
        createdAt: '2026-09-08T08:50:00.000Z',
        updatedAt: '2026-09-08T12:10:00.000Z',
        audit: [
          { at: '2026-09-08T12:00:00.000Z', actorRole: 'customer', actorLabel: 'eleanor.frost.demo@example.com', action: 'payment.received', detail: 'INV-2026-0000 paid in full.' },
          { at: '2026-09-08T12:10:00.000Z', actorRole: 'agent', actorLabel: JORDAN_EMAIL, action: 'order.completed', detail: 'Order marked completed after payment.' },
        ],
      },
      {
        id: 'mt-3001',
        agentEmail: NADIA_EMAIL,
        clientName: 'Terry Boone',
        clientEmail: 'terry.boone.demo@example.com',
        title: 'Bookkeeping cleanup for small bakery',
        category: 'Tax documents',
        stage: 'paid',
        quoteAmountUsd: 900,
        deliverables: [{ filename: 'ledger-cleanup.xlsx', mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', sizeBytes: 84000, uploadedAt: '2026-09-08T11:20:00.000Z' }],
        exception: null,
        createdAt: '2026-09-08T08:20:00.000Z',
        updatedAt: '2026-09-08T12:05:00.000Z',
        audit: [{ at: '2026-09-08T12:05:00.000Z', actorRole: 'customer', actorLabel: 'avery.wilson.demo@example.com', action: 'payment.received', detail: 'INV-2026-0002 paid in full.' }],
      },

      {
        id: 'mt-2101',
        agentEmail: CARLOS_EMAIL,
        clientName: 'Jordan Rivera',
        clientEmail: JORDAN_EMAIL,
        title: 'Move-out cleaning — 2 bedroom apartment',
        category: 'Home services',
        stage: 'quote_awaiting_accept',
        quoteAmountUsd: 150,
        deliverables: [],
        exception: null,
        createdAt: '2026-09-08T10:30:00.000Z',
        updatedAt: '2026-09-08T12:50:00.000Z',
        audit: [
          { at: '2026-09-08T10:31:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'opportunity.accepted', detail: 'Accepted opportunity opp-2101' },
          { at: '2026-09-08T10:40:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'estimate.prepared', detail: 'Estimate $150.00 prepared.' },
          { at: '2026-09-08T10:45:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'quote.sent', detail: 'Quote sent to client for acceptance.' },
        ],
      },
      {
        id: 'mt-2102',
        agentEmail: CARLOS_EMAIL,
        clientName: 'Jordan Rivera',
        clientEmail: JORDAN_EMAIL,
        title: 'Small office declutter and donation run',
        category: 'Home services',
        stage: 'work_awaiting_accept',
        quoteAmountUsd: 260,
        deliverables: [
          { filename: 'declutter-summary.pdf', mimeType: 'application/pdf', sizeBytes: 1200, uploadedAt: '2026-09-08T12:35:00.000Z' },
        ],
        exception: null,
        createdAt: '2026-09-08T10:50:00.000Z',
        updatedAt: '2026-09-08T12:55:00.000Z',
        audit: [
          { at: '2026-09-08T10:51:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'opportunity.accepted', detail: 'Accepted opportunity opp-2102' },
          { at: '2026-09-08T11:00:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'quote.sent', detail: 'Quote sent to client for acceptance.' },
          { at: '2026-09-08T11:10:00.000Z', actorRole: 'customer', actorLabel: JORDAN_EMAIL, action: 'quote.accepted', detail: 'jordan.rivera.preview@example.com accepted the quote; work may begin.' },
          { at: '2026-09-08T12:35:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'deliverable.uploaded', detail: 'Uploaded declutter-summary.pdf (metadata only).' },
          { at: '2026-09-08T12:40:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'work.awaiting_accept', detail: 'Requested client acceptance of deliverables.' },
        ],
      },
      {
        id: 'mt-2103',
        agentEmail: CARLOS_EMAIL,
        clientName: 'Jordan Rivera',
        clientEmail: JORDAN_EMAIL,
        title: 'Garage shelving install',
        category: 'Home services',
        stage: 'invoice_issued',
        quoteAmountUsd: 240,
        deliverables: [
          { filename: 'install-summary.pdf', mimeType: 'application/pdf', sizeBytes: 900, uploadedAt: '2026-09-08T13:00:00.000Z' },
        ],
        exception: null,
        createdAt: '2026-09-08T11:20:00.000Z',
        updatedAt: '2026-09-08T13:06:00.000Z',
        audit: [
          { at: '2026-09-08T11:21:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'opportunity.accepted', detail: 'Accepted opportunity opp-2103' },
          { at: '2026-09-08T11:25:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'quote.sent', detail: 'Quote sent to client for acceptance.' },
          { at: '2026-09-08T11:30:00.000Z', actorRole: 'customer', actorLabel: JORDAN_EMAIL, action: 'quote.accepted', detail: 'jordan.rivera.preview@example.com accepted the quote; work may begin.' },
          { at: '2026-09-08T12:45:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'deliverable.uploaded', detail: 'Uploaded install-summary.pdf (metadata only).' },
          { at: '2026-09-08T12:50:00.000Z', actorRole: 'customer', actorLabel: JORDAN_EMAIL, action: 'work.accepted', detail: 'jordan.rivera.preview@example.com accepted the deliverables; invoicing may proceed.' },
          { at: '2026-09-08T13:05:00.000Z', actorRole: 'agent', actorLabel: CARLOS_EMAIL, action: 'invoice.issued', detail: 'INV-2026-2103 issued for $240.00.' },
        ],
      },
    ],
    invoices: [
      { id: 'inv-mt-2103', number: 'INV-2026-2103', matterId: 'mt-2103', agentEmail: CARLOS_EMAIL, amountUsd: 240, status: 'issued', issuedAt: '2026-09-08T13:05:00.000Z', paidAt: null, refundRequestedAt: null, refundNote: null },
      { id: 'inv-mt-2003', number: 'INV-2026-0000', matterId: 'mt-2003', agentEmail: JORDAN_EMAIL, amountUsd: 210, status: 'paid', issuedAt: '2026-09-08T11:00:00.000Z', paidAt: '2026-09-08T12:00:00.000Z', refundRequestedAt: null, refundNote: null },
      { id: 'inv-mt-2002', number: 'INV-2026-0001', matterId: 'mt-2002', agentEmail: JORDAN_EMAIL, amountUsd: 480, status: 'issued', issuedAt: '2026-09-08T12:40:00.000Z', paidAt: null, refundRequestedAt: null, refundNote: null },
      { id: 'inv-mt-3001', number: 'INV-2026-0002', matterId: 'mt-3001', agentEmail: NADIA_EMAIL, amountUsd: 900, status: 'refund_requested', issuedAt: '2026-09-08T10:30:00.000Z', paidAt: '2026-09-08T12:00:00.000Z', refundRequestedAt: '2026-09-08T12:20:00.000Z', refundNote: null },
    ],
    payments: [
      { id: 'pay-inv-mt-2003', invoiceId: 'inv-mt-2003', amountUsd: 210, provider: 'card', receivedAt: '2026-09-08T12:00:00.000Z' },
      { id: 'pay-inv-mt-3001', invoiceId: 'inv-mt-3001', amountUsd: 900, provider: 'card', receivedAt: '2026-09-08T12:00:00.000Z' },
    ],
    adminRole: 'super_admin',
    audit: [
      { at: '2026-09-08T12:00:00.000Z', actorRole: 'system', actorLabel: 'system', action: 'demo.seeded', detail: 'Preview business world seeded with fictional accounts, matters and invoices.' },
    ],
  }
  return base
}

export function seedBusinessState(kind: BusinessSeedKind): BusinessState {
  const base = defaultBusinessState()
  const jordan = JORDAN_EMAIL
  let next: BusinessState = base
  const activeKinds: BusinessSeedKind[] = ['activated', 'suspended', 'paused']
  if (activeKinds.includes(kind)) {
    const active: AccountRecord = {
      ...base.accounts.find((a) => a.email === jordan)!,
      roles: ['customer', 'agent'],
      agentAccess: 'activated',
      agentUsername: deriveAgentUsername('Jordan Rivera'),
      activatedAt: '2026-09-08T12:30:00.000Z',
      passwordSetAt: '2026-09-08T12:30:00.000Z',
    }
    next = { ...next, accounts: next.accounts.map((a) => (a.email === jordan ? active : a)) }
  }
  if (kind === 'approved_ready') {
    const granted: AccountRecord = {
      ...base.accounts.find((a) => a.email === jordan)!,
      agentAccess: 'granted',
    }
    next = { ...next, accounts: next.accounts.map((a) => (a.email === jordan ? granted : a)) }
  }
  if (kind === 'paused') {
    const r = setSubscriptionStatus(next, jordan, 'paused')
    if (r.ok) next = r.state
  }
  return next
}
