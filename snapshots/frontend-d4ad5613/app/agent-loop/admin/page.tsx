import { redirect } from 'next/navigation'
import AdminReview from '@/app/components/agent-loop/AdminReview'
import Gate from '@/app/components/agent-loop/Gate'
import { getSession, requestToken, upstreamFetch } from '@/app/lib/agent-loop/server'
import { clerkAuthState } from '@/app/lib/clerk-entry'
import type { Application } from '@/app/lib/agent-loop/api'

export const dynamic = 'force-dynamic'

/**
 * Minimal agent-review page for administrators. It is an additional page, not
 * a rewrite of the existing administrator back office.
 *
 * Ordinary users and un-approved agents get 403 from the API; the queue is only
 * loaded (and only then rendered) after a successful admin call.
 */
export default async function AdminPage() {
  const session = await getSession()
  if (!session) redirect('/agent-loop/login?next=/agent-loop/admin')

  const res = await upstreamFetch('/admin/applications', await requestToken())
  if (!res.ok) {
    let code = 'admin_required'
    try {
      const payload = (await res.json()) as { error?: { code?: string } }
      if (payload?.error?.code) code = payload.error.code
    } catch {
      /* keep the default code */
    }
    return (
      <Gate
        code={code}
        title="Administrator access required"
        message="The review queue is only available to accounts holding the admin role. The server rejected this request, so no applicant data was sent to the browser."
        back={{ href: '/agent-loop/customer', label: 'Back to user dashboard' }}
      />
    )
  }

  const queue = (await res.json()) as { count: number; items: Application[] }
  return <AdminReview user={session.user} clerkAuth={clerkAuthState() === 'enabled'} initialQueue={queue.items} />
}
