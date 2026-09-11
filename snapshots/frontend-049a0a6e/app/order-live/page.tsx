'use client'

import { useEffect, useState } from 'react'

const ORDER_KEY='goaa_active_order_id'
const CUSTOMER='goaa_order_customer_token'
const AGENT='goaa_order_agent_token'
const ADMIN='goaa_order_admin_token'

export default function OrderLiveCenter(){
 const [orderId,setOrderId]=useState('GOAA-DEMO-ORDER-001')
 const [customerToken,setCustomerToken]=useState('')
 const [agentToken,setAgentToken]=useState('')
 const [adminToken,setAdminToken]=useState('')
 const [saved,setSaved]=useState(false)
 useEffect(()=>{setOrderId(localStorage.getItem(ORDER_KEY)||'GOAA-DEMO-ORDER-001');setCustomerToken(localStorage.getItem(CUSTOMER)||'');setAgentToken(localStorage.getItem(AGENT)||'');setAdminToken(localStorage.getItem(ADMIN)||'')},[])
 function save(){localStorage.setItem(ORDER_KEY,orderId.trim()||'GOAA-DEMO-ORDER-001');localStorage.setItem(CUSTOMER,customerToken.trim());localStorage.setItem(AGENT,agentToken.trim());localStorage.setItem(ADMIN,adminToken.trim());setSaved(true);setTimeout(()=>setSaved(false),1600)}
 const id=encodeURIComponent(orderId.trim()||'GOAA-DEMO-ORDER-001')
 return <main style={shell}><div style={wrap}>
  <div style={eyebrow}>GOAA · PHASE 3 LIVE INTEGRATION</div><h1 style={h1}>Three-Role Live Integration Console</h1><p style={muted}>Use the same real service_order_id with test identities for all three roles, open Customer, Agent, and Admin windows, and verify live DO Order Engine / PostgreSQL integration.</p>
  <section style={card}><h2 style={{marginTop:0}}>Integration Setup</h2><label style={label}>Service Order ID<input value={orderId} onChange={e=>setOrderId(e.target.value)} style={input}/></label><div style={grid3}><label style={label}>Customer Token<textarea value={customerToken} onChange={e=>setCustomerToken(e.target.value)} style={area}/></label><label style={label}>Agent Token<textarea value={agentToken} onChange={e=>setAgentToken(e.target.value)} style={area}/></label><label style={label}>Admin Token<textarea value={adminToken} onChange={e=>setAdminToken(e.target.value)} style={area}/></label></div><button onClick={save} style={primary}>{saved?'✓ Saved':'Save Setup'}</button><p style={{...muted,marginBottom:0}}>Tokens are stored only in this browser&apos;s localStorage for testing. Never show real production credentials in screenshots, logs, or production pages.</p></section>
  <div style={grid3}>
   <Role title="Customer" desc="Accept estimate, supplements, chat, view/download delivery package, confirm completion." href={`/customer-order-live?order=${id}`}/>
   <Role title="Agent" desc="Start service, request supplements, chat, upload and submit Delivery Package, await customer confirmation." href={`/agent-order-live?order=${id}`}/>
   <Role title="Admin" desc="View orders, supplements, delivery packages, flags, and reassignment." href={`/admin-order-live?order=${id}`}/>
  </div>
  <section style={card}><h2 style={{marginTop:0}}>Official E2E Acceptance Sequence</h2><div style={{display:'grid',gap:10,color:'#d3ccd9',fontSize:13,lineHeight:1.65}}>{['Agent submits quote → Customer accepts','Mock/Test Payment completes → all three sync to Paid','Agent starts service → Admin sees Processing','Agent requests supplements → Customer fills/uploads → Agent & Admin see Complete','Agent creates Delivery Package V1 → uploads files → submits','Customer views and downloads deliverables → confirms completion','Admin sees Completed / Settlement Ready','Create Delivery Package V2; verify V1 history remains','Another Customer identity attempts file/ZIP access; must be rejected'].map((x,i)=><div key={x} style={step}><b>{i+1}.</b><span>{x}</span></div>)}</div></section>
 </div></main>
}
function Role({title,desc,href}:{title:string;desc:string;href:string}){return <section style={card}><div style={eyebrow}>{title}</div><h2 style={{margin:'8px 0'}}>{title} Live</h2><p style={{...muted,minHeight:64}}>{desc}</p><a href={href} target="_blank" rel="noreferrer" style={link}>Open {title} Window</a></section>}
const shell={minHeight:'100vh',background:'#0d0b12',color:'#f7f5fb',fontFamily:'Inter,Arial,sans-serif',padding:'34px 18px 70px'} as const
const wrap={maxWidth:1120,margin:'0 auto'} as const
const eyebrow={color:'#9d7cff',fontSize:12,fontWeight:850,letterSpacing:'.08em'} as const
const h1={fontSize:34,margin:'8px 0'} as const
const muted={color:'#9993a4',fontSize:13,lineHeight:1.65} as const
const card={background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:20,marginTop:18} as const
const grid3={display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(260px,1fr))',gap:14,marginTop:16} as const
const label={display:'block',color:'#b4adbc',fontSize:12,fontWeight:700} as const
const input={width:'100%',boxSizing:'border-box' as const,marginTop:7,border:'1px solid #393342',borderRadius:10,background:'#100e15',color:'#fff',padding:'11px 12px',outline:'none'} as const
const area={...input,minHeight:95,resize:'vertical' as const}
const primary={marginTop:16,border:0,borderRadius:10,background:'#7655df',color:'#fff',padding:'11px 15px',fontWeight:800,cursor:'pointer'} as const
const link={display:'inline-block',background:'#7655df',color:'#fff',textDecoration:'none',borderRadius:10,padding:'10px 14px',fontWeight:800,fontSize:13} as const
const step={display:'flex',gap:10,padding:'10px 12px',border:'1px solid #2e2935',borderRadius:10,background:'#121018'} as const
