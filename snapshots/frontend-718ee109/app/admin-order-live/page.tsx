'use client'

import { useMemo, useState } from 'react'
import { RuntimeBadge, useOrderRuntime } from '../components/OrderRuntimeBridge'
import { runtimeActions } from '../lib/order-runtime'

type Action='flag'|'unflag'|'reassign'

export default function AdminOrderLivePage(){
 const runtime=useOrderRuntime('admin',2500)
 const [reason,setReason]=useState('')
 const [busy,setBusy]=useState<Action|''>('')
 const [notice,setNotice]=useState('')
 const order=runtime.data?.order
 const sup=runtime.data?.supplement
 const pkg=runtime.data?.deliveryPackage
 const completed=sup?.items?.filter(x=>x.status==='answered'||x.status==='complete').length||0
 const total=sup?.items?.length||0
 const stageLabel=useMemo(()=>({estimate:'Awaiting Customer Acceptance',accepted:'Awaiting Payment',paid:'Paid',processing:'Service in Progress',waiting_customer:'Waiting for Customer Info',delivered:'Awaiting Customer Confirmation',completed:'Completed'} as Record<string,string>)[order?.stage||'']||order?.stage||'—',[order?.stage])
 async function act(action:Action){try{setBusy(action);setNotice('');await runtimeActions.adminAction(runtime.orderId,action,reason.trim()||'Admin order management',runtime.token);await runtime.refresh();setNotice(action==='reassign'?'Reassignment request submitted.':action==='flag'?'Order flagged for review.':'Flag cleared.')}catch(e){setNotice(e instanceof Error?e.message:'Action failed')}finally{setBusy('')}}
 return <main style={shell}><div style={wrap}>
  <header style={row}><div><div style={eyebrow}>GOAA ADMIN · LIVE ORDER</div><h1 style={h1}>Order Console</h1><div style={muted}>Order #{runtime.orderId}</div></div><RuntimeBadge mode={runtime.data?.mode} loading={runtime.loading} error={runtime.error}/></header>
  {notice&&<div style={noticeStyle}>{notice}</div>}
  <div style={grid4}><Metric label="Order Amount" value={`$${order?.amount??'—'}`}/><Metric label="Order Status" value={stageLabel}/><Metric label="Information Progress" value={`${completed}/${total}`}/><Metric label="Settlement Status" value={order?.settlement==='paid'?'Settled':order?.settlement==='ready'?'Settlement Ready':'Locked'}/></div>
  <section style={card}><div style={row}><div><div style={eyebrow}>Order Details</div><h2 style={{margin:'8px 0'}}>{order?.serviceTitle||'Loading order…'}</h2></div><span style={pill}>{stageLabel}</span></div><div style={details}><Info label="Source" value={runtime.data?.mode==='api'?'Order Engine':'Preview'}/><Info label="Last Updated" value={order?.updatedAt?new Date(order.updatedAt).toLocaleString('en-US'):'—'}/><Info label="Delivery Package" value={pkg?`V${pkg.version} · ${pkg.files.length} files`:'Not Submitted'}/><Info label="Information Status" value={sup?.status||'No additional information requested'}/></div></section>
  <section style={card}><h2 style={{marginTop:0}}>Platform Admin Actions</h2><p style={muted}>In production these actions run through the Admin API and are written to the audit log — order states are never edited directly.</p><textarea value={reason} onChange={e=>setReason(e.target.value)} placeholder="Reason (e.g., customer requested a new Agent / Agent did not respond)" style={{...input,minHeight:86,resize:'vertical'}}/><div style={actions}><button disabled={!!busy} onClick={()=>act('flag')} style={secondary}>{busy==='flag'?'Processing…':'Flag Issue'}</button><button disabled={!!busy} onClick={()=>act('unflag')} style={secondary}>{busy==='unflag'?'Processing…':'Clear Flag'}</button><button disabled={!!busy} onClick={()=>act('reassign')} style={primary}>{busy==='reassign'?'Processing…':'Reassign Agent'}</button></div></section>
  <section style={card}><h2 style={{marginTop:0}}>Delivery Package</h2>{pkg?<><div style={details}><Info label="Version" value={`V${pkg.version}`}/><Info label="Status" value={pkg.status}/><Info label="Files" value={String(pkg.files.length)}/><Info label="Submitted" value={pkg.submittedAt?new Date(pkg.submittedAt).toLocaleString('en-US'):'—'}/></div><div style={{display:'grid',gap:8,marginTop:14}}>{pkg.files.map(f=><div key={f.id} style={fileRow}><div><b>{f.name}</b><div style={muted}>{f.category} · V{f.version}</div></div><span style={pill}>{f.mimeType||'file'}</span></div>)}</div></>:<div style={muted}>No delivery package yet.</div>}</section>
  {order?.invoice&&<section style={card}><h2 style={{marginTop:0}}>Service Invoice</h2><div style={details}><Info label="Invoice Number" value={order.invoice.invoiceNumber}/><Info label="Payment Status" value={order.invoice.status==='paid'?'Paid':'Pending'}/><Info label="Professional Service Fee" value={`$${(order.invoice.amount||0).toFixed(2)}`}/><Info label="Service" value={order.invoice.serviceTitle}/></div></section>}
  <section style={card}><h2 style={{marginTop:0}}>Required Information</h2>{sup?.items?.length?<div style={{display:'grid',gap:8}}>{sup.items.map(x=><div key={x.id} style={fileRow}><div><b>{x.label}</b><div style={muted}>{x.type} · {x.required?'Required':'Optional'}</div></div><span style={{...pill,color:(x.status==='answered'||x.status==='complete')?'#86efac':'#cbb9ff'}}>{(x.status==='answered'||x.status==='complete')?'Completed':'Pending'}</span></div>)}</div>:<div style={muted}>No additional information requested.</div>}</section>
 </div></main>
}
function Metric({label,value}:{label:string;value:string}){return <div style={card}><div style={muted}>{label}</div><div style={{fontSize:22,fontWeight:850,marginTop:8}}>{value}</div></div>}
function Info({label,value}:{label:string;value:string}){return <div style={{display:'flex',justifyContent:'space-between',gap:12,padding:'10px 0',borderBottom:'1px solid #292530'}}><span style={muted}>{label}</span><b style={{fontSize:13}}>{value}</b></div>}
const shell={minHeight:'100vh',background:'#0d0b12',color:'#f7f5fb',fontFamily:'Inter,Arial,sans-serif',padding:'28px 18px 70px'} as const
const wrap={maxWidth:1100,margin:'0 auto'} as const
const row={display:'flex',justifyContent:'space-between',gap:16,alignItems:'center',flexWrap:'wrap' as const}
const h1={fontSize:30,margin:'7px 0'} as const
const eyebrow={color:'#9d7cff',fontSize:12,fontWeight:800,letterSpacing:'.08em'} as const
const muted={color:'#9993a4',fontSize:12,lineHeight:1.6} as const
const grid4={display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(190px,1fr))',gap:12,margin:'18px 0'} as const
const card={background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:20} as const
const details={display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))',columnGap:22,marginTop:12} as const
const pill={padding:'6px 9px',borderRadius:20,background:'#211e28',color:'#cbb9ff',fontSize:11} as const
const fileRow={display:'flex',justifyContent:'space-between',gap:12,alignItems:'center',padding:12,border:'1px solid #302a39',borderRadius:10,background:'#121018'} as const
const input={width:'100%',boxSizing:'border-box' as const,border:'1px solid #393342',borderRadius:10,background:'#100e15',color:'#f7f5fb',padding:'11px 12px',outline:'none'} as const
const actions={display:'flex',gap:10,flexWrap:'wrap' as const,marginTop:12}
const primary={border:0,borderRadius:10,background:'#7655df',color:'#fff',padding:'10px 14px',fontWeight:750,cursor:'pointer'} as const
const secondary={border:'1px solid #3b3545',borderRadius:10,background:'transparent',color:'#c7c0cf',padding:'9px 13px',cursor:'pointer'} as const
const noticeStyle={marginTop:16,padding:'12px 14px',border:'1px solid #493b68',borderRadius:12,background:'#181322',color:'#d7ccf7',fontSize:13} as const
