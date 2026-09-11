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
    <div className="goaa-portal" style={{ display: 'grid', placeItems: 'center', padding: 24 }}>
      <section className="goaa-card" data-testid="access-gate" data-gate-code={code} style={{ maxWidth: 640, width: '100%' }}>
        <span className="goaa-pill outline">{code}</span>
        <h1 className="goaa-h1" style={{ marginTop: 12 }}>{title}</h1>
        <p className="goaa-muted" style={{ margin: '10px 0 18px' }}>{message}</p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {back ? (
            <Link className="goaa-btn goaa-btn-secondary" data-testid="gate-back" href={back.href}>
              {back.label}
            </Link>
          ) : null}
          <Link className="goaa-btn goaa-btn-secondary" href="/agent-loop/login">
            Sign in with another account
          </Link>
        </div>
        <p className="goaa-muted" style={{ marginTop: 18, fontSize: 13 }}>Permission is re-checked on the server on every request, every refresh and every direct URL.</p>
      </section>
    </div>
  )
}
