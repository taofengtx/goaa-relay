'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'

type Stage = 'estimate' | 'accepted' | 'paid' | 'processing' | 'delivered' | 'completed'
type OrderState = {
  stage: Stage
  amount: number
  serviceTitle: string
  scope: string
  agentMessages: string[]
  customerMessages: string[]
  settlement?: 'ready' | 'paid'
  updatedAt?: string
}

const KEY = 'goaa_order_demo_v1'
const initial: OrderState = {
  stage: 'estimate', amount: 600, serviceTitle: 'Life Protection Planning Service',
  scope: 'Professional analysis, plan explanation, and follow-up service per the confirmed scope.',
  agentMessages: [], customerMessages: [],
}
const steps: Array<[Stage,string]> = [
  ['estimate','Estimate'],['accepted','Accepted'],['paid','Paid'],['processing','In Progress'],['delivered','Delivered'],['completed','Confirmed']
]

export default function OrderWorkspacePage(){
  const router = useRouter()
  const [state,setState] = useState<OrderState>(initial)
  const [message,setMessage] = useState('')

  useEffect(()=>{
    if(!localStorage.getItem('agent_token')){ router.replace('/agent-login'); return }
    hydrate()
    const onStorage=(e:StorageEvent)=>{ if(e.key===KEY) hydrate() }
    window.addEventListener('storage',onStorage)
    return ()=>window.removeEventListener('storage',onStorage)
  },[router])

  function hydrate(){
    try{ const raw=localStorage.getItem(KEY); if(raw) setState({...initial,...JSON.parse(raw)}) }catch{}
  }
  function persist(next:OrderState){ const value={...next,updatedAt:new Date().toISOString()}; setState(value); localStorage.setItem(KEY,JSON.stringify(value)) }
  function patch(values:Partial<OrderState>){ persist({...state,...values}) }
  function sendMessage(){ const clean=message.trim(); if(!clean)return; patch({agentMessages:[...state.agentMessages,clean]}); setMessage('') }

  const index=steps.findIndex(([id])=>id===state.stage)
  const accepted=index>=1, paid=index>=2, processing=index>=3, delivered=index>=4, completed=index>=5
  const customerLatest=useMemo(()=>state.customerMessages.slice(-3).reverse(),[state.customerMessages])

  return <main style={{minHeight:'100vh',background:'#0d0b12',color:'#f7f5fb',fontFamily:'Inter,system-ui,sans-serif',padding:'28px 18px 70px'}}>
    <div style={{maxWidth:1180,margin:'0 auto'}}>
      <div style={{display:'flex',justifyContent:'space-between',gap:16,alignItems:'center',flexWrap:'wrap'}}>
        <div><div style={{color:'#9d7cff',fontSize:12,fontWeight:800}}>GOAA.ai · SERVICE ORDER</div><h1 style={{margin:'7px 0 0',fontSize:30}}>Service Order Workspace</h1></div>
        <div style={{display:'flex',gap:8}}><button style={secondary} onClick={()=>router.push('/agent-dashboard/service-orders')}>Back to Service Orders</button><button style={secondary} onClick={()=>{localStorage.removeItem(KEY);setState(initial)}}>Reset Demo</button></div>
      </div>

      <section style={{...card,marginTop:18,background:'linear-gradient(145deg,#211735,#15121d)'}}>
        <div style={{color:'#a993f3',fontSize:12,fontWeight:800}}>SERVICE ORDER #GOAA-DEMO-001</div>
        <h2 style={{margin:'9px 0 5px'}}>{state.serviceTitle}</h2>
        <div style={{color:'#9b94a4',fontSize:13}}>California · Customer contact hidden from Agents</div>
        <p style={{color:'#bbb4c6',lineHeight:1.65,marginBottom:0}}>CustCommunication is relayed Customer AI ↔ GOAA ↔ Agent AI. Quote, payment, progress, files, delivery, and settlement are all bound to this order.。</p>
      </section>

      <section style={card}><div style={{fontWeight:800}}>Order Tracking</div><div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(130px,1fr))',gap:8,marginTop:14}}>{steps.map(([id,label],i)=><div key={id} style={{padding:'11px 9px',borderRadius:10,border:'1px solid #302a39',textAlign:'center',fontSize:12,fontWeight:700,background:i<index?'#193523':i===index?'#2b2146':'#121018',color:i<index?'#86efac':i===index?'#cbb9ff':'#77717f'}}>{label}</div>)}</div></section>

      <div style={{display:'grid',gridTemplateColumns:'minmax(0,1.35fr) minmax(300px,.65fr)',gap:16,marginTop:16}}>
        <section style={card}>
          <div style={{display:'flex',justifyContent:'space-between',gap:18,flexWrap:'wrap'}}><div><h2 style={{margin:0}}>Service Estimate</h2><p style={{color:'#9993a4',fontSize:13}}>Agent sends an estimate first; formal fulfillment starts after the customer accepts and pays.</p></div><div style={{fontSize:30,fontWeight:850}}>${state.amount}</div></div>
          <label style={labelStyle}>Service Name<input disabled={accepted} value={state.serviceTitle} onChange={e=>patch({serviceTitle:e.target.value})} style={input}/></label>
          <label style={labelStyle}>Estimated Fee (USD)<input disabled={accepted} value={state.amount} onChange={e=>patch({amount:Number(e.target.value.replace(/[^0-9.]/g,''))||0})} style={input}/></label>
          <label style={labelStyle}>Scope<textarea disabled={accepted} value={state.scope} onChange={e=>patch({scope:e.target.value})} style={{...input,minHeight:100,resize:'vertical'}}/></label>
          {!accepted && <button style={primary} onClick={()=>patch({stage:'estimate'})}>Send to Customer AI</button>}
          {accepted && !paid && <Status text='Customer accepted the estimate. Awaiting Stripe payment.'/>}
          {paid && !processing && <button style={primary} onClick={()=>patch({stage:'processing'})}>Start Service</button>}
          {processing && !delivered && <button style={primary} onClick={()=>patch({stage:'delivered'})}>Submit Final Delivery</button>}
          {delivered && !completed && <Status text='Deliverables sent to the customer. Awaiting confirmation.'/>}
          {completed && <Status good text='Customer confirmed completion. This order meets Stripe Connect settlement conditions.'/>}
        </section>

        <aside style={{display:'grid',gap:16,alignContent:'start'}}>
          <section style={card}><h2 style={{margin:0,fontSize:18}}>Payment & Settlement</h2><div style={{display:'grid',gap:10,marginTop:14}}><Mini label='Customer Confirmation' value={accepted?'Accepted':'Awaiting Acceptance'}/><Mini label='Stripe Payment' value={paid?`$${state.amount} Paid`:'Not Paid'}/><Mini label='Agent Settlement' value={state.settlement==='paid'?'In Stripe Connect Payout':completed?'Settlement Ready':'Locked Until Completion'}/></div>{completed&&state.settlement!=='paid'&&<button style={{...primary,marginTop:14}} onClick={()=>patch({settlement:'paid'})}>Simulate Stripe Connect Settlement</button>}</section>
          <section style={card}><h2 style={{margin:0,fontSize:18}}>AI-Relayed Chat</h2><p style={{color:'#9993a4',fontSize:13,lineHeight:1.6}}>Phone and email are never shown. Messages sync to the customer&apos;s order window.</p><textarea value={message} onChange={e=>setMessage(e.target.value)} placeholder='e.g., please provide last year&apos;s tax return…' style={{...input,minHeight:78}}/><button style={{...primary,marginTop:9}} onClick={sendMessage}>Send to Customer AI</button>{customerLatest.length>0&&<div style={{marginTop:12}}><div style={{color:'#8f8999',fontSize:12}}>Recent Customer Replies</div>{customerLatest.map((m,i)=><div key={i} style={{marginTop:7,padding:9,borderRadius:9,background:'#121018',fontSize:12}}>{m}</div>)}</div>}</section>
        </aside>
      </div>
    </div>
  </main>
}

function Mini({label,value}:{label:string;value:string}){return <div style={{display:'flex',justifyContent:'space-between',gap:12,paddingBottom:9,borderBottom:'1px solid #292530',fontSize:13}}><span style={{color:'#8f8999'}}>{label}</span><span>{value}</span></div>}
function Status({text,good=false}:{text:string;good?:boolean}){return <div style={{marginTop:12,padding:12,borderRadius:10,background:good?'#193523':'#171321',color:good?'#86efac':'#cdbff7',fontSize:13}}>{text}</div>}
const card={background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:20} as const
const primary={border:0,borderRadius:10,background:'#7655df',color:'#fff',padding:'10px 14px',fontWeight:750,cursor:'pointer'} as const
const secondary={border:'1px solid #3b3545',borderRadius:10,background:'transparent',color:'#c7c0cf',padding:'9px 13px',cursor:'pointer'} as const
const input={width:'100%',boxSizing:'border-box' as const,border:'1px solid #393342',borderRadius:10,background:'#100e15',color:'#f7f5fb',padding:'11px 12px',outline:'none',marginTop:7} as const
const labelStyle={display:'block',color:'#aaa3b5',fontSize:12,fontWeight:700,marginTop:12} as const
