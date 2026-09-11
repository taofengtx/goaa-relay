'use client'

/**
 * Account Settings — isolated /portal-preview/settings candidate.
 *
 * Minimal preview page for the account menu item. It shows the demo
 * identity stored in the two local preview stores (never a production
 * account) and lets the user return to a portal or sign out of the
 * preview world. No real account, password, session or backend is used.
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  PREVIEW_STORE_KEY,
  readPortalPreviewState,
} from '../../lib/portal-preview/preview-store'
import {
  BUSINESS_STORE_KEY,
  readBusinessState,
} from '../../lib/portal-preview/preview-business-store'
import type { AccountRecord } from '../../lib/portal-preview/preview-business'
import '../../portal-preview/portal-preview.css'

export default function PortalPreviewSettingsPage() {
  const [account, setAccount] = useState<AccountRecord | undefined>(undefined)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search)
      const seed = params.get('seed')
      if (seed) {
        window.history.replaceState(null, '', window.location.pathname)
      }
    } catch {
      // ignore history errors in SSR-like edge cases
    }
    const store = readPortalPreviewState()
    const biz = readBusinessState()
    const active = store.activeEmail ? biz.accounts.find((a) => a.email === store.activeEmail) : biz.accounts.find((a) => a.email === biz.sessionEmail)
    setAccount(active)
  }, [])

  function signOut() {
    if (typeof window === 'undefined') return
    try {
      window.localStorage.removeItem(PREVIEW_STORE_KEY)
      window.localStorage.removeItem(BUSINESS_STORE_KEY)
    } catch {
      // preview storage is best-effort
    }
    setAccount(undefined)
    setNotice('Preview session cleared. This only removes the local demo store — production authentication is untouched.')
  }

  return (
    <div className="pp-root">
      <header className="pp-topbar">
        <div className="pp-brand">GOAA <span className="pp-brand-sub">portal preview — account settings</span></div>
        <span className="pp-badge">Candidate concept · not production</span>
      </header>
      <div className="pp-main" style={{ maxWidth: 720 }}>
        <h1 className="pp-h1">Account Settings</h1>
        <p className="pp-muted pp-body">
          Preview-only settings for the shared single-account demo. This page never reads or changes a real account,
          password, subscription, payment method or production session.
        </p>

        {notice && <p className="pp-note">{notice}</p>}

        {account ? (
          <article className="pp-panel">
            <h2 className="pp-h2">Demo identity</h2>
            <div className="pp-kv">
              <span className="pp-label">Name</span><span>{account.displayName}</span>
              <span className="pp-label">Email</span><span>{account.email}</span>
              <span className="pp-label">Roles</span><span>{account.roles.join(' + ')}</span>
              <span className="pp-label">Agent access</span><span>{account.agentAccess}</span>
              <span className="pp-label">Agent username</span><span>{account.agentUsername ?? '—'}</span>
              <span className="pp-label">Subscription</span><span>{account.subscription.plan} · {account.subscription.status}</span>
              <span className="pp-label">Created at</span><span>{account.createdAt.slice(0, 16).replace('T', ' ')} UTC</span>
            </div>
            <div className="pp-actions">
              <Link className="pp-btn pp-btn-secondary" href="/portal-preview/customer?seed=activated">Customer Portal</Link>
              {account.roles.includes('agent') && account.agentAccess === 'activated' && (
                <Link className="pp-btn pp-btn-secondary" href="/portal-preview/agent?seed=activated">Agent Portal</Link>
              )}
              <button className="pp-btn pp-btn-danger" onClick={signOut}>Sign Out of preview</button>
            </div>
          </article>
        ) : (
          <article className="pp-panel">
            <h2 className="pp-h2">No preview session</h2>
            <p className="pp-muted">
              The local preview store is empty. Open a portal from the entry page and it will create a fresh demo world
              (or an activated demo world when you use the seeded links).
            </p>
            <div className="pp-actions">
              <Link className="pp-btn pp-btn-primary" href="/portal-preview">Portal entry</Link>
            </div>
          </article>
        )}
      </div>
      <footer className="pp-footer">Candidate concept only — production authentication, subscription and payment settings are never touched.</footer>
    </div>
  )
}
