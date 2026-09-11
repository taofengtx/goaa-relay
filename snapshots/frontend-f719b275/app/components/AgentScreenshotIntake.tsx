'use client'

import { ChangeEvent, useRef, useState } from 'react'
import { analyzeAgentIntake } from '../lib/personal-agent-intake'
import { createAttachmentSignal, updateAgentSignal } from '../lib/personal-agent-signals'

type IntakeMode = 'email_screenshot' | 'physical_mail' | 'document'
type IntakeState = 'idle' | 'analyzing' | 'done' | 'error'

const MODES: { id: IntakeMode; label: string; hint: string }[] = [
  { id: 'email_screenshot', label: 'Email Screenshot', hint: 'Screenshot an important email and give it to your Agent.' },
  { id: 'physical_mail', label: 'Letter / Mail', hint: 'Photograph a letter, notice, bill, or statement.' },
  { id: 'document', label: 'Document', hint: 'Upload a PDF or document that may require action.' },
]

export default function AgentScreenshotIntake() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [mode, setMode] = useState<IntakeMode>('email_screenshot')
  const [note, setNote] = useState('')
  const [savedName, setSavedName] = useState('')
  const [state, setState] = useState<IntakeState>('idle')
  const [statusText, setStatusText] = useState('')

  function chooseFile() {
    if (state !== 'analyzing') inputRef.current?.click()
  }

  async function onFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    const ownerNote = note.trim()
    const localSignal = createAttachmentSignal({ source: mode, fileName: file.name, fileType: file.type, note: ownerNote })
    setSavedName(file.name)
    setNote('')
    setState('analyzing')
    setStatusText('I received it. I’m checking what it is, what needs attention, and whether there is a deadline.')

    try {
      const result = await analyzeAgentIntake({ file, source: mode, note: ownerNote })
      const analysis = result.signal
      updateAgentSignal(localSignal.id, {
        title: analysis.title || localSignal.title,
        summary: analysis.summary || localSignal.summary,
        status: analysis.needs_action ? 'needs_action' : 'understood',
        suggestedMatterTitle: analysis.suggested_matter_title || undefined,
        dueDate: analysis.due_date || undefined,
        organization: analysis.organization || undefined,
        amount: analysis.amount || undefined,
        documentType: analysis.document_type || undefined,
        urgency: analysis.urgency,
        riskFlags: analysis.risk_flags,
        ownerActions: analysis.owner_actions,
        agentCanDoNext: analysis.agent_can_do_next,
        missingInformation: analysis.missing_information,
        professionalNeeded: analysis.professional_needed,
        professionalCategory: analysis.professional_category || undefined,
        analyzedAt: new Date().toISOString(),
        analysisError: undefined,
      })
      setState('done')
      setStatusText(analysis.needs_action ? 'I found something that needs attention. I organized the next steps below.' : 'I understood it. Nothing in the current item appears to require immediate action.')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Document understanding is temporarily unavailable.'
      updateAgentSignal(localSignal.id, { analysisError: message })
      setState('error')
      setStatusText('I received the item safely, but I could not finish understanding it yet. I have not guessed or marked it complete.')
    }
  }

  return (
    <div style={{ marginTop: 12, border: '1px solid rgba(139,92,246,0.28)', borderRadius: 14, padding: '12px', background: 'rgba(124,58,237,0.06)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <div>
          <div style={{ color: '#c4b5fd', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Give it to your Butler</div>
          <strong style={{ display: 'block', color: '#f3f0fb', fontSize: 13, marginTop: 3 }}>Screenshot it. Photograph it. Drop it here.</strong>
        </div>
        <span style={{ color: '#858091', fontSize: 10 }}>You choose exactly what your Agent can see.</span>
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 }}>
        {MODES.map((item) => (
          <button key={item.id} type="button" onClick={() => setMode(item.id)} disabled={state === 'analyzing'} title={item.hint} style={{ cursor: state === 'analyzing' ? 'wait' : 'pointer', border: mode === item.id ? '1px solid rgba(167,139,250,0.65)' : '1px solid rgba(255,255,255,0.10)', background: mode === item.id ? 'rgba(124,58,237,0.18)' : 'rgba(255,255,255,0.02)', color: mode === item.id ? '#ede9fe' : '#aaa5b7', borderRadius: 999, padding: '6px 9px', fontSize: 10 }}>{item.label}</button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) auto', gap: 8, marginTop: 9 }}>
        <input value={note} disabled={state === 'analyzing'} onChange={(event) => setNote(event.target.value)} placeholder="Optional: tell your Butler anything useful" style={{ width: '100%', boxSizing: 'border-box', border: '1px solid rgba(255,255,255,0.10)', borderRadius: 10, background: 'rgba(0,0,0,0.15)', color: '#ede9fe', padding: '9px 10px', fontSize: 11, outline: 'none' }} />
        <button type="button" onClick={chooseFile} disabled={state === 'analyzing'} style={{ cursor: state === 'analyzing' ? 'wait' : 'pointer', border: '1px solid rgba(167,139,250,0.55)', borderRadius: 10, background: 'rgba(124,58,237,0.20)', color: '#ede9fe', padding: '8px 12px', fontSize: 11, fontWeight: 650, whiteSpace: 'nowrap', opacity: state === 'analyzing' ? 0.65 : 1 }}>{state === 'analyzing' ? 'Understanding…' : 'Give to my Agent'}</button>
      </div>

      <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={onFile} style={{ display: 'none' }} />
      <p style={{ color: '#817b8e', fontSize: 9, lineHeight: 1.45, margin: '7px 0 0' }}>Your Agent only analyzes the item you explicitly choose. It will not claim a document was understood unless the analysis endpoint returns successfully.</p>

      {savedName && state !== 'idle' && (
        <div role="status" style={{ marginTop: 8, border: `1px solid ${state === 'error' ? 'rgba(248,113,113,0.25)' : 'rgba(52,211,153,0.22)'}`, borderRadius: 10, padding: '9px 10px', background: state === 'error' ? 'rgba(248,113,113,0.05)' : 'rgba(52,211,153,0.06)' }}>
          <strong style={{ color: state === 'error' ? '#fecaca' : '#d1fae5', fontSize: 11 }}>{state === 'analyzing' ? '收到，我马上去办。' : state === 'done' ? '我看明白了，继续往下办。' : '我已经接住了，不会乱猜。'}</strong>
          <div style={{ color: '#9ca3af', fontSize: 9, marginTop: 3 }}>{statusText}</div>
          <div style={{ color: '#777184', fontSize: 8, marginTop: 3 }}>{savedName}</div>
        </div>
      )}
    </div>
  )
}
