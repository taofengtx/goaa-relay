'use client'

import { useEffect, useMemo, useState } from 'react'
import { useOrderRuntime } from './OrderRuntimeBridge'
import {executeApprovedAgentAction} from '../lib/agent-action-executor'
import {ensureActionProposal,transitionActionProposal,type AgentActionProposal} from '../lib/agent-action-proposals'

function clean(values?: string[]) { return Array.isArray(values) ? values.filter((v): v is string => typeof v === 'string' && Boolean(v.trim())).slice(0, 8) : [] }
function text(value: unknown) { return typeof value === 'string' ? value.trim() : '' }

export default function ProfessionalAssistantActionDrafts() {
  const runtime = useOrderRuntime('agent', 4500)
  const order = runtime.data?.order
  const orderId = order?.id || ''
  const handoff = order?.handoffContext || order?.handoff_context
  const missing = clean(handoff?.missingInformation)
  const missingSnapshot = JSON.stringify(missing)
  const risks = clean(handoff?.risks)
  const next = clean(handoff?.agentNextSteps)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [requestProposal,setRequestProposal]=useState<AgentActionProposal|null>(null)
  const scopeDraft = useMemo(() => {if (!handoff) return '';return [text(handoff.summary),handoff.organization ? `Organization: ${handoff.organization}` : '',handoff.dueDate ? `Target date: ${handoff.dueDate}` : '',next.length ? `Planned work: ${next.join('; ')}` : '',risks.length ? `Items requiring professional review: ${risks.join('; ')}` : ''].filter(Boolean).join('\n')}, [handoff, next, risks])
  const customerMessageDraft = useMemo(() => {const missingItems=JSON.parse(missingSnapshot) as string[];return !missingItems.length ? '' : `To move this Matter forward, please provide or confirm the following:\n${missingItems.map((item, index) => `${index + 1}. ${item}`).join('\n')}\n\nOnce received, I can continue the professional review.`}, [missingSnapshot])
  const hasSupplement = Boolean(runtime.data?.supplement)
  useEffect(()=>{const missingItems=JSON.parse(missingSnapshot) as string[];if(!orderId||!missingItems.length||hasSupplement){setRequestProposal(null);return}const scopeKey=`missing:${missingItems.join('|')}`;setRequestProposal(ensureActionProposal({orderId,actionType:'request_information',authorizer:'professional',scopeKey,title:'Request missing information',rationale:'Customer-reviewed Matter context identifies information needed before professional work can continue.',willHappen:['One canonical supplement request will be created with the listed required items.'],willNotHappen:['No customer answer will be invented','No message will be silently sent outside the Order Engine','No estimate or fee will change','No filing will occur','No order will be marked complete'],payloadPreview:{items:missingItems.map(label=>({label,type:'text',required:true}))}}))},[orderId,missingSnapshot,hasSupplement])
  if (!order || !handoff) return null
  async function copy(value: string, label: string) {if (!value || typeof navigator === 'undefined' || !navigator.clipboard) return;await navigator.clipboard.writeText(value);setNotice(`${label} copied. Review it before using it.`)}
  async function requestMissingInformation() {
    const proposal=requestProposal,token=runtime.token
    if (!orderId || !missing.length || hasSupplement || !token || !proposal || busy || proposal.status!=='proposed') return
    setBusy(true)
    setNotice('')
    try {
      let executing:AgentActionProposal|null=null
      try{
        const approved=transitionActionProposal(proposal.id,'approved')
        if(!approved||approved.status!=='approved'){setNotice('This proposal is no longer awaiting authorization. No request was created.');return}
        setRequestProposal(approved)
        executing=transitionActionProposal(proposal.id,'executing')
      }catch{
        setNotice('Could not save the local authorization state. No request was created.')
        return
      }
      if(!executing||executing.status!=='executing'){setNotice('Could not enter execution state. No request was created.');return}
      setRequestProposal(executing)
      let receipt:Awaited<ReturnType<typeof executeApprovedAgentAction>>
      try{
        receipt=await executeApprovedAgentAction(executing,token)
      }catch(e){
        const message=(e instanceof Error?e.message:'Action could not be confirmed').slice(0,2000)
        let failureSaved=false
        try{
          const failed=transitionActionProposal(proposal.id,'failed',{failureMessage:message})
          if(failed)setRequestProposal(failed)
          failureSaved=failed?.status==='failed'
        }catch{failureSaved=false}
        setNotice(`Could not confirm the approved information request. Check the canonical supplement before preparing a retry.${failureSaved?'':' The local failure record could not be saved.'}`)
        return
      }
      // A canonical receipt remains successful even if local storage or refresh fails.
      let receiptSaved=false
      try{
        const done=transitionActionProposal(proposal.id,'executed',{canonicalResultKind:receipt.kind,canonicalResultId:receipt.id})
        if(done)setRequestProposal(done)
        receiptSaved=done?.status==='executed'&&done.canonicalResultKind===receipt.kind&&done.canonicalResultId===receipt.id
      }catch{receiptSaved=false}
      const successNotice=`Approved information request created through the canonical supplement workflow. Receipt: ${receipt.id}${receiptSaved?'':' The local receipt could not be saved. Check the canonical supplement; do not resend.'}`
      setNotice(successNotice)
      try{await runtime.refresh()}catch{setNotice(`${successNotice} Order refresh is unavailable; the canonical receipt remains valid.`)}
    }finally { setBusy(false) }
  }
  return <section style={{maxWidth:1180,margin:'12px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><div style={{border:'1px solid rgba(34,197,94,.22)',borderRadius:18,padding:16,background:'#101a14',color:'#ecfdf5'}}><div style={{fontSize:11,fontWeight:850,letterSpacing:'.08em',color:'#86efac'}}>PROFESSIONAL AI ASSISTANT · ACTION DRAFTS</div><div style={{display:'flex',justifyContent:'space-between',gap:12,flexWrap:'wrap',marginTop:5}}><strong>Do the preparation first. You approve the action.</strong><span style={{fontSize:10,color:'#86efac'}}>No silent sending · No invented fee</span></div><div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(260px,1fr))',gap:10,marginTop:12}}><Draft title="Service scope draft" body={scopeDraft || 'No reviewed scope is available yet.'} action={scopeDraft ? () => copy(scopeDraft, 'Scope draft') : undefined} actionLabel="Copy scope draft" /><Draft title="Customer clarification draft" body={customerMessageDraft || 'No missing information was identified in the reviewed Matter.'} action={customerMessageDraft ? () => copy(customerMessageDraft, 'Customer message draft') : undefined} actionLabel="Copy message draft" /></div>{missing.length>0&&<div style={{marginTop:10,padding:12,border:'1px solid rgba(134,239,172,.16)',borderRadius:12,background:'rgba(255,255,255,.025)'}}><div style={{fontSize:11,fontWeight:800,color:'#bbf7d0'}}>Suggested information request</div><div style={{fontSize:11,lineHeight:1.55,color:'#bbcfbf',marginTop:5}}>{missing.join(' · ')}</div>{requestProposal&&<div style={{fontSize:9,color:'#86efac',marginTop:6}}>Proposal status: {requestProposal.status}</div>}<button type="button" disabled={busy||hasSupplement||!requestProposal||requestProposal.status!=='proposed'} onClick={requestMissingInformation} style={{...button,opacity:(busy||hasSupplement||!requestProposal||requestProposal.status!=='proposed')?0.55:1,cursor:(busy||hasSupplement||!requestProposal||requestProposal.status!=='proposed')?'not-allowed':'pointer'}}>{hasSupplement?'An information request already exists':busy?'Executing approved request…':requestProposal?.status==='failed'?'Failed — prepare a new retry':'Approve & request these items'}</button></div>}{notice&&<div style={{marginTop:9,fontSize:10,color:'#a7f3d0'}}>{notice}</div>}<div style={{marginTop:10,fontSize:10,lineHeight:1.55,color:'#799080'}}>The assistant may prepare drafts and organize missing information. Immediately before execution, the bounded executor rechecks the canonical order and supplement state, and can run only capabilities explicitly allowed by the Agent action contract. High-risk actions remain in their canonical user workflows.</div></div></section>
}
function Draft({title,body,action,actionLabel}:{title:string;body:string;action?:()=>void;actionLabel:string}) {return <div style={{padding:12,border:'1px solid rgba(255,255,255,.08)',borderRadius:12,background:'rgba(255,255,255,.025)'}}><div style={{fontSize:11,fontWeight:800,color:'#bbf7d0'}}>{title}</div><pre style={{whiteSpace:'pre-wrap',fontFamily:'inherit',fontSize:10,lineHeight:1.55,color:'#c7d8ca',margin:'7px 0 0'}}>{body}</pre>{action&&<button type="button" onClick={action} style={button}>{actionLabel}</button>}</div>}
const button={marginTop:10,border:'1px solid rgba(134,239,172,.28)',borderRadius:999,background:'rgba(34,197,94,.10)',color:'#bbf7d0',padding:'6px 10px',fontSize:10,fontWeight:750} as const
