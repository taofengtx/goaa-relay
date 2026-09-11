'use client'

/**
 * AgentPortalPreview.tsx — isolated /portal-preview/agent candidate (phase 2).
 *
 * Self-contained: no golden component/route/lib/CSS is touched.
 *
 * Access gate (license layer, preview-store)
 *   approved + activated + at least one valid license -> open
 *   everything else -> locked with a reason that distinguishes the real
 *   state: not granted yet, approved but not activated, suspended,
 *   expired, etc. The $99/month subscription never opens this page and
 *   approval never grants paid features by itself.
 *
 * Professional workbench (business layer, preview-business-store)
 *   The open workbench lists 11 sections. The agent can only perform
 *   agent-owned steps: accept opportunities, prepare estimates, send
 *   quotes, upload deliverables, request work acceptance, issue invoices,
 *   complete paid orders. There are NO customer simulation controls here —
 *   no "simulate customer acceptance", no "simulate customer payment".
 *   Accepting a quote, accepting work and paying an invoice are customer
 *   actions that only happen on the Customer Portal for matters where the
 *   signed-in account is the client.
 */

import { useEffect, useMemo, useState } from 'react'
import {
  agentAccessFor,
  applySeedToStoredState,
  defaultState,
  isSeedKind,
  PREVIEW_STORE_KEY,
  readPortalPreviewState,
  type PortalPreviewState,
} from '../../lib/portal-preview/preview-store'
import {
  BUSINESS_STORE_KEY,
  applyBusinessSeed,
  readBusinessState,
  writeBusinessState,
} from '../../lib/portal-preview/preview-business-store'
import {
  type BusinessState,
  type Matter,
  type MatterStage,
  agentAcceptOpportunity,
  agentCompleteOrder,
  agentIssueInvoice,
  agentPrepareEstimate,
  agentRequestWorkAcceptance,
  agentSendQuote,
  agentUploadDeliverable,
  mattersVisibleToAgent,
  type AccountRecord,
} from '../../lib/portal-preview/preview-business'
import '../../portal-preview/portal-preview.css'

const SECTIONS = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'opportunities', label: 'Opportunities', icon: '📋' },
  { id: 'matters', label: 'My Matters', icon: '🗂️' },
  { id: 'messages', label: 'Client Messages', icon: '💬' },
  { id: 'quotes', label: 'Estimates & Quotes', icon: '📐' },
  { id: 'deliverables', label: 'Deliverables', icon: '📤' },
  { id: 'invoices', label: 'Invoices', icon: '🧾' },
  { id: 'earnings', label: 'Payments & Earnings', icon: '💰' },
  { id: 'ai', label: 'AI Assistant', icon: '🤖' },
  { id: 'skills', label: 'Skills', icon: '🧰' },
  { id: 'profile', label: 'License & Profile', icon: '🪪' },
] as const
type SectionId = (typeof SECTIONS)[number]['id']

const STAGE_LABEL: Record<MatterStage, string> = {
  opportunity: 'New',
  accepted: 'Accepted',
  estimate_prepared: 'Estimate ready',
  quote_awaiting_accept: 'Waiting on customer',
  quote_declined: 'Quote declined',
  in_progress: 'In progress',
  deliverables_uploaded: 'Deliverables uploaded',
  work_awaiting_accept: 'Awaiting acceptance',
  rework_requested: 'Rework requested',
  work_accepted: 'Accepted by customer',
  invoice_issued: 'Invoice issued',
  paid: 'Paid',
  completed: 'Completed',
}

function tone(stage: MatterStage): string {
  if (stage === 'completed' || stage === 'paid') return 'good'
  if (stage === 'quote_awaiting_accept' || stage === 'work_awaiting_accept' || stage === 'rework_requested') return 'warn'
  return 'review'
}

const SKILL_CARDS = [
  { id: 's1', name: 'Compliance Monitor', source: 'GOAA', price: 'Included · $0', state: 'Installed', desc: 'Watches filing windows and license expiry dates.' },
  { id: 's2', name: 'Client Intake', source: 'GOAA', price: 'Included · $0', state: 'Installed', desc: 'Collects client basics and calendars discovery calls.' },
  { id: 's3', name: 'Tax Document Organizer', source: 'GOAA', price: '$2/month', state: 'Not installed', desc: 'Helps your AI assistant sort tax paperwork by category.' },
  { id: 's4', name: 'Insurance Needs Analysis', source: 'Third party — Riverstone Labs', price: '$3/month', state: 'Not installed', desc: 'Frames discovery questions. Never issues coverage or quotes.' },
  { id: 's5', name: 'International Affairs Brief', source: 'Third party — Halcyon Data', price: '$3/month', state: 'Not installed', desc: 'Country briefings for clients with cross-border matters.' },
  { id: 's6', name: 'Professional Matching', source: 'GOAA', price: 'Included · $0', state: 'Installed', desc: 'Suggests licensed professionals; never bypasses verification.' },
]

const UPLOAD_PRESETS = [
  'work-summary.pdf',
  'completion-notes.pdf',
  'photo-inventory.pdf',
  'final-report.pdf',
]

export default function AgentPortalPreview() {
  const [store, setStore] = useState<PortalPreviewState>(() => defaultState())
  const [biz, setBiz] = useState<BusinessState>(() => readBusinessState())
  const [section, setSection] = useState<SectionId>('overview')
  const [menuOpen, setMenuOpen] = useState(false)
  const [flash, setFlash] = useState<{ ok: boolean; message: string } | null>(null)

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

  const access = useMemo(() => agentAccessFor(store), [store])
  const app = access.application
  const open = access.gate.allowed

  const account = useMemo<AccountRecord | undefined>(() => biz.accounts.find((a) => a.email === biz.sessionEmail), [biz])
  const sessionEmail = account?.email ?? biz.sessionEmail

  const matters = useMemo(() => mattersVisibleToAgent(biz, sessionEmail).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)), [biz, sessionEmail])
  const opportunities = biz.opportunities.filter((o) => o.status === 'open')
  const myInvoices = biz.invoices.filter((i) => i.agentEmail === sessionEmail)
  const paidInvoices = myInvoices.filter((i) => i.status === 'paid')
  const earnings = biz.payments.filter((p) => paidInvoices.some((i) => i.id === p.invoiceId)).reduce((n, p) => n + p.amountUsd, 0)
  const paused = account?.subscription.status === 'paused'

  function runAction(label: string, fn: () => { ok: boolean; state?: BusinessState; error?: string }) {
    const res = fn()
    if (res.ok && res.state) {
      setBiz(writeBusinessState(res.state))
      setFlash({ ok: true, message: `${label} recorded in this preview.` })
    } else {
      setFlash({ ok: false, message: `${label} blocked: ${res.error ?? 'not allowed at this stage.'}` })
    }
    window.setTimeout(() => setFlash(null), 3000)
  }

  const menu = (
    <div className="pp-user-area">
      <button className="pp-user-btn" onClick={() => setMenuOpen((v) => !v)}>
        <span className="pp-user-avatar">{(account?.displayName ?? 'Demo User').slice(0, 1).toUpperCase()}</span>
        <span className="pp-user-meta">
          <strong>{account?.displayName ?? 'Demo User'}</strong>
          <span>{account?.email ?? ''}</span>
        </span>
        <span className="pp-user-caret">{menuOpen ? '▲' : '▼'}</span>
      </button>
      {menuOpen && (
        <div className="pp-user-pop">
          <a className="pp-menu-item" href="/portal-preview/customer?seed=activated">User Dashboard</a>
          <a className="pp-menu-item" href="/portal-preview/customer?seed=activated">Switch to User Portal</a>
          <a className="pp-menu-item" href="/portal-preview/settings?seed=activated">Account Settings</a>
          <button className="pp-menu-item pp-menu-danger" onClick={() => {
            if (typeof window !== 'undefined') {
              try {
                window.localStorage.removeItem(PREVIEW_STORE_KEY)
                window.localStorage.removeItem(BUSINESS_STORE_KEY)
              } catch {
                // preview storage is best-effort
              }
              window.location.href = '/portal-preview'
            }
          }}>Sign Out</button>
        </div>
      )}
    </div>
  )

  if (!open) {
    const subActive = access.subscription === 'active' || access.subscription === 'trial'
    return (
      <div className="pp-root">
        <header className="pp-topbar">
          <div className="pp-brand">GOAA <span className="pp-brand-sub">portal preview — agent</span></div>
          <div className="pp-topbar-right">
            <span className="pp-badge">Candidate concept · not production</span>
            {menu}
          </div>
        </header>
        <div className="pp-gate-card">
          <div className="pp-gate-badge">AGENT PORTAL — ACCESS LOCKED</div>
          <h1 className="pp-h1">Your agent dashboard is not open yet</h1>
          <p className="pp-muted">{access.gate.reason}</p>
          {app && (
            <div className="pp-kv">
              <span className="pp-label">Application status</span>
              <span>{app.status}</span>
              <span className="pp-label">Activated</span>
              <span>{app.activation?.tokenUsed ? 'Yes' : 'No — use the one-time activation link after approval'}</span>
              <span className="pp-label">License review</span>
              <span>{app.status === 'approved' ? 'approved' : 'not approved yet'}</span>
              <span className="pp-label">$99/month subscription</span>
              <span>{subActive ? 'Active (never grants access by itself)' : access.subscription}</span>
            </div>
          )}
          {!app && <p className="pp-note">There is no application for the active demo profile yet. Start the customer flow to see the gate open after approval and activation.</p>}
          <p className="pp-note">Existing paid dashboard routes are untouched. This gate stays closed until review, activation and license validity all pass — the $99/month plan never replaces review.</p>
        </div>
      </div>
    )
  }

  const agentName = account?.displayName ?? app?.applicant?.fullName ?? 'Fictional Agent'

  function stageChips(m: Matter) {
    return (
      <div className="pp-chip-row">
        <span className={`pp-status pp-status-${tone(m.stage)}`}>{STAGE_LABEL[m.stage]}</span>
        <span className="pp-chip">{m.category}</span>
        {m.quoteAmountUsd && <span className="pp-chip">${m.quoteAmountUsd}</span>}
      </div>
    )
  }

  function matterActions(m: Matter) {
    const email = sessionEmail
    const common = { email, matterId: m.id }
    const row: React.ReactNode[] = []
    const push = (label: string, fn: () => { ok: boolean; state?: BusinessState; error?: string }, disabled = false) => row.push(
      <button key={label} className="pp-btn pp-btn-secondary" disabled={disabled} onClick={() => runAction(label, fn)}>{label}</button>,
    )
    if (m.stage === 'accepted' || m.stage === 'estimate_prepared') push('Prepare estimate', () => agentPrepareEstimate(biz, { ...common, amountUsd: m.quoteAmountUsd ?? 180 }))
    if (m.stage === 'estimate_prepared') push('Send quote', () => agentSendQuote(biz, common))
    if (m.stage === 'in_progress' || m.stage === 'deliverables_uploaded' || m.stage === 'rework_requested') {
      const n = m.deliverables.length
      const filename = UPLOAD_PRESETS[n % UPLOAD_PRESETS.length]
      push('Upload deliverable', () => agentUploadDeliverable(biz, { ...common, filename, mimeType: 'application/pdf', sizeBytes: 1024 * (n + 2) }))
    }
    if (m.stage === 'deliverables_uploaded') push('Request acceptance', () => agentRequestWorkAcceptance(biz, common))
    if (m.stage === 'work_accepted') push('Issue invoice', () => agentIssueInvoice(biz, common))
    if (m.stage === 'paid') push('Complete order', () => agentCompleteOrder(biz, common))
    return row.length ? <div className="pp-actions">{row}</div> : null
  }

  function renderSection() {
    switch (section) {
      case 'overview':
        return (
          <div className="pp-stack">
            <div className="pp-section-head">
              <div>
                <h1 className="pp-h1">Overview</h1>
                <p className="pp-muted">Agent workspace for {agentName}. Orders below flow through the same business loop as production: accept → quote → customer accepts → execute → deliver → customer accepts → invoice → customer pays → complete.</p>
              </div>
              <span className="pp-chip">Approved + activated</span>
            </div>
            <div className="pp-cards">
              <article className="pp-card"><div className="pp-card-head"><strong>Open opportunities</strong></div><p className="pp-h2">{opportunities.length}</p><p className="pp-muted">Available to accept from the public preview board.</p></article>
              <article className="pp-card"><div className="pp-card-head"><strong>Active matters</strong></div><p className="pp-h2">{matters.filter((m) => ['in_progress', 'deliverables_uploaded', 'work_awaiting_accept', 'rework_requested'].includes(m.stage)).length}</p><p className="pp-muted">{matters.length} matters total in your visibility set.</p></article>
              <article className="pp-card"><div className="pp-card-head"><strong>Pending invoices</strong></div><p className="pp-h2">{myInvoices.filter((i) => i.status === 'issued').reduce((n, i) => n + i.amountUsd, 0).toFixed(2)} USD</p><p className="pp-muted">Waiting for the customer to pay from the Customer Portal.</p></article>
              <article className="pp-card"><div className="pp-card-head"><strong>Settled earnings</strong></div><p className="pp-h2">${earnings.toFixed(2)}</p><p className="pp-muted">Recorded payments for your invoices.</p></article>
            </div>
            {paused && <p className="pp-note">Your $99/month subscription is paused. License state and agent access are unchanged; paid add-on features are the only thing limited.</p>}
            <article className="pp-panel">
              <h2 className="pp-h2">Recent order activity</h2>
              {matters.length === 0 && <p className="pp-muted">No matters assigned to your agent account yet.</p>}
              <div className="pp-item-list">
                {matters.slice(0, 6).map((m) => (
                  <div key={m.id} className="pp-item-row">
                    <div>
                      <strong>{m.title}</strong>
                      <div className="pp-muted">{m.clientName} · updated {m.updatedAt.slice(11, 16)} UTC</div>
                    </div>
                    {stageChips(m)}
                  </div>
                ))}
              </div>
            </article>
          </div>
        )
      case 'opportunities':
        return (
          <div className="pp-stack">
            <div className="pp-section-head"><div><h1 className="pp-h1">Opportunities</h1><p className="pp-muted">New work published for licensed agents. Accepting creates a matter you own.</p></div></div>
            {opportunities.length === 0 && <p className="pp-muted">No open opportunities right now.</p>}
            {opportunities.map((o) => (
              <article key={o.id} className="pp-panel">
                <div className="pp-card-head"><strong>{o.title}</strong><span className="pp-chip">{o.feeRange}</span></div>
                <p className="pp-muted">{o.clientName} · {o.category} · published {o.createdAt.slice(0, 10)}</p>
                <div className="pp-actions">
                  <button className="pp-btn pp-btn-primary" onClick={() => runAction('Accept opportunity', () => agentAcceptOpportunity(biz, { email: sessionEmail, opportunityId: o.id }))}>Accept opportunity</button>
                </div>
              </article>
            ))}
          </div>
        )
      case 'matters':
        return (
          <div className="pp-stack">
            <div className="pp-section-head"><div><h1 className="pp-h1">My Matters</h1><p className="pp-muted">Only matters assigned to your agent account are visible here.</p></div></div>
            {matters.length === 0 && <p className="pp-muted">No matters assigned to this agent account.</p>}
            {matters.map((m) => (
              <article key={m.id} className="pp-panel">
                <div className="pp-card-head"><strong>{m.title}</strong></div>
                {stageChips(m)}
                <p className="pp-muted">{m.clientName} ({m.clientEmail}) · created {m.createdAt.slice(0, 10)} · {m.deliverables.length} deliverable{m.deliverables.length === 1 ? '' : 's'}</p>
                {matterActions(m)}
              </article>
            ))}
          </div>
        )
      case 'messages':
        return (
          <div className="pp-stack">
            <div className="pp-section-head"><div><h1 className="pp-h1">Client Messages</h1><p className="pp-muted">Threads attached to your matters. In production these connect to the existing chat product; this pane previews placement only.</p></div></div>
            {matters.length === 0 && <p className="pp-muted">No client threads yet.</p>}
            {matters.map((m) => (
              <article key={m.id} className="pp-panel">
                <div className="pp-card-head"><strong>{m.clientName}</strong><span className="pp-chip">Matter {m.id}</span></div>
                <p className="pp-muted">{m.title}</p>
                <p className="pp-note">Last update: {m.updatedAt.slice(11, 16)} UTC · status {STAGE_LABEL[m.stage]}</p>
              </article>
            ))}
          </div>
        )
      case 'quotes':
        return (
          <div className="pp-stack">
            <div className="pp-section-head"><div><h1 className="pp-h1">Estimates &amp; Quotes</h1><p className="pp-muted">Prepare a positive estimate then send the quote. Only the customer can accept it.</p></div></div>
            {matters.filter((m) => ['accepted', 'estimate_prepared', 'quote_awaiting_accept', 'quote_declined'].includes(m.stage)).length === 0 && <p className="pp-muted">No estimates in progress.</p>}
            {matters.filter((m) => ['accepted', 'estimate_prepared', 'quote_awaiting_accept', 'quote_declined'].includes(m.stage)).map((m) => (
              <article key={m.id} className="pp-panel">
                <div className="pp-card-head"><strong>{m.title}</strong>{stageChips(m)}</div>
                <p className="pp-muted">Client: {m.clientName}</p>
                {matterActions(m)}
              </article>
            ))}
            <article className="pp-panel"><h2 className="pp-h2">Quote policy</h2><p className="pp-muted">Estimates are always reviewed and sent by the agent. Customer acceptance and payment happen on the Customer Portal — never simulated from this workbench.</p></article>
          </div>
        )
      case 'deliverables':
        return (
          <div className="pp-stack">
            <div className="pp-section-head"><div><h1 className="pp-h1">Deliverables</h1><p className="pp-muted">Upload metadata for completed work. Files stay fictional in this preview.</p></div></div>
            {matters.length === 0 && <p className="pp-muted">No matters yet.</p>}
            {matters.map((m) => (
              <article key={m.id} className="pp-panel">
                <div className="pp-card-head"><strong>{m.title}</strong>{stageChips(m)}</div>
                {m.deliverables.length === 0 ? <p className="pp-muted">No deliverables uploaded.</p> : (
                  <table className="pp-table">
                    <thead><tr><th>File (metadata)</th><th>Type</th><th>Size</th><th>Uploaded</th></tr></thead>
                    <tbody>
                      {m.deliverables.map((d) => (
                        <tr key={d.filename + d.uploadedAt}><td>{d.filename}</td><td>{d.mimeType}</td><td>{d.sizeBytes} B</td><td>{d.uploadedAt.slice(11, 16)} UTC</td></tr>
                      ))}
                    </tbody>
                  </table>
                )}
                {matterActions(m)}
              </article>
            ))}
          </div>
        )
      case 'invoices':
        return (
          <div className="pp-stack">
            <div className="pp-section-head"><div><h1 className="pp-h1">Invoices</h1><p className="pp-muted">Issue invoices only after the customer accepted the work. Payment is a customer action.</p></div></div>
            {myInvoices.length === 0 && <p className="pp-muted">No invoices for this agent yet.</p>}
            {myInvoices.map((inv) => {
              const m = matters.find((x) => x.id === inv.matterId)
              return (
                <article key={inv.id} className="pp-panel">
                  <div className="pp-card-head"><strong>{inv.number}</strong><span className={`pp-status pp-status-${inv.status === 'paid' ? 'good' : inv.status === 'refund_requested' || inv.status === 'refund_approved' ? 'warn' : 'review'}`}>{inv.status}</span></div>
                  <p className="pp-muted">{m?.title ?? inv.matterId} · ${inv.amountUsd.toFixed(2)} · issued {inv.issuedAt.slice(0, 10)}</p>
                  {inv.paidAt && <p className="pp-muted">Paid {inv.paidAt.slice(0, 10)} by customer.</p>}
                  {inv.status === 'issued' && <p className="pp-note">Awaiting payment from the customer in the Customer Portal.</p>}
                </article>
              )
            })}
            {matters.filter((m) => m.stage === 'work_accepted').map((m) => (
              <article key={m.id} className="pp-panel"><div className="pp-card-head"><strong>{m.title}</strong><span className="pp-chip">work accepted</span></div><p className="pp-muted">Ready to invoice — the next agent-owned step.</p>{matterActions(m)}</article>
            ))}
          </div>
        )
      case 'earnings':
        return (
          <div className="pp-stack">
            <div className="pp-section-head"><div><h1 className="pp-h1">Payments &amp; Earnings</h1><p className="pp-muted">Payments &amp; Earnings is a paid feature of the $99/month subscription. Pausing the subscription hides nothing about license state.</p></div></div>
            {paused && <p className="pp-inline-hint">Subscription paused — Payments &amp; Earnings is limited until the subscription is active again. Agent access and license state are unchanged.</p>}
            <div className="pp-cards">
              <article className="pp-card"><strong>Settled</strong><p className="pp-h2">${earnings.toFixed(2)}</p><p className="pp-muted">{paidInvoices.length} paid invoices</p></article>
              <article className="pp-card"><strong>Outstanding</strong><p className="pp-h2">${myInvoices.filter((i) => i.status === 'issued').reduce((n, i) => n + i.amountUsd, 0).toFixed(2)}</p><p className="pp-muted">Waiting on customer payment</p></article>
            </div>
            {biz.payments.length === 0 && <p className="pp-muted">No payment records yet.</p>}
            {biz.payments.filter((p) => paidInvoices.some((i) => i.id === p.invoiceId)).length === 0 && biz.payments.length > 0 && <p className="pp-muted">Payments recorded for other agents are not visible here.</p>}
            <table className="pp-table">
              <thead><tr><th>Invoice</th><th>Amount</th><th>Received</th></tr></thead>
              <tbody>
                {biz.payments.filter((p) => paidInvoices.some((i) => i.id === p.invoiceId)).map((p) => (
                  <tr key={p.id}><td>{p.invoiceId}</td><td>${p.amountUsd.toFixed(2)}</td><td>{p.receivedAt.slice(0, 16)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      case 'ai':
        return (
          <div className="pp-stack">
            <div className="pp-section-head"><div><h1 className="pp-h1">AI Assistant</h1><p className="pp-muted">AI Assistant is a paid feature of the $99/month subscription. Suggestions never replace licensed advice.</p></div></div>
            {paused && <p className="pp-inline-hint">Subscription paused — AI Assistant is limited until the subscription is active again.</p>}
            <article className="pp-panel">
              <div className="pp-card-head"><strong>Draft summary — {matters[0]?.title ?? 'no active matter'}</strong><span className="pp-chip">fictional</span></div>
              <p className="pp-muted">Draft a short client-facing update for the most recently updated matter, including completed steps and the next milestone.</p>
              <div className="pp-actions"><button className="pp-btn pp-btn-secondary">Suggest draft</button><button className="pp-btn pp-btn-ghost">Regenerate</button></div>
            </article>
            <article className="pp-panel">
              <h2 className="pp-h2">Boundary</h2>
              <p className="pp-muted">AI output in this preview is canned copy. In production it would be reviewed by the licensed professional before it reaches a client — the tool never issues a quote, acceptance, invoice or license decision.</p>
            </article>
          </div>
        )
      case 'skills':
        return (
          <div className="pp-stack">
            <div className="pp-section-head"><div><h1 className="pp-h1">Skills</h1><p className="pp-muted">Skills extend your own AI workspace. Installing a skill never replaces the licensed professional or the compliance rules.</p></div></div>
            <div className="pp-cards">
              {SKILL_CARDS.map((s) => (
                <article key={s.id} className="pp-card">
                  <div className="pp-card-head"><strong>{s.name}</strong><span className={`pp-status ${s.state === 'Installed' ? 'pp-status-good' : 'pp-status-muted'}`}>{s.state}</span></div>
                  <p className="pp-muted">{s.desc}</p>
                  <div className="pp-price-line">{s.price} · {s.source}</div>
                  <div className="pp-actions"><button className="pp-btn pp-btn-secondary">{s.state === 'Installed' ? 'Manage' : 'Install'}</button></div>
                </article>
              ))}
            </div>
          </div>
        )
      case 'profile':
        return (
          <div className="pp-stack">
            <div className="pp-section-head"><div><h1 className="pp-h1">License &amp; Profile</h1><p className="pp-muted">Approval and activation were granted through the Admin Portal Preview; this workbench only reads them.</p></div></div>
            <div className="pp-grid-2">
              <article className="pp-panel"><span className="pp-label">Display name</span><p>{account?.displayName ?? agentName}</p><span className="pp-label">Email</span><p>{account?.email ?? app?.applicant?.email ?? ''}</p><span className="pp-label">Roles</span><p>{(account?.roles ?? ['customer']).join(' + ')}</p></article>
              <article className="pp-panel"><span className="pp-label">Agent username</span><p>{account?.agentUsername ?? '—'}</p><span className="pp-label">Activated at</span><p>{account?.activatedAt ? account.activatedAt.slice(0, 16) : '—'}</p><span className="pp-label">Password</span><p>Set by agent at activation · never generated or stored</p></article>
            </div>
            {app?.licenses && (
              <table className="pp-table">
                <thead><tr><th>License</th><th>Issuer</th><th>Status</th></tr></thead>
                <tbody>
                  {app.licenses.map((l) => (
                    <tr key={l.localId}><td>{l.category.replace('_', ' ').toUpperCase()}</td><td>{l.issuer}</td><td>Verified</td></tr>
                  ))}
                </tbody>
              </table>
            )}
            <article className="pp-panel">
              <h2 className="pp-h2">Plan note</h2>
              <p className="pp-muted">The $99/month subscription never replaces review, never grants access by itself, and pausing it never changes your approved license or activation state. Agent access only opens after a review decision, one-time activation link and self-set password.</p>
            </article>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="pp-root">
      <header className="pp-topbar">
        <div className="pp-brand">GOAA <span className="pp-brand-sub">portal preview — agent</span></div>
        <div className="pp-topbar-right">
          <span className="pp-badge">Candidate concept · not production</span>
          {menu}
        </div>
      </header>
      <div className="pp-layout">
        <aside className="pp-rail">
          <div className="pp-rail-user">
            <strong>{agentName}</strong>
            <span className="pp-muted">{account?.agentUsername ?? 'agent'}</span>
          </div>
          {SECTIONS.map((s) => (
            <button key={s.id} className={`pp-rail-item ${section === s.id ? 'pp-active' : ''}`} onClick={() => setSection(s.id)}>
              <span className="pp-rail-ic">{s.icon}</span><span>{s.label}</span>
            </button>
          ))}
        </aside>
        <main className="pp-main">
          {flash && <p className={`pp-note ${flash.ok ? 'pp-ok' : 'pp-err'}`}>{flash.message}</p>}
          {renderSection()}
          <p className="pp-footnote">No customer actions are simulated on this page. Quotes are accepted, work is accepted and invoices are paid only by the customer on the Customer Portal.</p>
        </main>
      </div>
    </div>
  )
}
