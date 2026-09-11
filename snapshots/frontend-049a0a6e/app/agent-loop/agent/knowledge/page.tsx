import { redirect } from 'next/navigation'
import GrowthPage, { ComingSoon } from '@/app/components/agent-loop/GrowthPage'
import { getSession, hasRole } from '@/app/lib/agent-loop/server'
import { clerkAuthState } from '@/app/lib/clerk-entry'

export const dynamic = 'force-dynamic'

export default async function Page() {
  const session = await getSession()
  if (!session) redirect('/agent-loop/login?next=/agent-loop/agent/knowledge')
  const canEnterAgent = hasRole(session.user, 'agent') && session.application?.status === 'approved'
  return (
    <GrowthPage user={session.user} canEnterAgent={canEnterAgent} clerkAuth={clerkAuthState() === 'enabled'} portal="agent" activeId="knowledge" eyebrow="Agent Portal" title="Knowledge Base">
      <ComingSoon what="Knowledge Base" />
    </GrowthPage>
  )
}
