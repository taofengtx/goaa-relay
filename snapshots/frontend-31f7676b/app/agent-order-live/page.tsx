'use client'

import { ChangeEvent, useEffect, useState } from 'react'
import { RuntimeBadge, useOrderRuntime } from '../components/OrderRuntimeBridge'
import { runtimeActions } from '../lib/order-runtime'
import { orderApi } from '../lib/order-api'
import type { DeliveryCategory, SupplementType } from '../lib/order-api'

const categories:Array<[DeliveryCategory,string]>=[['final','Final Files'],['receipt','Government/Receipt'],['policy_contract','Policy/Contract'],['tax','Tax Documents'],['approval_notice','Approval/Notice'],['report','Service Report'],['other','Other']]

export default function AgentOrderLivePage(){
 const runtime=useOrderRuntime('agent',2500)
 const order=runtime.data?.order
 const orderId=runtime.orderId
 const token=runtime.token

 // Agent Auth Bridge: no agent token for this order → save the return target
 // and go through the formal Agent Login, then come back to the SAME order
 // (never bounce to the Agent homepage).
 useEffect(()=>{
   if (typeof window==='undefined') return
   if (token) return
   if (!orderId || orderId==='GOAA-DEMO-001') return
   const target=`/agent-order-live?order=${encodeURIComponent(orderId)}`
   try{window.localStorage.setItem('goaa_agent_return_v1',target)}catch{}
   window.location.replace(`/agent-login?resume=1&reason=order&order=${encodeURIComponent(orderId)}`)
 },[token,orderId])

 const supplement=runtime.data?.supplement
 const delivery=runtime.data?.deliveryPackage
 const [message,setMessage]=useState('')
 const [label,setLabel]=useState('')
 const [type,setType]=useState<SupplementType>('text')
 const [draftItems,setDraftItems]=useState<Array<{label:string;type:SupplementType;required:boolean}>>([])
 const [note,setNote]=useState('')
 const [category,setCategory]=useState<DeliveryCategory>('final')
 const [busy,setBusy]=useState('')
 const [packageId,setPackageId]=useState('')
 const [serviceTitle,setServiceTitle]=useState('')
 const [scopeText,setScopeText]=useState('')
 const [amountInput,setAmountInput]=useState('')
 const [estMsg,setEstMsg]=useState('')
 async function run(name:string,fn:()=>Promise<unknown>){try{setBusy(name);await fn();await runtime.refresh()}finally{setBusy('')}}
 async function startService(){await run('start',()=>runtimeActions.startService(runtime.orderId,runtime.token))}
 async function send(){const clean=message.trim();if(!clean)return;setMessage('');await run('message',()=>runtimeActions.sendMessage(runtime.orderId,'agent',clean,runtime.token))}
 function addItem(){const clean=label.trim();if(!clean)return;setDraftItems(v=>[...v,{label:clean,type,required:true}]);setLabel('')}
 async function submitSupplement(){if(!draftItems.length)return;await run('supplement',async()=>{await runtimeActions.createSupplement(runtime.orderId,draftItems,runtime.token);setDraftItems([])})}
 async function ensurePackage(){if(packageId)return packageId;if(delivery?.id){setPackageId(delivery.id);return delivery.id}const pkg=await runtimeActions.createDeliveryPackage(runtime.orderId,note.trim(),runtime.token);setPackageId(pkg.id);return pkg.id}
 async function upload(e:ChangeEvent<HTMLInputElement>){const files=Array.from(e.target.files||[]);e.target.value='';if(!files.length)return;await run('upload',async()=>{const id=await ensurePackage();for(const file of files)await runtimeActions.uploadDeliveryFile(runtime.orderId,id,file,category,runtime.token)})}
 async function submitDelivery(){await run('delivery',async()=>{const id=await ensurePackage();await runtimeActions.submitDeliveryPackage(runtime.orderId,id,runtime.token)})}
 const estimate=order?.estimate
 const preEstimate=order?.stage==='estimate'&&!estimate&&!(Number(order?.amount||0)>0)
 const postEstimate=order?.stage==='estimate'&&(estimate||Number(order?.amount||0)>0)
 async function sendEstimate(){
   const svc=serviceTitle.trim()||order?.serviceTitle?.trim()||''
   const sc=scopeText.trim()
   const amt=Number(amountInput)
   if(!svc){setEstMsg('Please enter a service name');return}
   if(!sc){setEstMsg('Please enter the service scope');return}
   if(!Number.isFinite(amt)||amt<=0){setEstMsg('Professional service fee must be greater than 0 (USD)');return}
   try{
     setBusy('estimate');setEstMsg('')
     await orderApi.createEstimate(runtime.orderId,{serviceTitle:svc,amount:amt,scope:sc},runtime.token)
     await runtime.refresh()
     setEstMsg('Estimate sent. Awaiting customer confirmation.')
   }catch(e){setEstMsg(e instanceof Error?e.message:'Failed to send estimate')}finally{setBusy('')}
 }
 const stage=order?.stage||'estimate';const canStart=stage==='paid';const canWork=['processing','waiting_customer'].includes(stage);const files=delivery?.files||[]
 const stageLabel=({estimate:'Awaiting Customer Confirmation',accepted:'Estimate Accepted',paid:'Payment Received',processing:'Service in Progress',waiting_customer:'Waiting for Customer Information',delivered:'Awaiting Customer Confirmation',completed:'Completed'} as Record<string,string>)[stage]||stage||'—'
 const settleLabel=order?.settlement==='paid'?'Settled':order?.settlement==='ready'?'Awaiting Settlement':'Not Started'
 const invoiceLabel=order?.invoice?'Generated':'Not Generated'
 const paymentLabel=(order?.invoice?.status==='paid'||stage==='completed')?`$${((order?.invoice?.amount??order?.amount)||0).toFixed(2)} · Paid`:`$${Number(order?.amount||0).toFixed(2)} · Awaiting Payment`
 const suppStatusLabel=({draft:'Draft',collecting:'Collecting',complete:'Complete'} as Record<string,string>)
 const itemStatusLabel=({draft:'Pending',answered:'Submitted',complete:'Submitted',skipped:'Skipped'} as Record<string,string>)
 const typeLabel=({text:'Text',date:'Date',amount:'Amount',choice:'Choice',image:'Image',pdf:'PDF File',file:'File'} as Record<string,string>)
 const pkgStatusLabel=({draft:'Draft',submitted:'Submitted',superseded:'Updated'} as Record<string,string>)
 const fileCategoryLabel=({final:'Final Files',receipt:'Government/Receipt',policy_contract:'Policy/Contract',tax:'Tax Documents',approval_notice:'Approval/Notice',report:'Service Report',other:'Other'} as Record<string,string>)
 const dbStage=order?.dbStage||''
 const supplementComplete=!!supplement&&supplement.status==='complete'
 const supplementBlocked=!!supplement&&supplement.status!=='complete'
 const requiredDone=!!supplement&&supplement.items.length>0&&supplement.items.every(x=>!x.required||x.status==='answered'||x.status==='complete'||x.status==='skipped')
 const canCompleteSupplement=!!supplement&&order?.stage==='waiting_customer'&&supplementComplete&&requiredDone
 const docsComplete=dbStage==='documents_complete'
 const canSubmitDelivery=files.length>0&&delivery?.status!=='submitted'&&(!supplement||(supplementComplete&&(dbStage==='in_progress'||dbStage==='documents_complete')))
 async function completeSupplement(){await run('complete-supp',async()=>{await runtimeActions.completeSupplements(runtime.orderId,runtime.token)})}

 if(!token){return <main style={shell}><div style={wrap}><div style={eyebrow}>GOAA AGENT · AUTH BRIDGE</div><h1 style={h1}>Signing in to Agent…</h1><div style={muted}>You will return to Service Order #{orderId} after signing in.</div></div></main>}

 return <main style={shell}><div style={wrap}><header style={row}><div><div style={eyebrow}>GOAA AGENT</div><h1 style={h1}>Service Order Workspace</h1><div style={muted}>Order #{runtime.orderId}</div></div><RuntimeBadge mode={runtime.data?.mode} loading={runtime.loading} error={runtime.error}/></header>
 <section style={card}><div style={row}><div><h2 style={h2}>{order?.serviceTitle||'Loading order…'}</h2><div style={{display:'flex',gap:8,flexWrap:'wrap',marginTop:8}}>{stage==='completed'&&<span style={okPill}>✓ Completed</span>}{stage==='completed'&&<span style={okPill}>✓ Customer Confirmed</span>}{order?.settlement==='paid'&&<span style={okPill}>✓ Settled</span>}</div></div><div style={{fontSize:28,fontWeight:850}}>${Number(order?.amount||0).toFixed(2)}</div></div>{canStart&&<button disabled={busy==='start'} onClick={startService} style={primary}>{busy==='start'?'Processing…':'Start Service'}</button>}{stage==='completed'&&<div style={success}>{order?.settlement==='paid'?'✓ Customer confirmed completion — service settled.':'✓ Customer confirmed completion — awaiting settlement.'}</div>}</section>
 {order?.stage==='estimate'&&<section style={card}><h2 style={h2}>Service Estimate</h2>{preEstimate?<div style={{display:'grid',gap:10}}><input value={serviceTitle||order?.serviceTitle||''} onChange={e=>setServiceTitle(e.target.value)} placeholder="Service name" style={input}/><textarea value={scopeText} onChange={e=>setScopeText(e.target.value)} placeholder="Describe the service scope..." style={{...input,minHeight:96}}/><input type="number" min="0.01" step="0.01" value={amountInput} onChange={e=>setAmountInput(e.target.value)} placeholder="Professional service fee (USD, must be greater than 0)" style={input}/><button disabled={busy==='estimate'} onClick={sendEstimate} style={primary}>{busy==='estimate'?'Sending…':'Send Estimate to Customer'}</button>{estMsg&&<div style={estMsg.startsWith('Estimate sent')?success:error}>{estMsg}</div>}<p style={{...muted,marginBottom:0}}>This fee is your professional service quote and is completely separate from the $39.90 GOAA connection pass.</p></div>:<div style={{display:'grid',gap:8}}>{order?.estimate&&<><div style={item}><b>{order.estimate.serviceTitle||order.serviceTitle}</b><span style={{fontWeight:800,fontSize:18}}>${order.amount||0}</span></div>{order.estimate.scope&&<div style={muted}>{order.estimate.scope}</div>}</>}<div style={success}>✓ Estimate sent. Awaiting customer confirmation.</div></div>}</section>}
 <div style={grid}><div style={{display:'grid',gap:16}}><section style={card}><h2 style={h2}>Information Collection</h2>{supplement?<><div style={muted}>{supplement.status==='complete'?'Required Information Received':'Status: '+(suppStatusLabel[supplement.status]||supplement.status)} · {supplement.items.filter(x=>x.status==='complete'||x.status==='answered').length}/{supplement.items.length}</div><div style={{display:'grid',gap:8,marginTop:12}}>{supplement.items.map(x=><div key={x.id} style={item}><b>{x.label}</b><span style={muted}>{typeLabel[x.type]||x.type} · {itemStatusLabel[x.status]||x.status}</span></div>)}</div>{canCompleteSupplement&&<div style={{display:'grid',gap:10,marginTop:14,padding:14,border:'1px solid #4a4256',borderRadius:12,background:'#121018'}}><div style={{color:'#86efac',fontWeight:800}}>✓ All required information received</div><div style={muted}>All requested information has been submitted. Once confirmed, you can move to final delivery.</div><button disabled={busy==='complete-supp'} onClick={completeSupplement} style={primary}>{busy==='complete-supp'?'Confirming…':'Confirm Information Complete'}</button></div>}{docsComplete&&<div style={success}>✓ Required information received</div>}</>:<><div style={{display:'grid',gridTemplateColumns:'1fr 140px auto',gap:8,marginTop:12}}><input value={label} onChange={e=>setLabel(e.target.value)} placeholder="e.g., last year's Tax Return" style={input}/><select value={type} onChange={e=>setType(e.target.value as SupplementType)} style={input}>{['text','date','amount','choice','image','pdf','file'].map(v=><option key={v} value={v}>{typeLabel[v]||v}</option>)}</select><button onClick={addItem} style={secondary}>+ Add</button></div><div style={{display:'grid',gap:7,marginTop:10}}>{draftItems.map((x,i)=><div key={i} style={item}><span>{x.label}</span><span style={muted}>{typeLabel[x.type]||x.type}</span></div>)}</div>{draftItems.length>0&&<button disabled={busy==='supplement'} onClick={submitSupplement} style={{...primary,marginTop:12}}>{busy==='supplement'?'Submitting…':'Request Information from Customer'}</button>}</>}</section>
 {canWork&&<section style={card}><h2 style={h2}>Delivery Package</h2><p style={muted}>Tax returns, policies, receipts, immigration documents, approvals, and the final report are saved to this order.</p><textarea value={note} onChange={e=>setNote(e.target.value)} placeholder="Delivery notes" style={{...input,minHeight:80}}/><div style={{display:'flex',gap:8,marginTop:10,flexWrap:'wrap'}}><select value={category} onChange={e=>setCategory(e.target.value as DeliveryCategory)} style={{...input,maxWidth:210}}>{categories.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select><label style={primary}>+ Upload Delivery Files<input type="file" multiple onChange={upload} style={{display:'none'}}/></label></div><div style={{display:'grid',gap:8,marginTop:12}}>{files.map(f=><div key={f.id} style={item}><div><b>📄 {f.name}</b><div style={muted}>{fileCategoryLabel[f.category]||f.category} · V{f.version}</div></div></div>)}</div>{files.length>0&&delivery?.status!=='submitted'&&<><button disabled={!!busy||!canSubmitDelivery} onClick={submitDelivery} style={{...primary,marginTop:12}}>{busy==='delivery'?'Submitting…':'Submit Delivery Package'}</button>{supplementBlocked&&<div style={error}>Customer information is incomplete. Wait until the customer provides all requested items before submitting delivery.</div>}{supplement&&!supplementBlocked&&!canSubmitDelivery&&<div style={error}>Confirm information collection is complete before submitting delivery.</div>}</>}{delivery?.status==='submitted'&&<div style={success}>✓ Delivery package submitted. Awaiting customer confirmation.</div>}</section>}</div>
 <aside style={{display:'grid',gap:16,alignContent:'start'}}><section style={card}><h2 style={h2}>Order Status</h2><Info label="Order Status" value={stageLabel}/><Info label="Customer Payment" value={paymentLabel}/><Info label="Information Status" value={supplement?`${supplementComplete?'Required Information Received':(suppStatusLabel[supplement.status]||supplement.status)+' · '+supplement.items.filter(x=>x.status==='complete'||x.status==='answered').length+'/'+supplement.items.length}`:'Not Started'}/><Info label="Deliverables" value={delivery?`V${delivery.version} · ${delivery.status==='submitted'?'Delivered':(pkgStatusLabel[delivery.status]||delivery.status)}`:'Not Delivered'}/><Info label="Settlement Status" value={`${order?.settlement==='paid'?'✓ ':''}${settleLabel}`}/><Info label="Service Invoice" value={`${order?.invoice?'✓ ':''}${invoiceLabel}`}/></section><section style={card}><h2 style={h2}>Settlement & Invoice</h2><Info label="Professional Service Fee" value={`$${((order?.invoice?.amount??order?.amount)||0).toFixed(2)}`}/><Info label="Customer Payment" value={order?.invoice?.status==='paid'||stage==='completed'?'Paid':'Awaiting Payment'}/><Info label="Settlement Status" value={settleLabel}/><Info label="Service Invoice" value={order?.invoice?order.invoice.invoiceNumber:'Not Generated'}/></section><section style={card}><h2 style={h2}>Message Customer</h2><textarea value={message} onChange={e=>setMessage(e.target.value)} placeholder="Type a message…" style={{...input,minHeight:90}}/><button disabled={busy==='message'} onClick={send} style={{...primary,marginTop:10}}>{busy==='message'?'Sending…':'Send to Customer'}</button></section></aside></div></div></main>
}
function Info({label,value}:{label:string;value:string}){return <div style={{display:'flex',justifyContent:'space-between',gap:12,padding:'10px 0',borderBottom:'1px solid #292530'}}><span style={muted}>{label}</span><b style={{fontSize:13}}>{value}</b></div>}
const shell={minHeight:'100vh',background:'#0d0b12',color:'#f7f5fb',fontFamily:'Inter,Arial,sans-serif',padding:'28px 18px 70px'} as const
const wrap={maxWidth:1180,margin:'0 auto'} as const
const row={display:'flex',justifyContent:'space-between',gap:16,alignItems:'center',flexWrap:'wrap' as const}
const grid={display:'grid',gridTemplateColumns:'minmax(0,1.35fr) minmax(300px,.65fr)',gap:16,marginTop:16} as const
const card={background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:20} as const
const okPill={padding:'6px 11px',borderRadius:20,background:'#193523',color:'#86efac',fontSize:12,fontWeight:800} as const
const item={padding:'11px 12px',border:'1px solid #302a39',borderRadius:10,background:'#121018',display:'flex',justifyContent:'space-between',gap:10} as const
const h1={fontSize:30,margin:'7px 0'} as const
const h2={fontSize:18,margin:'0 0 10px'} as const
const eyebrow={color:'#9d7cff',fontSize:12,fontWeight:800} as const
const muted={color:'#9993a4',fontSize:12,lineHeight:1.6} as const
const primary={border:0,borderRadius:10,background:'#7655df',color:'#fff',padding:'10px 14px',fontWeight:750,cursor:'pointer',display:'inline-block'} as const
const secondary={border:'1px solid #3b3545',borderRadius:10,background:'transparent',color:'#c7c0cf',padding:'9px 13px',cursor:'pointer'} as const
const input={width:'100%',boxSizing:'border-box' as const,border:'1px solid #393342',borderRadius:10,background:'#100e15',color:'#f7f5fb',padding:'11px 12px',outline:'none'} as const
const success={marginTop:12,padding:12,borderRadius:10,background:'#193523',color:'#86efac',fontSize:13} as const
const error={marginTop:12,padding:12,borderRadius:10,background:'#3d1d1d',color:'#fca5a5',fontSize:13} as const
