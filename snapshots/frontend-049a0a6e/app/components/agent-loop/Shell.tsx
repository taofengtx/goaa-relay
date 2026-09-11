'use client'

/**
 * Shell.tsx — visual shell for the isolated /agent-loop/* front end.
 *
 * Round C1: the shell now renders the shared PortalShell (planning.goaa.ai
 * look: logo + portal brand + account menu, left rail card, main card).
 * The sign-out decision is unchanged and still lives in lib/agent-loop/signout.ts.
 * Props are backwards compatible; `portal` and `activeId` pick the rail preset.
 */

import Link from 'next/link'
import { useState } from 'react'
import type { ReactNode } from 'react'
import type { SessionUser } from '@/app/lib/agent-loop/api'
import { api } from '@/app/lib/agent-loop/api'
import { performSignOut } from '@/app/lib/agent-loop/signout'
import PortalShell, { ADMIN_RAIL, AGENT_RAIL, CUSTOMER_RAIL } from '@/app/components/portal/PortalShell'
import type { RailSection } from '@/app/components/portal/PortalShell'

export type { RailItem, RailSection } from '@/app/components/portal/PortalShell'

export default function Shell({
  user,
  canEnterAgent,
  isAgentView,
  clerkAuth = false,
  portal,
  activeId,
  sections,
  eyebrow,
  title,
  headerRight,
  aside,
  children,
}: {
  user: SessionUser
  /** Server-verified: the account holds the agent role AND the application is approved. */
  canEnterAgent: boolean
  isAgentView?: boolean
  /** Server-decided: this deployment signs people in through Clerk. */
  clerkAuth?: boolean
  portal?: 'customer' | 'agent' | 'admin'
  activeId?: string
  sections?: RailSection[]
  eyebrow?: string
  title?: ReactNode
  headerRight?: ReactNode
  aside?: ReactNode
  children: ReactNode
}) {
  const [busy, setBusy] = useState(false)
  const [signOutError, setSignOutError] = useState<string | null>(null)

  const which = portal ?? (isAgentView ? 'agent' : 'customer')
  const rail = sections ?? (which === 'agent' ? AGENT_RAIL : which === 'admin' ? ADMIN_RAIL : CUSTOMER_RAIL)

  /**
   * Sign out. Never report a sign-out that did not happen: only a refusal
   * lands back here and is shown; the Clerk branch navigates through the SDK.
   */
  async function signOut() {
    if (busy) return
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
    if (result.status !== 'redirected') {
      setBusy(false)
      setSignOutError(result.message)
    }
  }

  const railFooter = (
    <div style={{ padding: '4px 8px 0', display: 'grid', gap: 6, fontSize: 13 }}>
      {which === 'agent' ? (
        <Link className="goaa-rail-item" data-testid="switch-to-user" href="/agent-loop/customer">⇄ Back to Customer</Link>
      ) : canEnterAgent ? (
        <Link className="goaa-rail-item" data-testid="switch-to-agent" href="/agent-loop/agent">⇄ Switch to Agent Portal</Link>
      ) : which === 'customer' ? (
        <span className="goaa-muted" style={{ padding: '0 6px' }}>Agent Portal opens after your licence is approved.</span>
      ) : null}
      {user.roles.includes('admin') && which !== 'admin' ? (
        <Link className="goaa-rail-item" data-testid="go-admin-review" href="/agent-loop/admin">Admin review queue</Link>
      ) : null}
      <span className="goaa-muted" style={{ padding: '0 6px', fontSize: 12 }}>{user.email}</span>
      {signOutError ? (
        <div role="alert" data-testid="sign-out-error" style={{ color: 'var(--goaa-danger)', padding: '0 6px' }}>{signOutError}</div>
      ) : null}
    </div>
  )

  return (
    <PortalShell
      portal={which}
      brandHref={which === 'customer' ? '/planning' : `/agent-loop/${which}`}
      signedIn
      onLogout={signOut}
      sections={rail}
      activeId={activeId ?? ''}
      railFooter={railFooter}
      eyebrow={eyebrow}
      title={title}
      headerRight={headerRight}
      aside={aside}
    >
      {children}
    </PortalShell>
  )
}
