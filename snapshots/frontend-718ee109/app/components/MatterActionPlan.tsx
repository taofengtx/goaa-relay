'use client'

import { PersonalAgentMatter } from '../lib/personal-agent-matter'
import { buildButlerActionPlan } from '../lib/personal-agent-action-plan'

const labels = { butler: 'Butler', owner: 'You', professional: 'Professional' } as const

export default function MatterActionPlan({ matter }: { matter: PersonalAgentMatter }) {
  if (matter.source !== 'agent_signal') return null
  const plan = buildButlerActionPlan(matter)
  return (
    <div style={{ marginTop: 10, border: '1px solid rgba(167,139,250,0.18)', borderRadius: 12, padding: '10px 11px', background: 'rgba(124,58,237,0.035)' }}>
      <div style={{ color: '#c4b5fd', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Butler Action Plan</div>
      <strong style={{ display: 'block', color: '#f5f3ff', fontSize: 11, marginTop: 2 }}>Here’s how I’ll move this Matter forward.</strong>
      <div style={{ marginTop: 8, display: 'grid', gap: 5 }}>
        {plan.slice(0, 8).map((item) => (
          <div key={item.id} style={{ display: 'grid', gridTemplateColumns: '72px 1fr auto', gap: 7, alignItems: 'start', padding: '6px 7px', borderRadius: 8, background: 'rgba(255,255,255,0.025)' }}>
            <span style={{ color: item.owner === 'butler' ? '#a7f3d0' : item.owner === 'professional' ? '#93c5fd' : '#ddd6fe', fontSize: 9 }}>{labels[item.owner]}</span>
            <span style={{ color: '#aaa5b7', fontSize: 9, lineHeight: 1.4 }}>{item.title}</span>
            <span style={{ color: item.status === 'ready' ? '#86efac' : item.status === 'blocked' ? '#fbbf24' : '#8f899b', fontSize: 8, textTransform: 'uppercase' }}>{item.status}</span>
          </div>
        ))}
      </div>
      <div style={{ color: '#777184', fontSize: 8.5, lineHeight: 1.4, marginTop: 7 }}>Ready means I can move it forward safely. Waiting/blocked means I need a real input, permission, or handoff before claiming progress.</div>
    </div>
  )
}
