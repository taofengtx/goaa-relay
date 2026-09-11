'use client'

const capabilities = [
  { label: 'Agent Home', hint: 'Your AI relationship and current focus', href: '/planning', active: true },
  { label: 'Inbox', hint: 'Signals from email, letters, and documents', href: '/planning#inbox' },
  { label: 'Knowledge', hint: 'What your Agent remembers about you', href: '/planning#knowledge' },
  { label: 'Skills', hint: 'Capabilities your Agent can use for you', href: '/planning#skills' },
]

export default function PersonalAgentIdentity() {
  return (
    <section
      aria-label="My Personal AI Agent"
      style={{
        maxWidth: 1160,
        margin: '14px auto 0',
        padding: '14px 18px 12px',
        border: '1px solid rgba(139, 92, 246, 0.24)',
        borderRadius: 18,
        background: 'rgba(20, 14, 45, 0.34)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
          <div aria-hidden="true" style={{ width: 38, height: 38, borderRadius: 999, display: 'grid', placeItems: 'center', background: 'linear-gradient(135deg, #8b5cf6, #5b21b6)', color: '#fff', fontWeight: 700, flex: '0 0 auto' }}>G</div>
          <div style={{ minWidth: 0 }}>
            <div style={{ color: '#a78bfa', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase' }}>My Personal AI Agent</div>
            <div style={{ color: '#f5f3ff', fontSize: 17, fontWeight: 700, marginTop: 2 }}>Your AI that remembers, plans, and helps get things done</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#c4b5fd', fontSize: 12, whiteSpace: 'nowrap' }}><span aria-hidden="true" style={{ color: '#34d399' }}>●</span>Active</div>
      </div>

      <nav aria-label="Personal AI Agent capabilities" style={{ display: 'flex', gap: 8, marginTop: 12, overflowX: 'auto' }}>
        {capabilities.map((item) => (
          <a key={item.label} href={item.href} title={item.hint} aria-current={item.active ? 'page' : undefined} style={{ textDecoration: 'none', border: item.active ? '1px solid rgba(167, 139, 250, 0.55)' : '1px solid rgba(255,255,255,0.10)', background: item.active ? 'rgba(124, 58, 237, 0.18)' : 'rgba(255,255,255,0.025)', borderRadius: 999, padding: '7px 12px', color: item.active ? '#ede9fe' : '#b9b4c9', fontSize: 12, fontWeight: item.active ? 700 : 500, whiteSpace: 'nowrap' }}>{item.label}</a>
        ))}
      </nav>
    </section>
  )
}
