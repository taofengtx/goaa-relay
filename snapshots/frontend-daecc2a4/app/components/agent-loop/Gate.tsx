'use client'

/**
 * Gate.tsx — the access-gate card shown when a server-side role check fails.
 *
 * The gate is always produced by a *server* decision (the page calls the API
 * with the session cookie before rendering). A client can therefore never
 * reach a gated view by editing localStorage or by typing the URL directly.
 */

import Link from 'next/link'

export default function Gate({
  code,
  title,
  message,
  back,
}: {
  code: string
  title: string
  message: string
  back?: { href: string; label: string }
}) {
  return (
    <div className="pp-root">
      <header className="pp-topbar">
        <div className="pp-brand">
          goaa.ai<span className="pp-brand-sub">Access gate</span>
        </div>
        <span className="pp-badge">C2 isolated · synthetic data</span>
      </header>
      <main className="pp-main" style={{ maxWidth: 640 }}>
        <section className="pp-gate-card" data-testid="access-gate" data-gate-code={code}>
          <span className="pp-gate-badge">{code}</span>
          <h1 className="pp-h1">{title}</h1>
          <p className="pp-body pp-muted">{message}</p>
          <div className="pp-actions">
            {back ? (
              <Link className="pp-btn pp-btn-secondary" data-testid="gate-back" href={back.href}>
                {back.label}
              </Link>
            ) : null}
            <Link className="pp-btn pp-btn-ghost" href="/agent-loop/login">
              Sign in with another account
            </Link>
          </div>
        </section>
      </main>
      <footer className="pp-footer">
        Permission is re-checked on the server on every request, every refresh and every direct URL.
      </footer>
    </div>
  )
}
