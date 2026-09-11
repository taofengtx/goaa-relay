import { redirect } from 'next/navigation'
import GrowthPage from '@/app/components/agent-loop/GrowthPage'
import { getSession, hasRole } from '@/app/lib/agent-loop/server'
import { clerkAuthState } from '@/app/lib/clerk-entry'

export const dynamic = 'force-dynamic'

export default async function Page() {
  const session = await getSession()
  if (!session) redirect('/agent-loop/login?next=/agent-loop/customer/get-licensed')
  const canEnterAgent = hasRole(session.user, 'agent') && session.application?.status === 'approved'
  return (
    <GrowthPage user={session.user} canEnterAgent={canEnterAgent} clerkAuth={clerkAuthState() === 'enabled'} portal="customer" activeId="licensed" eyebrow="Get Licensed" title="Two paths to the same application">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
        <div className="goaa-card-2">
          <h2 className="goaa-h2">Learn first</h2>
          <p className="goaa-muted">Partner courses prepare you for the licence exam. Course access opens when the partner connection is live.</p>
          <button type="button" className="goaa-btn goaa-btn-secondary" disabled>Coming soon</button>
        </div>
        <div className="goaa-card-2">
          <h2 className="goaa-h2">Apply now</h2>
          <p className="goaa-muted">Already hold a licence? Submit it for review. Approval opens the Agent Portal on this same account.</p>
          <a className="goaa-btn goaa-btn-primary" data-testid="apply-now" href="/agent-loop/apply">Start application</a>
        </div>
      </div>
      <p className="goaa-muted" style={{ fontSize: 13, marginTop: 16 }}>Review is manual. AI only suggests; photos never count as official validity.</p>
    </GrowthPage>
  )
}
