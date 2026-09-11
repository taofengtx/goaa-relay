'use client'

import { PersonalAgentMatter } from '../lib/personal-agent-matter'
import { evaluateMatterProgress } from '../lib/personal-agent-matter-progress'
import { buildProfessionalHandoffPackage } from '../lib/personal-agent-handoff-package'
import { CUSTOMER_JOURNEY_KEYS, writeCustomerJourney } from '../lib/customer-journey'
import { BOOKING_URL } from '../lib/paid-connection'

const HANDOFF_PACKAGE_KEY = 'goaa_pending_professional_handoff_v1'

export default function MatterProfessionalConnect({ matter }: { matter: PersonalAgentMatter }) {
  if (matter.source !== 'agent_signal' || matter.knownFacts.professional_needed !== true) return null
  const gate = evaluateMatterProgress(matter)
  const category = typeof matter.knownFacts.professional_category === 'string' && matter.knownFacts.professional_category.trim() ? matter.knownFacts.professional_category : 'licensed professional'
  const ready = gate.from === 'Connect' || (gate.from === 'Plan' && gate.canAdvance)

  function connect() {
    if (!ready || typeof window === 'undefined') return
    const handoff = buildProfessionalHandoffPackage(matter)
    window.localStorage.setItem(HANDOFF_PACKAGE_KEY, JSON.stringify(handoff))
    window.localStorage.setItem(CUSTOMER_JOURNEY_KEYS.authReturn, '/connect-pass?source=matter')
    writeCustomerJourney({ step: 'need_ready', planningSessionId: matter.sessionId || undefined })
    window.location.assign('/connect-pass?source=matter')
  }

  return (
    <>
    <div className="goaa-paid-closed" data-testid="matter-paid-closed" style={{ marginTop: 10, border: '1px solid rgba(96,165,250,0.20)', borderRadius: 12, padding: '10px 11px', background: 'rgba(37,99,235,0.035)' }}>
      <div style={{ color: '#93c5fd', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Professional Connection</div>
      <strong style={{ display: 'block', color: '#eff6ff', fontSize: 11, marginTop: 2 }}>Paid connection to a {category} is opening soon.</strong>
      <p style={{ color: '#9ca3af', fontSize: 9, lineHeight: 1.45, margin: '6px 0 0' }}>For now, book a 30-minute assessment with the GOAA team — booking never charges you.</p>
      <a href={BOOKING_URL} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-block', marginTop: 8, border: '1px solid rgba(96,165,250,0.34)', borderRadius: 999, background: 'rgba(37,99,235,0.10)', color: '#bfdbfe', padding: '6px 10px', fontSize: 9, fontWeight: 650, textDecoration: 'none' }}>Book a 30-minute assessment ↗</a>
    </div>
    <div className="goaa-paid-open-only" style={{ marginTop: 10, border: '1px solid rgba(96,165,250,0.20)', borderRadius: 12, padding: '10px 11px', background: 'rgba(37,99,235,0.035)' }}>
      <div style={{ color: '#93c5fd', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Professional Connection</div>
      <strong style={{ display: 'block', color: '#eff6ff', fontSize: 11, marginTop: 2 }}>When you’re ready, I can carry this Matter to the right {category}.</strong>
      <p style={{ color: '#9ca3af', fontSize: 9, lineHeight: 1.45, margin: '6px 0 0' }}>I’ll pass the reviewed Matter into GOAA’s existing Connect Pass journey. Authentication, payment verification, matching, and the live service order remain canonical — this Butler does not create a second checkout path.</p>
      <button type="button" onClick={connect} disabled={!ready} style={{ marginTop: 8, cursor: ready ? 'pointer' : 'not-allowed', opacity: ready ? 1 : .55, border: '1px solid rgba(96,165,250,0.34)', borderRadius: 999, background: 'rgba(37,99,235,0.10)', color: '#bfdbfe', padding: '6px 10px', fontSize: 9, fontWeight: 650 }}>{ready ? 'Continue to protected connection →' : 'Finish assessment before connecting'}</button>
    </div>
    </>
  )
}
