import { redirect } from 'next/navigation'
import ApplicationForm from '@/app/components/agent-loop/ApplicationForm'
import { getSession, requestToken, upstreamFetch } from '@/app/lib/agent-loop/server'
import { clerkAuthState } from '@/app/lib/clerk-entry'
import type { Application } from '@/app/lib/agent-loop/api'
import '../../portal-preview/portal-preview.css'

export const dynamic = 'force-dynamic'

/**
 * "Become an Agent". Visiting this URL while signed out sends the visitor to
 * the sign-in page instead of showing an application form.
 */
export default async function ApplyPage() {
  const session = await getSession()
  if (!session) redirect('/agent-loop/login?next=/agent-loop/apply')

  let application: Application | null = null
  const res = await upstreamFetch('/applications/me', await requestToken())
  if (res.ok) {
    const payload = (await res.json()) as { application: Application | null }
    application = payload.application
  }

  return <ApplicationForm user={session.user} clerkAuth={clerkAuthState() === 'enabled'} initialApplication={application} />
}
