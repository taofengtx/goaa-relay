import { redirect } from 'next/navigation'
import AgentPanel from '@/app/components/agent-loop/AgentPanel'
import Gate from '@/app/components/agent-loop/Gate'
import { getSession, requestToken, upstreamFetch } from '@/app/lib/agent-loop/server'
import type { License } from '@/app/lib/agent-loop/api'
import { clerkAuthState } from '@/app/lib/clerk-entry'

export const dynamic = 'force-dynamic'

type Panel = {
  status: string
  application_id: string
  granted_at: string | null
  licenses: License[]
}

/**
 * Professional panel. The permission is decided by the API on every request
 * (role + approved application), so a suspended, revoked or rejected account
 * loses this page immediately — even with an old tab or a typed URL.
 */
export default async function AgentPage() {
  const session = await getSession()
  if (!session) redirect('/agent-loop/login?next=/agent-loop/agent')

  const res = await upstreamFetch('/agent/panel', await requestToken())
  if (!res.ok) {
    let code = 'agent_role_required'
    try {
      const payload = (await res.json()) as { error?: { code?: string; message?: string } }
      if (payload?.error?.code) code = payload.error.code
    } catch {
      /* keep the default code */
    }
    return (
      <Gate
        code={code}
        title="Agent panel is locked"
        message="This view needs an approved agent licence on the signed-in account. The server refused the request, so the panel was not rendered. Apply or wait for review, then try again."
        back={{ href: '/agent-loop/customer', label: 'Back to user dashboard' }}
      />
    )
  }

  const panel = (await res.json()) as Panel
  return <AgentPanel user={session.user} panel={panel} clerkAuth={clerkAuthState() === 'enabled'} />
}
