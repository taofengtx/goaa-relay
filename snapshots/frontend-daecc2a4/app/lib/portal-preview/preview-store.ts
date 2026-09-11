/**
 * preview-store.ts — PROTOTYPE unified state layer for the three-portal
 * candidate preview (customer / agent / admin).
 *
 * WHY THIS LAYER EXISTS
 *   The three portal-preview routes share one simulated data flow:
 *     customer submits -> system/AI reviews (suggestions only) -> admin
 *     decides -> customer reads the RESULT -> agent gate opens after
 *     approved + activated.
 *
 * BOUNDARIES (enforced here and by the page components)
 *   - A CUSTOMER can only: start/save a draft, attach simulated photos,
 *     submit, resubmit after a supplement request, activate through the
 *     one-time link, and READ status. A customer NEVER writes an admin
 *     conclusion, license state, agent permission or account-opening
 *     decision. There is no customer-side admin action exported here.
 *   - ADMIN actions live in this layer too (the page calls adminDecision /
 *     adminLifecycle), because this layer plays the role the server +
 *     database will play in production. The admin portal page is the only
 *     place those functions are wired to buttons.
 *   - AI suggestions are read-only until an admin decides; conflict /
 *     high-risk applications block one-click approval.
 *   - License approval decides agent identity; the $99/month subscription
 *     only gates paid features and never grants identity.
 *   - Photos are simulated metadata only; nothing is uploaded or stored
 *     beyond this prototype key. In production the server and database
 *     are authoritative — this localStorage key is demo-only.
 */

import {
  type Application,
  type AgentSubStatus,
  type DocQuality,
  activateApplication,
  addDocMeta,
  adminDecide,
  canOpenAgentPreview,
  createApplication,
  provisionActivation,
  resubmitAfterSupplement,
  runSimulatedReview,
  setLicenseLifecycle,
  submitApplication,
} from './preview-core'
import { type AdminActionId, type AdminRole, adminCan } from './preview-business'

export const PREVIEW_STORE_KEY = 'goaa_portal_preview_store_v1'
export const DEMO_CUSTOMER_EMAIL = 'jordan.rivera.preview@example.com'

export interface AuditEntry {
  at: string
  actor: string
  action: string
  detail: string
}

export interface PortalPreviewState {
  version: 1
  activeEmail: string
  applications: Application[]
  subscriptions: Record<string, AgentSubStatus>
  audit: AuditEntry[]
}

/* ------------------------------------------------------------------ */
/* Storage adapter (browser localStorage for prototype; injectable     */
/* memory backend so node tests can exercise the same code).          */
/* ------------------------------------------------------------------ */

export interface PreviewStorageLike {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

class MemoryStorage implements PreviewStorageLike {
  private map = new Map<string, string>()
  getItem(key: string) { return this.map.has(key) ? this.map.get(key)! : null }
  setItem(key: string, value: string) { this.map.set(key, value) }
  removeItem(key: string) { this.map.delete(key) }
}

let memoryOverride: PreviewStorageLike | null = null

export function _testUseMemoryStorage(): PreviewStorageLike {
  memoryOverride = new MemoryStorage()
  return memoryOverride
}

function browserStorage(): PreviewStorageLike | null {
  try {
    return typeof localStorage !== 'undefined' ? (localStorage as PreviewStorageLike) : null
  } catch {
    return null
  }
}

function storage(): PreviewStorageLike | null {
  return memoryOverride ?? browserStorage()
}

/* ------------------------------------------------------------------ */
/* Fixtures (all fictional)                                            */
/* ------------------------------------------------------------------ */

export type SeedKind =
  | 'fresh'
  | 'under_review'
  | 'supplement'
  | 'approved_ready'
  | 'activated'
  | 'suspended'
  | 'rejected'
  | 'paused'

export const SEED_KINDS: SeedKind[] = ['fresh', 'under_review', 'supplement', 'approved_ready', 'activated', 'suspended', 'rejected', 'paused']

export function isSeedKind(value: unknown): value is SeedKind {
  return typeof value === 'string' && (SEED_KINDS as string[]).includes(value)
}

const JORDAN = {
  fullName: 'Jordan Rivera',
  phone: '(555) 010-2233',
  address: '880 Previs Lane, Austin, TX 78701',
  email: DEMO_CUSTOMER_EMAIL,
}

const JORDAN_LICENSES = [
  { localId: 'j-lic-1', category: 'insurance', licenseNumber: '0H1234567', issuer: 'CA', expiresAt: '2028-06-30' },
  { localId: 'j-lic-2', category: 'real_estate', licenseNumber: 'RE-009911', issuer: 'NY', expiresAt: '2029-03-31' },
]

const MORGAN = { fullName: 'Morgan Hale', phone: '(555) 010-7712', address: '22 Harbor Row, Tampa, FL 33602', email: 'morgan.hale.preview@example.com' }
const CASEY = { fullName: 'Casey Nguyen', phone: '(555) 010-5534', address: '90 Cedar Bend, Austin, TX 78745', email: 'casey.nguyen.preview@example.com' }
const TAYLOR = { fullName: 'Taylor Brooks', phone: '(555) 010-8821', address: '440 Mesa Court, Denver, CO 80202', email: 'taylor.brooks.preview@example.com' }

function addFrontDocs(app: Application, quality: DocQuality = 'good'): Application {
  let next = app
  for (const lic of next.licenses) {
    if (!lic.docs.some((d) => d.kind === 'front')) {
      next = addDocMeta(next, lic.localId, { kind: 'front', filename: `${lic.category}-front.jpg`, sizeBytes: 187200, mimeType: 'image/jpeg', quality })
    }
  }
  return next
}

function submittedApp(opts: { applicant: typeof JORDAN; licenses: typeof JORDAN_LICENSES; quality?: DocQuality; ocrName?: string; ocrNumber?: string }): Application {
  const base = createApplication(opts.applicant, opts.licenses)
  const withDocs = addFrontDocs(base, opts.quality ?? 'good')
  const sub = submitApplication(withDocs)
  if (!sub.ok) throw new Error(`seed submit failed: ${(sub.errors ?? []).join('; ')}`)
  return runSimulatedReview(sub.app, { quality: opts.quality ?? 'good', ocrName: opts.ocrName, ocrNumber: opts.ocrNumber })
}

export function seedPortalPreviewState(kind: SeedKind): PortalPreviewState {
  const state: PortalPreviewState = {
    version: 1,
    activeEmail: DEMO_CUSTOMER_EMAIL,
    applications: [],
    subscriptions: {},
    audit: [],
  }
  const push = (app: Application, sub?: AgentSubStatus) => {
    state.applications.push(app)
    if (sub) state.subscriptions[app.applicant.email] = sub
  }

  if (kind === 'fresh' || kind === 'under_review') {
    push(submittedApp({ applicant: JORDAN, licenses: JORDAN_LICENSES }))
    push(submittedApp({ applicant: MORGAN, licenses: [{ localId: 'm-lic-1', category: 'insurance', licenseNumber: '0H9988776', issuer: 'FL', expiresAt: '2027-08-19' }], quality: 'blurry', ocrName: 'Morgan T. Hale' }))
    push(submittedApp({ applicant: CASEY, licenses: [{ localId: 'c-lic-1', category: 'real_estate', licenseNumber: 'RE-220118', issuer: 'TX', expiresAt: '2028-11-30' }], quality: 'blurry' }))
    push(submittedApp({ applicant: TAYLOR, licenses: [{ localId: 't-lic-1', category: 'cdl', licenseNumber: 'CDL-554011', issuer: 'CO', expiresAt: '2027-02-14' }] }))
  }
  if (kind === 'supplement' || kind === 'approved_ready' || kind === 'activated' || kind === 'suspended' || kind === 'rejected' || kind === 'paused') {
    const j = submittedApp({ applicant: JORDAN, licenses: JORDAN_LICENSES })
    if (kind === 'rejected') {
      const decided = adminDecide(j, 'reject', 'Materials did not pass the verification policy.', '2026-09-08T11:00:00.000Z')
      if (!decided.ok) throw new Error(decided.error ?? 'reject failed')
      decided.app.customerMessage = 'Your application was not approved. You may start a new application when you have corrected materials.'
      push(decided.app)
    } else {
      const supplemented = adminDecide(j, 'supplement', 'Front photos were not readable.', '2026-09-08T11:05:00.000Z')
      if (!supplemented.ok) throw new Error(supplemented.error ?? 'supplement failed')
      supplemented.app.customerMessage = 'Our reviewer could not read the front photos. Please upload clearer, well-lit photos of every license.'
      if (kind === 'supplement') {
        // Terminal supplement seed: the store contains exactly this record.
        push(supplemented.app)
      } else {
        // Later lifecycle seeds replay the supplement round and end on the
        // requested state; the interim supplement record is never stored.
        const re = resubmitAfterSupplement(supplemented.app, '2026-09-08T11:10:00.000Z')
        if (!re.ok) throw new Error(re.error ?? 'resubmit failed')
        const again = addFrontDocs(re.app, 'good')
        const resub = submitApplication(again, '2026-09-08T11:12:00.000Z')
        if (!resub.ok) throw new Error('second submit failed')
        const reviewed = runSimulatedReview(resub.app, { quality: 'good' }, '2026-09-08T11:13:00.000Z')
        const approved = adminDecide(reviewed, 'approve', 'Clear photos; identity matches the official check (reserved).', '2026-09-08T11:15:00.000Z')
        if (!approved.ok) throw new Error(approved.error ?? 'approve failed')
        approved.app.customerMessage = 'Your application was approved. Use the activation link to set your password and open agent access.'
        const prov = provisionActivation(approved.app, '2026-09-08T11:16:00.000Z')
        if (!prov.ok) throw new Error(prov.error ?? 'provision failed')
        let finalApp = prov.app
        if (kind === 'activated' || kind === 'suspended' || kind === 'paused') {
          const act = activateApplication(finalApp, '2026-09-08T11:30:00.000Z')
          if (!act.ok) throw new Error(act.error ?? 'activation failed')
          finalApp = act.app
        }
        if (kind === 'suspended') {
          finalApp = setLicenseLifecycle(finalApp, 'suspended', 'Official database check returned a hold.', '2026-09-08T12:00:00.000Z')
          finalApp.customerMessage = 'Agent access is paused while the license record is re-verified. No decision is final until the official check resolves.'
        }
        push(finalApp, kind === 'paused' ? 'paused' : 'active')
      }
    }
  }

  if (state.applications.length === 0 && kind !== 'fresh') {
    // Every non-fresh seed is expected to have produced the Jordan record.
    throw new Error(`seed ${kind} produced no application`)
  }
  return state
}

/* ------------------------------------------------------------------ */
/* Read / write                                                        */
/* ------------------------------------------------------------------ */

export function defaultState(): PortalPreviewState {
  return { version: 1, activeEmail: DEMO_CUSTOMER_EMAIL, applications: [], subscriptions: {}, audit: [] }
}

export function readPortalPreviewState(): PortalPreviewState {
  const s = storage()
  if (!s) return defaultState()
  try {
    const raw = s.getItem(PREVIEW_STORE_KEY)
    if (!raw) return defaultState()
    const parsed = JSON.parse(raw) as PortalPreviewState
    if (!parsed || parsed.version !== 1 || !Array.isArray(parsed.applications)) return defaultState()
    return parsed
  } catch {
    return defaultState()
  }
}

export function writePortalPreviewState(state: PortalPreviewState): PortalPreviewState {
  const s = storage()
  if (s) s.setItem(PREVIEW_STORE_KEY, JSON.stringify(state))
  return state
}

export function resetPortalPreviewState(): PortalPreviewState {
  const s = storage()
  if (s) s.removeItem(PREVIEW_STORE_KEY)
  return defaultState()
}

export function applySeedToStoredState(kind: SeedKind): PortalPreviewState {
  return writePortalPreviewState(seedPortalPreviewState(kind))
}

export function auditPush(state: PortalPreviewState, actor: string, action: string, detail: string): void {
  state.audit.push({ at: new Date().toISOString(), actor, action, detail })
}

function withApp(state: PortalPreviewState, appId: string, mutate: (app: Application) => Application | { ok: false; error: string }): { ok: true; state: PortalPreviewState } | { ok: false; error: string } {
  const idx = state.applications.findIndex((a) => a.id === appId)
  if (idx === -1) return { ok: false, error: `Application ${appId} not found.` }
  const next = mutate(state.applications[idx])
  if (!next || (next as { ok?: boolean }).ok === false) {
    return { ok: false, error: (next as { error?: string } | null)?.error ?? 'Unknown store error.' }
  }
  const copy: PortalPreviewState = { ...state, applications: state.applications.slice() }
  copy.applications[idx] = next as Application
  writePortalPreviewState(copy)
  return { ok: true, state: copy }
}

function assertStateIntegrity(state: PortalPreviewState): void {
  if (!state || state.version !== 1 || !Array.isArray(state.applications)) {
    throw new Error('preview-store: invalid state object')
  }
}

/* ------------------------------------------------------------------ */
/* CUSTOMER actions (no admin power here)                              */
/* ------------------------------------------------------------------ */

/** Start (or resume) a draft application for the demo customer. */
export function customerStartApplication(): PortalPreviewState {
  let state = readPortalPreviewState()
  assertStateIntegrity(state)
  const existing = state.applications.find((a) => a.applicant.email === state.activeEmail)
  if (existing && (existing.status === 'draft' || existing.status === 'supplement_required')) return state
  const draft = createApplication(JORDAN, JORDAN_LICENSES)
  draft.customerMessage = 'Draft saved locally in this prototype. Nothing has been submitted or uploaded.'
  const next: PortalPreviewState = { ...state, applications: [...state.applications, draft] }
  return writePortalPreviewState(next)
}

/** Attach simulated photo metadata. Draft fills any license missing a front
 *  photo; a supplement-required application appends a new “clearer” front
 *  photo to every license so the resubmission is visible to the reviewer. */
export function customerAttachPhotos(appId: string): { state: PortalPreviewState; changed: boolean; error?: string } {
  const state = readPortalPreviewState()
  assertStateIntegrity(state)
  const app = state.applications.find((a) => a.id === appId)
  if (!app) return { state, changed: false, error: `Application ${appId} not found.` }
  if (app.status !== 'draft' && app.status !== 'supplement_required') {
    return { state, changed: false, error: 'Photos can only be attached to a draft or while supplement is requested.' }
  }
  let next = app
  if (app.status === 'draft') {
    for (const lic of next.licenses) {
      if (!lic.docs.some((d) => d.kind === 'front')) {
        next = addDocMeta(next, lic.localId, { kind: 'front', filename: `${lic.category}-front.jpg`, sizeBytes: 187200, mimeType: 'image/jpeg', quality: 'good' })
      }
    }
  } else {
    for (const lic of next.licenses) {
      next = addDocMeta(next, lic.localId, { kind: 'front', filename: `${lic.category}-clearer.jpg`, sizeBytes: 174800, mimeType: 'image/jpeg', quality: 'good' })
    }
  }
  const changed = next.licenses.some((l, i) => l.docs.length !== app.licenses[i].docs.length)
  const copy: PortalPreviewState = { ...state, applications: state.applications.map((a) => (a.id === appId ? next : a)) }
  writePortalPreviewState(copy)
  return { state: copy, changed }
}

/** Customer submits a draft (or resubmits after supplement). System review
 *  runs and produces a SUGGESTION only; the customer cannot decide. */
export function customerSubmitApplication(appId: string): { state: PortalPreviewState; ok: boolean; errors?: string[] } {
  const state = readPortalPreviewState()
  assertStateIntegrity(state)
  const app = state.applications.find((a) => a.id === appId)
  if (!app) return { state, ok: false, errors: [`Application ${appId} not found.`] }
  if (app.status !== 'draft' && app.status !== 'supplement_required') {
    return { state, ok: false, errors: ['Only a draft or a supplement-required application can be submitted.'] }
  }
  const sub = app.status === 'supplement_required' ? resubmitAfterSupplement(app) : { ok: true, app }
  if (!sub.ok) return { state, ok: false, errors: [sub.error ?? 'Resubmit blocked.'] }
  const submit = submitApplication(sub.app)
  if (!submit.ok) return { state, ok: false, errors: submit.errors ?? [] }
  const reviewed = runSimulatedReview(submit.app, { quality: 'good' })
  reviewed.customerMessage = undefined
  const copy: PortalPreviewState = { ...state, applications: state.applications.map((a) => (a.id === appId ? reviewed : a)) }
  writePortalPreviewState(copy)
  return { state: copy, ok: true }
}

/** Customer uses the one-time activation link (simulated). */
export function customerActivate(appId: string): { state: PortalPreviewState; ok: boolean; error?: string } {
  const state = readPortalPreviewState()
  assertStateIntegrity(state)
  const app = state.applications.find((a) => a.id === appId)
  if (!app) return { state, ok: false, error: `Application ${appId} not found.` }
  if (app.status !== 'approved' || !app.activation || app.activation.tokenUsed) {
    return { state, ok: false, error: 'There is no pending activation link for this application.' }
  }
  const act = activateApplication(app)
  if (!act.ok) return { state, ok: false, error: act.error }
  act.app.customerMessage = 'Your account is activated. Agent access is open because your license is approved and valid.'
  const copy: PortalPreviewState = { ...state, applications: state.applications.map((a) => (a.id === appId ? act.app : a)) }
  writePortalPreviewState(copy)
  return { state: copy, ok: true }
}

/** Read-only helper for the customer view: which application belongs to the
 *  active demo customer? */
export function customerApplicationFor(state: PortalPreviewState): Application | undefined {
  return state.applications.find((a) => a.applicant.email === state.activeEmail)
}

/* ------------------------------------------------------------------ */
/* ADMIN actions (server/db stand-in)                                  */
/* ------------------------------------------------------------------ */

export type AdminDecisionKind = 'approve' | 'supplement' | 'reject'

function friendlySupplementMessage(app: Application): string {
  const categories = app.licenses.map((l) => l.category.replace('_', ' ')).join(', ')
  return `Our reviewer could not read some of your photos. Please upload clearer, well-lit photos for: ${categories}.`
}

export const ADMIN_DECISION_ACTION: Record<AdminDecisionKind, AdminActionId> = {
  approve: 'approve_application',
  supplement: 'request_supplement',
  reject: 'reject_application',
}

function deniedAuditEntry(state: PortalPreviewState, actorRole: AdminRole, action: string, appId: string): PortalPreviewState {
  return { ...state, audit: [...state.audit, { at: new Date().toISOString(), actor: 'admin', action: 'admin.decision_denied', detail: `${actorRole} blocked from ${action} on ${appId}.` }] }
}

export function adminDecision(appId: string, action: AdminDecisionKind, note: string, opts: { actorRole: AdminRole }): { state: PortalPreviewState; ok: boolean; error?: string } {
  const state = readPortalPreviewState()
  assertStateIntegrity(state)
  const app = state.applications.find((a) => a.id === appId)
  if (!app) return { state, ok: false, error: `Application ${appId} not found.` }
  if (!adminCan(opts.actorRole, ADMIN_DECISION_ACTION[action])) {
    const denied = deniedAuditEntry(state, opts.actorRole, action, appId)
    writePortalPreviewState(denied)
    return { state: denied, ok: false, error: `Only Review Admin and Super Admin can make review decisions. ${opts.actorRole} cannot ${action}.` }
  }
  if (app.status !== 'ai_review') return { state, ok: false, error: 'Only an AI-reviewed application can be decided.' }
  if (!note.trim()) return { state, ok: false, error: 'A decision note is required.' }
  const decided = adminDecide(app, action, note)
  if (!decided.ok) return { state, ok: false, error: decided.error ?? 'Decision blocked.' }
  let next = decided.app
  next.customerMessage = action === 'approve' ? 'Your application was approved. An activation link was prepared for you.' : action === 'supplement' ? friendlySupplementMessage(app) : 'Your application was not approved at this time.'
  auditPush(state, 'admin', `decision_${action}`, `${app.applicant.fullName} (${app.id}) — ${note}`)
  if (action === 'approve') {
    const prov = provisionActivation(next)
    if (!prov.ok) return { state, ok: false, error: prov.error ?? 'Provisioning failed after approval.' }
    next = prov.app
    auditPush(state, 'system', 'provisioning_sent', `One-time activation link prepared for ${app.applicant.email} (simulated).`)
  }
  const copy: PortalPreviewState = { ...state, applications: state.applications.map((a) => (a.id === appId ? next : a)) }
  writePortalPreviewState(copy)
  return { state: copy, ok: true }
}

export const ADMIN_LIFECYCLE_ACTION: Record<'suspended' | 'expired', AdminActionId> = {
  suspended: 'suspend_agent',
  expired: 'mark_expired',
}

export function adminLifecycle(appId: string, status: 'suspended' | 'expired', reason: string, opts: { actorRole: AdminRole }): { state: PortalPreviewState; ok: boolean; error?: string } {
  const state = readPortalPreviewState()
  assertStateIntegrity(state)
  const app = state.applications.find((a) => a.id === appId)
  if (!app) return { state, ok: false, error: `Application ${appId} not found.` }
  if (!adminCan(opts.actorRole, ADMIN_LIFECYCLE_ACTION[status])) {
    const denied = deniedAuditEntry(state, opts.actorRole, `lifecycle_${status}`, appId)
    writePortalPreviewState(denied)
    return { state: denied, ok: false, error: `Only Review Admin and Super Admin can change license lifecycle. ${opts.actorRole} cannot ${status}.` }
  }
  const updated = setLicenseLifecycle(app, status, reason)
  auditPush(state, 'admin', `lifecycle_${status}`, `${app.applicant.fullName} (${app.id}) — ${reason}`)
  const copy: PortalPreviewState = { ...state, applications: state.applications.map((a) => (a.id === appId ? updated : a)) }
  writePortalPreviewState(copy)
  return { state: copy, ok: true }
}

/* ------------------------------------------------------------------ */
/* AGENT helpers (gate driven by the same store)                       */
/* ------------------------------------------------------------------ */

export interface AgentAccess {
  application?: Application
  subscription: AgentSubStatus
  gate: { allowed: boolean; reason: string }
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

function hasValidLicense(app: Application | undefined): boolean {
  if (!app) return false
  const today = todayIso()
  return app.licenses.some((l) => l.expiresAt >= today)
}

export function agentAccessFor(state: PortalPreviewState, email?: string): AgentAccess {
  const active = email ?? state.activeEmail
  const application = state.applications.find((a) => a.applicant.email === active)
  const gate = canOpenAgentPreview({
    status: application?.status,
    activated: Boolean(application?.activation?.tokenUsed),
    anyLicenseValid: hasValidLicense(application),
  })
  return {
    application,
    subscription: state.subscriptions[active] ?? 'none',
    gate,
  }
}
