import { redirect } from 'next/navigation'
import CustomerPanel from '@/app/components/agent-loop/CustomerPanel'
import { getSession, hasRole } from '@/app/lib/agent-loop/server'
import { clerkAuthState } from '@/app/lib/clerk-entry'
import '../../portal-preview/portal-preview.css'

export const dynamic = 'force-dynamic'

/**
 * User dashboard. The role check happens on the server: a stale or edited
 * browser state can never unlock the Agent entry.
 */
export default async function CustomerPage() {
  const session = await getSession()
  if (!session) redirect('/agent-loop/login?next=/agent-loop/customer')

  const canEnterAgent = hasRole(session.user, 'agent') && session.application?.status === 'approved'

  return (
    <CustomerPanel
      user={session.user}
      application={session.application}
      canEnterAgent={canEnterAgent}
      clerkAuth={clerkAuthState() === 'enabled'}
    />
  )
}
