'use client'

import {useEffect,useMemo,useState} from 'react'
import {evaluateAgentActionReadiness} from '../lib/agent-action-readiness'
import {listActionProposals,type AgentActionProposal,type AgentAuthorizer} from '../lib/agent-action-proposals'
import {useOrderRuntime} from './OrderRuntimeBridge'

export default function AgentActionReadinessPanel({role}:{role:'customer'|'agent'}){
 const runtime=useOrderRuntime(role,9500)
 const authorizer:AgentAuthorizer=role==='customer'?'customer':'professional'
 const orderId=runtime.data?.order?.id
 const [proposal,setProposal]=useState<AgentActionProposal|null>(null)
 useEffect(()=>{if(!orderId){setProposal(null);return}const load=()=>setProposal(listActionProposals(orderId,authorizer).find(x=>['proposed','approved','executing'].includes(x.status))||null);load();const listener=()=>load();window.addEventListener('goaa-agent-action-proposals-updated',listener);const t=window.setInterval(load,5000);return()=>{window.removeEventListener('goaa-agent-action-proposals-updated',listener);window.clearInterval(t)}},[orderId,authorizer])
 const readiness=useMemo(()=>proposal?evaluateAgentActionReadiness(proposal,runtime.token):null,[proposal,runtime.token])
 if(!proposal||!readiness)return null
 return <section style={{maxWidth:1180,margin:'10px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><div style={{border:'1px solid rgba(59,130,246,.18)',borderRadius:16,padding:14,background:'#0c1524',color:'#eaf2ff'}}><div style={{display:'flex',justifyContent:'space-between',gap:10,flexWrap:'wrap'}}><div><div style={{fontSize:10,fontWeight:850,letterSpacing:'.08em',color:'#93c5fd'}}>{role==='customer'?'AI BUTLER':'PROFESSIONAL AI ASSISTANT'} · ACTION READINESS</div><div style={{fontSize:12,fontWeight:850,marginTop:5}}>{proposal.title}</div></div><span style={{fontSize:10,fontWeight:850,color:readiness.ready?'#86efac':'#fbbf24'}}>{readiness.ready?'READY':'NOT READY'}</span></div><div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(210px,1fr))',gap:6,marginTop:10}}>{readiness.checks.map(check=><div key={check.label} style={{fontSize:9,padding:'7px 8px',borderRadius:9,border:'1px solid rgba(148,163,184,.12)',color:check.pass?'#bbf7d0':'#fde68a',background:'rgba(255,255,255,.02)'}}>{check.pass?'✓':'○'} {check.label}</div>)}</div><div style={{fontSize:9,lineHeight:1.45,color:'#7f93b4',marginTop:8}}>{readiness.reason} Readiness never changes Golden Flow state by itself.</div></div></section>
}
