'use client'

import { useEffect, useMemo, useState } from 'react'

type Stage='need'|'connect_paid'|'matched'|'quoted'|'service_paid'|'processing'|'delivered'|'confirmed'|'settled'
type DemoState={stage:Stage;need:string;connectPaid:boolean;agentMatched:boolean;quote:number;serviceTitle:string;serviceDetails:string;servicePaid:boolean;delivered:boolean;confirmed:boolean;settled:boolean;invoiceGenerated:boolean}
const KEY='goaa_full_flow_demo_v2', CHANNEL='goaa-full-flow-demo-v2'
const initial:DemoState={stage:'need',need:'I want to plan life protection for my family and would like help reviewing suitable options.',connectPaid:false,agentMatched:false,quote:600,serviceTitle:'Family Protection Planning Consultation',serviceDetails:'Needs analysis\nPlan comparison\nApplication support\nOngoing service',servicePaid:false,delivered:false,confirmed:false,settled:false,invoiceGenerated:false}

export default function FullFlowDemo(){
 const [s,setS]=useState(initial)
 useEffect(()=>{try{const r=localStorage.getItem(KEY);if(r)setS(JSON.parse(r))}catch{}},[])
 useEffect(()=>{const bc=new BroadcastChannel(CHANNEL);bc.onmessage=e=>setS(e.data);return()=>bc.close()},[])
 function save(n:DemoState){setS(n);localStorage.setItem(KEY,JSON.stringify(n));try{const bc=new BroadcastChannel(CHANNEL);bc.postMessage(n);bc.close()}catch{}}
 function patch(p:Partial<DemoState>){save({...s,...p})}
 const reset=()=>save(initial)
 const step=useMemo(()=>({need:1,connect_paid:2,matched:3,quoted:4,service_paid:5,processing:6,delivered:7,confirmed:8,settled:9}[s.stage]),[s.stage])
 const status=step<=1?'Customer Describing Needs':step===2?'$39.9 Pass Purchased':step===3?'Professional Matched, Preparing Quote':step===4?'Customer Received Agent Quote':step===5?'Service Fee Paid':step===6?'Professional In Service':step===7?'Deliverables Delivered':step===8?'Customer Confirmed Complete':'Professional Received Settlement'
 return <main style={shell}><div style={wrap}>
  <header style={top}><div><div style={eyebrow}>GOAA · FULL FLOW DEMO V2</div><h1 style={h1}>Customer × Agent × Admin Three-Role Demo</h1><p style={muted}>Agent sets scope and price → Customer accepts and pays → service and delivery → Customer confirms → platform settles → Invoice.</p></div><button onClick={reset} style={ghost}>Reset Demo</button></header>
  <section style={statusCard}><b>Current Status: {status}</b><div style={bar}><div style={{...fill,width:`${Math.round(step/9*100)}%`}}/></div><div style={steps}>{['Request','$39.9 Pass','Match Agent','Agent Quote','Customer Pays','In Service','Deliver','Confirm','Settle'].map((x,i)=><span key={x} style={{opacity:i<step?1:.38}}>{i+1}. {x}</span>)}</div></section>
  <div style={grid}>
   <RoleCard title='Customer App' tag='CUSTOMER'>
    <label style={label}>My Request</label><textarea value={s.need} onChange={e=>patch({need:e.target.value})} style={area}/>
    {step===1&&<button style={primary} onClick={()=>patch({stage:'connect_paid',connectPaid:true})}>Confirm Request & Pay $39.9 Connection Fee</button>}
    {step>=2&&<Notice>✓ $39.9 one-time connection purchased · Valid 30 days</Notice>}
    {step===2&&<button style={primary} onClick={()=>patch({stage:'matched',agentMatched:true})}>Start Matching with a Professional</button>}
    {step>=3&&<Notice>✓ Matched with a professional: Licensed Professional Demo</Notice>}
    {step===4&&<><Estimate s={s}/><button style={primary} onClick={()=>patch({stage:'service_paid',servicePaid:true})}>Accept Quote & Pay ${s.quote}</button></>}
    {step>=5&&<Notice>✓ ${s.quote} paid · Service payment settles after the order completes</Notice>}
    {step===7&&<><Notice>📦 Delivery Package received: Plan Summary.pdf / Service Receipt.pdf</Notice><button style={primary} onClick={()=>patch({stage:'confirmed',confirmed:true})}>Confirm Service Complete</button></>}
    {step>=8&&<Notice>✓ Confirmed complete</Notice>}
    {s.invoiceGenerated&&<Invoice s={s}/>} 
   </RoleCard>
   <RoleCard title='Agent App' tag='AGENT'>
    {step<3&&<Empty>Waiting for the platform to push a matched order…</Empty>}
    {step>=3&&<Notice>New matched request: {s.need}</Notice>}
    {step===3&&<div style={formBox}><div style={eyebrow}>CREATE SERVICE ESTIMATE</div><label style={label2}>Service Name</label><input value={s.serviceTitle} onChange={e=>patch({serviceTitle:e.target.value})} style={input}/><label style={label2}>Service Description / Scope</label><textarea value={s.serviceDetails} onChange={e=>patch({serviceDetails:e.target.value})} style={{...area,minHeight:110}}/><label style={label2}>Professional Service Fee (USD)</label><div style={moneyRow}><span>$</span><input type='number' min='1' value={s.quote} onChange={e=>patch({quote:Math.max(0,Number(e.target.value)||0)})} style={moneyInput}/></div><div style={quick}>{[300,500,600,1000].map(v=><button key={v} onClick={()=>patch({quote:v})} style={chip}>${v}</button>)}</div><button disabled={!s.quote||!s.serviceTitle.trim()} style={primary} onClick={()=>patch({stage:'quoted'})}>Send Estimate to Customer</button></div>}
    {step>=4&&<Estimate s={s}/>} 
    {step===5&&<button style={primary} onClick={()=>patch({stage:'processing'})}>Start Service</button>}
    {step===6&&<><Notice>Service in progress: chatting, collecting information, and completing the professional work.</Notice><button style={primary} onClick={()=>patch({stage:'delivered',delivered:true})}>Upload & Submit Delivery Package</button></>}
    {step>=7&&<Notice>✓ Delivery Package submitted</Notice>}
    {step>=5&&!s.invoiceGenerated&&<button style={secondary} onClick={()=>patch({invoiceGenerated:true})}>Generate Customer Invoice</button>}
    {s.invoiceGenerated&&<Notice>🧾 Invoice generated and synced to the Customer order</Notice>}
    {step===8&&<Notice>Customer confirmed complete · Awaiting platform settlement</Notice>}
    {step===9&&<Notice>💰 Settlement complete: Agent received ${s.quote}</Notice>}
   </RoleCard>
   <RoleCard title='Admin App' tag='ADMIN'>
    <Metric label='Connection Fee' value={s.connectPaid?'$39.90 Paid':'Pending'}/><Metric label='Agent Match' value={s.agentMatched?'Matched':'Waiting'}/><Metric label='Agent Quote' value={step>=4?`$${s.quote}`:'Pending'}/><Metric label='Service Fee' value={s.servicePaid?`$${s.quote} Paid / Held`:'Pending'}/><Metric label='Invoice' value={s.invoiceGenerated?'Generated':'Not generated'}/><Metric label='Order Status' value={status}/><Metric label='Settlement Status' value={step<8?'Locked':step===8?'Ready':'Paid'}/>
    {step===8&&<button style={primary} onClick={()=>patch({stage:'settled',settled:true})}>Simulate Stripe Connect Settlement to Agent</button>}{step===9&&<Notice>✓ Settlement Paid · ${s.quote} → Agent</Notice>}
    <div style={adminNote}>$39.9 is the GOAA connection fee; the professional service price is set by the Agent. Service starts after the customer accepts and pays; settlement begins only after the customer confirms completion.</div>
   </RoleCard>
  </div>
  <section style={flowCard}><b>V2 Business Loop</b><div style={flow}>Customer request → $39.9 pass → Agent match → Agent sets scope and quote → Customer accepts/pays → Agent service → Delivery Package → Customer confirms → Platform settlement → Invoice archived/download</div><p style={muted}>This is still a frontend flow demo with no real charges. The Invoice demo confirms the business experience; the real Invoice/PDF and payment data will be connected later.</p></section>
 </div></main>
}
function RoleCard({title,tag,children}:{title:string;tag:string;children:React.ReactNode}){return <section style={card}><div style={eyebrow}>{tag}</div><h2 style={{margin:'8px 0 16px'}}>{title}</h2>{children}</section>}
function Notice({children}:{children:React.ReactNode}){return <div style={notice}>{children}</div>}
function Empty({children}:{children:React.ReactNode}){return <div style={empty}>{children}</div>}
function Estimate({s}:{s:DemoState}){return <div style={quote}><div style={eyebrow}>SERVICE ESTIMATE</div><h3 style={{margin:'8px 0 4px'}}>{s.serviceTitle}</h3><div style={{fontSize:32,fontWeight:900}}>${s.quote}</div><div style={{...muted,whiteSpace:'pre-line' as const,marginTop:8}}>{s.serviceDetails}</div></div>}
function Invoice({s}:{s:DemoState}){return <div style={invoice}><div style={invoiceTop}><div><div style={eyebrow}>GOAA SERVICE INVOICE</div><b>INV-DEMO-001</b></div><b style={{fontSize:22}}>${s.quote}</b></div><div style={muted}>{s.serviceTitle}</div><div style={{...muted,marginTop:6}}>Status: {s.servicePaid?'PAID':'OPEN'} · Order: GOAA-DEMO-001</div><button style={secondary} onClick={()=>alert('Demo: the production version downloads the Invoice PDF here')}>Download Invoice PDF</button></div>}
function Metric({label,value}:{label:string;value:string}){return <div style={metric}><span>{label}</span><b>{value}</b></div>}
const shell={minHeight:'100vh',background:'#0d0b12',color:'#f7f5fb',fontFamily:'Inter,Arial,sans-serif',padding:'34px 18px 70px'} as const,wrap={maxWidth:1380,margin:'0 auto'} as const,top={display:'flex',justifyContent:'space-between',gap:20,alignItems:'flex-start',flexWrap:'wrap' as const} as const,eyebrow={color:'#9d7cff',fontSize:12,fontWeight:850,letterSpacing:'.08em'} as const,h1={fontSize:34,margin:'8px 0'} as const,muted={color:'#9993a4',fontSize:13,lineHeight:1.65} as const,statusCard={background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:20,marginTop:20} as const,bar={height:8,background:'#24202b',borderRadius:99,overflow:'hidden',marginTop:12} as const,fill={height:'100%',background:'linear-gradient(90deg,#7655df,#9d7cff)',borderRadius:99,transition:'width .25s'} as const,steps={display:'grid',gridTemplateColumns:'repeat(9,1fr)',gap:8,fontSize:11,color:'#b7afc0',marginTop:10} as const,grid={display:'grid',gridTemplateColumns:'repeat(3,minmax(0,1fr))',gap:16,marginTop:18} as const,card={background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:20,minHeight:580} as const,label={display:'block',color:'#b4adbc',fontSize:12,fontWeight:700,marginBottom:7} as const,label2={...label,marginTop:12} as const,area={width:'100%',boxSizing:'border-box' as const,minHeight:120,border:'1px solid #393342',borderRadius:12,background:'#100e15',color:'#fff',padding:'12px',resize:'vertical' as const,outline:'none',lineHeight:1.55} as const,input={...area,minHeight:0,height:44,resize:'none' as const} as const,primary={marginTop:12,width:'100%',border:0,borderRadius:11,background:'#7655df',color:'#fff',padding:'12px 15px',fontWeight:850,cursor:'pointer'} as const,secondary={...primary,background:'#25202f',border:'1px solid #453965'} as const,ghost={border:'1px solid #393342',borderRadius:11,background:'#17151e',color:'#d8d1df',padding:'10px 14px',fontWeight:800,cursor:'pointer'} as const,notice={marginTop:12,padding:'12px 13px',border:'1px solid #3b3450',borderRadius:11,background:'#14111b',fontSize:13,lineHeight:1.55,color:'#ddd6e7'} as const,empty={marginTop:12,padding:'18px',border:'1px dashed #393342',borderRadius:11,color:'#7e7787',fontSize:13,textAlign:'center' as const} as const,quote={marginTop:12,padding:'16px',border:'1px solid #453965',borderRadius:14,background:'#13101a'} as const,formBox={...quote,padding:16} as const,moneyRow={display:'flex',alignItems:'center',gap:8,fontSize:24,fontWeight:900,background:'#100e15',border:'1px solid #393342',borderRadius:11,padding:'5px 12px'} as const,moneyInput={width:'100%',background:'transparent',border:0,outline:'none',color:'#fff',fontSize:24,fontWeight:900} as const,quick={display:'flex',gap:7,marginTop:8,flexWrap:'wrap' as const} as const,chip={border:'1px solid #393342',background:'#17151e',color:'#d8d1df',borderRadius:99,padding:'6px 10px',cursor:'pointer'} as const,metric={display:'flex',justifyContent:'space-between',gap:16,padding:'12px 0',borderBottom:'1px solid #2a2630',fontSize:13} as const,adminNote={marginTop:18,padding:'12px',borderRadius:11,background:'#111016',color:'#8f8797',fontSize:12,lineHeight:1.6} as const,flowCard={background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:20,marginTop:18} as const,flow={marginTop:10,padding:'14px',borderRadius:12,background:'#111016',fontSize:14,lineHeight:1.8,color:'#ddd6e7'} as const,invoice={marginTop:12,padding:16,border:'1px solid #4d4560',borderRadius:14,background:'#f6f3fa',color:'#17131d'} as const,invoiceTop={display:'flex',justifyContent:'space-between',gap:10,marginBottom:10} as const
