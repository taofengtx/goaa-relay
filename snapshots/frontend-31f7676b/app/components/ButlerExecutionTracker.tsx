'use client'

import { useEffect } from 'react'
import { useOrderRuntime } from './OrderRuntimeBridge'
import { syncMatterExecution } from '../lib/personal-agent-execute-sync'

const stageCopy: Record<string,string> = {
  estimate: 'The professional is preparing or has sent the service scope and estimate.',
  accepted: 'You accepted the professional scope. I’m tracking payment and next actions.',
  paid: 'Professional service payment is confirmed. Execution can begin.',
  processing: 'The professional is actively working on this Matter.',
  waiting_customer: 'The professional needs information from you. I’ll keep the Matter open until it is supplied.',
  delivered: 'The professional delivered the work. I’m waiting for your confirmation before calling it complete.',
  completed: 'You confirmed completion. This Matter can now close.',
}

export default function ButlerExecutionTracker() {
  const runtime = useOrderRuntime('customer', 3000)
  const order = runtime.data?.order
  const supplement = runtime.data?.supplement
  useEffect(() => { if (order) syncMatterExecution(order) }, [order])
  if (!order) return null

  const pendingItems = (supplement?.items || []).filter(item => item.required && !['answered','complete','skipped'].includes(item.status)).map(item => item.label).slice(0, 6)
  const ownerActions: string[] = []
  if (order.stage === 'estimate' && order.estimate) ownerActions.push('Review the professional estimate and decide whether to accept it.')
  if (order.stage === 'accepted') ownerActions.push('Complete the professional service payment when you are ready to proceed.')
  if (pendingItems.length) ownerActions.push(`Provide the requested information: ${pendingItems.join('; ')}`)
  if (order.stage === 'delivered') ownerActions.push('Review the deliverables. Confirm completion only when you are satisfied the service is actually complete.')

  return <section style={{maxWidth:1180,margin:'18px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><div style={{border:'1px solid rgba(52,211,153,.24)',borderRadius:18,padding:16,background:'#0f1f1a',color:'#ecfdf5'}}><div style={{fontSize:11,fontWeight:850,letterSpacing:'.08em',color:'#6ee7b7'}}>YOUR AI BUTLER · EXECUTION TRACKING</div><div style={{display:'flex',justifyContent:'space-between',gap:12,flexWrap:'wrap',marginTop:5}}><strong style={{fontSize:16}}>I’m still following this Matter.</strong><span style={{fontSize:11,color:'#a7f3d0'}}>{order.stage}</span></div><p style={{margin:'7px 0 0',fontSize:12,lineHeight:1.6,color:'#a7b8b0'}}>{stageCopy[order.stage] || 'I’m tracking the service order and will keep this Matter open until there is a real completion signal.'}</p>{ownerActions.length>0&&<div style={{marginTop:10,padding:11,borderRadius:12,border:'1px solid rgba(167,243,208,.14)',background:'rgba(255,255,255,.025)'}}><div style={{fontSize:10,fontWeight:800,color:'#a7f3d0'}}>WHAT I NEED FROM YOU NOW</div><div style={{display:'grid',gap:5,marginTop:6}}>{ownerActions.map(action=><div key={action} style={{fontSize:11,lineHeight:1.5,color:'#d1fae5'}}>• {action}</div>)}</div></div>}<div style={{marginTop:9,fontSize:10,color:'#7f9d91'}}>I do not mark the Matter complete from payment, matching, or delivery alone. Completion requires the real customer-confirmed order state.</div></div></section>
}
