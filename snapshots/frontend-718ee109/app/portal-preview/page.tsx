import Link from 'next/link'
import './portal-preview.css'

/**
 * Portal Preview entry — isolated /portal-preview landing.
 *
 * This is the public preview entry for the three candidate portals. It
 * never links into golden navigation, never mutates production session and
 * is not deployed. Fixture seeds are demo worlds only; every identity,
 * license, matter, invoice and payment shown in previews is fictional.
 */

export default function PortalPreviewEntryPage() {
  return (
    <div className="pp-root">
      <header className="pp-topbar">
        <div className="pp-brand">GOAA <span className="pp-brand-sub">portal preview — entry</span></div>
        <span className="pp-badge">Candidate concept · not production</span>
      </header>
      <div className="pp-main" style={{ maxWidth: 860 }}>
        <h1 className="pp-h1">Portal Preview</h1>
        <p className="pp-muted pp-body">
          Public preview of the three candidate portals. Every path below stays inside
          <code> /portal-preview/** </code> and uses a fictional demo world stored only in this browser.
          No golden page, navigation, middleware, production session or real payment is touched.
        </p>

        <div className="pp-cards">
          <article className="pp-panel">
            <h2 className="pp-h2">Customer Portal</h2>
            <p className="pp-muted">Fresh world — no application yet. Start with Chat/Matters, browse Skills, then choose a Get Licensed path.</p>
            <div className="pp-actions">
              <Link className="pp-btn pp-btn-primary" href="/portal-preview/customer">Open Customer Portal</Link>
            </div>
          </article>

          <article className="pp-panel">
            <h2 className="pp-h2">Demo worlds (activated)</h2>
            <p className="pp-muted">Same single account with customer + activated agent roles, licensed application approved, and a business loop pre-seeded for screenshots.</p>
            <div className="pp-actions">
              <Link className="pp-btn pp-btn-secondary" href="/portal-preview/customer?seed=activated">Customer</Link>
              <Link className="pp-btn pp-btn-secondary" href="/portal-preview/agent?seed=activated">Agent</Link>
              <Link className="pp-btn pp-btn-secondary" href="/portal-preview/admin?seed=activated">Admin</Link>
            </div>
          </article>
        </div>

        <p className="pp-footnote">
          Entry to the Agent Portal always goes through the access gate. If the account is not yet approved/activated,
          the gate explains the exact missing step instead of opening a workbench.
        </p>
      </div>
      <footer className="pp-footer">Candidate concept only — all identities, licenses, matters, invoices and payments are fictional and local-only.</footer>
    </div>
  )
}
