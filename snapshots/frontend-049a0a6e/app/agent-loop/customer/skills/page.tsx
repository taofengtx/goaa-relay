import { redirect } from 'next/navigation'
import GrowthPage from '@/app/components/agent-loop/GrowthPage'
import { getSession, hasRole } from '@/app/lib/agent-loop/server'
import { clerkAuthState } from '@/app/lib/clerk-entry'

export const dynamic = 'force-dynamic'

export default async function Page() {
  const session = await getSession()
  if (!session) redirect('/agent-loop/login?next=/agent-loop/customer/skills')
  const canEnterAgent = hasRole(session.user, 'agent') && session.application?.status === 'approved'
  return (
    <GrowthPage user={session.user} canEnterAgent={canEnterAgent} clerkAuth={clerkAuthState() === 'enabled'} portal="customer" activeId="skills" eyebrow="Skills Marketplace" title="Capabilities you can add to your AI Butler">
      <div className="goaa-notice" data-testid="skills-partner-pending">Partner setup pending — the catalog goes live once Pipedream Connect is configured.</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
        {[
          ['Tax & income', 'Model filing status and deductions before decisions.'],
          ['Insurance & risk', 'See what coverage your life needs and where you are over- or under-insured.'],
          ['Housing & relocation', 'Rent, buy or move with tax, schooling and timing in one plan.'],
          ['Education & family', 'Plan schooling, savings and residency together.'],
        ].map(([name, blurb]) => (
          <div key={name} className="goaa-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}><b>{name}</b><span className="goaa-pill ok">Free</span></div>
            <p className="goaa-muted" style={{ fontSize: 13, margin: '8px 0 12px' }}>{blurb}</p>
            <a className="goaa-btn goaa-btn-secondary" href={`/planning?prompt=${encodeURIComponent('Help me with ' + name.toLowerCase())}`}>Use this skill</a>
          </div>
        ))}
      </div>
    </GrowthPage>
  )
}
