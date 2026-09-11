'use client'

import {useEffect,useMemo,useState} from 'react'
import {orderApi,type OrderRole} from '../lib/order-api'
import {deriveAgentEscalation} from '../lib/agent-escalation-policy'
import {useOrderRuntime} from './OrderRuntimeBridge'

type Event={at:number}
function eventTime(raw:unknown):Event|null{if(!raw||typeof raw!=='object')return null;const r=raw as Record<string,unknown>;const at=Date.parse(String(r.createdAt||r.created_at||r.at||''));return Number.isFinite(at)?{at}:null}
export default function AgentEscalationAdvisor({role}:{role:Extract<OrderRole,'customer'|'agent'>}){
 const runtime=useOrderRuntime(role,8000);const order=runtime.data?.order;const supplement=runtime.data?.supplement;const [events,setEvents]=useState<Event[]>([])
 useEffect(()=>{let cancelled=false;async function load(){if(!runtime.token||!runtime.orderId||runtime.orderId==='GOAA-DEMO-001')return;try{const raw=await orderApi.getTimeline(runtime.orderId,runtime.token);const list=(Array.isArray(raw)?raw:[]).map(eventTime).filter((x):x is Event=>Boolean(x));if(!cancelled)setEvents(list)}catch{}}void load();const t=window.setInterval(load,60000);return()=>{cancelled=true;window.clearInterval(t)}},[runtime.orderId,runtime.token])
 const advice=useMemo(()=>{if(!order)return null;const latest=events.reduce<number>((m,e)=>Math.max(m,e.at),0);const updated=order.updatedAt?Date.parse(order.updatedAt):0;const anchor=Math.max(latest,Number.isFinite(updated)?updated:0)||Date.now();return deriveAgentEscalation({order,supplement:supplement??null,inactiveHours:Math.max(0,(Date.now()-anchor)/36e5)})},[order,supplement,events])
 if(!advice||advice.level!=='recommended')return null
 const copy=role==='customer'?advice.customerCopy:advice.professionalCopy
 return <section style={{maxWidth:1180,margin:'10px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><div style={{border:'1px solid rgba(244,63,94,.25)',borderRadius:16,padding:14,background:'#211015',color:'#fff1f2'}}><div style={{fontSize:10,fontWeight:850,letterSpacing:'.08em',color:'#fda4af'}}>{role==='customer'?'AI BUTLER':'PROFESSIONAL AI ASSISTANT'} · ESCALATION ADVISOR</div><div style={{fontSize:13,fontWeight:850,marginTop:6}}>{advice.title}</div><div style={{fontSize:11,lineHeight:1.55,color:'#fecdd3',marginTop:5}}>{copy}</div><div style={{display:'flex',gap:7,flexWrap:'wrap',marginTop:8,fontSize:9,color:'#fda4af'}}><span style={pill}>Recommended target: {advice.target}</span><span style={pill}>Automatic external action: OFF</span></div><div style={{fontSize:9,lineHeight:1.45,color:'#a9898f',marginTop:7}}>Guardrail: {advice.safeAction}</div></div></section>
}
const pill={border:'1px solid rgba(253,164,175,.18)',borderRadius:999,padding:'4px 7px'} as const
