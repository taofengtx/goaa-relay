'use client'

import { useEffect,useMemo,useState } from 'react'
import { orderApi,type OrderRole } from '../lib/order-api'
import { useOrderRuntime } from './OrderRuntimeBridge'

type SeenEvent={type:string;at:number}
function normalize(raw:unknown):SeenEvent|null{
 if(!raw||typeof raw!=='object')return null
 const r=raw as Record<string,unknown>
 const type=String(r.type||r.event_type||r.eventType||'').trim()
 const rawAt=String(r.createdAt||r.created_at||r.at||'').trim()
 const at=Date.parse(rawAt)
 return type&&Number.isFinite(at)?{type,at}:null
}
function hoursSince(ms:number){return Math.max(0,(Date.now()-ms)/36e5)}

export default function OrderStallIntelligence({role}:{role:Extract<OrderRole,'customer'|'agent'>}){
 const runtime=useOrderRuntime(role,7000)
 const order=runtime.data?.order
 const supplement=runtime.data?.supplement
 const [events,setEvents]=useState<SeenEvent[]>([])
 useEffect(()=>{
  let cancelled=false
  async function load(){
   if(!runtime.token||!runtime.orderId||runtime.orderId==='GOAA-DEMO-001')return
   try{const raw=await orderApi.getTimeline(runtime.orderId,runtime.token);const list=(Array.isArray(raw)?raw:[]).map(normalize).filter((x):x is SeenEvent=>Boolean(x));if(!cancelled)setEvents(list)}catch{}
  }
  void load();const timer=window.setInterval(load,30000);return()=>{cancelled=true;window.clearInterval(timer)}
 },[runtime.orderId,runtime.token])
 const signal=useMemo(()=>{
  if(!order||order.stage==='completed')return null
  const latestEvent=events.reduce<SeenEvent|null>((best,e)=>!best||e.at>best.at?e:best,null)
  const orderAt=order.updatedAt?Date.parse(order.updatedAt):NaN
  const anchor=latestEvent?.at||(Number.isFinite(orderAt)?orderAt:Date.now())
  const age=hoursSince(anchor)
  const pending=(supplement?.items||[]).some(x=>x.required&&!['answered','complete','skipped'].includes(x.status))
  if(order.stage==='estimate'&&!order.estimate&&age>=48)return{level:'attention',title:'Estimate has been pending for a while',customer:'I’m watching for the professional estimate. No customer action is required yet.',professional:'This matched Matter has been waiting for an estimate. Consider reviewing and preparing the scope.',age}
  if(order.stage==='estimate'&&order.estimate&&age>=72)return{level:'attention',title:'Estimate decision has been pending',customer:'The estimate is still waiting for your decision. Review it when you are ready.',professional:'The estimate is awaiting the customer. Do not treat the delay as acceptance.',age}
  if(order.stage==='accepted'&&age>=48)return{level:'attention',title:'Accepted scope is waiting for payment',customer:'The professional service has not started because verified payment is still pending.',professional:'Wait for verified payment before starting paid execution.',age}
  if(pending&&age>=72)return{level:'attention',title:'Required information is still outstanding',customer:'The professional is waiting for requested information. Providing it can unblock the Matter.',professional:'Required customer information is still outstanding. Keep the order open and avoid duplicate requests.',age}
  if(order.stage==='paid'&&age>=24)return{level:'attention',title:'Paid order has not started processing',customer:'Payment is confirmed. I’m watching for the professional to begin execution.',professional:'Payment is confirmed and execution has not started. Review the accepted scope and start when appropriate.',age}
  if(order.stage==='processing'&&age>=120)return{level:'watch',title:'Execution has had no recent workflow activity',customer:'The professional service is still open. I’m watching for the next verified update.',professional:'There has been no recent canonical workflow event. Review whether an update, supplement request, or delivery is appropriate.',age}
  if(order.stage==='delivered'&&age>=72)return{level:'watch',title:'Delivery is awaiting customer confirmation',customer:'Your deliverables are ready. Review them before confirming completion.',professional:'Delivery is waiting on the customer. Do not close the order on their behalf.',age}
  return null
 },[order,supplement,events])
 if(!signal)return null
 const copy=role==='customer'?signal.customer:signal.professional
 return <section style={{maxWidth:1180,margin:'10px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><div style={{border:'1px solid rgba(251,146,60,.23)',borderRadius:16,padding:14,background:'#21140e',color:'#fff7ed'}}><div style={{fontSize:10,fontWeight:850,letterSpacing:'.08em',color:'#fdba74'}}>{role==='customer'?'AI BUTLER':'PROFESSIONAL AI ASSISTANT'} · DELAY WATCH</div><div style={{fontSize:13,fontWeight:800,marginTop:6}}>{signal.title}</div><div style={{fontSize:11,lineHeight:1.55,color:'#fed7aa',marginTop:5}}>{copy}</div><div style={{fontSize:9,color:'#a8876b',marginTop:7}}>Attention signal based on canonical order inactivity (~{Math.floor(signal.age)}h), not a contractual SLA or proof of fault.</div></div></section>
}
