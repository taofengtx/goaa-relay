'use client'

/**
 * CustomerPanel.tsx — the user dashboard for the isolated /agent-loop/* routes.
 *
 * Rail (unchanged from the current candidate design):
 *   AI assistant area  : Chat · Matters · Skills Marketplace
 *   ---- divider ----
 *   growth area        : Get Licensed · Earning Opportunities
 * `Plan Result` and `Professional Execution` stay hidden (their golden source
 * is untouched, they are simply not rendered here).
 *
 * Only "Get Licensed -> Become an Agent" is wired to the real C2 back end.
 * Skills Marketplace and Earning Opportunities keep their preview state and
 * touch no third party and no price.
 */

import Link from 'next/link'
import Shell from './Shell'
import type { SessionUser } from '@/app/lib/agent-loop/api'

type Status = 'draft' | 'submitted' | 'info_requested' | 'approved' | 'rejected' | 'suspended'

const STATUS_LABEL: Record<Status, string> = {
  draft: 'Draft — not submitted',
  submitted: 'Submitted — waiting for review',
  info_requested: 'More information requested',
  approved: 'Approved — agent licence active',
  rejected: 'Rejected',
  suspended: 'Suspended',
}

const STATUS_CLASS: Record<Status, string> = {
  draft: 'pp-status pp-status-muted',
  submitted: 'pp-status pp-status-review',
  info_requested: 'pp-status pp-status-warn',
  approved: 'pp-status pp-status-good',
  rejected: 'pp-status pp-status-warn',
  suspended: 'pp-status pp-status-warn',
}

export default function CustomerPanel({
  user,
  application,
  canEnterAgent,
  clerkAuth,
}: {
  user: SessionUser
  application: { id: string; status: string } | null
  canEnterAgent: boolean
  /** Server-decided: this deployment signs people in through Clerk. */
  clerkAuth?: boolean
}) {
  const status = (application?.status || null) as Status | null

  return (
    <Shell user={user} canEnterAgent={canEnterAgent} clerkAuth={clerkAuth} portal="customer" activeId="licensed" eyebrow="Get Licensed" title="Agent licence application">
      <div data-testid="customer-main">
        <LicensedTab application={application} status={status} canEnterAgent={canEnterAgent} />
      </div>
    </Shell>
  )
}

function LicensedTab({
  application,
  status,
  canEnterAgent,
}: {
  application: { id: string; status: string } | null
  status: Status | null
  canEnterAgent: boolean
}) {
  return (
    <div className="pp-stack">
      <section className="pp-panel">
        <div className="pp-section-head">
          <div>
            <h1 className="pp-h1">Get Licensed</h1>
            <p className="pp-body pp-muted" style={{ marginBottom: 0 }}>
              A licence review decides whether this account may act as a professional agent.
              It is a separate question from any paid subscription: paying never bypasses review.
            </p>
          </div>
          {status ? (
            <span className={STATUS_CLASS[status]} data-testid="application-status">
              {STATUS_LABEL[status]}
            </span>
          ) : (
            <span className="pp-status pp-status-muted" data-testid="application-status">
              Not started
            </span>
          )}
        </div>

        {!application ? (
          <>
            <div className="pp-good-box">
              <h2 className="pp-h2">Become an Agent</h2>
              <p className="pp-muted" style={{ marginTop: 4 }}>
                Apply with your licence details and a photo of each licence. Your application and
                the resulting agent permission always belong to <strong>this user account</strong> —
                no second account, no separate username or password.
              </p>
            </div>
            <div className="pp-actions">
              <Link className="pp-btn pp-btn-primary" data-testid="become-an-agent" href="/agent-loop/apply">
                Become an Agent
              </Link>
            </div>
            <p className="pp-footnote">
              You must be signed in to apply. The application is saved against your account id.
            </p>
          </>
        ) : (
          <>
            <div className="pp-kv">
              <span className="pp-label">Application</span>
              <span className="pp-mono">{application.id}</span>
              <span className="pp-label">Status</span>
              <span data-testid="application-status-text">{status ? STATUS_LABEL[status] : 'unknown'}</span>
            </div>

            {status === 'draft' ? (
              <p className="pp-inline-hint">This application is a draft. Submit it when the details and photos are complete.</p>
            ) : null}
            {status === 'submitted' ? (
              <p className="pp-note">
                Submitted. The pre-review below is advisory only — it never approves anything. A
                human administrator makes the decision.
              </p>
            ) : null}
            {status === 'info_requested' ? (
              <p className="pp-warn-box">
                An administrator asked for more information. Open the application, add the missing
                material and resubmit.
              </p>
            ) : null}
            {status === 'rejected' ? (
              <p className="pp-warn-box">This application was rejected. The reason is shown on the application page.</p>
            ) : null}
            {status === 'suspended' ? (
              <p className="pp-warn-box">This agent licence is suspended. Agent access is blocked until it is restored.</p>
            ) : null}
            {status === 'approved' ? (
              <p className="pp-ok">Approved. The agent role is now active on this same account.</p>
            ) : null}

            <div className="pp-actions">
              <Link className="pp-btn pp-btn-primary" data-testid="open-application" href="/agent-loop/apply">
                {status === 'draft' ? 'Continue editing' : status === 'info_requested' ? 'Add information and resubmit' : 'View application'}
              </Link>
              {canEnterAgent ? (
                <Link className="pp-btn pp-btn-secondary" data-testid="switch-to-agent-inline" href="/agent-loop/agent">
                  Switch to Agent panel
                </Link>
              ) : null}
            </div>
          </>
        )}
      </section>

      <section className="pp-panel">
        <h2 className="pp-h2">How this works</h2>
        <ul className="pp-list">
          <li>The pre-review is a deterministic rules check of your documents. It is <strong>advisory only</strong>.</li>
          <li>The pre-review <strong>cannot</strong> approve an agent. A human administrator makes the final decision.</li>
          <li>Until it is approved you cannot enter the professional Agent panel.</li>
          <li>All names, licences and photos in this environment are synthetic.</li>
        </ul>
      </section>
    </div>
  )
}
