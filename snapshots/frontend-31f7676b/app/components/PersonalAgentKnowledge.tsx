'use client'

import { useEffect, useMemo, useState } from 'react'
import { derivePersonalKnowledge } from '../lib/personal-agent-knowledge'
import { readMatterHistory } from '../lib/personal-agent-matter'
import {
  KNOWLEDGE_VERIFICATION_EVENT,
  knowledgeFactSignature,
  readKnowledgeVerification,
  setKnowledgeFactStatus,
} from '../lib/personal-agent-knowledge-verification'

const FACT_LABEL: Record<string, string> = {
  age: 'Age', location: 'Location', insured_person: 'Insured Person', coverage_goal: 'Coverage Goal',
  coverage_amount: 'Coverage Amount', existing_coverage: 'Existing Coverage', health_status: 'Health Status',
  monthly_budget: 'Monthly Budget', current_savings: 'Current Savings', target_amount: 'Target Amount',
  time_horizon: 'Time Horizon', risk_preference: 'Risk Preference', child_age: 'Child Age',
  college_start_age: 'College Start Age', college_type: 'School Type',
}

function displayValue(value: unknown) {
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value)
  try { return JSON.stringify(value) } catch { return String(value) }
}

export default function PersonalAgentKnowledge() {
  const [version, setVersion] = useState(0)
  const [editing, setEditing] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  useEffect(() => {
    const refresh = () => setVersion((value) => value + 1)
    const timer = window.setInterval(refresh, 1800)
    window.addEventListener('storage', refresh)
    window.addEventListener('goaa:matter-restored', refresh)
    window.addEventListener(KNOWLEDGE_VERIFICATION_EVENT, refresh)
    return () => {
      window.clearInterval(timer)
      window.removeEventListener('storage', refresh)
      window.removeEventListener('goaa:matter-restored', refresh)
      window.removeEventListener(KNOWLEDGE_VERIFICATION_EVENT, refresh)
    }
  }, [])

  const snapshot = useMemo(() => ({ revision: version, knowledge: derivePersonalKnowledge(readMatterHistory()), verification: readKnowledgeVerification() }), [version])
  const { knowledge, verification } = snapshot
  const visibleKnowledge = knowledge.filter((item) => verification[knowledgeFactSignature(item.key, item.value)]?.status !== 'removed')
  const confirmed = visibleKnowledge.filter((item) => verification[knowledgeFactSignature(item.key, item.value)]?.status === 'confirmed').length
  const updated = visibleKnowledge.filter((item) => verification[knowledgeFactSignature(item.key, item.value)]?.status === 'updated').length

  return (
    <section id="knowledge" aria-label="What my AI Agent knows about me" style={{ maxWidth: 1160, margin: '12px auto 0', padding: '14px 18px', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 18, background: 'rgba(255,255,255,0.018)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'end', flexWrap: 'wrap' }}>
        <div>
          <div style={{ color: '#a78bfa', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase' }}>Personal Knowledge</div>
          <div style={{ color: '#f5f3ff', fontSize: 18, fontWeight: 700, marginTop: 3 }}>What my AI Agent knows about me</div>
          <p style={{ color: '#8f8a9e', fontSize: 11, margin: '5px 0 0', lineHeight: 1.5 }}>Recognized facts stay provisional until you confirm them. You can correct or remove anything your Agent misunderstood.</p>
        </div>
        <div style={{ color: '#8f8a9e', fontSize: 11 }}>{visibleKnowledge.length ? `${visibleKnowledge.length} visible · ${confirmed} confirmed · ${updated} corrected` : 'Knowledge grows as your Agent handles real matters.'}</div>
      </div>

      {visibleKnowledge.length ? (
        <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 8 }}>
          {visibleKnowledge.slice(0, 12).map((item) => {
            const signature = knowledgeFactSignature(item.key, item.value)
            const record = verification[signature]
            const status = record?.status || 'recognized'
            const value = status === 'updated' && record?.overrideValue !== undefined ? record.overrideValue : item.value
            const isEditing = editing === signature
            return (
              <article key={signature} style={{ border: status === 'confirmed' || status === 'updated' ? '1px solid rgba(52,211,153,0.26)' : '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: '10px 11px', background: status === 'confirmed' || status === 'updated' ? 'rgba(16,185,129,0.05)' : item.sourceCount > 1 ? 'rgba(124,58,237,0.08)' : 'rgba(255,255,255,0.018)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
                  <div style={{ color: '#9b95aa', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{FACT_LABEL[item.key] || item.key.split('_').join(' ')}</div>
                  <div style={{ color: status === 'recognized' ? '#fbbf24' : '#34d399', fontSize: 9, textTransform: 'uppercase' }}>{status}</div>
                </div>

                {isEditing ? (
                  <div style={{ marginTop: 7 }}>
                    <input value={editValue} onChange={(event) => setEditValue(event.target.value)} autoFocus style={{ width: '100%', boxSizing: 'border-box', border: '1px solid rgba(167,139,250,0.4)', borderRadius: 8, background: 'rgba(10,8,20,0.8)', color: '#f5f3ff', padding: '7px 8px', fontSize: 12 }} />
                    <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                      <button type="button" onClick={() => { const clean = editValue.trim(); if (clean) setKnowledgeFactStatus(signature, 'updated', clean); setEditing(null) }} style={{ border: '1px solid rgba(52,211,153,0.28)', borderRadius: 999, background: 'rgba(16,185,129,0.08)', color: '#a7f3d0', padding: '5px 8px', fontSize: 9, cursor: 'pointer' }}>Save correction</button>
                      <button type="button" onClick={() => setEditing(null)} style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: 999, background: 'transparent', color: '#9b95aa', padding: '5px 8px', fontSize: 9, cursor: 'pointer' }}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div style={{ color: '#ede9fe', fontSize: 13, fontWeight: 650, marginTop: 4, overflowWrap: 'anywhere' }}>{displayValue(value)}</div>
                )}

                <div style={{ color: '#7f798b', fontSize: 9, marginTop: 7, lineHeight: 1.45 }}>{item.sourceCount > 1 ? `Seen in ${item.sourceCount} matters` : `From: ${item.sourceMatterTitles[0] || 'Current matter'}`}</div>

                {!isEditing && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 8 }}>
                    {status !== 'confirmed' && <button type="button" onClick={() => setKnowledgeFactStatus(signature, 'confirmed')} style={{ border: '1px solid rgba(52,211,153,0.24)', borderRadius: 999, background: 'rgba(16,185,129,0.06)', color: '#a7f3d0', padding: '5px 8px', fontSize: 9, cursor: 'pointer' }}>Confirm</button>}
                    <button type="button" onClick={() => { setEditValue(displayValue(value)); setEditing(signature) }} style={{ border: '1px solid rgba(167,139,250,0.22)', borderRadius: 999, background: 'rgba(124,58,237,0.05)', color: '#c4b5fd', padding: '5px 8px', fontSize: 9, cursor: 'pointer' }}>Correct</button>
                    <button type="button" onClick={() => setKnowledgeFactStatus(signature, 'removed')} style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: 999, background: 'transparent', color: '#8f899b', padding: '5px 8px', fontSize: 9, cursor: 'pointer' }}>Remove</button>
                  </div>
                )}
              </article>
            )
          })}
        </div>
      ) : (
        <div style={{ marginTop: 12, border: '1px dashed rgba(255,255,255,0.10)', borderRadius: 12, padding: '14px', color: '#8f8a9e', fontSize: 11, lineHeight: 1.55 }}>No structured owner knowledge is visible yet. As conversations produce useful facts, this area will show what the Agent recognized and let you verify it before it becomes trusted owner knowledge.</div>
      )}
    </section>
  )
}
