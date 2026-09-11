'use client'

import { useState } from 'react'
import { PersonalAgentMatter } from '../lib/personal-agent-matter'
import { advanceCurrentMatter, evaluateMatterProgress } from '../lib/personal-agent-matter-progress'

const PENDING_PROMPT_KEY = 'goaa_pending_prompt_v1'

function stringList(value: unknown) {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && Boolean(item.trim())).slice(0, 4) : []
}

function buildAssessmentPrompt(matter: PersonalAgentMatter) {
  const organization = typeof matter.knownFacts.organization === 'string' ? matter.knownFacts.organization : ''
  const dueDate = typeof matter.knownFacts.due_date === 'string' ? matter.knownFacts.due_date : ''
  const amount = typeof matter.knownFacts.amount === 'string' || typeof matter.knownFacts.amount === 'number' ? String(matter.knownFacts.amount) : ''
  const urgency = typeof matter.knownFacts.urgency === 'string' ? matter.knownFacts.urgency : ''
  const ownerActions = stringList(matter.knownFacts.owner_actions)
  const agentActions = stringList(matter.knownFacts.agent_can_do_next)
  const missing = stringList(matter.knownFacts.missing_information)
  const risks = stringList(matter.knownFacts.risk_flags)
  const professionalNeeded = matter.knownFacts.professional_needed === true
  const professionalCategory = typeof matter.knownFacts.professional_category === 'string' ? matter.knownFacts.professional_category : ''

  const context = [
    `Matter: ${matter.title}`,
    organization ? `Organization: ${organization}` : '', dueDate ? `Due date: ${dueDate}` : '', amount ? `Amount: ${amount}` : '', urgency ? `Urgency: ${urgency}` : '',
    ownerActions.length ? `Owner actions identified: ${ownerActions.join('; ')}` : '', agentActions.length ? `Agent next steps identified: ${agentActions.join('; ')}` : '',
    missing.length ? `Missing information: ${missing.join('; ')}` : '', risks.length ? `Risks: ${risks.join('; ')}` : '',
    professionalNeeded ? `Professional support may be needed${professionalCategory ? `: ${professionalCategory}` : ''}.` : 'Professional support is not currently confirmed as necessary.',
  ].filter(Boolean).join('\n')

  return `Continue this Matter from the Assess step. Use the reviewed Signal context below. Do not make me repeat information already captured. First tell me what you can safely move forward yourself, then ask only for the minimum missing information or permission that truly requires me. Do not claim any external action is complete unless it was actually performed.\n\n${context}`
}

export default function MatterAssessmentPanel({ matter }: { matter: PersonalAgentMatter }) {
  const [progressText, setProgressText] = useState('')
  if (matter.source !== 'agent_signal') return null

  const ownerActions = stringList(matter.knownFacts.owner_actions)
  const agentActions = stringList(matter.knownFacts.agent_can_do_next)
  const missing = stringList(matter.knownFacts.missing_information)
  const risks = stringList(matter.knownFacts.risk_flags)
  const professionalNeeded = matter.knownFacts.professional_needed === true
  const professionalCategory = typeof matter.knownFacts.professional_category === 'string' ? matter.knownFacts.professional_category : ''
  const urgency = typeof matter.knownFacts.urgency === 'string' ? matter.knownFacts.urgency : ''
  const dueDate = typeof matter.knownFacts.due_date === 'string' ? matter.knownFacts.due_date : ''
  const gate = evaluateMatterProgress(matter)

  function continueAssessment() {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(PENDING_PROMPT_KEY, buildAssessmentPrompt(matter))
    window.location.reload()
  }

  function advance() {
    const next = advanceCurrentMatter()
    if (!next) { setProgressText(gate.reason); return }
    setProgressText(`Blueprint advanced to ${gate.to}.`)
    window.location.reload()
  }

  return (
    <div style={{ marginTop: 10, border: '1px solid rgba(52,211,153,0.18)', borderRadius: 12, padding: '10px 11px', background: 'rgba(16,185,129,0.035)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <div><div style={{ color: '#a7f3d0', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Butler Assessment</div><strong style={{ display: 'block', color: '#ecfdf5', fontSize: 11, marginTop: 2 }}>I understand the item. I’m separating what I can move forward from what needs you.</strong></div>
        <div style={{ color: urgency === 'urgent' || urgency === 'high' ? '#fbbf24' : '#8f899b', fontSize: 9, textTransform: 'uppercase' }}>{urgency || 'normal'}{dueDate ? ` · due ${dueDate}` : ''}</div>
      </div>
      {agentActions.length > 0 && <div style={{ marginTop: 8 }}><div style={{ color: '#a7f3d0', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em' }}>I can move these forward</div>{agentActions.map((item) => <div key={item} style={{ color: '#aaa5b7', fontSize: 9, lineHeight: 1.45, marginTop: 2 }}>• {item}</div>)}</div>}
      {ownerActions.length > 0 && <div style={{ marginTop: 8 }}><div style={{ color: '#c4b5fd', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em' }}>I need you only for these</div>{ownerActions.map((item) => <div key={item} style={{ color: '#aaa5b7', fontSize: 9, lineHeight: 1.45, marginTop: 2 }}>• {item}</div>)}</div>}
      {missing.length > 0 && <div style={{ marginTop: 8 }}><div style={{ color: '#8f899b', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Missing before I can safely continue</div>{missing.map((item) => <div key={item} style={{ color: '#777184', fontSize: 9, lineHeight: 1.45, marginTop: 2 }}>• {item}</div>)}</div>}
      {risks.length > 0 && <div style={{ marginTop: 8 }}><div style={{ color: '#fbbf24', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Risks I’m tracking</div>{risks.map((item) => <div key={item} style={{ color: '#aaa5b7', fontSize: 9, lineHeight: 1.45, marginTop: 2 }}>• {item}</div>)}</div>}

      <div style={{ marginTop: 9, borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 7, color: '#8f899b', fontSize: 9, lineHeight: 1.45 }}>
        Current Blueprint step: <span style={{ color: '#ddd6fe' }}>{gate.from}</span>. {gate.reason} {professionalNeeded ? `Professional support may be needed${professionalCategory ? ` (${professionalCategory})` : ''}.` : ''}
      </div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 9 }}>
        <button type="button" onClick={continueAssessment} style={{ cursor: 'pointer', border: '1px solid rgba(52,211,153,0.30)', borderRadius: 999, background: 'rgba(16,185,129,0.08)', color: '#a7f3d0', padding: '6px 10px', fontSize: 9, fontWeight: 650 }}>Continue with Butler →</button>
        {gate.canAdvance && gate.to && <button type="button" onClick={advance} style={{ cursor: 'pointer', border: '1px solid rgba(167,139,250,0.32)', borderRadius: 999, background: 'rgba(124,58,237,0.10)', color: '#ddd6fe', padding: '6px 10px', fontSize: 9, fontWeight: 650 }}>Advance to {gate.to} →</button>}
      </div>
      {progressText && <div role="status" style={{ color: '#9ca3af', fontSize: 9, marginTop: 5 }}>{progressText}</div>}
    </div>
  )
}
