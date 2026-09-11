'use client'

/**
 * AgentPanel.tsx — the professional panel home.
 *
 * This round only wires REAL permission plus a basic home page. Quoting,
 * delivery, invoices and payouts are deliberately NOT built here and are shown
 * as explicitly out of scope rather than as fake controls.
 *
 * Reaching this view requires: a signed-in session, the `agent` role and an
 * approved application — all re-checked on the server before this renders.
 */

import Shell from './Shell'
import type { License, SessionUser } from '@/app/lib/agent-loop/api'

export default function AgentPanel({
  user,
  panel,
  clerkAuth,
}: {
  user: SessionUser
  panel: { status: string; application_id: string; granted_at: string | null; licenses: License[] }
  /** Server-decided: this deployment signs people in through Clerk. */
  clerkAuth?: boolean
}) {
  return (
    <Shell user={user} canEnterAgent isAgentView clerkAuth={clerkAuth} portal="agent" activeId="overview" eyebrow="Agent overview" title="Agent panel">
      <div data-testid="agent-main">
          <div className="pp-stack">
            <section className="pp-panel">
              <div className="pp-section-head">
                <div>
                  <h1 className="pp-h1">Agent panel</h1>
                  <p className="pp-body pp-muted" style={{ marginBottom: 0 }}>
                    Signed in as {user.email}. This is the same account and the same session as the
                    user panel — you did not sign in twice and there is no second credential.
                  </p>
                </div>
                <span className="pp-status pp-status-good" data-testid="agent-status">
                  licence {panel.status}
                </span>
              </div>

              <div className="pp-kv">
                <span className="pp-label">Account id</span>
                <span className="pp-mono" data-testid="agent-account-id">
                  {user.id}
                </span>
                <span className="pp-label">Application</span>
                <span className="pp-mono">{panel.application_id}</span>
                <span className="pp-label">Licence granted</span>
                <span>{panel.granted_at ? new Date(panel.granted_at).toLocaleString() : '—'}</span>
                <span className="pp-label">Roles</span>
                <span data-testid="agent-roles">{user.roles.join(', ')}</span>
              </div>
            </section>

            <section className="pp-panel">
              <h2 className="pp-h2">Licences on file</h2>
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
                  {panel.licenses.map((lic) => (
                    <tr key={lic.id}>
                      <td>{lic.license_type}</td>
                      <td className="pp-mono">{lic.license_number}</td>
                      <td>{lic.jurisdiction || '—'}</td>
                      <td>{lic.issuer || '—'}</td>
                      <td>{lic.no_expiry ? 'no expiry' : lic.expires_on || '—'}</td>
                    </tr>
                  ))}
                  {panel.licenses.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="pp-muted">
                        no licence rows
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </section>

            <section className="pp-panel">
              <h2 className="pp-h2">Not in this round</h2>
              <p className="pp-muted pp-body">
                Quoting, delivery, invoices and payouts are intentionally out of scope for this
                increment. They are not stubbed with fake numbers here; the panel only proves the
                real permission boundary.
              </p>
              <div className="pp-chip-row">
                {['quoting — later', 'delivery — later', 'invoice — later', 'payout — later'].map((c) => (
                  <span className="pp-chip" key={c}>
                    {c}
                  </span>
                ))}
              </div>
            </section>
          </div>
      </div>
    </Shell>
  )
}
