import { redirect } from 'next/navigation'
import { getSession } from '@/app/lib/agent-loop/server'
import '../portal-preview/portal-preview.css'

export const dynamic = 'force-dynamic'

/**
 * Entry for the isolated agent-application loop.
 * Signed in -> the user dashboard. Not signed in -> the sign-in page.
 */
export default async function AgentLoopEntry() {
  const session = await getSession()
  if (!session) redirect('/agent-loop/login')
  redirect('/agent-loop/customer')
}
