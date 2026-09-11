'use client'

import {useEffect,useMemo,useState} from 'react'
import {orderApi,type OrderRole} from '../lib/order-api'
import {deriveAgentEscalation} from '../lib/agent-escalation-policy'
import {executeApprovedAgentAction} from '../lib/agent-action-executor'
import {ensureActionProposal,transitionActionProposal,type AgentActionProposal} from '../lib/agent-action-proposals'
import {useOrderRuntime} from './OrderRuntimeBridge'

type Event={at:number}
function eventTime(raw:unknown):Event|null{if(!raw||typeof raw!=='object')return null;const r=raw as Record<string,unknown>;const at=Date.parse(String(r.createdAt||r.created_at||r.at||''));return Number.isFinite(at)?{at}:null}
function draftFor(role:'customer'|'agent',stage:string,pending:string[]){if(role==='customer')return 'Hi, I’m checking on the current status of this service order. Please share the next verified step or let me know if you need anything from me. Thank you.';if(stage==='estimate')return 'Hi, your professional service estimate is ready for review. Please review the scope and fee when convenient. There is no automatic acceptance, and no action will be taken without your decision.';if(stage==='accepted')return 'Hi, the service scope is accepted and the order is waiting for your payment decision. The professional service will not begin until payment is verified.';if(pending.length)return `Hi, to continue this Matter, please provide the following requested information when convenient: ${pending.join('; ')}. Please let me know if anything is unclear.`;if(stage==='delivered')return 'Hi, the deliverables are ready for your review. Please confirm completion only after you are satisfied the service is complete.';return 'Hi, I’m following up on this service order. Please review the current order status and let me know if you have any questions or need clarification.'}
export default function AgentAuthorizedFollowup({role}:{role:Extract<OrderRole,'customer'|'agent'>}){
 const runtime=useOrderRuntime(role,8000);const order=runtime.data?.order;const supplement=runtime.data?.supplement;const [events,setEvents]=useState<Event[]>([]);const [draft,setDraft]=useState('');const [busy,setBusy]=useState(false);const [notice,setNotice]=useState('');const [proposal,setProposal]=useState<AgentActionProposal|null>(null)
 useEffect(()=>{let cancelled=false;async function load(){if(!runtime.token||!runtime.orderId||runtime.orderId==='GOAA-DEMO-001')return;try{const raw=await orderApi.getTimeline(runtime.orderId,runtime.token);const list=(Array.isArray(raw)?raw:[]).map(eventTime).filter((x):x is Event=>Boolean(x));if(!cancelled)setEvents(list)}catch{}}void load();const t=window.setInterval(load,60000);return()=>{cancelled=true;window.clearInterval(t)}},[runtime.orderId,runtime.token])
 const pending=(supplement?.items||[]).filter(x=>x.required&&!['answered','complete','skipped'].includes(x.status)).map(x=>x.label).slice(0,6)
 const pendingSnapshot=JSON.stringify(pending)
 const advice=useMemo(()=>{if(!order)return null;const latest=events.reduce<number>((m,e)=>Math.max(m,e.at),0);const updated=order.updatedAt?Date.parse(order.updatedAt):0;const anchor=Math.max(latest,Number.isFinite(updated)?updated:0)||Date.now();return deriveAgentEscalation({order,supplement:supplement??null,inactiveHours:Math.max(0,(Date.now()-anchor)/36e5)})},[order,supplement,events])
 const actionable=Boolean(advice&&advice.level==='recommended'&&((role==='customer'&&advice.target==='professional')||(role==='agent'&&advice.target==='customer')))
 const orderId=order?.id
 const orderStage=order?.stage
 const adviceReason=advice?.reason
 const adviceTarget=advice?.target
 useEffect(()=>{if(orderId&&orderStage&&actionable){const pendingItems=JSON.parse(pendingSnapshot) as string[];const text=draftFor(role,orderStage,pendingItems);const scopeKey=[orderStage,adviceTarget||'none',pendingItems.join('|')].join(':');const next=ensureActionProposal({orderId,actionType:'send_message',authorizer:role==='customer'?'customer':'professional',scopeKey,title:'Send follow-up message',rationale:adviceReason||'Follow-up recommended by escalation policy.',willHappen:['One message will be sent through the canonical Order Engine message channel.'],willNotHappen:['No estimate acceptance','No payment or charge','No professional reassignment','No filing or document submission','No completion confirmation'],payloadPreview:{message:text,target:adviceTarget||'none'}});setProposal(next);setDraft(typeof next.payloadPreview.message==='string'?next.payloadPreview.message:text)}else{setDraft('');setProposal(null)}},[actionable,orderId,orderStage,role,pendingSnapshot,adviceReason,adviceTarget])
 if(!order||!actionable||!advice||!proposal)return null
 const activeProposal=proposal
 async function send(){
  const content=draft.trim(),token=runtime.token
  if(!content||busy||!token)return
  setBusy(true)
  setNotice('')
  try{
   let executing:AgentActionProposal|null=null
   try{
    const approved=transitionActionProposal(activeProposal.id,'approved',{payloadPreview:{...activeProposal.payloadPreview,message:content}})
    if(!approved||approved.status!=='approved'){setNotice('This proposal is no longer awaiting authorization. No action was taken.');return}
    setProposal(approved)
    executing=transitionActionProposal(activeProposal.id,'executing')
   }catch{
    setNotice('Could not save the local authorization state. No external action was taken.')
    return
   }
   if(!executing||executing.status!=='executing'){setNotice('Could not enter execution state. No external action was taken.');return}
   setProposal(executing)
   let receipt:Awaited<ReturnType<typeof executeApprovedAgentAction>>
   try{
    receipt=await executeApprovedAgentAction(executing,token)
   }catch(e){
    const message=(e instanceof Error?e.message:'Action could not be confirmed').slice(0,2000)
    let failureSaved=false
    try{
     const failed=transitionActionProposal(activeProposal.id,'failed',{failureMessage:message})
     if(failed)setProposal(failed)
     failureSaved=failed?.status==='failed'
    }catch{failureSaved=false}
    setNotice(`Could not confirm the approved follow-up. Check the canonical order messages before preparing a retry.${failureSaved?'':' The local failure record could not be saved.'}`)
    return
   }
   // A canonical receipt remains successful even if local storage or refresh fails.
   let receiptSaved=false
   try{
    const done=transitionActionProposal(activeProposal.id,'executed',{canonicalResultKind:receipt.kind,canonicalResultId:receipt.id})
    if(done)setProposal(done)
    receiptSaved=done?.status==='executed'&&done.canonicalResultKind===receipt.kind&&done.canonicalResultId===receipt.id
   }catch{receiptSaved=false}
   const successNotice=`Approved follow-up sent through the canonical order message channel. Receipt: ${receipt.id}${receiptSaved?'':' The local receipt could not be saved. Check the canonical order; do not resend.'}`
   setNotice(successNotice)
   setDraft('')
   try{await runtime.refresh()}catch{setNotice(`${successNotice} Order refresh is unavailable; the canonical receipt remains valid.`)}
  }finally{setBusy(false)}
 }
 return <section style={{maxWidth:1180,margin:'10px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><div style={{border:'1px solid rgba(96,165,250,.25)',borderRadius:16,padding:14,background:'#0e1726',color:'#eff6ff'}}><div style={{fontSize:10,fontWeight:850,letterSpacing:'.08em',color:'#93c5fd'}}>{role==='customer'?'AI BUTLER':'PROFESSIONAL AI ASSISTANT'} · AUTHORIZED ACTION</div><div style={{fontSize:13,fontWeight:850,marginTop:6}}>I prepared the follow-up. You decide whether it is sent.</div><div style={{marginTop:7,fontSize:9,color:'#93c5fd'}}>Proposal status: {activeProposal.status}</div><textarea value={draft} onChange={e=>setDraft(e.target.value)} style={{width:'100%',boxSizing:'border-box',marginTop:9,minHeight:88,borderRadius:10,border:'1px solid rgba(147,197,253,.2)',background:'#0b1220',color:'#dbeafe',padding:10,fontSize:11,lineHeight:1.5}}/><button type="button" disabled={busy||!draft.trim()||activeProposal.status!=='proposed'} onClick={send} style={{marginTop:9,border:0,borderRadius:10,background:'#2563eb',color:'#fff',padding:'8px 11px',fontSize:10,fontWeight:800,cursor:busy?'wait':'pointer',opacity:busy||!draft.trim()||activeProposal.status!=='proposed'?0.55:1}}>{busy?'Executing approved action…':activeProposal.status==='executed'?'Executed':activeProposal.status==='failed'?'Failed — prepare a new retry':'Approve & Send Follow-up'}</button>{notice&&<div style={{marginTop:7,fontSize:9,color:'#bfdbfe'}}>{notice}</div>}<div style={{marginTop:8,fontSize:9,lineHeight:1.45,color:'#7185a7'}}>Authorization is scoped to this proposal only. Immediately before execution, the Agent rechecks canonical order state. The bounded executor permits only actions explicitly allowed by the Agent capability contract; it cannot accept an estimate, charge a card, reassign a professional, file anything, or confirm completion.</div></div></section>
}
