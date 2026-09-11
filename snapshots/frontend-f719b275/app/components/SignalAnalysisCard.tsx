'use client'

import { useState } from 'react'
import { restoreMatter } from '../lib/personal-agent-matter'
import { createMatterFromSignal } from '../lib/personal-agent-signal-matter'
import { AgentSignal, updateAgentSignal } from '../lib/personal-agent-signals'

function compact(items?: string[]) {
  return Array.isArray(items) ? items.filter(Boolean).slice(0, 4) : []
}

export default function SignalAnalysisCard({ signal }: { signal: AgentSignal }) {
  const [actionText, setActionText] = useState('')
  const ownerActions = compact(signal.ownerActions)
  const agentActions = compact(signal.agentCanDoNext)
  const missing = compact(signal.missingInformation)
  const risks = compact(signal.riskFlags)
  const hasAnalysis = Boolean(signal.analyzedAt || signal.documentType || signal.urgency || ownerActions.length || agentActions.length || missing.length || risks.length)

  if (!hasAnalysis && !signal.analysisError) return null

  if (signal.analysisError) {
    return (
      <div style={{ marginTop: 8, border: '1px solid rgba(248,113,113,0.18)', borderRadius: 10, padding: '8px 9px', background: 'rgba(248,113,113,0.04)' }}>
        <strong style={{ color: '#fecaca', fontSize: 10 }}>Understanding is not complete yet.</strong>
        <div style={{ color: '#8f899b', fontSize: 9, lineHeight: 1.45, marginTop: 3 }}>Your Butler kept the Signal but did not guess. You can retry the document after the analysis service is available.</div>
      </div>
    )
  }

  function createMatter() {
    const matter = createMatterFromSignal(signal)
    if (!matter) {
      setActionText('This Signal is not ready to become a Matter yet.')
      return
    }
    updateAgentSignal(signal.id, { ownerReviewedAt: new Date().toISOString(), linkedMatterId: matter.id })
    setActionText('Matter created. Your Butler is now tracking it through the Action Blueprint.')
  }

  function openMatter() {
    if (!signal.linkedMatterId) return
    const restored = restoreMatter(signal.linkedMatterId)
    setActionText(restored ? 'Matter opened in your Personal AI Agent workspace.' : 'The linked Matter could not be restored.')
  }

  return (
    <div style={{ marginTop: 8, border: '1px solid rgba(167,139,250,0.18)', borderRadius: 10, padding: '9px 10px', background: 'rgba(124,58,237,0.045)' }}>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        {signal.organization && <span style={{ color: '#ddd6fe', fontSize: 9 }}>{signal.organization}</span>}
        {signal.documentType && <span style={{ color: '#8f899b', fontSize: 9 }}>· {signal.documentType}</span>}
        {signal.urgency && <span style={{ color: signal.urgency === 'urgent' || signal.urgency === 'high' ? '#fbbf24' : '#9ca3af', fontSize: 9, textTransform: 'uppercase' }}>· {signal.urgency}</span>}
      </div>

      {(signal.dueDate || signal.amount) && (
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 6 }}>
          {signal.dueDate && <div style={{ color: '#f3f0fb', fontSize: 10 }}><span style={{ color: '#777184' }}>Due </span>{signal.dueDate}</div>}
          {signal.amount && <div style={{ color: '#f3f0fb', fontSize: 10 }}><span style={{ color: '#777184' }}>Amount </span>{signal.amount}</div>}
        </div>
      )}

      {ownerActions.length > 0 && (
        <div style={{ marginTop: 7 }}>
          <div style={{ color: '#c4b5fd', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em' }}>What needs you</div>
          {ownerActions.map((item) => <div key={item} style={{ color: '#aaa5b7', fontSize: 9, lineHeight: 1.45, marginTop: 2 }}>• {item}</div>)}
        </div>
      )}

      {agentActions.length > 0 && (
        <div style={{ marginTop: 7 }}>
          <div style={{ color: '#a7f3d0', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em' }}>What your Butler can do next</div>
          {agentActions.map((item) => <div key={item} style={{ color: '#aaa5b7', fontSize: 9, lineHeight: 1.45, marginTop: 2 }}>• {item}</div>)}
        </div>
      )}

      {risks.length > 0 && (
        <div style={{ marginTop: 7 }}>
          <div style={{ color: '#fbbf24', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Risks to watch</div>
          {risks.map((item) => <div key={item} style={{ color: '#aaa5b7', fontSize: 9, lineHeight: 1.45, marginTop: 2 }}>• {item}</div>)}
        </div>
      )}

      {missing.length > 0 && (
        <div style={{ marginTop: 7 }}>
          <div style={{ color: '#8f899b', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Still missing</div>
          {missing.map((item) => <div key={item} style={{ color: '#777184', fontSize: 9, lineHeight: 1.45, marginTop: 2 }}>• {item}</div>)}
        </div>
      )}

      {signal.professionalNeeded && (
        <div style={{ marginTop: 8, color: '#c4b5fd', fontSize: 9, lineHeight: 1.45 }}>Professional support may be useful{signal.professionalCategory ? `: ${signal.professionalCategory}` : ''}. Your Butler should prepare the context before handoff and keep tracking the Matter afterward.</div>
      )}

      <div style={{ marginTop: 9, borderTop: '1px solid rgba(255,255,255,0.07)', paddingTop: 8 }}>
        <div style={{ color: '#8f899b', fontSize: 9, lineHeight: 1.45 }}>Owner review · Your Agent can organize and suggest the next move, but you decide when this becomes a tracked Matter.</div>
        {signal.suggestedMatterTitle && <div style={{ color: '#ddd6fe', fontSize: 9, marginTop: 4 }}><span style={{ color: '#777184' }}>Suggested Matter · </span>{signal.suggestedMatterTitle}</div>}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 7 }}>
          {signal.linkedMatterId ? (
            <button type="button" onClick={openMatter} style={{ cursor: 'pointer', border: '1px solid rgba(52,211,153,0.30)', borderRadius: 999, background: 'rgba(16,185,129,0.08)', color: '#a7f3d0', padding: '6px 9px', fontSize: 9, fontWeight: 650 }}>Open Matter</button>
          ) : (
            <button type="button" onClick={createMatter} style={{ cursor: 'pointer', border: '1px solid rgba(167,139,250,0.32)', borderRadius: 999, background: 'rgba(124,58,237,0.10)', color: '#ddd6fe', padding: '6px 9px', fontSize: 9, fontWeight: 650 }}>Review & Create Matter</button>
          )}
        </div>
        {actionText && <div role="status" style={{ color: '#9ca3af', fontSize: 9, marginTop: 5 }}>{actionText}</div>}
      </div>
    </div>
  )
}
