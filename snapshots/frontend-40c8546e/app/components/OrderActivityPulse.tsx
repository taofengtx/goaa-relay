'use client'

import { useEffect,useState } from 'react'
import { orderApi,type OrderRole } from '../lib/order-api'
import { useOrderRuntime } from './OrderRuntimeBridge'

type NormalizedEvent={type:string;at:string}
function normalize(raw:unknown):NormalizedEvent|null{
 if(!raw||typeof raw!=='object')return null
 const r=raw as Record<string,unknown>
 const type=String(r.type||r.event_type||r.eventType||'').trim()
 const at=String(r.createdAt||r.created_at||r.at||'').trim()
 if(!type)return null
 return{type,at}
}
function label(value:string){return value.split('_').join(' ').replace(/\b\w/g,m=>m.toUpperCase())}

export default function OrderActivityPulse({role}:{role:Extract<OrderRole,'customer'|'agent'>}){
 const runtime=useOrderRuntime(role,6000)
 const [events,setEvents]=useState<NormalizedEvent[]>([])
 useEffect(()=>{
  let cancelled=false
  async function load(){
   if(!runtime.orderId||!runtime.token||runtime.orderId==='GOAA-DEMO-001')return
   try{
    const raw=await orderApi.getTimeline(runtime.orderId,runtime.token)
    const list=(Array.isArray(raw)?raw:[]).map(normalize).filter((x):x is NormalizedEvent=>Boolean(x)).slice(-6).reverse()
    if(!cancelled)setEvents(list)
   }catch{}
  }
  void load();const timer=window.setInterval(load,10000)
  return()=>{cancelled=true;window.clearInterval(timer)}
 },[runtime.orderId,runtime.token])
 if(!events.length)return null
 const latest=events[0]
 return <section style={{maxWidth:1180,margin:'10px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><div style={{border:'1px solid rgba(148,163,184,.16)',borderRadius:14,padding:'10px 12px',background:'#111318',color:'#e2e8f0',display:'flex',justifyContent:'space-between',gap:10,flexWrap:'wrap'}}><div><div style={{fontSize:9,fontWeight:850,letterSpacing:'.08em',color:'#94a3b8'}}>CANONICAL ORDER ACTIVITY · READ ONLY</div><div style={{fontSize:11,marginTop:4}}>Latest verified workflow event: <b>{label(latest.type)}</b></div></div><div style={{fontSize:9,color:'#64748b',alignSelf:'center'}}>{latest.at?new Date(latest.at).toLocaleString():'timestamp unavailable'}</div></div></section>
}
