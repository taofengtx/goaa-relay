'use client'

import {useEffect,useState} from 'react'
import {listActionProposals,type AgentActionProposal,type AgentAuthorizer} from '../lib/agent-action-proposals'
import {reconcileExecutedAgentAction,type ReconciliationResult} from '../lib/agent-action-reconciliation'
import {useOrderRuntime} from './OrderRuntimeBridge'

export default function AgentActionReconciliation({role}:{role:'customer'|'agent'}){
 const runtime=useOrderRuntime(role,12000)
 const orderId=runtime.data?.order?.id
 const authorizer:AgentAuthorizer=role==='customer'?'customer':'professional'
 const [proposal,setProposal]=useState<AgentActionProposal|null>(null)
 const [result,setResult]=useState<ReconciliationResult|null>(null)
 const [busy,setBusy]=useState(false)
 useEffect(()=>{if(!orderId){setProposal(null);return}const load=()=>setProposal(listActionProposals(orderId,authorizer).find(x=>x.status==='executed'&&Boolean(x.canonicalResultId))||null);load();window.addEventListener('goaa-agent-action-proposals-updated',load);return()=>window.removeEventListener('goaa-agent-action-proposals-updated',load)},[orderId,authorizer])
 useEffect(()=>{setResult(null)},[proposal?.id])
 if(!proposal)return null
 async function verify(){const currentProposal=proposal;const token=runtime.token;if(!currentProposal||!token||busy)return;setBusy(true);try{setResult(await reconcileExecutedAgentAction(currentProposal,token))}finally{setBusy(false)}}
 const state=result?.state||proposal.canonicalVerificationState||'unverified'
 const disabled=busy||!runtime.token
 return <section style={{maxWidth:1180,margin:'10px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><details style={{border:'1px solid rgba(34,211,238,.16)',borderRadius:16,padding:13,background:'#0a171c',color:'#cffafe'}}><summary style={{cursor:'pointer',fontSize:10,fontWeight:850,letterSpacing:'.07em',color:'#67e8f9'}}>AGENT ACTION · CANONICAL RECEIPT CHECK · {state.toUpperCase()}</summary><div style={{marginTop:9,fontSize:10,lineHeight:1.5,color:'#a5f3fc'}}>Local proposal: {proposal.title}</div><div style={{fontSize:9,color:'#5f8790',marginTop:4}}>Receipt: {proposal.canonicalResultKind} · {proposal.canonicalResultId}</div><button type="button" onClick={verify} disabled={disabled} style={{marginTop:9,border:'1px solid rgba(103,232,249,.22)',borderRadius:999,background:'rgba(6,182,212,.08)',color:'#a5f3fc',padding:'6px 9px',fontSize:9,fontWeight:800,opacity:disabled?0.55:1,cursor:disabled?'not-allowed':'pointer'}}>{busy?'Checking canonical record…':'Verify against Order Engine'}</button>{result&&<div style={{fontSize:9,lineHeight:1.45,color:result.state==='verified'?'#86efac':result.state==='not_found'?'#fca5a5':'#94a3b8',marginTop:7}}>{result.reason}</div>}<div style={{fontSize:9,lineHeight:1.45,color:'#526f76',marginTop:7}}>Verification is read-only. It never changes payment, matching, estimate, service, delivery, or completion state. Server-side proposal audit remains a separate future phase.</div></details></section>
}
