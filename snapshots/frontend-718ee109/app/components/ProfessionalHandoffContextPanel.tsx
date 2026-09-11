'use client'

import { useOrderRuntime } from './OrderRuntimeBridge'

function items(value?: string[]) { return Array.isArray(value) ? value.filter(Boolean).slice(0, 8) : [] }

export default function ProfessionalHandoffContextPanel() {
  const runtime = useOrderRuntime('agent', 3500)
  const handoff = runtime.data?.order.handoffContext || runtime.data?.order.handoff_context
  if (!handoff) return null
  const risks = items(handoff.risks)
  const missing = items(handoff.missingInformation)
  const next = items(handoff.agentNextSteps)
  return (
    <section style={{maxWidth:1180,margin:'18px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}>
      <div style={{border:'1px solid rgba(96,165,250,.28)',borderRadius:18,padding:18,background:'#111827',color:'#f8fafc'}}>
        <div style={{display:'flex',justifyContent:'space-between',gap:16,flexWrap:'wrap'}}>
          <div><div style={{fontSize:11,fontWeight:850,letterSpacing:'.08em',color:'#93c5fd'}}>PROFESSIONAL AI ASSISTANT · CUSTOMER-REVIEWED CONTEXT</div><h2 style={{fontSize:18,margin:'6px 0 4px'}}>{handoff.title}</h2><div style={{fontSize:12,color:'#94a3b8'}}>{handoff.category || 'Professional service'}{handoff.urgency ? ` · ${handoff.urgency} priority` : ''}</div></div>
          <div style={{fontSize:11,color:'#93c5fd'}}>Matter {handoff.matterId}</div>
        </div>
        {handoff.summary && <p style={{fontSize:13,lineHeight:1.65,color:'#cbd5e1',margin:'12px 0 0'}}>{handoff.summary}</p>}
        <div style={{display:'flex',gap:8,flexWrap:'wrap',marginTop:10}}>{handoff.organization&&<span style={pill}>Organization: {handoff.organization}</span>}{handoff.dueDate&&<span style={pill}>Due: {handoff.dueDate}</span>}{handoff.amount&&<span style={pill}>Amount: {handoff.amount}</span>}</div>
        {(risks.length>0||missing.length>0||next.length>0)&&<div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(210px,1fr))',gap:10,marginTop:12}}>
          {risks.length>0&&<List title="Customer-side risks" values={risks}/>} {missing.length>0&&<List title="Still missing" values={missing}/>} {next.length>0&&<List title="Butler-prepared next steps" values={next}/>} 
        </div>}
        <div style={{marginTop:12,paddingTop:10,borderTop:'1px solid rgba(255,255,255,.08)',fontSize:11,lineHeight:1.55,color:'#94a3b8'}}>Boundary: this is customer-reviewed context from the Customer AI Butler. It is not your professional advice, recommendation, authorization, or completion signal. The Professional AI Assistant represents you, the licensed professional.</div>
      </div>
    </section>
  )
}
function List({title,values}:{title:string;values:string[]}){return <div style={{padding:10,border:'1px solid rgba(255,255,255,.08)',borderRadius:12,background:'rgba(255,255,255,.025)'}}><div style={{fontSize:10,fontWeight:800,color:'#bfdbfe',marginBottom:5}}>{title}</div>{values.map(v=><div key={v} style={{fontSize:11,lineHeight:1.5,color:'#cbd5e1'}}>• {v}</div>)}</div>}
const pill={fontSize:10,padding:'5px 8px',borderRadius:999,border:'1px solid rgba(147,197,253,.22)',color:'#bfdbfe'} as const
