'use client'

/**
 * AdminPortalPreview.tsx — isolated /portal-preview/admin candidate.
 *
 * Official back-office console preview (15 sections). This is the ONLY
 * preview page with decision power. Application/lifecycle decisions go
 * through the shared prototype store (preview-store); business-loop admin
 * operations (agent access, matter assignment/exceptions, refunds,
 * settlements) go through the pure business layer with the role matrix
 * (preview-business). The customer page never writes a decision and the
 * agent page only reads the resulting state.
 *
 * Role boundary (live demo): the role picker changes which actions are
 * enabled via adminCan(). Production authority stays on the server: the
 * fixture store and the seed buttons below are for prototype screenshots
 * only and do not exist in production.
 */

import { useEffect, useMemo, useState } from 'react'
import {
  type Application,
  type ApplyStatus,
} from '../../lib/portal-preview/preview-core'
import {
  adminDecision,
  adminLifecycle,
  applySeedToStoredState,
  defaultState,
  isSeedKind,
  readPortalPreviewState,
  type PortalPreviewState,
  type SeedKind,
} from '../../lib/portal-preview/preview-store'
import {
  applyBusinessSeed,
  readBusinessState,
  writeBusinessState,
} from '../../lib/portal-preview/preview-business-store'
import {
  ADMIN_ACTIONS,
  ADMIN_ROLES,
  ADMIN_ROLE_ACTIONS,
  ADMIN_SECTIONS,
  adminApproveRefund,
  adminApproveSettlement,
  adminAssignMatter,
  adminCan,
  adminHandleOrderException,
  type AdminRole,
  type BusinessSeedKind,
  type BusinessState,
  openAgentAccess,
  setSubscriptionStatus,
} from '../../lib/portal-preview/preview-business'
import '../../portal-preview/portal-preview.css'

const STATUS_LABEL: Record<ApplyStatus, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  ai_review: 'AI Review',
  supplement_required: 'Supplement Required',
  approved: 'Approved',
  rejected: 'Rejected',
  suspended: 'Suspended',
  expired: 'Expired',
}

function tone(status: ApplyStatus): string {
  if (status === 'approved') return 'good'
  if (status === 'rejected' || status === 'suspended' || status === 'expired') return 'warn'
  if (status === 'supplement_required') return 'warn'
  return 'review'
}

function fmtAmount(n: number | null | undefined): string {
  return n == null ? '—' : `$${n.toFixed(2)}`
}

export default function AdminPortalPreview() {
  const [store, setStore] = useState<PortalPreviewState>(() => defaultState())
  const [biz, setBiz] = useState<BusinessState>(() => readBusinessState())
  const [section, setSection] = useState<string>('dashboard')
  const [roleId, setRoleId] = useState<AdminRole>('super_admin')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [note, setNote] = useState('')
  const [lifecycleNote, setLifecycleNote] = useState('')
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [bizResult, setBizResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [exceptionNote, setExceptionNote] = useState<Record<string, string>>({})
  const [refundNote, setRefundNote] = useState<Record<string, string>>({})

  // Restore the live role picker and active section after a refresh (demo
  // state itself already lives in localStorage). Defaults are never written
  // here so a StrictMode double effect run cannot clobber the stored value.
  useEffect(() => {
    try {
      const storedRole = localStorage.getItem('pp_admin_role')
      if (storedRole && ADMIN_ROLES.some((r) => r.id === storedRole)) setRoleId(storedRole as AdminRole)
      const storedSection = localStorage.getItem('pp_admin_section')
      if (storedSection && ADMIN_SECTIONS.some((s) => s.id === storedSection)) setSection(storedSection)
    } catch {
      // Ignore unavailable storage.
    }
  }, [])

  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search)
      const seed = params.get('seed')
      if (seed && isSeedKind(seed)) {
        setStore(applySeedToStoredState(seed))
        const bizSeeds = ['fresh', 'under_review', 'supplement', 'approved_ready', 'activated', 'suspended', 'rejected', 'paused'] as const
        if ((bizSeeds as readonly string[]).includes(seed)) {
          setBiz(applyBusinessSeed(seed as (typeof bizSeeds)[number]))
        } else {
          setBiz(readBusinessState())
        }
        setSelectedId(null)
        setResult(null)
        setBizResult(null)
        window.history.replaceState(null, '', window.location.pathname)
      } else {
        setStore(readPortalPreviewState())
        setBiz(readBusinessState())
      }
    } catch {
      setStore(readPortalPreviewState())
      setBiz(readBusinessState())
    }
  }, [])

  const apps = useMemo(() => [...store.applications].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)), [store])
  const selected = apps.find((a) => a.id === selectedId) ?? apps[0] ?? undefined
  const canOpenAccess = adminCan(roleId, 'open_agent_access')
  const canManagePlans = adminCan(roleId, 'manage_plans')
  const canHandleOps = adminCan(roleId, 'handle_order_exception') || adminCan(roleId, 'assign_client')
  const canFinance = adminCan(roleId, 'approve_refund') || adminCan(roleId, 'approve_settlement')
  const canReviewDecision = adminCan(roleId, 'approve_application') && adminCan(roleId, 'request_supplement') && adminCan(roleId, 'reject_application')
  const canReviewLifecycle = adminCan(roleId, 'suspend_agent') && adminCan(roleId, 'mark_expired')
  const roleLabel = ADMIN_ROLES.find((r) => r.id === roleId)?.label ?? roleId

  function applySeed(kind: SeedKind) {
    setStore(applySeedToStoredState(kind))
    setSelectedId(null)
    setResult(null)
    setBizResult(null)
    setNote('')
    setLifecycleNote('')
    setBiz(applyBusinessSeed(kind as BusinessSeedKind))
  }

  function bizRun(res: { ok: boolean; state?: BusinessState; error?: string }, okMsg: string) {
    if (!res.ok) {
      setBizResult({ ok: false, message: res.error ?? 'Blocked by the role matrix or business rule.' })
      return
    }
    if (res.state) setBiz(writeBusinessState(res.state))
    setBizResult({ ok: true, message: okMsg })
  }

  const sectionDef = ADMIN_SECTIONS.find((s) => s.id === section) ?? ADMIN_SECTIONS[0]
  const readyAccounts = [...biz.accounts].sort((a, b) => a.createdAt.localeCompare(b.createdAt))

  return (
    <div className="pp-root">
      <header className="pp-topbar">
        <div className="pp-brand">GOAA <span className="pp-brand-sub">admin portal preview — official console</span></div>
        <div className="pp-topbar-right">
          <label className="pp-inline-hint" style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>Admin role:
            <select className="pp-select" value={roleId} onChange={(e) => { const v = e.target.value as AdminRole; setRoleId(v); try { localStorage.setItem('pp_admin_role', v) } catch { /* ignore */ } }}>
              {ADMIN_ROLES.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
            </select>
          </label>
          <span className="pp-badge">Candidate concept · not production</span>
        </div>
      </header>

      <div className="pp-admin-bar">
        <span className="pp-admin-title">Review queue · official console — {sectionDef.label}</span>
        <button className="pp-btn pp-btn-ghost" onClick={() => setStore(readPortalPreviewState())}>Reload store</button>
        <button className="pp-btn pp-btn-ghost" onClick={() => applySeed('fresh')}>Seed: review queue</button>
        <button className="pp-btn pp-btn-ghost" onClick={() => applySeed('activated')}>Seed: activated</button>
        <button className="pp-btn pp-btn-ghost" onClick={() => applySeed('suspended')}>Seed: suspended</button>
        <span className="pp-admin-note">Fixture seeds drive demo screenshots only — production decisions live on the server.</span>
      </div>

      <div className="pp-layout pp-admin-layout">
        <nav className="pp-rail">
          <div className="pp-rail-kicker" style={{ margin: '4px 12px 6px' }}>SECTIONS</div>
          {ADMIN_SECTIONS.map((s) => (
            <button key={s.id} className={`pp-rail-item ${section === s.id ? 'pp-active' : ''}`} onClick={() => { setSection(s.id); try { localStorage.setItem('pp_admin_section', s.id) } catch { /* ignore */ } }}>
              <span className="pp-rail-ic">{(s.id === 'dashboard' ? '🏠' : s.id === 'users' ? '👥' : s.id === 'applications' ? '📜' : s.id === 'leads' ? '🎯' : s.id === 'matters' ? '🗂️' : s.id === 'estimates' ? '📄' : s.id === 'invoices' ? '🧾' : s.id === 'skills' ? '🧰' : s.id === 'courses' ? '🎓' : s.id === 'earnings' ? '💡' : s.id === 'plans' ? '💳' : s.id === 'referrals' ? '🤝' : s.id === 'integrations' ? '🔌' : s.id === 'roles' ? '🛡️' : '⚠️')}</span>
              <span>{s.label}</span>
            </button>
          ))}
        </nav>

        <main className="pp-main">
          {bizResult && <p className={bizResult.ok ? 'pp-ok' : 'pp-err'}>{bizResult.message}</p>}

          {section === 'dashboard' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Dashboard</h1>
              <p className="pp-muted pp-body">Cross-store operational overview. License review lives in the prototype store; business-loop objects (accounts, matters, invoices) live in the business world.</p>
              <div className="pp-grid-2">
                <article className="pp-panel"><h2 className="pp-h2">Licenses</h2><div className="pp-kv">
                  <span className="pp-label">Applications in store</span><span>{apps.length}</span>
                  <span className="pp-label">Under review</span><span>{apps.filter((a) => a.status === 'ai_review' || a.status === 'submitted').length}</span>
                  <span className="pp-label">Supplement needed</span><span>{apps.filter((a) => a.status === 'supplement_required').length}</span>
                  <span className="pp-label">Approved</span><span>{apps.filter((a) => a.status === 'approved').length}</span>
                </div></article>
                <article className="pp-panel"><h2 className="pp-h2">Business world</h2><div className="pp-kv">
                  <span className="pp-label">Accounts</span><span>{biz.accounts.length}</span>
                  <span className="pp-label">Open opportunities</span><span>{biz.opportunities.filter((o) => o.status === 'open').length}</span>
                  <span className="pp-label">Matters</span><span>{biz.matters.length}</span>
                  <span className="pp-label">Invoices issued</span><span>{biz.invoices.filter((i) => i.status === 'issued').length}</span>
                  <span className="pp-label">Payments</span><span>{biz.payments.length}</span>
                </div></article>
              </div>
            </section>
          )}

          {section === 'users' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Users &amp; Agents</h1>
              <p className="pp-muted pp-body">One account, multiple roles. Every account starts as a customer; agent role appears only after approval + activation. Opening agent access is guarded by the role matrix.</p>
              {readyAccounts.map((acc) => (
                <article key={acc.email} className="pp-panel">
                  <div className="pp-card-head">
                    <div>
                      <h2 className="pp-h2" style={{ margin: 0 }}>{acc.displayName}</h2>
                      <p className="pp-muted" style={{ margin: '4px 0 0', fontSize: 12.5 }}>{acc.email}</p>
                    </div>
                    <span className={`pp-status pp-status-${acc.roles.includes('agent') ? 'good' : 'review'}`}>{acc.roles.join(' + ') || 'customer'}</span>
                  </div>
                  <div className="pp-chip-row" style={{ marginTop: 10 }}>
                    <span className="pp-chip">agentAccess: {acc.agentAccess}</span>
                    <span className="pp-chip">agentUsername: {acc.agentUsername ?? '—'}</span>
                    <span className="pp-chip">subscription: {acc.subscription.plan} · {acc.subscription.status}</span>
                    <span className="pp-chip">activatedAt: {acc.activatedAt?.slice(0, 10) ?? '—'}</span>
                  </div>
                  {canOpenAccess && (
                    <div className="pp-actions">
                      <button className="pp-btn pp-btn-secondary" onClick={() => bizRun(openAgentAccess(biz, { email: acc.email, actorRole: roleId }), `Agent access opened for ${acc.displayName}.`)}>Open agent access</button>
                    </div>
                  )}
                </article>
              ))}
              <p className="pp-note">Opening access only grants the one-time activation step; it never approves licenses and never duplicates the account.</p>
            </section>
          )}

          {section === 'applications' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Applications &amp; Licenses</h1>
              <p className="pp-muted pp-body">Decision surface. The review role approves, requests supplement, or rejects. Lifecycle actions pause or expire an approved license.</p>
              <article className="pp-panel">
                <h2 className="pp-h2">Application queue</h2>
                {apps.length === 0 && <p className="pp-note">No applications in this store yet. Run a customer flow or use a fixture seed above.</p>}
                <div className="pp-chip-row">
                  {apps.map((app) => (
                    <button key={app.id} className={`pp-btn pp-btn-ghost ${selected?.id === app.id ? 'pp-active' : ''}`} onClick={() => { setSelectedId(app.id); setResult(null); }}>{app.applicant.fullName}</button>
                  ))}
                </div>
              </article>

              {selected && (
                <>
                  <article className="pp-panel">
                    <div className="pp-card-head">
                      <h2 className="pp-h2">{selected.applicant.fullName}</h2>
                      <span className={`pp-status pp-status-${tone(selected.status)}`}>{STATUS_LABEL[selected.status]}</span>
                    </div>
                    <p className="pp-muted" style={{ fontSize: 13 }}>{selected.applicant.email} · {selected.applicant.phone} · {selected.applicant.address}</p>
                    {lastRisk(selected) && <span className={`pp-risk pp-risk-${lastRisk(selected)}`}>{lastRisk(selected)} risk</span>}
                    <AiReviewCard app={selected} />
                  </article>

                  <article className="pp-panel">
                    <h2 className="pp-h2">Licenses &amp; photo metadata</h2>
                    <table className="pp-table">
                      <thead><tr><th>Category</th><th>Number</th><th>Issuer</th><th>Expires</th><th>Documents</th></tr></thead>
                      <tbody>
                        {selected.licenses.map((l) => (
                          <tr key={l.localId}>
                            <td>{l.category.replace('_', ' ').toUpperCase()}</td>
                            <td className="pp-mono">{l.licenseNumber}</td>
                            <td>{l.issuer}</td>
                            <td>{l.expiresAt}</td>
                            <td>
                              {l.docs.length
                                ? l.docs.map((d) => `${d.filename} (${d.quality})`).join(' · ')
                                : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <p className="pp-muted" style={{ fontSize: 12.5, marginTop: 8 }}>Fictional data only. The official database check is reserved and never bypassed by a readable photo.</p>
                  </article>

                  {selected.status === 'ai_review' && (
                    canReviewDecision ? (
                      <article className="pp-panel">
                        <h2 className="pp-h2">Review decision — review role only</h2>
                        <p className="pp-muted" style={{ fontSize: 13 }}>Approve provisions a one-time activation link. Request supplement asks the applicant for clearer photos. Reject closes the application. A decision note is required and becomes the customer-visible message.</p>
                        <textarea className="pp-textarea" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Required note for the applicant (and audit trail)…" />
                        <div className="pp-actions">
                          <button className="pp-btn pp-btn-primary" disabled={!note.trim()} onClick={() => decide('approve')}>Approve</button>
                          <button className="pp-btn pp-btn-secondary" disabled={!note.trim()} onClick={() => decide('supplement')}>Request supplement</button>
                          <button className="pp-btn pp-btn-danger" disabled={!note.trim()} onClick={() => decide('reject')}>Reject</button>
                        </div>
                      </article>
                    ) : (
                      <p className="pp-note pp-errors">Review decisions require Review Admin or Super Admin. Decision buttons are hidden for the current role ({roleLabel}).</p>
                    )
                  )}

                  {(selected.status === 'approved' || selected.status === 'suspended') && (
                    canReviewLifecycle ? (
                      <article className="pp-panel">
                        <h2 className="pp-h2">License lifecycle — review/system role only</h2>
                        <p className="pp-muted" style={{ fontSize: 13 }}>Pause or expire a license when the official record changes. The agent gate closes immediately. Reinstatement happens through a fresh approval flow.</p>
                        <textarea className="pp-textarea" value={lifecycleNote} onChange={(e) => setLifecycleNote(e.target.value)} placeholder="Reason (shown to the customer)…" />
                        <div className="pp-actions">
                          <button className="pp-btn pp-btn-secondary" onClick={() => lifecycle('suspended')}>Suspend license</button>
                          <button className="pp-btn pp-btn-danger" onClick={() => lifecycle('expired')}>Mark expired</button>
                        </div>
                      </article>
                    ) : (
                      <p className="pp-note pp-errors">License lifecycle changes require Review Admin or Super Admin. Lifecycle buttons are hidden for the current role ({roleLabel}).</p>
                    )
                  )}

                  {selected.status !== 'ai_review' && selected.status !== 'approved' && selected.status !== 'suspended' && (
                    <p className="pp-note">No decision action is available for {STATUS_LABEL[selected.status]} applications in this prototype.</p>
                  )}

                  {result && <p className={result.ok ? 'pp-note pp-good-text' : 'pp-errors'}>{result.message}</p>}
                </>
              )}

              <p className="pp-note">This page is the only decision surface in the preview. Customer and Agent pages have no admin buttons; production uses server/database authority and real roles.</p>
            </section>
          )}

          {section === 'leads' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Leads &amp; Opportunities</h1>
              <p className="pp-muted pp-body">Open and accepted client opportunities in the business world.</p>
              {biz.opportunities.map((o) => (
                <article key={o.id} className="pp-panel">
                  <div className="pp-card-head"><div><h2 className="pp-h2" style={{ margin: 0 }}>{o.title}</h2><p className="pp-muted" style={{ margin: '4px 0 0', fontSize: 12.5 }}>{o.clientName} · {o.clientEmail}</p></div><span className={`pp-status pp-status-${o.status === 'open' ? 'review' : 'good'}`}>{o.status}</span></div>
                  <div className="pp-chip-row" style={{ marginTop: 10 }}><span className="pp-chip">{o.category}</span><span className="pp-chip">{o.feeRange}</span></div>
                </article>
              ))}
            </section>
          )}

          {section === 'matters' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Matters &amp; Orders</h1>
              <p className="pp-muted pp-body">Agent order pipeline with audit trail. Operations role can assign clients; operations/support can handle order exceptions when the role matrix allows.</p>
              {biz.matters.map((m) => (
                <article key={m.id} className="pp-panel">
                  <div className="pp-card-head">
                    <div><h2 className="pp-h2" style={{ margin: 0 }}>{m.title}</h2><p className="pp-muted" style={{ margin: '4px 0 0', fontSize: 12.5 }}>{m.id} · agent {m.agentEmail} · client {m.clientEmail}</p></div>
                    <span className={`pp-status pp-status-${m.stage === 'completed' || m.stage === 'paid' ? 'good' : m.stage === 'quote_declined' ? 'warn' : 'review'}`}>{m.stage.replace(/_/g, ' ')}</span>
                  </div>
                  <div className="pp-chip-row" style={{ marginTop: 10 }}>
                    <span className="pp-chip">quote {fmtAmount(m.quoteAmountUsd)}</span>
                    <span className="pp-chip">updated {m.updatedAt.slice(0, 16).replace('T', ' ')}</span>
                    {m.exception && <span className="pp-chip pp-warn">exception: {m.exception.note}</span>}
                  </div>
                  {adminCan(roleId, 'assign_client') && (
                    <div className="pp-actions">
                      <select className="pp-select" value={m.agentEmail} onChange={(e) => bizRun(adminAssignMatter(biz, { actorRole: roleId, matterId: m.id, toEmail: e.target.value }), `Matter ${m.id} reassigned to ${e.target.value}.`)}>
                        {biz.accounts.map((acc) => <option key={acc.email} value={acc.email}>{acc.displayName}</option>)}
                      </select>
                      <button className="pp-btn pp-btn-secondary" onClick={() => bizRun(adminAssignMatter(biz, { actorRole: roleId, matterId: m.id, toEmail: m.agentEmail }), `Matter ${m.id} kept with the assigned agent.`)}>Confirm assignment</button>
                    </div>
                  )}
                  {adminCan(roleId, 'handle_order_exception') && (
                    <div className="pp-inline-hint">
                      <textarea className="pp-textarea" rows={2} placeholder="Exception note (recorded to audit)…" value={exceptionNote[m.id] ?? ''} onChange={(e) => setExceptionNote((v) => ({ ...v, [m.id]: e.target.value }))} />
                      <button className="pp-btn pp-btn-secondary" disabled={!(exceptionNote[m.id] ?? '').trim()} onClick={() => bizRun(adminHandleOrderException(biz, { actorRole: roleId, matterId: m.id, note: (exceptionNote[m.id] ?? '').trim() }), `Exception handled on ${m.id}.`)}>Handle order exception</button>
                    </div>
                  )}
                </article>
              ))}
            </section>
          )}

          {section === 'estimates' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Estimates &amp; Deliverables</h1>
              <p className="pp-muted pp-body">Quotes and uploaded deliverable metadata across matters.</p>
              {biz.matters.map((m) => (
                <article key={m.id} className="pp-panel">
                  <h2 className="pp-h2" style={{ margin: 0 }}>{m.title}</h2>
                  <p className="pp-muted" style={{ margin: '4px 0 0', fontSize: 12.5 }}>{m.id} · quote {fmtAmount(m.quoteAmountUsd)} · stage {m.stage}</p>
                  <ul className="pp-list" style={{ marginTop: 8 }}>
                    {m.deliverables.length === 0 && <li>No deliverable metadata yet.</li>}
                    {m.deliverables.map((d) => <li key={`${d.filename}-${d.uploadedAt}`}>{d.filename} · {d.mimeType} · {d.sizeBytes} bytes · {d.uploadedAt.slice(0, 16).replace('T', ' ')} UTC</li>)}
                  </ul>
                </article>
              ))}
            </section>
          )}

          {section === 'invoices' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Invoices &amp; Payments</h1>
              <p className="pp-muted pp-body">Issued invoices and card-provider payment records. Finance role can approve refunds when the role matrix allows.</p>
              {biz.invoices.map((inv) => (
                <article key={inv.id} className="pp-panel">
                  <div className="pp-card-head">
                    <div><h2 className="pp-h2" style={{ margin: 0 }}>{inv.number}</h2><p className="pp-muted" style={{ margin: '4px 0 0', fontSize: 12.5 }}>{inv.id} · {inv.matterId} · agent {inv.agentEmail}</p></div>
                    <span className={`pp-status pp-status-${inv.status === 'paid' ? 'good' : 'review'}`}>{inv.status}</span>
                  </div>
                  <div className="pp-chip-row" style={{ marginTop: 10 }}><span className="pp-chip">{fmtAmount(inv.amountUsd)}</span><span className="pp-chip">issued {inv.issuedAt.slice(0, 16).replace('T', ' ')}</span><span className="pp-chip">paid {inv.paidAt ? inv.paidAt.slice(0, 16).replace('T', ' ') : '—'}</span></div>
                  {inv.status === 'refund_requested' && adminCan(roleId, 'approve_refund') && (
                    <div className="pp-inline-hint">
                      <textarea className="pp-textarea" rows={2} placeholder="Refund reason…" value={refundNote[inv.id] ?? ''} onChange={(e) => setRefundNote((v) => ({ ...v, [inv.id]: e.target.value }))} />
                      <button className="pp-btn pp-btn-secondary" disabled={!(refundNote[inv.id] ?? '').trim()} onClick={() => bizRun(adminApproveRefund(biz, { actorRole: roleId, invoiceId: inv.id, reason: (refundNote[inv.id] ?? '').trim() }), `Refund approved on ${inv.number}.`)}>Approve refund</button>
                    </div>
                  )}
                </article>
              ))}
              {biz.payments.map((p) => (
                <p key={p.id} className="pp-muted" style={{ fontSize: 12.5 }}>Payment {p.id} · {fmtAmount(p.amountUsd)} · provider {p.provider} · {p.receivedAt.slice(0, 16).replace('T', ' ')} UTC</p>
              ))}
            </section>
          )}

          {section === 'skills' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Skills Marketplace</h1>
              <p className="pp-muted pp-body">Admin catalog for AI-assistant skills. The customer adds skills; content role curates the catalog in production.</p>
              <div className="pp-kv">
                <span className="pp-label">Skills listed</span><span>4 (Compliance Monitor, Client Intake, Form Prefill, Pipedream Connector)</span>
                <span className="pp-label">Free tier</span><span>Compliance Monitor, Client Intake</span>
                <span className="pp-label">Paid add-ons</span><span>Form Prefill $19/mo, Pipedream Connector $9/mo</span>
                <span className="pp-label">Third-party</span><span>Pipedream marketplace — bring your own account</span>
              </div>
            </section>
          )}

          {section === 'courses' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Licensing Courses</h1>
              <p className="pp-muted pp-body">Course catalog shown under Get Licensed for customers who choose the learn path.</p>
              <div className="pp-kv">
                <span className="pp-label">Catalog</span><span>Insurance Basics, P&amp;C Foundations, Real Estate Prep, CDL ELDT</span>
                <span className="pp-label">Pricing</span><span>Free in preview; partner courses keep their own enrollment</span>
                <span className="pp-label">Completion</span><span>Prints a preview badge only — never an approval</span>
              </div>
            </section>
          )}

          {section === 'earnings' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Earning Opportunities</h1>
              <p className="pp-muted pp-body">Admin view of the growth-area feed: paid task previews, course rewards and membership referrals. Insurance revenue is never a referral base.</p>
              <div className="pp-grid-2">
                <article className="pp-panel"><h2 className="pp-h2">Paid task preview</h2><p className="pp-muted">“Help a neighbor compare two auto quotes” — $18 per completed task.</p></article>
                <article className="pp-panel"><h2 className="pp-h2">Referral rule</h2><p className="pp-muted">20% of the first $99/month membership only. Commissions and premiums are excluded by domain rule.</p></article>
              </div>
              {canFinance && (
                <div className="pp-actions">
                  <button className="pp-btn pp-btn-secondary" onClick={() => bizRun(adminApproveSettlement(biz, { actorRole: roleId, batch: 'settle-2026-09-08', amountUsd: 1180 }), 'Settlement batch approved (fictional $1,180).')}>Approve settlement batch</button>
                </div>
              )}
            </section>
          )}

          {section === 'plans' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Plans &amp; Subscriptions</h1>
              <p className="pp-muted pp-body">$99/month premium plan. Pausing only limits paid features; it never touches license or application state. Finance/support roles can change status when allowed.</p>
              {biz.accounts.map((acc) => (
                <article key={acc.email} className="pp-panel">
                  <div className="pp-card-head">
                    <div><h2 className="pp-h2" style={{ margin: 0 }}>{acc.displayName}</h2><p className="pp-muted" style={{ margin: '4px 0 0', fontSize: 12.5 }}>{acc.email}</p></div>
                    <span className={`pp-status pp-status-${acc.subscription.status === 'active' ? 'good' : 'warn'}`}>{acc.subscription.status}</span>
                  </div>
                  <div className="pp-chip-row" style={{ marginTop: 10 }}>
                    <span className="pp-chip">{acc.subscription.plan}</span>
                    <span className="pp-chip">pausedAt: {acc.subscription.pausedAt?.slice(0, 10) ?? '—'}</span>
                  </div>
                  {canManagePlans && (
                    <div className="pp-actions">
                      {acc.subscription.status === 'active'
                        ? <button className="pp-btn pp-btn-secondary" onClick={() => bizRun(setSubscriptionStatus(biz, acc.email, 'paused'), `Subscription paused for ${acc.displayName}. Paid features only are limited.`)}>Pause subscription</button>
                        : <button className="pp-btn pp-btn-secondary" onClick={() => bizRun(setSubscriptionStatus(biz, acc.email, 'active'), `Subscription resumed for ${acc.displayName}.`)}>Resume subscription</button>}
                    </div>
                  )}
                </article>
              ))}
              <p className="pp-note">Pausing a subscription never pauses the license or the application — those are separate review decisions.</p>
            </section>
          )}

          {section === 'referrals' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Referral Rewards</h1>
              <p className="pp-muted pp-body">Membership referrals only. Insurance premiums, policy commissions and course fees never qualify for rewards.</p>
              <div className="pp-kv">
                <span className="pp-label">Rule</span><span>20% of first $99/month membership paid by the referred friend</span>
                <span className="pp-label">Excluded sources</span><span>Insurance premium revenue, policy commissions, course partner payouts</span>
                <span className="pp-label">Status</span><span>Reviewable in this console; settlement is a finance action</span>
              </div>
            </section>
          )}

          {section === 'integrations' && (
            <section className="pp-stack">
              <h1 className="pp-h1">AI &amp; Third-party Integrations</h1>
              <p className="pp-muted pp-body">Adapter catalog. This preview reserves server environment names only; no real credentials, webhooks or partner endpoints are referenced.</p>
              <div className="pp-kv">
                <span className="pp-label">Adapters</span><span>chat-history, matter-archive, skills-marketplace, connector-registry (reserved)</span>
                <span className="pp-label">Provider mode</span><span>demo fallback OFF in fail-closed builds; production uses the real openclaw URL</span>
                <span className="pp-label">Security</span><span>No secret-like literals in portal preview source files</span>
              </div>
            </section>
          )}

          {section === 'roles' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Roles &amp; Permissions</h1>
              <p className="pp-muted pp-body">Live seven-role matrix below mirrors the role picker at the top of this console. Every action button is gated by the same adminCan() used by the domain layer.</p>
              <article className="pp-panel">
                <h2 className="pp-h2">Admin role matrix (live policy)</h2>
                <table className="pp-table">
                  <thead><tr><th>Role</th><th>Allowed</th><th>Denied</th></tr></thead>
                  <tbody>
                    {ADMIN_ROLES.map((r) => {
                      const allowed = ADMIN_ROLE_ACTIONS[r.id] ?? []
                      const denied = ADMIN_ACTIONS.filter((a) => !allowed.includes(a.id))
                      return (
                        <tr key={r.id}>
                          <td>{r.label}</td>
                          <td>{allowed.map((id) => ADMIN_ACTIONS.find((a) => a.id === id)?.label ?? id).join(', ') || '—'}</td>
                          <td className="pp-warn">{denied.map((a) => a.label).join(', ')}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
                <p className="pp-muted" style={{ fontSize: 12.5 }}>Enforcement is not cosmetic: a direct domain call with a role outside this matrix is refused and written to audit as admin.denied. License decisions additionally require the decision function to receive and validate actorRole — the UI never decides alone.</p>
              </article>
            </section>
          )}

          {section === 'risk' && (
            <section className="pp-stack">
              <h1 className="pp-h1">Risk &amp; Audit</h1>
              <p className="pp-muted pp-body">Allowed and refused management actions are both written to audit. Denied attempts appear as admin.denied / admin.decision_denied and never include credentials, card numbers or other secrets.</p>
              <p style={{ fontWeight: 600, margin: '14px 0 6px' }}>Application &amp; license audit</p>
              <div className="pp-item-list">
                {store.audit.length === 0 && <p className="pp-note">No application/decision audit entries yet.</p>}
                {store.audit.slice().reverse().map((a, idx) => (
                  <div key={`s-${a.at}-${a.action}-${idx}`} className="pp-item-row">
                    <div className="pp-item-main">
                      <div className="pp-item-title">{a.action}</div>
                      <div className="pp-item-sub">{a.detail}</div>
                    </div>
                    <span className="pp-chip">{a.actor}</span>
                    <span className="pp-chip">{a.at.slice(0, 16).replace('T', ' ')} UTC</span>
                  </div>
                ))}
              </div>
              <p style={{ fontWeight: 600, margin: '18px 0 6px' }}>Business audit</p>
              <div className="pp-item-list">
                {biz.audit.slice().reverse().map((a, idx) => (
                  <div key={`${a.at}-${a.action}-${idx}`} className="pp-item-row">
                    <div className="pp-item-main">
                      <div className="pp-item-title">{a.action}</div>
                      <div className="pp-item-sub">{a.detail}</div>
                    </div>
                    <span className="pp-chip">{a.actorLabel}</span>
                    <span className="pp-chip">{a.actorRole}</span>
                    <span className="pp-chip">{a.at.slice(0, 16).replace('T', ' ')} UTC</span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </main>
      </div>
      <footer className="pp-footer">Candidate concept only — golden admin routes, DB/API and production config are untouched. All people, licenses, accounts and photos in this store are fictional.</footer>
    </div>
  )

  function decide(action: 'approve' | 'supplement' | 'reject') {
    if (!selected) return
    const res = adminDecision(selected.id, action, note.trim(), { actorRole: roleId })
    setStore(res.state)
    setResult(res.ok ? { ok: true, message: `Decision recorded: ${action}.` } : { ok: false, message: res.error ?? 'Decision blocked.' })
    if (res.ok) setNote('')
  }

  function lifecycle(status: 'suspended' | 'expired') {
    if (!selected) return
    const res = adminLifecycle(selected.id, status, lifecycleNote.trim() || 'Admin lifecycle change (prototype).', { actorRole: roleId })
    setStore(res.state)
    setResult(res.ok ? { ok: true, message: `Lifecycle change recorded: ${status}.` } : { ok: false, message: res.error ?? 'Lifecycle blocked.' })
  }
}

function lastRisk(app: Application): string | undefined {
  const s = app.aiSuggestions[app.aiSuggestions.length - 1]
  return s?.riskLevel
}

function AiReviewCard({ app }: { app: Application }) {
  const s = app.aiSuggestions[app.aiSuggestions.length - 1]
  if (!s) return (
    <article className="pp-panel">
      <h2 className="pp-h2">AI review summary</h2>
      <p className="pp-muted">No AI review yet for this application state.</p>
    </article>
  )
  return (
    <article className="pp-panel">
      <h2 className="pp-h2">AI review summary <span className={`pp-risk pp-risk-${s.riskLevel}`}>{s.riskLevel} risk</span></h2>
      <p className="pp-muted" style={{ fontSize: 12.5 }}>Reviewed {s.reviewedAt}. Suggestion: <strong>{s.recommendation}</strong> — never a final decision; a reviewer decides.</p>
      <div className="pp-kv">
        <span className="pp-label">OCR name</span><span>{s.ocr.fullName}</span>
        <span className="pp-label">OCR numbers</span><span>{s.ocr.licenseNumbers.join(', ') || '—'}</span>
        <span className="pp-label">Name consistent</span><span>{bool(s.checks.nameConsistent)}</span>
        <span className="pp-label">Number consistent</span><span>{bool(s.checks.numberConsistent)}</span>
        <span className="pp-label">Issuer consistent</span><span>{bool(s.checks.issuerConsistent)}</span>
        <span className="pp-label">Expiry valid</span><span>{bool(s.checks.expiryValid)}</span>
        <span className="pp-label">Image quality</span><span>{s.imageQuality}</span>
        <span className="pp-label">Missing materials</span><span>{s.missingMaterials.length ? s.missingMaterials.join(', ') : 'none'}</span>
        <span className="pp-label">Official database</span><span>{s.officialDb.status.replace(/_/g, ' ')} — {s.officialDb.note}</span>
      </div>
      {s.flags.length > 0 && (
        <ul className="pp-list">
          {s.flags.map((f) => <li key={f}>{f}</li>)}
        </ul>
      )}
    </article>
  )
}

function bool(v: boolean): string {
  return v ? 'yes' : 'no'
}
