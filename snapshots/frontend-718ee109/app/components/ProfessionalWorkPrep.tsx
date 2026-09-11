'use client'

import { useOrderRuntime } from './OrderRuntimeBridge'

function clean(values?: string[]) { return Array.isArray(values) ? values.filter(Boolean).slice(0, 8) : [] }

export default function ProfessionalWorkPrep() {
  const runtime = useOrderRuntime('agent', 4000)
  const order = runtime.data?.order
  const handoff = order?.handoffContext || order?.handoff_context
  if (!order || !handoff) return null

  const missing = clean(handoff.missingInformation)
  const next = clean(handoff.agentNextSteps)
  const risks = clean(handoff.risks)
  const prep = [
    ...next.map(value => ({ label: 'Prepare', value })),
    ...missing.map(value => ({ label: 'Clarify', value })),
    ...risks.map(value => ({ label: 'Review', value })),
  ].slice(0, 10)

  if (!prep.length) return null
  return <section style={{maxWidth:1180,margin:'12px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}>
    <div style={{border:'1px solid rgba(167,139,250,.25)',borderRadius:18,padding:16,background:'#171326',color:'#f5f3ff'}}>
      <div style={{fontSize:11,fontWeight:850,letterSpacing:'.08em',color:'#c4b5fd'}}>PROFESSIONAL AI ASSISTANT · WORK PREP</div>
      <div style={{display:'flex',justifyContent:'space-between',gap:12,flexWrap:'wrap',marginTop:5}}><strong>Prepare the professional before taking action</strong><span style={{fontSize:11,color:'#a78bfa'}}>{prep.length} reviewed items</span></div>
      <div style={{display:'grid',gap:7,marginTop:10}}>{prep.map((item,index)=><div key={`${item.label}-${index}-${item.value}`} style={{display:'grid',gridTemplateColumns:'72px 1fr',gap:10,padding:'8px 10px',borderRadius:10,background:'rgba(255,255,255,.035)',fontSize:11,lineHeight:1.5}}><b style={{color:'#c4b5fd'}}>{item.label}</b><span style={{color:'#ddd6fe'}}>{item.value}</span></div>)}</div>
      <div style={{marginTop:10,fontSize:10,lineHeight:1.55,color:'#8f88a5'}}>Preparation only. The Professional AI Assistant may organize and surface work, but it does not silently send messages, quote fees, file documents, give regulated advice, or mark work complete.</div>
    </div>
  </section>
}
