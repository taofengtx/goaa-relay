import { Suspense } from 'react'
import { redirect } from 'next/navigation'
import AuthPanel from '@/app/components/agent-loop/AuthPanel'
import { getSession } from '@/app/lib/agent-loop/server'

export const dynamic = 'force-dynamic'

export default async function AgentLoopLogin() {
  const session = await getSession()
  if (session) redirect('/agent-loop/customer')
  return (
    <Suspense fallback={null}>
      <AuthPanel />
    </Suspense>
  )
}
