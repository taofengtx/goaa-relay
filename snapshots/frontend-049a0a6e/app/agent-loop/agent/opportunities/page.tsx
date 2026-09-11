import { redirect } from 'next/navigation'
import GrowthPage, { ComingSoon } from '@/app/components/agent-loop/GrowthPage'
import { getSession, hasRole } from '@/app/lib/agent-loop/server'
import { clerkAuthState } from '@/app/lib/clerk-entry'

export const dynamic = 'force-dynamic'

export default async function Page() {
  const session = await getSession()
  if (!session) redirect('/agent-loop/login?next=/agent-loop/agent/opportunities')
  const canEnterAgent = hasRole(session.user, 'agent') && session.application?.status === 'approved'
  return (
    <GrowthPage user={session.user} canEnterAgent={canEnterAgent} clerkAuth={clerkAuthState() === 'enabled'} portal="agent" activeId="opportunities" eyebrow="Agent Portal" title="Opportunities">
      <ComingSoon what="Opportunities" />
    </GrowthPage>
  )
}
