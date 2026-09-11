'use client'

import { useEffect,useMemo,useRef,useState } from 'react'
import { RuntimeBadge,useOrderRuntime } from '../components/OrderRuntimeBridge'
import { runtimeActions } from '../lib/order-runtime'
import { orderApi } from '../lib/order-api'
import { CUSTOMER_READ_DEADLINE_MS,withReadDeadline } from '../lib/customer-read-recovery'

export default function CustomerOrderLivePage(){
 const runtime=useOrderRuntime('customer',2500)
 const order=runtime.data?.order
 const sup=runtime.data?.supplement
 const pkg=runtime.data?.deliveryPackage
 const [message,setMessage]=useState('')
 const [answers,setAnswers]=useState<Record<string,string>>({})
 const [busy,setBusy]=useState('')
 const [notice,setNotice]=useState('')
 const [confirmArmed,setConfirmArmed]=useState(false)
 const [loadSlow,setLoadSlow]=useState(false)
 const [checking,setChecking]=useState(false)
 const [checkError,setCheckError]=useState('')
 const checkingRef=useRef(false)
 const hasOrder=!!order
 useEffect(()=>{
   setLoadSlow(false)
   if(hasOrder)return
   const timer=window.setTimeout(()=>setLoadSlow(true),CUSTOMER_READ_DEADLINE_MS)
   return ()=>window.clearTimeout(timer)
 },[hasOrder,runtime.orderId,runtime.token])
 async function recheckOrder(){
   if(checkingRef.current)return
   checkingRef.current=true;setChecking(true);setCheckError('')
   try{await withReadDeadline(runtime.refresh())}
   catch{setCheckError('状态查询仍未完成，请返回 AI 管家并保留订单号。不要重复付款。')}
   finally{checkingRef.current=false;setChecking(false)}
 }
 // Golden Candidate Final UX — Stripe Checkout return context restore.
 // URL carries only non-sensitive navigation context (order id + payment
 // status + Stripe session id). No bearer token / payment secret / Stripe
 // secret ever appears in the URL. Identity comes from the authenticated
 // browser session; server-side order/payment state is refreshed by the
 // runtime poller (useOrderRuntime).
 useEffect(()=>{
   const sp=new URLSearchParams(window.location.search)
   const oid=sp.get('order')
   if(oid){localStorage.setItem('goaa_active_order_id',oid)}
   const pay=sp.get('payment')
   if(pay==='success'){
     setNotice('Checkout return received. Checking payment status with the server — a redirect alone does not confirm payment.')
     void runtime.refresh()
   } else if(pay==='cancelled'){
     setNotice('Payment cancelled. You can retry payment later.')
   }
   if(sp.get('payment')||sp.get('session_id')){
     sp.delete('payment');sp.delete('session_id')
     const qs=sp.toString()
     window.history.replaceState(null,'',window.location.pathname+(qs?`?${qs}`:''))
   }
   // eslint-disable-next-line react-hooks/exhaustive-deps
 },[runtime])
 const completed=sup?.items?.filter(x=>x.status==='answered'||x.status==='complete').length||0
 const total=sup?.items?.length||0
 const estimate=order?.estimate
 const preEstimate=order?.stage==='estimate'&&!estimate&&!(Number(order?.amount||0)>0)
 const postEstimate=order?.stage==='estimate'&&(estimate||Number(order?.amount||0)>0)
 const canConfirm=!!pkg&&['delivery_submitted','customer_review','documents_complete'].includes(order?.dbStage||'')
 const typeLabel=({text:'Text',date:'Date',amount:'Amount',choice:'Choice',image:'Image',pdf:'PDF File',file:'File'} as Record<string,string>)
 const fileStatusLabel=({answered:'Submitted',complete:'Submitted',skipped:'Skipped'} as Record<string,string>)
 const pkgStatusLabel=({draft:'Draft',submitted:'Delivered',superseded:'Updated'} as Record<string,string>)
 const fileCategoryLabel=({final:'Final Deliverables',receipt:'Government/Receipt',policy_contract:'Policy/Contract',tax:'Tax Documents',approval_notice:'Approval/Notice',report:'Service Report',other:'Other'} as Record<string,string>)
 const paidStage=['paid','processing','waiting_customer','delivered','completed'] as string[]
 const estAccepted=!!estimate&&estimate.status==='accepted'||paidStage.includes(order?.stage||'')
 const servicePaid=paidStage.includes(order?.stage||'')||order?.invoice?.status==='paid'
 const materialsDone=sup?.status==='complete'&&sup.items.length>0
 const delivered=pkg?.status==='submitted'
 const isCompleted=order?.stage==='completed'
 const progressSteps=[
  {label:'Request Submitted',done:!!order},
  {label:'Matched with a Professional',done:!!order?.matched},
  {label:'Estimate Accepted',done:estAccepted},
  {label:'Professional Service Fee Paid',done:servicePaid},
  {label:'Required Information Submitted',done:materialsDone},
  {label:'Deliverables Ready',done:delivered},
  {label:'Completed',done:isCompleted},
 ]
 const stageLabel=useMemo(()=>{
   if(order?.stage==='estimate')return preEstimate?'Waiting for Estimate':'Estimate Ready'
   if(order?.dbStage==='waiting_for_customer')return 'Additional Info Needed'
   if(order?.dbStage==='documents_complete')return 'Ready for Delivery'
   return ({estimate:'Awaiting Your Confirmation',accepted:'Accepted · Awaiting Payment',paid:'Paid',processing:'Service in Progress',waiting_customer:'Additional Info Needed',delivered:'Deliverables Ready',completed:'Completed'} as Record<string,string>)[order?.stage||'']||order?.stage||'—'
 },[order?.stage,preEstimate,order?.dbStage])
 async function run(name:string,fn:()=>Promise<unknown>){try{setBusy(name);setNotice('');await fn();await runtime.refresh()}catch(e){setNotice(e instanceof Error?e.message:'Action failed')}finally{setBusy('')}}
 async function accept(){await run('accept',async()=>{await runtimeActions.acceptEstimate(runtime.orderId,runtime.token);const session=await orderApi.createServiceCheckout(runtime.orderId,runtime.token);if(session?.checkoutUrl){window.location.href=session.checkoutUrl;return}setNotice('Estimate accepted. Redirecting to payment…')})}
 async function send(){const text=message.trim();if(!text)return;await run('message',()=>runtimeActions.sendMessage(runtime.orderId,'customer',text,runtime.token));setMessage('');setNotice('Message sent.')}
 async function answer(itemId:string){const text=(answers[itemId]||'').trim();if(!text)return;await run(`answer-${itemId}`,()=>runtimeActions.answerSupplement(runtime.orderId,itemId,text,runtime.token));setNotice('Information submitted.')}
 async function upload(itemId:string,file?:File){if(!file)return;await run(`file-${itemId}`,()=>runtimeActions.uploadSupplementFile(runtime.orderId,itemId,file,runtime.token));setNotice('File uploaded.')}
 async function confirm(){await run('confirm',async()=>{await runtimeActions.confirmCompletion(runtime.orderId,runtime.token)});setConfirmArmed(false);setNotice('Service completion confirmed.')}
 async function downloadZip(){if(!pkg)return;try{setBusy('zip');const url=orderApi.packageDownloadUrl(runtime.orderId,pkg.id);const r=await fetch(url,{headers:runtime.token?{Authorization:`Bearer ${runtime.token}`}:{}});if(!r.ok)throw new Error(`Download failed ${r.status}`);const blob=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`GOAA-${runtime.orderId}-Delivery-V${pkg.version}.zip`;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(a.href);setNotice('Deliverables download started.')}catch(e){setNotice(e instanceof Error?e.message:'Download failed')}finally{setBusy('')}}
 async function viewInvoice(){const inv=order?.invoice;if(!inv)return;try{setBusy('invoice');const r=await fetch(orderApi.invoicePdfUrl(runtime.orderId),{headers:runtime.token?{Authorization:`Bearer ${runtime.token}`}:{}});if(!r.ok)throw new Error(`Failed to load invoice ${r.status}`);const blob=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`${inv.invoiceNumber}.pdf`;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),30000);setNotice('Invoice opened.')}catch(e){setNotice(e instanceof Error?e.message:'Failed to load invoice')}finally{setBusy('')}}
 if(!order)return <main style={shell}><div style={wrap}>
   <h1>{runtime.error||loadSlow?'订单暂未加载 · Order not loaded':'正在查询订单 · Loading order…'}</h1>
   <p role="status" style={muted}>{runtime.error||loadSlow?'订单查询失败或等待时间较长。尚不能确认付款、匹配或服务进度，请勿重复下单或付款。':'正在向服务器查询订单；这不表示已付款或尚未付款。'}</p>
   <p style={muted}>Order #{runtime.orderId}</p>
   {checkError&&<p role="alert">{checkError}</p>}
   <button onClick={recheckOrder} disabled={checking} style={secondary}>{checking?'正在查询…':'重新查询状态 · Re-check status'}</button>
   <p><a href="/planning" style={{color:'#c7b6ff'}}>← 返回 AI 管家</a></p>
 </div></main>
 return <main style={shell}><div style={wrap}>
  {(runtime.error||checkError)&&<section role="alert" style={noticeStyle}>
   <p>刷新失败，下面可能是上次加载的订单信息。请重新查询，不要重复付款。</p>
   <button onClick={recheckOrder} disabled={checking} style={secondary}>{checking?'正在查询…':'重新查询状态 · Re-check status'}</button>
  </section>}
  <header style={row}>
   <div>
    <div style={eyebrow}>My Service Order</div>
    <h1 style={{fontSize:30,margin:'7px 0 3px'}}>{order?.serviceTitle||'Loading order…'}</h1>
    <div style={{display:'flex',alignItems:'center',gap:10,flexWrap:'wrap'}}>
     <span style={muted}>Professional Service Fee: <b style={{color:'#f7f5fb'}}>{preEstimate?'等待专业人士报价 · Awaiting estimate':`$${(Number(order?.amount||0)).toFixed(2)}`}</b></span>
     <span style={pill}>{stageLabel}</span>
    </div>
    <div style={{...muted,fontSize:11,marginTop:8}}>Order #{runtime.orderId}</div>
   </div>
   <RuntimeBadge mode={runtime.data?.mode} loading={runtime.loading} error={runtime.error}/>
  </header>
  {notice&&<div style={noticeStyle}>{notice}</div>}
  <section style={card}><h2 style={{marginTop:0}}>Service Progress</h2><div style={{display:'grid',gap:10}}>{progressSteps.map(s=><div key={s.label} style={progressRow}><span style={s.done?progressDone:progressPending}>{s.done?'✓':''}</span><b style={{color:s.done?'#e9e4f3':'#8a8494'}}>{s.label}</b></div>)}</div></section>
  {order?.connectPaid&&<section style={card}><div style={row}><div><h2 style={{margin:'0 0 5px'}}>30-Day Professional Connection Pass</h2><div style={{color:'#86efac',fontWeight:750}}>✓ Active</div></div></div><div style={{display:'grid',gap:8,marginTop:12}}><div style={fileRow}><span style={muted}>Pass Fee</span><b>$39.90 · One-time</b></div><div style={fileRow}><span style={muted}>Validity</span><b>30 Days · No Auto-Renewal</b></div></div><p style={{...muted,marginBottom:0}}>This is GOAA&apos;s professional connection pass — not a professional service fee.</p></section>}
  {preEstimate&&<section style={card}><div style={{display:'grid',gap:8}}><div style={{fontWeight:800}}>Current Status: Waiting for Estimate</div><div style={muted}>Your professional is reviewing your request. Once your estimate is ready, you can review it before accepting and paying.</div></div></section>}
  <section style={card}><h2 style={{marginTop:0}}>Message Your Professional</h2>{isCompleted&&<div style={{...muted,marginBottom:10}}>This service is complete. Your message history remains available.</div>}<div style={{display:'flex',gap:8,flexWrap:'wrap'}}><input value={message} onChange={e=>setMessage(e.target.value)} placeholder="Type a question or update…" style={{...input,flex:1,minWidth:260}}/><button disabled={!!busy} onClick={send} style={secondary}>{busy==='message'?'Sending…':'Send'}</button></div></section>
  <section style={card}><div style={row}><div><h2 style={{margin:'0 0 5px'}}>Required Information</h2><div style={muted}>Submit each item; your professional will see the full package at once.</div></div><span style={pill}>{sup?.status==='complete'?'All Required Information Received':`${completed}/${total}`}</span></div>{sup?.items?.length?<div style={{display:'grid',gap:10,marginTop:14}}>{sup.items.map(item=><div key={item.id} style={fileRow}><div style={{flex:1}}><b>{item.label}{item.required?' *':''}</b><div style={muted}>{typeLabel[item.type]||item.type} · {(item.status==='answered'||item.status==='complete')?'Submitted':'Pending'}</div>{['file','pdf','image'].includes(item.type)?<input type="file" onChange={e=>upload(item.id,e.target.files?.[0])} style={{marginTop:9}}/>:<div style={{display:'flex',gap:8,marginTop:9,flexWrap:'wrap'}}><input value={answers[item.id]||item.answer||''} onChange={e=>setAnswers(v=>({...v,[item.id]:e.target.value}))} style={{...input,flex:1,minWidth:220}}/><button disabled={!!busy} onClick={()=>answer(item.id)} style={secondary}>{busy===`answer-${item.id}`?'Submitting…':'Submit'}</button></div>}</div></div>)}</div>:<div style={{...muted,marginTop:12}}>No additional information is needed right now.</div>}</section>
  <section style={card}><div style={row}><div><h2 style={{margin:'0 0 5px'}}>Deliverables</h2><div style={muted}>{order?.serviceTitle||''} · Final Deliverables</div></div>{pkg&&<span style={pill}>Version V{pkg.version} · {pkgStatusLabel[pkg.status]||pkg.status}</span>}</div>{pkg?<><div style={{display:'grid',gap:8,marginTop:14}}>{pkg.files.map(f=><div key={f.id} style={fileRow}><div><b>{f.name}</b><div style={muted}>{fileCategoryLabel[f.category]||f.category} · V{f.version}{f.size?` · ${formatSize(f.size)}`:''}</div></div></div>)}</div>{pkg.note&&<div style={{...muted,marginTop:12}}>Delivery Notes: {pkg.note}</div>}<div style={{display:'flex',gap:9,marginTop:14,flexWrap:'wrap'}}><button disabled={!!busy} onClick={downloadZip} style={secondary}>{busy==='zip'?'Downloading…':'Download Deliverables'}</button>{canConfirm&&!confirmArmed&&<button disabled={!!busy} onClick={()=>setConfirmArmed(true)} style={primary}>Confirm Completion</button>}</div>{canConfirm&&<>{!confirmArmed?<div style={{...muted,marginTop:12}}>Confirming will complete this order.</div>:<div style={{display:'grid',gap:10,marginTop:16,border:'1px solid #4a4256',borderRadius:12,padding:16,background:'#121018'}}><div style={{fontWeight:850,fontSize:16}}>Confirm that this service is complete?</div><div style={muted}>Review your deliverables before confirming. GOAA will then complete the remaining order processing.</div><div style={{display:'flex',gap:9,flexWrap:'wrap'}}><button disabled={!!busy} onClick={()=>setConfirmArmed(false)} style={secondary}>Review Again</button><button disabled={!!busy} onClick={confirm} style={{...primary,marginTop:0}}>{busy==='confirm'?'Confirming…':'Confirm'}</button></div></div>}</>}</>:<div style={{...muted,marginTop:12}}>Your professional has not submitted the delivery package yet.</div>}</section>
  {order?.invoice&&<section style={card}><div style={row}><div><div style={eyebrow}>Service Invoice</div><h2 style={{margin:'8px 0'}}>Professional Service Fee</h2></div>{order.invoice.status==='paid'?<span style={{...pill,background:'#193523',color:'#86efac'}}>✓ Paid</span>:<span style={pill}>Pending</span>}</div><div style={{display:'grid',gap:8,marginTop:14}}><div style={fileRow}><span style={muted}>Invoice No.</span><b>{order.invoice.invoiceNumber}</b></div><div style={fileRow}><span style={muted}>Service</span><b>{order.invoice.serviceTitle}</b></div><div style={fileRow}><span style={muted}>Professional Service Fee</span><b style={{fontSize:18}}>${(order.invoice.amount||0).toFixed(2)}</b></div><div style={fileRow}><span style={muted}>Payment Status</span><b style={{color:order.invoice.status==='paid'?'#86efac':'#8a8494'}}>{order.invoice.status==='paid'?'✓ Paid':'Pending'}</b></div></div><button disabled={busy==='invoice'} onClick={viewInvoice} style={{...secondary,marginTop:14}}>{busy==='invoice'?'Loading…':'View Invoice'}</button></section>}
  {isCompleted&&<section style={card}><div style={{display:'grid',gap:8}}><div style={{color:'#86efac',fontWeight:850,fontSize:17}}>✓ Completed</div><div style={muted}>Your service is complete. Your deliverables and payment records remain available here.</div><div style={fileRow}><span style={muted}>Professional Service Fee</span><b>${((order?.invoice?.amount??order?.amount)||0).toFixed(2)} · Paid</b></div><div style={fileRow}><span style={muted}>Service Invoice</span><b>{order.invoice?'Generated':'Not Generated'}</b></div><div style={fileRow}><span style={muted}>Deliverables</span><b>{delivered?'Ready':'Not Delivered'}</b></div></div></section>}
 </div></main>
}
function formatSize(v:number){if(v<1024)return`${v} B`;if(v<1024*1024)return`${Math.round(v/1024)} KB`;return`${(v/1024/1024).toFixed(1)} MB`}
const shell={minHeight:'100vh',background:'#0d0b12',color:'#f7f5fb',fontFamily:'Inter,Arial,sans-serif',padding:'28px 18px 70px'} as const
const wrap={maxWidth:1080,margin:'0 auto'} as const
const row={display:'flex',justifyContent:'space-between',gap:16,alignItems:'center',flexWrap:'wrap' as const}
const h1={fontSize:30,margin:'7px 0'} as const
const eyebrow={color:'#9d7cff',fontSize:12,fontWeight:800,letterSpacing:'.08em'} as const
const muted={color:'#9993a4',fontSize:12,lineHeight:1.6} as const
const grid4={display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(190px,1fr))',gap:12,margin:'18px 0'} as const
const card={background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:20,marginTop:16} as const
const pill={padding:'6px 9px',borderRadius:20,background:'#211e28',color:'#cbb9ff',fontSize:11} as const
const fileRow={display:'flex',justifyContent:'space-between',gap:12,alignItems:'center',padding:12,border:'1px solid #302a39',borderRadius:10,background:'#121018'} as const
const progressRow={display:'flex',gap:10,alignItems:'center',padding:'9px 12px',border:'1px solid #262130',borderRadius:10,background:'#121018'} as const
const progressDone={display:'flex',alignItems:'center',justifyContent:'center',width:22,height:22,borderRadius:'50%',background:'#1c4a2c',color:'#86efac',fontSize:12,fontWeight:900} as const
const progressPending={display:'flex',alignItems:'center',justifyContent:'center',width:22,height:22,borderRadius:'50%',background:'#221f2b',color:'#3a3542',fontSize:12,fontWeight:900} as const
const input={boxSizing:'border-box' as const,border:'1px solid #393342',borderRadius:10,background:'#100e15',color:'#f7f5fb',padding:'10px 11px',outline:'none'} as const
const primary={border:0,borderRadius:10,background:'#7655df',color:'#fff',padding:'10px 14px',fontWeight:750,cursor:'pointer',marginTop:14} as const
const secondary={border:'1px solid #3b3545',borderRadius:10,background:'transparent',color:'#c7c0cf',padding:'9px 13px',cursor:'pointer'} as const
const noticeStyle={marginTop:16,padding:'12px 14px',border:'1px solid #493b68',borderRadius:12,background:'#181322',color:'#d7ccf7',fontSize:13} as const
