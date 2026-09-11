'use client'

const steps = [
  {
    number: '01',
    title: 'Understand the Goal',
    description: 'Clarify what the owner wants solved and what matters most.',
  },
  {
    number: '02',
    title: 'Assess the Situation',
    description: 'Organize known facts, identify gaps, risks, constraints, and options.',
  },
  {
    number: '03',
    title: 'Build the Action Plan',
    description: 'Turn the situation into a personalized, practical path forward.',
  },
  {
    number: '04',
    title: 'Connect the Right Professional',
    description: 'Bring in a licensed professional only when real execution requires one.',
  },
  {
    number: '05',
    title: 'Execute, Track & Optimize',
    description: 'Follow the work through completion, keep context, and improve the next step.',
  },
]

export default function AgentProblemSolvingModel() {
  return (
    <section
      id="agent-problem-solving-model"
      aria-label="How your Personal AI Agent gets things done"
      style={{
        maxWidth: 1160,
        margin: '12px auto 0',
        padding: '14px 18px',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 18,
        background: 'rgba(255,255,255,0.018)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 18, alignItems: 'end', flexWrap: 'wrap' }}>
        <div>
          <div style={{ color: '#a78bfa', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
            Agent Problem-Solving Model
          </div>
          <div style={{ color: '#f5f3ff', fontSize: 18, fontWeight: 700, marginTop: 3 }}>
            One Agent. Every problem follows a clear path to completion.
          </div>
        </div>
        <div style={{ color: '#8f8a9e', fontSize: 12 }}>
          Understand → Assess → Plan → Connect → Execute
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 8,
          marginTop: 12,
        }}
      >
        {steps.map((step) => (
          <article
            key={step.number}
            style={{
              border: '1px solid rgba(139, 92, 246, 0.16)',
              borderRadius: 14,
              padding: '11px 12px',
              background: 'rgba(20, 14, 45, 0.22)',
            }}
          >
            <div style={{ color: '#8b5cf6', fontSize: 11 }}>{step.number}</div>
            <strong style={{ display: 'block', color: '#ede9fe', fontSize: 13, marginTop: 4 }}>{step.title}</strong>
            <p style={{ color: '#9d98aa', fontSize: 11, lineHeight: 1.5, margin: '5px 0 0' }}>{step.description}</p>
          </article>
        ))}
      </div>
    </section>
  )
}
