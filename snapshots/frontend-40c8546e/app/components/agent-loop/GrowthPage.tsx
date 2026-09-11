'use client'

/**
 * GrowthPage.tsx — thin client wrapper so server pages can mount Shell with
 * a rail preset, a heading and static content. Used by the customer growth
 * pages (Skills Marketplace / Get Licensed / Earning Opportunities) and by
 * the agent/admin placeholder routes.
 */

import type { ReactNode } from 'react'
import Shell from './Shell'
import type { SessionUser } from '@/app/lib/agent-loop/api'

export default function GrowthPage({
  user,
  canEnterAgent,
  clerkAuth,
  portal,
  activeId,
  eyebrow,
  title,
  children,
}: {
  user: SessionUser
  canEnterAgent: boolean
  clerkAuth?: boolean
  portal: 'customer' | 'agent' | 'admin'
  activeId: string
  eyebrow: string
  title: string
  children: ReactNode
}) {
  return (
    <Shell user={user} canEnterAgent={canEnterAgent} clerkAuth={clerkAuth} portal={portal} activeId={activeId} eyebrow={eyebrow} title={title}>
      {children}
    </Shell>
  )
}

export function ComingSoon({ what }: { what: string }) {
  return (
    <div className="goaa-card-2">
      <h2 className="goaa-h2">{what}</h2>
      <p className="goaa-muted" style={{ margin: 0 }}>Coming in a later round.</p>
    </div>
  )
}
