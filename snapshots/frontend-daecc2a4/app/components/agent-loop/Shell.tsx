'use client'

/**
 * Shell.tsx — visual shell for the isolated /agent-loop/* front end.
 *
 * It reuses the existing portal-preview design system (pp-* classes) so the
 * candidate pages keep the current look, spacing and navigation behaviour.
 * It does NOT import or modify any golden page, component or stylesheet.
 */

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import type { SessionUser } from '@/app/lib/agent-loop/api'
import { api } from '@/app/lib/agent-loop/api'
import { performSignOut } from '@/app/lib/agent-loop/signout'

export type RailItem = {
  id: string
  label: string
  icon?: ReactNode
  /** Small caption under the item, e.g. "existing golden view". */
  kicker?: string
  /** Draws a separator above the item. */
  divider?: boolean
  /** Shows the "New" tag. */
  isNew?: boolean
}

export function Rail({
  items,
  active,
  onSelect,
}: {
  items: RailItem[]
  active: string
  onSelect: (id: string) => void
}) {
  return (
    <nav className="pp-rail" aria-label="main navigation">
      {items.map((item) => (
        <div key={item.id}>
          <button
            type="button"
            data-testid={`rail-${item.id}`}
            className={`pp-rail-item${active === item.id ? ' pp-active' : ''}${
              item.divider ? ' pp-divider-top' : ''
            }`}
            aria-current={active === item.id ? 'page' : undefined}
            onClick={() => onSelect(item.id)}
          >
            <span className="pp-rail-ic" aria-hidden="true">
              {item.icon}
            </span>
            <span>{item.label}</span>
            {item.isNew ? <span className="pp-new-tag">New</span> : null}
          </button>
          {item.kicker ? <span className="pp-rail-kicker">{item.kicker}</span> : null}
        </div>
      ))}
    </nav>
  )
}

export default function Shell({
  user,
  canEnterAgent,
  isAgentView,
  clerkAuth = false,
  children,
}: {
  user: SessionUser
  /** Server-verified: the account holds the agent role AND the application is approved. */
  canEnterAgent: boolean
  isAgentView?: boolean
  /** Server-decided: this deployment signs people in through Clerk. */
  clerkAuth?: boolean
  children: ReactNode
}) {
  const router = useRouter()
  const [menuOpen, setMenuOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [signOutError, setSignOutError] = useState<string | null>(null)

  useEffect(() => {
    function onDoc(event: MouseEvent) {
      // A React stopPropagation on the wrapper does not stop a listener that is
      // registered directly on document, so the trigger click would close the
      // popover in the same tick that opens it. Ignore clicks inside the area.
      const target = event.target as HTMLElement | null
      if (target && target.closest('.pp-user-area')) return
      setMenuOpen(false)
    }
    document.addEventListener('click', onDoc)
    return () => document.removeEventListener('click', onDoc)
  }, [])

  /**
   * Sign out.
   *
   * The decision — and the refusal to claim a sign-out that did not happen —
   * lives in lib/agent-loop/signout.ts, where all three cases are tested.
   */
  async function signOut() {
    setBusy(true)
    setSignOutError(null)

    const result = await performSignOut({
      clerkAuth,
      browser: typeof window === 'undefined' ? null : window,
      legacy: async () => {
        try {
          await api.logout()
        } catch {
          /* signing out locally is enough for the isolated legacy loop */
        }
      },
      navigate: (url) => window.location.assign(url),
    })

    // The Clerk branch navigates through the SDK; only a refusal lands here.
    if (result.status !== 'redirected') {
      setBusy(false)
      setSignOutError(result.message)
    }
  }

  const initials = (user.full_name || user.email || '?').trim().slice(0, 1).toUpperCase()

  return (
    <div className="pp-root">
      <header className="pp-topbar">
        <div className="pp-brand">
          goaa.ai
          <span className="pp-brand-sub">
            {isAgentView ? 'Agent panel' : 'Personal Service Center'}
          </span>
        </div>
        <div className="pp-topbar-right">
          <span className="pp-badge">C2 isolated · synthetic data</span>
          <div className="pp-user-area" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="pp-user-btn"
              data-testid="account-menu-button"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((v) => !v)}
            >
              <span className="pp-user-avatar" aria-hidden="true">
                {initials}
              </span>
              <span className="pp-user-email">{user.email}</span>
              <span className="pp-user-caret" aria-hidden="true">
                ▾
              </span>
            </button>
            {menuOpen ? (
              <div className="pp-user-pop" role="menu" data-testid="account-menu">
                <div className="pp-user-head">
                  <div className="pp-user-name">{user.full_name || 'Unnamed account'}</div>
                  <div className="pp-user-meta">
                    roles: {user.roles.join(', ') || 'none'}
                  </div>
                </div>
                {isAgentView ? (
                  <Link className="pp-menu-item" data-testid="switch-to-user" href="/agent-loop/customer">
                    ⇄ Switch to User panel
                  </Link>
                ) : canEnterAgent ? (
                  <Link className="pp-menu-item" data-testid="switch-to-agent" href="/agent-loop/agent">
                    ⇄ Switch to Agent panel
                  </Link>
                ) : null}
                {user.roles.includes('admin') ? (
                  <Link className="pp-menu-item" data-testid="go-admin-review" href="/agent-loop/admin">
                    🛡️ Agent review queue
                  </Link>
                ) : null}
                <div className="pp-menu-sep" />
                {signOutError ? (
                  <div className="pp-menu-item pp-menu-note" role="alert" data-testid="sign-out-error">
                    {signOutError}
                  </div>
                ) : null}
                <button
                  type="button"
                  className="pp-menu-item"
                  data-testid="sign-out"
                  disabled={busy}
                  onClick={signOut}
                >
                  Sign out
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </header>
      {children}
    </div>
  )
}
