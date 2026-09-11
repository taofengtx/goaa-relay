'use client'

import {GOLDEN_FLOW_INVARIANTS} from '../lib/golden-flow-boundary'

export default function AgentGoldenBoundaryStatus({role}:{role:'customer'|'agent'}){
 return <section style={{maxWidth:1180,margin:'10px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><details style={{border:'1px solid rgba(250,204,21,.14)',borderRadius:14,padding:'10px 12px',background:'#17150b',color:'#fef9c3'}}><summary style={{cursor:'pointer',fontSize:10,fontWeight:850,letterSpacing:'.06em'}}>GOLDEN FLOW PROTECTED · {role==='customer'?'AI BUTLER':'PROFESSIONAL AI ASSISTANT'} IS AN OVERLAY</summary><div style={{fontSize:9,lineHeight:1.55,color:'#c9bd80',marginTop:8}}>This Agent layer may prepare, explain, remind, and execute only explicitly whitelisted post-Golden actions. It does not replace the canonical consultation, 30-day access, matching, estimate, payment, service, delivery, or customer-confirmed completion journey.</div><div style={{display:'grid',gap:4,marginTop:7}}>{GOLDEN_FLOW_INVARIANTS.slice(1,7).map(text=><div key={text} style={{fontSize:8,color:'#a89f70'}}>• {text}</div>)}</div></details></section>
}
