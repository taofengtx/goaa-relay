'use client'

/**
 * ApplicationForm.tsx — "Become an Agent" for the signed-in account.
 *
 * Everything here belongs to the SAME user id as the session: the application
 * is keyed by user_id on the server, no second account is created and no
 * second credential is ever shown or sent.
 *
 * Locking rule: an application is editable only while it is a draft or while
 * an administrator has asked for more information. After submission the server
 * returns 409 `application_locked`; the form mirrors that by disabling edits.
 */

import { useCallback, useMemo, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import Shell from './Shell'
import { api, ApiError } from '@/app/lib/agent-loop/api'
import type { Application, DocumentRow, License, PreReview, SessionUser } from '@/app/lib/agent-loop/api'

const LICENSE_TYPES = ['Insurance', 'Real estate', 'Tax', 'Driver licence', 'Other']
const EDITABLE = new Set(['draft', 'info_requested'])

type DraftLicense = {
  key: string
  id?: string
  license_type: string
  license_number: string
  issuer: string
  jurisdiction: string
  expires_on: string
  no_expiry: boolean
}

function newKey(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return `k-${Math.random().toString(36).slice(2)}`
}

function blankLicense(): DraftLicense {
  return {
    key: newKey(),
    license_type: 'Insurance',
    license_number: '',
    issuer: '',
    jurisdiction: '',
    expires_on: '',
    no_expiry: false,
  }
}

function toDraft(licenses: License[] | undefined): DraftLicense[] {
  if (!licenses || licenses.length === 0) return [blankLicense()]
  return licenses.map((l) => ({
    key: newKey(),
    id: l.id,
    license_type: l.license_type,
    license_number: l.license_number,
    issuer: l.issuer || '',
    jurisdiction: l.jurisdiction || '',
    expires_on: l.expires_on || '',
    no_expiry: l.no_expiry,
  }))
}

export default function ApplicationForm({
  user,
  initialApplication,
  clerkAuth,
}: {
  user: SessionUser
  /** Server-decided: this deployment signs people in through Clerk. */
  clerkAuth?: boolean
  initialApplication: Application | null
}) {
  const router = useRouter()
  const [app, setApp] = useState<Application | null>(initialApplication)
  const [documents, setDocuments] = useState<DocumentRow[]>(initialApplication?.documents || [])
  const [fullName, setFullName] = useState(initialApplication?.full_name || user.full_name || '')
  const [phone, setPhone] = useState(initialApplication?.phone || user.phone || '')
  const [email, setEmail] = useState(initialApplication?.email || user.email || '')
  const [address, setAddress] = useState(initialApplication?.address || '')
  const [terms, setTerms] = useState(!!initialApplication?.terms_accepted)
  const [licenses, setLicenses] = useState<DraftLicense[]>(toDraft(initialApplication?.licenses))
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)

  const status = app?.status || 'none'
  // A brand-new application (no row on the server yet) is editable; only a row
  // in a decided/submitted state is locked.
  const locked = app !== null && !EDITABLE.has(status)
  const preReview: PreReview | null = app?.pre_review || null

  const payload = useCallback(
    () => ({
      full_name: fullName || null,
      phone: phone || null,
      email: email || null,
      address: address || null,
      terms_accepted: terms,
      licenses: licenses
        .filter((l) => l.license_number.trim() || l.id)
        .map((l) => ({
          id: l.id,
          license_type: l.license_type,
          license_number: l.license_number.trim(),
          issuer: l.issuer || null,
          jurisdiction: l.jurisdiction || null,
          expires_on: l.no_expiry || !l.expires_on ? null : l.expires_on,
          no_expiry: l.no_expiry,
        })),
    }),
    [fullName, phone, email, address, terms, licenses],
  )

  function applyServer(application: Application) {
    setApp(application)
    setDocuments(application.documents || [])
    setLicenses(toDraft(application.licenses))
  }

  async function saveDraft(): Promise<Application | null> {
    setError(null)
    setInfo(null)
    try {
      const res = await api.saveDraft(payload())
      applyServer(res.application)
      setInfo('Draft saved.')
      return res.application
    } catch (err) {
      setError(err instanceof ApiError ? `${err.code}: ${err.message}` : 'could not save the draft')
      return null
    }
  }

  async function onSubmit() {
    setBusy('submit')
    try {
      const saved = await saveDraft()
      if (!saved) return
      const res = await api.submit()
      applyServer(res.application)
      setInfo('Submitted for review.')
      router.refresh()
    } catch (err) {
      setError(
        err instanceof ApiError
          ? `${err.code}: ${err.message}`
          : 'could not submit the application',
      )
    } finally {
      setBusy(null)
    }
  }

  async function onUpload(licenseKey: string, file: File) {
    setBusy(`upload:${licenseKey}`)
    setError(null)
    setInfo(null)
    try {
      // make sure the application and the licence row exist before attaching
      let current = app
      if (!current || !EDITABLE.has(current.status)) {
        setError('save a draft before uploading documents')
        return
      }
      const savedNow = await saveDraft()
      current = savedNow || current
      const row = licenses.find((l) => l.key === licenseKey)
      const serverRow = current.licenses?.find(
        (l) => l.id && l.id === row?.id,
      )
      const res = await api.uploadDocument(file, 'front', serverRow?.id)
      setDocuments((d) => [...d, res.document])
      setInfo(`Uploaded ${res.document.mime_type} (${res.document.size_bytes} bytes).`)
    } catch (err) {
      setError(err instanceof ApiError ? `${err.code}: ${err.message}` : 'upload failed')
    } finally {
      setBusy(null)
    }
  }

  function viewDocument(documentId: string) {
    window.open(api.documentContentUrl(documentId), '_blank', 'noopener,noreferrer')
  }

  const statusLabel = useMemo(() => {
    switch (status) {
      case 'none':
        return 'Not started'
      case 'draft':
        return 'Draft'
      case 'submitted':
        return 'Submitted — waiting for review'
      case 'info_requested':
        return 'Information requested'
      case 'approved':
        return 'Approved'
      case 'rejected':
        return 'Rejected'
      case 'suspended':
        return 'Suspended'
      default:
        return status
    }
  }, [status])

  const statusClass =
    status === 'approved'
      ? 'pp-status pp-status-good'
      : status === 'submitted'
        ? 'pp-status pp-status-review'
        : status === 'info_requested' || status === 'rejected' || status === 'suspended'
          ? 'pp-status pp-status-warn'
          : 'pp-status pp-status-muted'

  return (
    <Shell
      user={user}
      canEnterAgent={user.roles.includes('agent') && status === 'approved'}
      clerkAuth={clerkAuth}
      portal="customer"
      activeId="licensed"
      eyebrow="Get Licensed"
      title="Agent application"
    >
      <div data-testid="apply-main">
          <div className="pp-stack">
            <section className="pp-panel">
              <div className="pp-section-head">
                <div>
                  <h1 className="pp-h1">Become an Agent</h1>
                  <p className="pp-body pp-muted" style={{ marginBottom: 0 }}>
                    Applying as <strong data-testid="apply-account-email">{user.email}</strong>. The
                    application, the licences and any agent permission stay attached to this one
                    account id — no separate agent login is created.
                  </p>
                </div>
                <span className={statusClass} data-testid="apply-status">
                  {statusLabel}
                </span>
              </div>

              {error ? (
                <p className="pp-err" data-testid="apply-error">
                  {error}
                </p>
              ) : null}
              {info ? (
                <p className="pp-ok" data-testid="apply-info">
                  {info}
                </p>
              ) : null}

              {status === 'info_requested' ? (
                <div className="pp-warn-box" data-testid="info-requested">
                  <strong>An administrator asked for more information.</strong>
                  {app?.decision_reason ? <div className="pp-muted">“{app.decision_reason}”</div> : null}
                  <div className="pp-muted">Add the missing material below and submit again.</div>
                </div>
              ) : null}
              {status === 'rejected' ? (
                <div className="pp-warn-box" data-testid="rejected-note">
                  <strong>This application was rejected.</strong>
                  {app?.decision_reason ? <div className="pp-muted">“{app.decision_reason}”</div> : null}
                </div>
              ) : null}
              {status === 'suspended' ? (
                <div className="pp-warn-box" data-testid="suspended-note">
                  <strong>This agent licence is suspended.</strong>
                  {app?.decision_reason ? <div className="pp-muted">“{app.decision_reason}”</div> : null}
                </div>
              ) : null}
              {status === 'approved' ? (
                <div className="pp-good-box" data-testid="approved-note">
                  <strong>Approved.</strong>
                  <div className="pp-muted">
                    The agent role is active on this account.{' '}
                    <Link href="/agent-loop/agent">Open the Agent panel →</Link>
                  </div>
                </div>
              ) : null}
              {locked && status === 'submitted' ? (
                <p className="pp-note" data-testid="locked-note">
                  Submitted applications cannot be changed. An administrator can request more
                  information, which reopens editing.
                </p>
              ) : null}
              {status === 'approved' || status === 'rejected' || status === 'suspended' ? (
                <p className="pp-note" data-testid="locked-note">
                  A decided application is read-only.
                </p>
              ) : null}
            </section>

            <section className="pp-panel">
              <h2 className="pp-h2">Applicant details</h2>
              <div className="pp-form-grid">
                <label className="pp-field">
                  <span>Name</span>
                  <input
                    data-testid="field-full-name"
                    value={fullName}
                    disabled={locked}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </label>
                <label className="pp-field">
                  <span>Phone</span>
                  <input
                    data-testid="field-phone"
                    value={phone}
                    disabled={locked}
                    onChange={(e) => setPhone(e.target.value)}
                  />
                </label>
                <label className="pp-field">
                  <span>Contact e-mail</span>
                  <input
                    data-testid="field-email"
                    type="email"
                    value={email}
                    disabled={locked}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </label>
              </div>
              <p className="pp-footnote">
                The contact e-mail can be updated, but it never changes which account owns the
                application — ownership follows the signed-in user id ({user.id}).
              </p>
              <label className="pp-field">
                <span>Address</span>
                <textarea
                  className="pp-textarea"
                  data-testid="field-address"
                  value={address}
                  disabled={locked}
                  onChange={(e) => setAddress(e.target.value)}
                />
              </label>
            </section>

            <section className="pp-panel">
              <div className="pp-section-head">
                <h2 className="pp-h2">Licences</h2>
                {!locked ? (
                  <button
                    type="button"
                    className="pp-btn pp-btn-secondary"
                    data-testid="add-license"
                    onClick={() => setLicenses((l) => [...l, blankLicense()])}
                  >
                    + Add licence
                  </button>
                ) : null}
              </div>
              {licenses.map((lic, index) => (
                <div className="pp-panel-inner" key={lic.key} data-testid={`license-${index}`}>
                  <div className="pp-form-grid">
                    <label className="pp-field">
                      <span>Licence type</span>
                      <select
                        className="pp-select"
                        data-testid={`license-type-${index}`}
                        value={lic.license_type}
                        disabled={locked}
                        onChange={(e) =>
                          setLicenses((rows) =>
                            rows.map((r) => (r.key === lic.key ? { ...r, license_type: e.target.value } : r)),
                          )
                        }
                      >
                        {LICENSE_TYPES.map((t) => (
                          <option key={t} value={t}>
                            {t}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="pp-field">
                      <span>Licence number</span>
                      <input
                        data-testid={`license-number-${index}`}
                        value={lic.license_number}
                        disabled={locked}
                        onChange={(e) =>
                          setLicenses((rows) =>
                            rows.map((r) => (r.key === lic.key ? { ...r, license_number: e.target.value } : r)),
                          )
                        }
                      />
                    </label>
                    <label className="pp-field">
                      <span>State / region</span>
                      <input
                        data-testid={`license-region-${index}`}
                        value={lic.jurisdiction}
                        disabled={locked}
                        onChange={(e) =>
                          setLicenses((rows) =>
                            rows.map((r) => (r.key === lic.key ? { ...r, jurisdiction: e.target.value } : r)),
                          )
                        }
                      />
                    </label>
                    <label className="pp-field">
                      <span>Issuing authority</span>
                      <input
                        data-testid={`license-issuer-${index}`}
                        value={lic.issuer}
                        disabled={locked}
                        onChange={(e) =>
                          setLicenses((rows) =>
                            rows.map((r) => (r.key === lic.key ? { ...r, issuer: e.target.value } : r)),
                          )
                        }
                      />
                    </label>
                    <label className="pp-field">
                      <span>Expires on</span>
                      <input
                        type="date"
                        data-testid={`license-expiry-${index}`}
                        value={lic.expires_on}
                        disabled={locked || lic.no_expiry}
                        onChange={(e) =>
                          setLicenses((rows) =>
                            rows.map((r) => (r.key === lic.key ? { ...r, expires_on: e.target.value } : r)),
                          )
                        }
                      />
                    </label>
                  </div>
                  <div className="pp-toggle-row">
                    <label className="pp-inline-label" style={{ flexDirection: 'row', gap: 8 }}>
                      <input
                        type="checkbox"
                        data-testid={`license-no-expiry-${index}`}
                        checked={lic.no_expiry}
                        disabled={locked}
                        onChange={(e) =>
                          setLicenses((rows) =>
                            rows.map((r) => (r.key === lic.key ? { ...r, no_expiry: e.target.checked } : r)),
                          )
                        }
                      />
                      <span>This licence has no expiry date</span>
                    </label>
                  </div>
                  <div className="pp-actions">
                    <label className="pp-btn pp-btn-secondary" style={{ display: 'inline-block' }}>
                      {busy === `upload:${lic.key}` ? 'Uploading…' : 'Upload licence photo (synthetic)'}
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp,application/pdf"
                        data-testid={`license-upload-${index}`}
                        style={{ display: 'none' }}
                        disabled={locked || busy !== null}
                        onChange={(e) => {
                          const file = e.target.files?.[0]
                          if (file) void onUpload(lic.key, file)
                          e.target.value = ''
                        }}
                      />
                    </label>
                    {licenses.length > 1 && !locked ? (
                      <button
                        type="button"
                        className="pp-btn pp-btn-ghost"
                        onClick={() => setLicenses((rows) => rows.filter((r) => r.key !== lic.key))}
                      >
                        Remove
                      </button>
                    ) : null}
                    {lic.id ? <span className="pp-chip">saved on server</span> : <span className="pp-chip">not saved yet</span>}
                  </div>
                </div>
              ))}
            </section>

            <section className="pp-panel">
              <h2 className="pp-h2">Supporting documents</h2>
              <p className="pp-muted pp-body">
                Documents are stored privately and are only reachable through a short-lived signed
                link bound to the owner. Use synthetic images only.
              </p>
              <table className="pp-table">
                <thead>
                  <tr>
                    <th>Side</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Storage</th>
                    <th>Scan</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id} data-testid="document-row">
                      <td>{doc.side}</td>
                      <td className="pp-mono">{doc.mime_type}</td>
                      <td>{doc.size_bytes}</td>
                      <td>{doc.storage_label}</td>
                      <td>{doc.scan_status}</td>
                      <td>
                        <button
                          type="button"
                          className="pp-btn pp-btn-ghost"
                          data-testid="view-document"
                          onClick={() => void viewDocument(doc.id)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                  {documents.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="pp-muted" data-testid="no-documents">
                        no document uploaded yet
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </section>

            {preReview ? (
              <section className="pp-panel" data-testid="pre-review">
                <div className="pp-section-head">
                  <h2 className="pp-h2">Pre-review</h2>
                  <span className="pp-chip pp-flag">advisory only — never a decision</span>
                </div>
                <div className="pp-kv">
                  <span className="pp-label">Engine</span>
                  <span className="pp-mono">
                    {preReview.engine} · {preReview.mode}
                  </span>
                  <span className="pp-label">Recommendation</span>
                  <span data-testid="pre-review-recommendation">{preReview.recommendation}</span>
                  <span className="pp-label">Can auto-approve</span>
                  <span data-testid="pre-review-auto-approve">{String(preReview.can_auto_approve)}</span>
                  <span className="pp-label">Documents</span>
                  <span>
                    {preReview.document_count} · licences {preReview.license_count} · expired{' '}
                    {preReview.expired_licenses}
                  </span>
                </div>
                {preReview.missing_fields?.length ? (
                  <p className="pp-flag">missing fields: {preReview.missing_fields.join(', ')}</p>
                ) : null}
                <ul className="pp-list">
                  {preReview.reasons.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                  {preReview.reasons.length === 0 ? <li>no rule flagged anything</li> : null}
                </ul>
                <p className="pp-note">
                  This pre-review exists only to help a human read the file. It cannot grant the
                  agent role and it cannot change the status. A final licence decision is always
                  made by an administrator.
                </p>
              </section>
            ) : null}

            {!locked ? (
              <section className="pp-panel">
                <h2 className="pp-h2">Submit</h2>
                <label className="pp-inline-label" style={{ flexDirection: 'row', gap: 8 }}>
                  <input
                    type="checkbox"
                    data-testid="terms"
                    checked={terms}
                    onChange={(e) => setTerms(e.target.checked)}
                  />
                  <span>
                    I confirm the information is accurate and I accept the terms for licence review.
                  </span>
                </label>
                <div className="pp-actions">
                  <button
                    type="button"
                    className="pp-btn pp-btn-secondary"
                    data-testid="save-draft"
                    disabled={busy !== null}
                    onClick={() => void saveDraft()}
                  >
                    Save draft
                  </button>
                  <button
                    type="button"
                    className="pp-btn pp-btn-primary"
                    data-testid="submit-application"
                    disabled={busy !== null}
                    onClick={() => void onSubmit()}
                  >
                    {status === 'info_requested' ? 'Resubmit for review' : 'Submit for review'}
                  </button>
                </div>
                <p className="pp-footnote">
                  You must be signed in. Submitting does not grant agent access — only an
                  administrator can approve it.
                </p>
              </section>
            ) : null}
          </div>
      </div>
    </Shell>
  )
}
