'use client'

import { useEffect, useState } from 'react'
import { AGENT_SIGNAL_EVENT, AgentSignal, readAgentSignals } from '../lib/personal-agent-signals'
import AgentScreenshotIntake from './AgentScreenshotIntake'
import SignalAnalysisCard from './SignalAnalysisCard'

const sourceLabel = {
  email_screenshot: 'Email Screenshot',
  physical_mail: 'Letter / Mail',
  document: 'Document',
  manual: 'Manual',
} as const

export default function PersonalAgentInbox() {
  const [signals, setSignals] = useState<AgentSignal[]>([])

  useEffect(() => {
    const refresh = () => setSignals(readAgentSignals())
    refresh()
    const timer = window.setInterval(refresh, 1800)
    window.addEventListener('storage', refresh)
    window.addEventListener(AGENT_SIGNAL_EVENT, refresh)
    return () => {
      window.clearInterval(timer)
      window.removeEventListener('storage', refresh)
      window.removeEventListener(AGENT_SIGNAL_EVENT, refresh)
    }
  }, [])

  const actionCount = signals.filter((item) => item.status === 'needs_action').length

  return (
    <section id="inbox" aria-label="Personal AI Agent inbox" style={{ maxWidth: 1160, margin: '12px auto 0', padding: '14px 18px', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 18, background: 'rgba(255,255,255,0.018)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'end', flexWrap: 'wrap' }}>
        <div>
          <div style={{ color: '#a78bfa', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase' }}>Agent Inbox</div>
          <div style={{ color: '#f5f3ff', fontSize: 18, fontWeight: 700, marginTop: 3 }}>Show your Agent what arrived. Let it find what needs doing.</div>
          <p style={{ color: '#8f8a9e', fontSize: 11, margin: '5px 0 0', lineHeight: 1.5 }}>Give your Butler a screenshot, photo, or PDF. It can understand the item, identify deadlines and risks, separate what you need to do from what the Agent can do next, and keep the work moving.</p>
        </div>
        <div style={{ color: '#8f8a9e', fontSize: 11 }}>{signals.length ? `${signals.length} signal${signals.length === 1 ? '' : 's'} · ${actionCount} need action` : 'No signals captured yet'}</div>
      </div>

      <AgentScreenshotIntake />

      {signals.length > 0 && (
        <div style={{ marginTop: 10, display: 'grid', gap: 6 }}>
          {signals.slice(0, 6).map((item) => (
            <article key={item.id} style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '9px 10px', background: 'rgba(255,255,255,0.015)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                <strong style={{ color: '#ddd8e8', fontSize: 11 }}>{item.title}</strong>
                <span style={{ color: '#8f899b', fontSize: 9 }}>{sourceLabel[item.source]}</span>
              </div>
              <div style={{ color: '#8f899b', fontSize: 10, lineHeight: 1.45, marginTop: 4 }}>{item.summary}</div>
              {item.intakeNote && <div style={{ color: '#aaa5b7', fontSize: 9, marginTop: 5 }}>Owner note: {item.intakeNote}</div>}
              <SignalAnalysisCard signal={item} />
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
