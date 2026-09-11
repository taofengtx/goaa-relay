'use client'

import {useEffect,useState} from 'react'
import {auditAgentLayerContract} from '../lib/agent-layer-contract-audit'
import {explainAgentActionDecision} from '../lib/agent-action-explainability'
import {checkProposalIntegrity} from '../lib/agent-action-integrity'
import {listActionProposals,type AgentActionProposal,type AgentAuthorizer} from '../lib/agent-action-proposals'
import {useOrderRuntime} from './OrderRuntimeBridge'

export default function AgentActionDecisionReceipt({role}:{role:'customer'|'agent'}){
 const runtime=useOrderRuntime(role,11000)
 const orderId=runtime.data?.order?.id
 const [proposal,setProposal]=useState<AgentActionProposal|null>(null)
 useEffect(()=>{if(!orderId)return;const authorizer:AgentAuthorizer=role==='customer'?'customer':'professional';const load=()=>setProposal(listActionProposals(orderId,authorizer)[0]||null);load();const listener=()=>load();window.addEventListener('goaa-agent-action-proposals-updated',listener);const t=window.setInterval(load,5000);return()=>{window.removeEventListener('goaa-agent-action-proposals-updated',listener);window.clearInterval(t)}},[orderId,role])
 if(!proposal)return null
 const x=explainAgentActionDecision(proposal);const audit=auditAgentLayerContract();const integrity=checkProposalIntegrity(proposal);const healthy=audit.pass&&integrity.pass
 return <section style={{maxWidth:1180,margin:'10px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><details style={{border:'1px solid rgba(125,211,252,.16)',borderRadius:16,padding:13,background:'#0c1720',color:'#e0f2fe'}}><summary style={{cursor:'pointer',fontSize:10,fontWeight:850,letterSpacing:'.07em',color:healthy?'#7dd3fc':'#fca5a5'}}>AGENT ACTION · DECISION RECEIPT · {healthy?'SAFETY CONTRACT HEALTHY':'LOCAL SAFETY CHECK FAILED'}</summary><div style={{marginTop:10,display:'grid',gap:8}}><div><strong style={{fontSize:12}}>{x.headline}</strong><div style={muted}>{x.why}</div></div><div style={grid}><Fact label="Controlled by" value={x.controlledBy}/><Fact label="Canonical path" value={x.canonicalPath}/><Fact label="Lifecycle" value={x.lifecycle}/><Fact label="Next" value={x.nextStep}/></div><div style={{...muted,color:'#67e8f9'}}>Golden boundary: {x.goldenBoundary}</div>{!healthy&&<div style={{...box,borderColor:'rgba(248,113,113,.22)'}}><div style={{...labelStyle,color:'#fca5a5'}}>Execution blocked by local safety checks</div><div style={{...valueStyle,color:'#fecaca'}}>{[...audit.checks,...integrity.checks].filter(c=>!c.pass).map(c=>c.label).join(' · ')}</div></div>}<div style={grid}><Box title="If approved, this may happen" items={x.willHappen}/><Box title="This authorization does NOT include" items={x.willNotHappen}/></div><div style={{fontSize:9,lineHeight:1.45,color:'#57727f'}}>This receipt explains the frontend proposal decision. It is a local transparency record, not a substitute for canonical Order Engine business truth or a server-side audit ledger.</div></div></details></section>
}
function Fact({label,value}:{label:string;value:string}){return <div style={box}><div style={labelStyle}>{label}</div><div style={valueStyle}>{value}</div></div>}
function Box({title,items}:{title:string;items:string[]}){return <div style={box}><div style={labelStyle}>{title}</div>{items.length?<div style={{...valueStyle,display:'grid',gap:3}}>{items.map((v,i)=><span key={`${v}-${i}`}>• {v}</span>)}</div>:<div style={valueStyle}>None recorded.</div>}</div>}
const grid={display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(230px,1fr))',gap:7} as const
const box={border:'1px solid rgba(125,211,252,.10)',borderRadius:10,padding:9,background:'rgba(255,255,255,.02)'} as const
const labelStyle={fontSize:9,fontWeight:800,color:'#7dd3fc'} as const
const valueStyle={fontSize:9,lineHeight:1.5,color:'#bae6fd',marginTop:3} as const
const muted={fontSize:9,lineHeight:1.5,color:'#7c9aaa',marginTop:3} as const
