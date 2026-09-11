import { redirect } from 'next/navigation'
import GrowthPage from '@/app/components/agent-loop/GrowthPage'
import { getSession, hasRole } from '@/app/lib/agent-loop/server'
import { clerkAuthState } from '@/app/lib/clerk-entry'

export const dynamic = 'force-dynamic'

export default async function Page() {
  const session = await getSession()
  if (!session) redirect('/agent-loop/login?next=/agent-loop/customer/earning')
  const canEnterAgent = hasRole(session.user, 'agent') && session.application?.status === 'approved'
  return (
    <GrowthPage user={session.user} canEnterAgent={canEnterAgent} clerkAuth={clerkAuthState() === 'enabled'} portal="customer" activeId="earning" eyebrow="Earning Paths" title="Ways to earn with GOAA">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
        <div className="goaa-card-2">
          <h2 className="goaa-h2">Become a licensed agent</h2>
          <p className="goaa-muted">Take client orders through GOAA with an approved licence.</p>
          <a className="goaa-btn goaa-btn-primary" href="/agent-loop/customer/get-licensed">See how</a>
        </div>
        <div className="goaa-card-2">
          <h2 className="goaa-h2">Refer a member</h2>
          <p className="goaa-muted">Rewards apply to GOAA membership fees only — never to insurance premiums or commissions.</p>
          <button type="button" className="goaa-btn goaa-btn-secondary" disabled>Coming soon</button>
        </div>
      </div>
    </GrowthPage>
  )
}
