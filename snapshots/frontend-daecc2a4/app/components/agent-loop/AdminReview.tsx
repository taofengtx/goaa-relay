'use client'

/**
 * AdminReview.tsx — minimal agent-review surface for administrators.
 *
 * The whole existing administrator back office is NOT rewritten; this is one
 * additional page. Every request goes through /admin/* on the API and is
 * rejected with 403 unless the caller holds the admin role.
 *
 * The audit stream is read-only here: `agent_review_events` is append-only in
 * the database, and this page never offers a way to edit or delete history.
 */

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import Shell from './Shell'
import { api, ApiError } from '@/app/lib/agent-loop/api'
import type { Application, AuditEvent, DocumentRow, SessionUser } from '@/app/lib/agent-loop/api'

const FILTERS = ['', 'submitted', 'info_requested', 'approved', 'rejected', 'suspended', 'draft']

function newKey(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return `decide-${Math.random().toString(36).slice(2)}`
}

export default function AdminReview({
  user,
  initialQueue,
  clerkAuth,
}: {
  user: SessionUser
  /** Server-decided: this deployment signs people in through Clerk. */
  clerkAuth?: boolean
  initialQueue: Application[]
}) {
  const [items, setItems] = useState<Application[]>(initialQueue)
  const [filter, setFilter] = useState('')
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<{ application: Application; events: AuditEvent[] } | null>(null)
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)
  const [docUrls, setDocUrls] = useState<Record<string, string>>({})

  const reloadQueue = useCallback(
    async (status: string) => {
      try {
        const res = await api.adminQueue(status || undefined)
        setItems(res.items)
      } catch (err) {
        setError(err instanceof ApiError ? `${err.code}: ${err.message}` : 'could not load the queue')
      }
    },
    [],
  )

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    setDetail(null)
    setDocUrls({})
    void (async () => {
      try {
        const res = await api.adminDetail(selected)
        if (cancelled) return
        setDetail(res)
      } catch (err) {
        if (cancelled) return
        setError(err instanceof ApiError ? `${err.code}: ${err.message}` : 'could not load the application')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [selected])

  function openDocument(doc: DocumentRow) {
    setDocUrls((m) => ({ ...m, [doc.id]: api.documentContentUrl(doc.id) }))
  }

  async function decide(action: 'approve' | 'reject' | 'request-info' | 'suspend') {
    if (!detail) return
    setBusy(action)
    setError(null)
    setInfo(null)
    try {
      const body: Record<string, unknown> =
        action === 'approve' ? {} : { reason: reason || undefined }
      const res = await api.adminDecide(detail.application.id, action, body, newKey())
      if (res.application) {
        const refreshed = await api.adminDetail(detail.application.id)
        setDetail(refreshed)
      }
      setInfo(`admin.${action} applied.`)
      setReason('')
      await reloadQueue(filter)
    } catch (err) {
      setError(err instanceof ApiError ? `${err.code}: ${err.message}` : `${action} failed`)
    } finally {
      setBusy(null)
    }
  }

  async function rerunAi() {
    if (!detail) return
    setBusy('rerun-ai')
    setError(null)
    try {
      await api.adminRerunAi(detail.application.id)
      const refreshed = await api.adminDetail(detail.application.id)
      setDetail(refreshed)
      setInfo('pre-review recomputed (advisory only).')
    } catch (err) {
      setError(err instanceof ApiError ? `${err.code}: ${err.message}` : 'could not re-run the pre-review')
    } finally {
      setBusy(null)
    }
  }

  const app = detail?.application
  const preReview = app?.pre_review

  return (
    <Shell user={user} canEnterAgent={false} clerkAuth={clerkAuth}>
      <div className="pp-layout">
        <nav className="pp-rail" aria-label="admin navigation">
          <Link className="pp-rail-item" href="/agent-loop/customer">
            <span className="pp-rail-ic" aria-hidden="true">
              ←
            </span>
            <span>User dashboard</span>
          </Link>
          <button type="button" className="pp-rail-item pp-active" data-testid="admin-rail-queue">
            <span className="pp-rail-ic" aria-hidden="true">
              🛡️
            </span>
            <span>Agent review</span>
          </button>
          <span className="pp-rail-kicker">admin role required · server-verified</span>
        </nav>

        <main className="pp-main" data-testid="admin-main">
          <div className="pp-stack">
            <section className="pp-panel">
              <div className="pp-section-head">
                <div>
                  <h1 className="pp-h1">Agent review queue</h1>
                  <p className="pp-muted" style={{ marginBottom: 0 }}>
                    Every decision below is written to the append-only audit stream. The pre-review
                    is advisory: it cannot approve and it cannot change a status.
                  </p>
                </div>
                <span className="pp-badge">admin · {user.email}</span>
              </div>

              <div className="pp-tabs">
                {FILTERS.map((f) => (
                  <button
                    key={f || 'all'}
                    type="button"
                    className={`pp-tab${filter === f ? ' pp-active' : ''}`}
                    data-testid={`admin-filter-${f || 'all'}`}
                    onClick={() => {
                      setFilter(f)
                      void reloadQueue(f)
                    }}
                  >
                    {f || 'all'}
                  </button>
                ))}
              </div>

              {error ? (
                <p className="pp-err" data-testid="admin-error">
                  {error}
                </p>
              ) : null}
              {info ? (
                <p className="pp-ok" data-testid="admin-info">
                  {info}
                </p>
              ) : null}

              <table className="pp-table">
                <thead>
                  <tr>
                    <th>Applicant</th>
                    <th>Contact</th>
                    <th>Status</th>
                    <th>Updated</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id} data-testid="admin-queue-row">
                      <td>{item.full_name || '—'}</td>
                      <td className="pp-mono">{item.email}</td>
                      <td>
                        <span className="pp-status pp-status-muted">{item.status}</span>
                      </td>
                      <td>{new Date(item.updated_at).toLocaleString()}</td>
                      <td>
                        <button
                          type="button"
                          className="pp-btn pp-btn-ghost"
                          data-testid={`admin-open-${item.id}`}
                          onClick={() => setSelected(item.id)}
                        >
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="pp-muted" data-testid="admin-queue-empty">
                        queue is empty for this filter
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </section>

            {app ? (
              <section className="pp-panel" data-testid="admin-detail">
                <div className="pp-section-head">
                  <h2 className="pp-h2">Application {app.id}</h2>
                  <span className="pp-status pp-status-muted">{app.status}</span>
                </div>

                <div className="pp-kv">
                  <span className="pp-label">Applicant</span>
                  <span data-testid="admin-applicant-name">{app.full_name || '—'}</span>
                  <span className="pp-label">E-mail (masked)</span>
                  <span className="pp-mono" data-testid="admin-applicant-email">
                    {app.email}
                  </span>
                  <span className="pp-label">Phone</span>
                  <span>{app.phone || '—'}</span>
                  <span className="pp-label">Address (masked)</span>
                  <span>{app.address || '—'}</span>
                  <span className="pp-label">Submitted</span>
                  <span>{app.submitted_at ? new Date(app.submitted_at).toLocaleString() : 'not submitted'}</span>
                </div>

                <h3 className="pp-h3" style={{ marginTop: 14 }}>
                  Licences
                </h3>
                <table className="pp-table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Number</th>
                      <th>Region</th>
                      <th>Issuer</th>
                      <th>Expires</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(app.licenses || []).map((lic) => (
                      <tr key={lic.id} data-testid="admin-license-row">
                        <td>{lic.license_type}</td>
                        <td className="pp-mono">{lic.license_number}</td>
                        <td>{lic.jurisdiction || '—'}</td>
                        <td>{lic.issuer || '—'}</td>
                        <td>{lic.no_expiry ? 'no expiry' : lic.expires_on || '—'}</td>
                      </tr>
                    ))}
                    {(app.licenses || []).length === 0 ? (
                      <tr>
                        <td colSpan={5} className="pp-muted">
                          no licence on file
                        </td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>

                <h3 className="pp-h3" style={{ marginTop: 14 }}>
                  Documents
                </h3>
                <table className="pp-table">
                  <thead>
                    <tr>
                      <th>Side</th>
                      <th>Type</th>
                      <th>Storage</th>
                      <th>Scan</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {(app.documents || []).map((doc) => (
                      <tr key={doc.id} data-testid="admin-document-row">
                        <td>{doc.side}</td>
                        <td className="pp-mono">{doc.mime_type}</td>
                        <td>{doc.storage_label}</td>
                        <td>{doc.scan_status}</td>
                        <td>
                          <button
                            type="button"
                            className="pp-btn pp-btn-ghost"
                            data-testid={`admin-view-document-${doc.id}`}
                            onClick={() => void openDocument(doc)}
                          >
                            Secure view
                          </button>
                        </td>
                      </tr>
                    ))}
                    {(app.documents || []).length === 0 ? (
                      <tr>
                        <td colSpan={5} className="pp-muted">
                          no document uploaded
                        </td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
                {Object.entries(docUrls).map(([id, url]) => (
                  <div className="pp-panel-inner" key={id}>
                    <span className="pp-label">served through the BFF · short lived · owner bound</span>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={url}
                      alt="synthetic licence document"
                      data-testid={`admin-document-image-${id}`}
                      style={{ maxWidth: '100%', borderRadius: 10, border: '1px solid #2a3450' }}
                    />
                  </div>
                ))}

                <div className="pp-section-head" style={{ marginTop: 16 }}>
                  <h3 className="pp-h3" style={{ marginBottom: 0 }}>
                    Pre-review
                  </h3>
                  <span className="pp-chip pp-flag">advisory only — reference, not a decision</span>
                </div>
                {preReview ? (
                  <div className="pp-panel-inner">
                    <div className="pp-kv">
                      <span className="pp-label">Engine</span>
                      <span className="pp-mono">
                        {preReview.engine} · {preReview.mode}
                      </span>
                      <span className="pp-label">Recommendation</span>
                      <span data-testid="admin-pre-review-recommendation">{preReview.recommendation}</span>
                      <span className="pp-label">Can auto-approve</span>
                      <span data-testid="admin-pre-review-auto-approve">
                        {String(preReview.can_auto_approve)}
                      </span>
                      <span className="pp-label">Docs / licences</span>
                      <span>
                        {preReview.document_count} / {preReview.license_count} · expired{' '}
                        {preReview.expired_licenses}
                      </span>
                    </div>
                    <ul className="pp-list">
                      {preReview.reasons.map((r) => (
                        <li key={r}>{r}</li>
                      ))}
                      {preReview.reasons.length === 0 ? <li>no rule flagged anything</li> : null}
                    </ul>
                  </div>
                ) : (
                  <p className="pp-muted">no pre-review stored yet</p>
                )}

                <h3 className="pp-h3" style={{ marginTop: 16 }}>
                  Review history (append-only)
                </h3>
                <table className="pp-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Action</th>
                      <th>Actor</th>
                      <th>When</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(detail?.events || []).map((ev) => (
                      <tr key={ev.id} data-testid="admin-event-row">
                        <td>{ev.id}</td>
                        <td className="pp-mono">{ev.action}</td>
                        <td>{ev.actor_role}</td>
                        <td>{new Date(ev.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                    {(detail?.events || []).length === 0 ? (
                      <tr>
                        <td colSpan={4} className="pp-muted">
                          no events
                        </td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
                <p className="pp-footnote">
                  History is written by the server only. There is no edit or delete control here.
                </p>

                <h3 className="pp-h3" style={{ marginTop: 16 }}>
                  Decision
                </h3>
                <label className="pp-field">
                  <span>Reason / note (recorded in the audit stream)</span>
                  <textarea
                    className="pp-textarea"
                    data-testid="admin-reason"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </label>
                <div className="pp-actions">
                  <button
                    type="button"
                    className="pp-btn pp-btn-primary"
                    data-testid="admin-approve"
                    disabled={busy !== null}
                    onClick={() => void decide('approve')}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="pp-btn pp-btn-secondary"
                    data-testid="admin-request-info"
                    disabled={busy !== null}
                    onClick={() => void decide('request-info')}
                  >
                    Request more information
                  </button>
                  <button
                    type="button"
                    className="pp-btn pp-btn-danger"
                    data-testid="admin-reject"
                    disabled={busy !== null}
                    onClick={() => void decide('reject')}
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    className="pp-btn pp-btn-danger"
                    data-testid="admin-suspend"
                    disabled={busy !== null}
                    onClick={() => void decide('suspend')}
                  >
                    Suspend
                  </button>
                  <button
                    type="button"
                    className="pp-btn pp-btn-ghost"
                    data-testid="admin-rerun-ai"
                    disabled={busy !== null}
                    onClick={() => void rerunAi()}
                  >
                    Re-run pre-review
                  </button>
                </div>
              </section>
            ) : null}
          </div>
        </main>
      </div>
      <footer className="pp-footer">
        C2 isolated candidate · admin role verified on the server for every /admin/* call
      </footer>
    </Shell>
  )
}
