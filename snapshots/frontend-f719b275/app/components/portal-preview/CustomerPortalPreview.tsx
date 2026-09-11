'use client'

/**
 * CustomerPortalPreview.tsx — isolated /portal-preview/customer candidate.
 *
 * Self-contained: imports ONLY the new portal-preview CSS and the prototype
 * store/core/business libs. It never imports or touches a golden component,
 * route, navigation, middleware or style sheet.
 *
 * CUSTOMER POWER BOUNDARY
 *   This portal is the account holder's own dashboard:
 *     - Chat / Matters / Skills Marketplace (AI assistant area),
 *     - Get Licensed / Earning Opportunities (personal growth area).
 *   The Customer can browse skills as products and manage enabled ones; it
 *   can start / resume / save an application, attach simulated photo
 *   metadata, submit (or resubmit after a supplement request), activate
 *   through the one-time link after approval, and READ status/result.
 *   On Matters the Customer performs REAL customer actions: accept/reject a
 *   quote, accept work or request changes, pay an issued invoice. These are
 *   account-holder actions verified against matter.clientEmail; they are
 *   never admin approval buttons.
 *   There are NO admin decision buttons here — no approve, no supplement
 *   request, no reject, no lifecycle change. Decisions happen in the Admin
 *   Portal Preview through the shared prototype store.
 */

import { useEffect, useMemo, useState } from 'react'
import {
  type Application,
  type ApplyStatus,
} from '../../lib/portal-preview/preview-core'
import {
  applySeedToStoredState,
  customerActivate,
  customerApplicationFor,
  customerAttachPhotos,
  customerStartApplication,
  customerSubmitApplication,
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
  type AccountRecord,
  type BusinessState,
  customerAcceptsQuote,
  customerAcceptsWork,
  customerPaysInvoice,
  customerRejectsQuote,
  customerRequestsWorkChanges,
  type Invoice,
  type Matter,
  type OpResult,
} from '../../lib/portal-preview/preview-business'
import '../../portal-preview/portal-preview.css'

const LICENSE_CATEGORY_LABEL: Record<string, string> = {
  insurance: 'Insurance (Life/Health/P&C)',
  real_estate: 'Real Estate',
  cdl: 'Commercial Driver License (CDL)',
  tax: 'Tax / Enrolled Agent',
  standard_drivers_license: 'Standard Driver License (identity only)',
  other: 'Other regulated occupation',
}

const STATUS_LABEL: Record<ApplyStatus, string> = {
  draft: 'Draft',
  submitted: 'Under Review',
  ai_review: 'Under Review',
  supplement_required: 'Supplement Required',
  approved: 'Approved',
  rejected: 'Not Approved',
  suspended: 'Access Paused',
  expired: 'License Expired',
}

function statusTone(status: ApplyStatus | undefined): string {
  if (!status || status === 'draft') return 'muted'
  if (status === 'submitted' || status === 'ai_review') return 'review'
  if (status === 'approved') return 'good'
  return 'warn'
}

type NavId = 'chat' | 'matters' | 'skills' | 'licensed' | 'earning'

interface NavDef {
  id: NavId
  label: string
  icon: string
  kicker?: string
}

const NAV_ITEMS: NavDef[] = [
  { id: 'chat', label: 'Chat', icon: '💬' },
  { id: 'matters', label: 'Matters', icon: '🗂️' },
  { id: 'skills', label: 'Skills Marketplace', icon: '🧰' },
  { id: 'licensed', label: 'Get Licensed', icon: '📜', kicker: 'NEW' },
  { id: 'earning', label: 'Earning Opportunities', icon: '💡', kicker: 'NEW' },
]

interface SkillDef {
  id: string
  name: string
  desc: string
  price: string
  source: string
  enabled: boolean
}

const SKILLS: SkillDef[] = [
  { id: 's1', name: 'Compliance Monitor', desc: 'Watches filing windows and license expiry dates for your AI assistant.', price: 'Free', source: 'GOAA first-party', enabled: true },
  { id: 's2', name: 'Client Intake', desc: 'Collects client basics and calendars discovery calls.', price: 'Free', source: 'GOAA first-party', enabled: true },
  { id: 's3', name: 'Form Prefill', desc: 'Fills routine state forms from your saved answers.', price: '$19/month', source: 'GOAA add-on', enabled: false },
  { id: 's4', name: 'Pipedream Connector', desc: 'Bridge GOAA tasks into your Pipedream workflows.', price: '$9/month', source: 'Pipedream marketplace', enabled: false },
]

const COURSES = [
  { id: 'c1', name: 'Insurance Basics — Life/Health', hours: '12h', cost: 'Free', partner: 'GOAA partner curriculum' },
  { id: 'c2', name: 'Property & Casualty Foundations', hours: '20h', cost: 'Free', partner: 'GOAA partner curriculum' },
  { id: 'c3', name: 'Real Estate License Prep', hours: '30h', cost: 'Free', partner: 'State-approved course partner' },
  { id: 'c4', name: 'CDL Entry Level Driver Training', hours: '40h', cost: 'Free', partner: 'FMCSA-registered training partner' },
]

function stageLabel(m: Matter): string {
  switch (m.stage) {
    case 'quote_awaiting_accept': return 'Quote awaiting your decision'
    case 'quote_declined': return 'Quote declined'
    case 'in_progress': return 'In progress — agent is working'
    case 'deliverables_uploaded': return 'Deliverables uploaded'
    case 'work_awaiting_accept': return 'Work awaiting your acceptance'
    case 'rework_requested': return 'Changes requested — agent is revising'
    case 'work_accepted': return 'Work accepted'
    case 'invoice_issued': return 'Invoice issued'
    case 'paid': return 'Paid'
    case 'completed': return 'Completed'
    default: return m.stage.replace(/_/g, ' ')
  }
}

export default function CustomerPortalPreview() {
  const [nav, setNav] = useState<NavId>('chat')
  const [store, setStore] = useState<PortalPreviewState>(() => defaultState())
  const [biz, setBiz] = useState<BusinessState>(() => readBusinessState())
  const [notice, setNotice] = useState('')
  const [errors, setErrors] = useState<string[]>([])
  const [learnView, setLearnView] = useState(false)
  const [changeNote, setChangeNote] = useState<Record<string, string>>({})
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search)
      const seed = params.get('seed')
      if (seed && isSeedKind(seed)) {
        const next = applySeedToStoredState(seed)
        setStore(next)
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

  const myApp = useMemo(() => customerApplicationFor(store), [store])
  const account = useMemo<AccountRecord | undefined>(() => biz.accounts.find((a) => a.email === biz.sessionEmail), [biz])
  const canSwitchAgent = !!account && account.roles.includes('agent') && account.agentAccess === 'activated'
  const initials = (account?.displayName ?? 'Guest').split(/\s+/).map((w) => w[0] ?? '').slice(0, 2).join('').toUpperCase()

  const clientMatters = useMemo(
    () => biz.matters
      .filter((m) => account && m.clientEmail === account.email)
      .slice()
      .sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1)),
    [biz, account],
  )

  function refresh(next?: PortalPreviewState) {
    setStore(next ?? readPortalPreviewState())
    setErrors([])
  }

  function bizFlash(msg: string, isErr = false) {
    setNotice(msg)
    if (isErr) setErrors([msg]); else setErrors([])
  }

  function doBizAction(res: OpResult, okMsg: string) {
    if (!res.ok) {
      bizFlash(res.error ?? 'Action blocked.', true)
      return
    }
    if (res.state) setBiz(writeBusinessState(res.state))
    bizFlash(okMsg)
  }

  function signOut() {
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.removeItem(PREVIEW_STORE_KEY)
        window.localStorage.removeItem(BUSINESS_STORE_KEY)
      } catch {
        // preview storage is best-effort
      }
      window.location.href = '/portal-preview'
    }
  }

  const activeSection = useMemo(() => {
    if (nav === 'chat') return { title: 'Chat', body: 'Your chat threads continue to live in the golden Chat view. The rail item shows where this sits next to the AI assistant area.' }
    if (nav === 'matters') return { title: 'Matters', body: 'Real account-holder actions for matters where you are the client: quotes, deliverables and invoices.' }
    if (nav === 'skills') return { title: 'Skills Marketplace', body: 'Products that add capabilities to your AI assistant. Free and monthly-priced skills appear here like a marketplace.' }
    if (nav === 'licensed') return { title: 'Get Licensed', body: 'Two independent paths: learn first, or apply directly when you already hold a license. Both lead to the same application pipeline.' }
    if (nav === 'earning') return { title: 'Earning Opportunities', body: 'Paid task previews, partner courses and membership referrals for the growth area.' }
    return { title: '', body: '' }
  }, [nav])

  function railButton(item: NavDef, i: number) {
    return (
      <div key={item.id}>
        {i === 3 && <div className="pp-rail-sep" />}
        <button className={`pp-rail-item ${nav === item.id ? 'pp-active' : ''}`} onClick={() => setNav(item.id)}>
          <span className="pp-rail-ic">{item.icon}</span>
          <span>{item.label}</span>
          {item.kicker && <span className="pp-new-tag">{item.kicker}</span>}
        </button>
      </div>
    )
  }

  return (
    <div className="pp-root pp-customer">
      <header className="pp-topbar">
        <div className="pp-brand">GOAA <span className="pp-brand-sub">portal preview — customer</span></div>
        <div className="pp-topbar-right">
          <span className="pp-badge">Candidate concept · not production</span>
          {account && (
            <div className="pp-user-area">
              <button className="pp-user-btn" onClick={() => setMenuOpen((v) => !v)} aria-label="Open account menu">
                <span className="pp-user-avatar">{initials}</span>
                <span className="pp-user-meta">
                  <strong style={{ fontSize: 13 }}>{account.displayName}</strong>
                  <span className="pp-muted" style={{ fontSize: 11 }}>Customer account</span>
                </span>
                <span className="pp-user-caret">▾</span>
              </button>
              {menuOpen && (
                <div className="pp-user-pop">
                  <div className="pp-user-head">
                    <div className="pp-user-name">{account.displayName}</div>
                    <div className="pp-user-email">{account.email}</div>
                  </div>
                  <button className="pp-menu-item" onClick={() => { setNav('chat'); setMenuOpen(false) }}>🏠 User Dashboard</button>
                  {canSwitchAgent && (
                    <button className="pp-menu-item" onClick={() => { window.location.href = '/portal-preview/agent?seed=activated' }}>🔄 Switch to Agent Portal</button>
                  )}
                  <button className="pp-menu-item" onClick={() => { window.location.href = '/portal-preview/settings?seed=activated' }}>⚙️ Account Settings…</button>
                  <div className="pp-menu-sep" />
                  <button className="pp-menu-item pp-menu-danger" onClick={signOut}>↩ Sign Out</button>
                </div>
              )}
            </div>
          )}
        </div>
      </header>
      <div className="pp-layout">
        <nav className="pp-rail">
          {NAV_ITEMS.map(railButton)}
        </nav>

        <main className="pp-main">
          <h1 className="pp-h1">{activeSection.title}</h1>
          <p className="pp-muted pp-body">{activeSection.body}</p>

          {nav === 'chat' && (
            <section className="pp-panel">
              <h2 className="pp-h2">Chat</h2>
              <p className="pp-muted">The full assistant conversation lives in the golden Chat experience; this preview confirms the rail placement inside the AI assistant area, above the growth divider.</p>
              <p className="pp-note">Nothing in this preview re-hosts a golden view.</p>
            </section>
          )}

          {nav === 'matters' && (
            <section className="pp-stack">
              {notice && <p className="pp-note">{notice}</p>}
              {errors.map((e) => <p key={e} className="pp-errors" style={{ marginTop: 8 }}>{e}</p>)}
              {clientMatters.length === 0 && (
                <article className="pp-panel"><p className="pp-muted">No matters are assigned to your customer account in this preview world.</p></article>
              )}
              {clientMatters.map((m) => {
                const invoice: Invoice | undefined = biz.invoices.find((i) => i.matterId === m.id)
                return (
                  <article key={m.id} className="pp-panel">
                    <div className="pp-card-head">
                      <div>
                        <h2 className="pp-h2" style={{ margin: 0 }}>{m.title}</h2>
                        <p className="pp-muted" style={{ margin: '4px 0 0', fontSize: 12.5 }}>{m.id} · {m.category} · Agent {m.agentEmail}</p>
                      </div>
                      <span className={`pp-status pp-status-${m.stage === 'quote_declined' || m.stage === 'rework_requested' ? 'warn' : m.stage === 'completed' || m.stage === 'paid' ? 'good' : 'review'}`}>{stageLabel(m)}</span>
                    </div>
                    <div className="pp-chip-row" style={{ marginTop: 10 }}>
                      {m.quoteAmountUsd != null && <span className="pp-chip">Quote ${m.quoteAmountUsd.toFixed(2)}</span>}
                      <span className="pp-chip">Updated {m.updatedAt.slice(0, 16).replace('T', ' ')} UTC</span>
                      {invoice && <span className="pp-chip">{invoice.number} · ${invoice.amountUsd.toFixed(2)} · {invoice.status}</span>}
                    </div>

                    {m.stage === 'quote_awaiting_accept' && (
                      <div className="pp-actions">
                        <button className="pp-btn pp-btn-primary" onClick={() => doBizAction(customerAcceptsQuote(biz, { email: account?.email, matterId: m.id }), 'Quote accepted. The agent can begin work.')}>Accept Quote</button>
                        <button className="pp-btn pp-btn-secondary" onClick={() => doBizAction(customerRejectsQuote(biz, { email: account?.email, matterId: m.id }), 'Quote declined.')}>Decline Quote</button>
                      </div>
                    )}

                    {(m.stage === 'work_awaiting_accept' || m.stage === 'deliverables_uploaded') && (
                      <div className="pp-actions">
                        <button className="pp-btn pp-btn-primary" onClick={() => doBizAction(customerAcceptsWork(biz, { email: account?.email, matterId: m.id }), 'Work accepted. Invoicing may proceed.')}>Accept Work</button>
                        <div className="pp-inline-hint" style={{ marginLeft: 0 }}>
                          <textarea className="pp-textarea" rows={2} placeholder="What should the agent change?" value={changeNote[m.id] ?? ''} onChange={(e) => setChangeNote((v) => ({ ...v, [m.id]: e.target.value }))} />
                          <button className="pp-btn pp-btn-secondary" onClick={() => {
                            const note = (changeNote[m.id] ?? '').trim()
                            if (!note) { bizFlash('Describe the requested changes first.', true); return }
                            doBizAction(customerRequestsWorkChanges(biz, { email: account?.email, matterId: m.id, note }), 'Changes requested. The agent is revising.')
                            setChangeNote((v) => ({ ...v, [m.id]: '' }))
                          }}>Request Changes</button>
                        </div>
                      </div>
                    )}

                    {m.stage === 'invoice_issued' && invoice && invoice.status === 'issued' && (
                      <div className="pp-actions">
                        <button className="pp-btn pp-btn-primary" onClick={() => doBizAction(customerPaysInvoice(biz, { email: account?.email, invoiceId: invoice.id }), 'Invoice paid in this preview (card provider, simulated metadata).')}>Pay Invoice</button>
                      </div>
                    )}

                    {m.stage === 'paid' && <p className="pp-good-text">Payment recorded for {invoice?.number ?? 'this matter'}.</p>}
                    {m.stage === 'completed' && <p className="pp-good-text">Order completed. Thank you for working with this preview.</p>}
                  </article>
                )
              })}
              <p className="pp-note">These actions are performed by your logged-in customer account only — review decisions happen in the Admin Portal Preview.</p>
            </section>
          )}

          {nav === 'skills' && (
            <section className="pp-stack">
              {notice && <p className="pp-note">{notice}</p>}
              <div className="pp-item-list">
                {SKILLS.map((s) => (
                  <div key={s.id} className="pp-item-row">
                    <div className="pp-item-main">
                      <div className="pp-item-title">{s.name}</div>
                      <div className="pp-item-sub">{s.desc}</div>
                    </div>
                    <div className="pp-chip-row">
                      <span className="pp-chip">{s.price}</span>
                      <span className="pp-chip">{s.source}</span>
                      <span className={`pp-status pp-status-${s.enabled ? 'good' : 'muted'}`}>{s.enabled ? 'Enabled' : 'Not added'}</span>
                    </div>
                    <div className="pp-inline-actions">
                      {s.enabled
                        ? <button className="pp-btn pp-btn-secondary" onClick={() => bizFlash(`${s.name} management panel is opened in the marketplace preview.`)}>Manage</button>
                        : <button className="pp-btn pp-btn-primary" onClick={() => bizFlash(`${s.name} added to your AI assistant for $9–$19/month (simulated checkout).`)}>Add</button>}
                    </div>
                  </div>
                ))}
              </div>
              <p className="pp-note">Skills Marketplace sits above the personal growth divider: these are capabilities for your AI assistant, not customer courses.</p>
            </section>
          )}

          {nav === 'earning' && (
            <section className="pp-stack">
              <article className="pp-panel">
                <h2 className="pp-h2">Paid task preview</h2>
                <p className="pp-muted">A fictional, non-binding paid task: “Help a neighbor compare two auto quotes” — $18 per completed task.</p>
              </article>
              <article className="pp-panel">
                <h2 className="pp-h2">Partner course rewards</h2>
                <p className="pp-muted">Finish partner courses under Get Licensed and earn preview badges for your customer profile. Insurance revenue is never a referral base.</p>
              </article>
              <article className="pp-panel">
                <h2 className="pp-h2">Membership referral</h2>
                <p className="pp-muted">When your GOAA membership is active, a referred friend who activates the $99/month plan earns you a fictional $20 preview credit. Commissions, premiums and policy sales never qualify for referral rewards.</p>
              </article>
              <p className="pp-note">Earning Opportunities are shown as content only. Payment, payouts and referral settlement are Admin Portal Preview finance actions, never customer buttons.</p>
            </section>
          )}

          {nav === 'licensed' && (
            <section className="pp-stack">
              {notice && <p className="pp-note">{notice}</p>}
              <div className="pp-grid-2">
                <article className="pp-panel">
                  <h2 className="pp-h2">Learn &amp; Get Licensed</h2>
                  <p className="pp-muted">Prefer courses first? Choose a regulated occupation, complete partner training, then apply through the same pipeline.</p>
                  <ol className="pp-list">
                    <li>Browse partner courses for insurance, real estate, CDL, tax or another regulated role.</li>
                    <li>Study at your own pace — nothing here is required before the direct path.</li>
                    <li>When ready, Apply directly below; the review pipeline is identical.</li>
                  </ol>
                  <div className="pp-actions">
                    <button className="pp-btn pp-btn-secondary" onClick={() => setLearnView((v) => !v)}>{learnView ? 'Hide courses' : 'Browse training courses'}</button>
                  </div>
                </article>
                <article className="pp-panel">
                  <h2 className="pp-h2">Already hold a license?</h2>
                  <p className="pp-muted">Skip the course queue and Apply directly as an Agent candidate. You can still take courses later for growth.</p>
                  <ul className="pp-list">
                    <li>Professional licenses (insurance, real estate, tax, CDL) qualify for their own category.</li>
                    <li>A standard driver license can be recorded as identity but never grants professional order categories.</li>
                    <li>Submitting does not create a second account — the same customer identity is upgraded after admin review and activation.</li>
                  </ul>
                  <div className="pp-actions">
                    <button className="pp-btn pp-btn-primary" onClick={() => { refresh(customerStartApplication()); setNotice('Draft saved locally in this prototype — nothing submitted yet.') }}>Apply directly</button>
                  </div>
                </article>
              </div>

              {learnView && (
                <article className="pp-panel">
                  <h2 className="pp-h2">Training courses (fictional catalog)</h2>
                  <div className="pp-item-list">
                    {COURSES.map((c) => (
                      <div key={c.id} className="pp-item-row">
                        <div className="pp-item-main">
                          <div className="pp-item-title">{c.name}</div>
                          <div className="pp-item-sub">{c.partner}</div>
                        </div>
                        <span className="pp-chip">{c.hours}</span>
                        <span className="pp-chip">{c.cost}</span>
                        <button className="pp-btn pp-btn-secondary" onClick={() => bizFlash('Preview only: partner course enrollment is reserved for the golden skills marketplace.')}>Enroll</button>
                      </div>
                    ))}
                  </div>
                </article>
              )}

              {myApp ? (
                <ApplicationPanel app={myApp} onRefresh={refresh} setNotice={(m) => { setNotice(m); setErrors([]) }} />
              ) : (
                <p className="pp-note">No application yet — use either independent path above. Direct apply is available even if you never took a course.</p>
              )}
            </section>
          )}
        </main>
      </div>
      <footer className="pp-footer">Candidate concept only — golden portal routes, components, tests, styles and pricing are untouched. All identities, licenses and photos in this preview are fictional; the shared prototype store is local-only.</footer>
    </div>
  )
}

function ApplicationPanel({
  app,
  onRefresh,
  setNotice,
}: {
  app: Application
  onRefresh: (next?: PortalPreviewState) => void
  setNotice: (msg: string) => void
}) {
  const [errors, setErrors] = useState<string[]>([])
  const [clearedPhotos, setClearedPhotos] = useState(false)

  function doStartOrAttach() {
    const res = customerAttachPhotos(app.id)
    onRefresh(res.state)
    if (!res.changed) {
      setErrors(['Photos are already attached to every license in this draft.'])
    } else {
      setErrors([])
      setClearedPhotos(true)
      setNotice('Simulated photo metadata attached to the draft — front photos marked readable.')
    }
  }

  function doSubmit() {
    const res = customerSubmitApplication(app.id)
    onRefresh(res.state)
    if (!res.ok) {
      setErrors(res.errors ?? ['Application could not be submitted.'])
    } else {
      setErrors([])
      setClearedPhotos(false)
      setNotice('Application submitted. Review decisions happen in the Admin Portal Preview.')
    }
  }

  function doActivate() {
    const res = customerActivate(app.id)
    onRefresh(res.state)
    if (!res.ok) {
      setErrors([res.error ?? 'Activation blocked.'])
    } else {
      setErrors([])
      setNotice('Account activated through the one-time link (simulated). No password is stored or displayed.')
    }
  }

  const needsFront = app.licenses.some((l) => l.docs.length === 0)
  const canSubmitDraft = app.status === 'draft' && !needsFront
  const canSubmitSupplement = app.status === 'supplement_required' && clearedPhotos

  return (
    <article className="pp-panel">
      <div className="pp-card-head">
        <h2 className="pp-h2">Application — direct apply</h2>
        <span className={`pp-status pp-status-${statusTone(app.status)}`}>{STATUS_LABEL[app.status]}</span>
      </div>

      <div className="pp-label">Applicant (read-only in this prototype)</div>
      <div className="pp-form-grid">
        <div className="pp-field"><span>Full name</span><input readOnly value={app.applicant.fullName} /></div>
        <div className="pp-field"><span>Phone</span><input readOnly value={app.applicant.phone} /></div>
        <div className="pp-field"><span>Email</span><input readOnly value={app.applicant.email} /></div>
        <div className="pp-field"><span>Address</span><input readOnly value={app.applicant.address} /></div>
      </div>

      <div className="pp-label">Licenses (fictional)</div>
      <table className="pp-table">
        <thead><tr><th>Type</th><th>License number</th><th>State / issuing agency</th><th>Expires</th><th>Photo metadata</th></tr></thead>
        <tbody>
          {app.licenses.map((l) => (
            <tr key={l.localId}>
              <td>{LICENSE_CATEGORY_LABEL[l.category] ?? l.category}</td>
              <td>{l.licenseNumber}</td>
              <td>{l.issuer}</td>
              <td>{l.expiresAt}</td>
              <td>{l.docs.length ? l.docs.map((d) => d.filename).join(', ') : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="pp-footnote">A standard driver license is accepted as identity in this form; it is never auto-promoted to insurance, real estate, tax or other professional order eligibility.</p>

      {errors.length > 0 && (
        <div className="pp-errors">{errors.join(' · ')}</div>
      )}

      {/* Draft state — customer can attach photos and submit */}
      {app.status === 'draft' && (
        <div className="pp-actions">
          <button className="pp-btn pp-btn-secondary" onClick={doStartOrAttach}>Attach license photos (simulated)</button>
          <button className="pp-btn pp-btn-primary" disabled={!canSubmitDraft} onClick={doSubmit}>Submit application</button>
          <span className="pp-muted" style={{ fontSize: 12 }}>{needsFront ? 'Attach photos first — the reviewer needs readable front photos.' : 'Your draft is saved locally; submit when ready.'}</span>
        </div>
      )}

      {/* Under review — strictly read-only */}
      {(app.status === 'submitted' || app.status === 'ai_review') && (
        <div className="pp-panel-inner">
          <h3 className="pp-h3">Under review</h3>
          <p className="pp-muted">Your materials were received and are being verified. You will see the result here — you cannot change your application while it is in review.</p>
          <p className="pp-note" style={{ marginTop: 10 }}>Reviewers may ask for clearer photos before making a decision.</p>
        </div>
      )}

      {/* Supplement required — customer may attach clearer photos and resubmit */}
      {app.status === 'supplement_required' && (
        <div className="pp-panel-inner">
          <h3 className="pp-h3">Supplement required</h3>
          {app.customerMessage && <p className="pp-muted">{app.customerMessage}</p>}
          {!app.customerMessage && <p className="pp-muted">Please upload clearer photos for the listed licenses.</p>}
          <div className="pp-actions">
            <button className="pp-btn pp-btn-secondary" onClick={doStartOrAttach}>Upload clearer photos (simulated)</button>
            <button className="pp-btn pp-btn-primary" disabled={!canSubmitSupplement} onClick={doSubmit}>Resubmit after supplement</button>
          </div>
        </div>
      )}

      {/* Approved — activation entry (customer-side, one-time link) */}
      {app.status === 'approved' && !app.activation?.tokenUsed && (
        <div className="pp-panel-inner">
          <h3 className="pp-h3">Approved</h3>
          <p className="pp-muted">Congratulations — your license materials passed the review. Open the one-time activation link and set your password to continue.</p>
          <div className="pp-actions">
            <button className="pp-btn pp-btn-primary" onClick={doActivate}>Open activation link (simulated)</button>
          </div>
        </div>
      )}

      {/* Activated or later states — outcome only, no admin controls */}
      {(app.status === 'approved' && app.activation?.tokenUsed) || app.status === 'suspended' || app.status === 'expired' ? (
        <div className="pp-panel-inner">
          <h3 className="pp-h3">
            {app.status === 'suspended' ? 'Access paused' : app.status === 'expired' ? 'License expired' : 'Activated'}
          </h3>
          {app.activation?.tokenUsed && app.status === 'approved' ? (
            <>
              <p className="pp-muted">This account is now activated on the same customer identity. Agent Portal access depends on agent review in the Admin Portal Preview.</p>
              <a className="pp-btn pp-btn-primary" href="/portal-preview/agent?seed=activated">Continue to Agent Portal Preview</a>
            </>
          ) : (
            <p className="pp-muted">Your application outcome is final in this preview world. You can start a new application later from Get Licensed if your materials change.</p>
          )}
        </div>
      ) : null}

      {/* Rejected — outcome only */}
      {app.status === 'rejected' && (
        <div className="pp-panel-inner">
          <h3 className="pp-h3">Not approved</h3>
          {app.customerMessage && <p className="pp-muted">{app.customerMessage}</p>}
          <div className="pp-actions">
            <button className="pp-btn pp-btn-secondary" onClick={() => { onRefresh(customerStartApplication()); setNotice('A new draft is ready — correct the materials and resubmit.') }}>Start a new application</button>
          </div>
        </div>
      )}
    </article>
  )
}
