'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { OrderSummary, orderApi } from '../../lib/order-api'

// Customer-friendly status mapping. Uses the formal Order Engine stage
// (frontend 7-state) and falls back to the DB stage for extended states.
// Settlement is an internal platform/Professional financial state: a settled
// order is shown to the Customer as "Completed" and no settlement/payout
// details are ever rendered here.
const stageLabel: Record<string, string> = {
  estimate: 'Estimate Ready',
  accepted: 'Estimate Accepted',
  paid: 'Payment Received',
  processing: 'Service in Progress',
  waiting_customer: 'Information Needed',
  documents_complete: 'Information Received',
  delivery_submitted: 'Deliverables Ready',
  customer_review: 'Review Deliverables',
  delivered: 'Awaiting Your Confirmation',
  completed: 'Completed',
  settled: 'Completed',
  settlement_ready: 'Completed',
  closed: 'Completed',
}

function orderStatus(o: OrderSummary): string {
  const key = (o.stage && stageLabel[o.stage]) ? o.stage : (o.dbStage && stageLabel[o.dbStage]) ? o.dbStage : o.stage || o.dbStage || ''
  return stageLabel[key] || key || 'In Progress'
}

export default function ClientOrdersPage() {
  const router = useRouter()
  const [orders, setOrders] = useState<OrderSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const token = localStorage.getItem('client_token')
      if (!token) { router.replace('/client-login'); return }
      // Formal Order Engine: GET /orders is scoped server-side to this
      // customer (WHERE customer_user_id = token user). Details are fetched
      // per order so cards show real service title / amount / invoice.
      const rows = await orderApi.listOrders(token)
      const ids = (rows.orders || []).map(r => String(r.id || '')).filter(Boolean)
      const details = await Promise.all(ids.map(id => orderApi.getOrder(id, token).catch(() => null)))
      setOrders(details.filter((x): x is OrderSummary => !!x))
    } catch {
      setError("We couldn't load your service orders. Please try again.")
    } finally {
      setLoading(false)
    }
  }, [router])

  useEffect(() => {
    void load()
  }, [load])

  const sorted = useMemo(() => {
    return [...orders].sort((a, b) => {
      const ta = a.updatedAt ? new Date(a.updatedAt).getTime() : 0
      const tb = b.updatedAt ? new Date(b.updatedAt).getTime() : 0
      return tb - ta
    })
  }, [orders])

  return <main style={{minHeight:'100vh',background:'#fafaf9',color:'#18181b',fontFamily:'Inter,system-ui,sans-serif',padding:'34px 18px'}}>
    <div style={{maxWidth:980,margin:'0 auto'}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:16,flexWrap:'wrap'}}>
        <div><div style={{fontSize:12,color:'#7c3aed',fontWeight:800}}>GOAA.ai Customer Center</div><h1 style={{margin:'7px 0 4px',fontSize:30}}>My Service Orders</h1><p style={{margin:0,color:'#71717a'}}>View your estimates, payments, service progress, deliverables, and invoices in one place.</p></div>
        <div style={{display:'flex',gap:8,flexWrap:'wrap'}}><button onClick={()=>router.push('/client-dashboard')} style={secondary}>Back to Customer Center</button><button onClick={()=>router.push('/')} style={primary}>Continue with GOAA AI</button></div>
      </div>

      {loading ? <section style={{...card,marginTop:22,textAlign:'center',padding:42}}><p style={{margin:0,color:'#71717a'}}>Loading your service orders…</p></section> :
      error ? <section style={{...card,marginTop:22,textAlign:'center',padding:42}}><p style={{margin:0,color:'#71717a',lineHeight:1.7}}>{error}</p><button style={{...primary,marginTop:14}} onClick={()=>void load()}>Try Again</button></section> :
      sorted.length === 0 ? <section style={{...card,marginTop:22,textAlign:'center',padding:42}}><h2 style={{marginTop:0}}>No Service Orders Yet</h2><p style={{color:'#71717a',lineHeight:1.7}}>When you connect with a professional and receive a service estimate, your order will appear here.</p><button style={primary} onClick={()=>router.push('/')}>Continue with GOAA AI</button></section> :
      <div style={{display:'grid',gap:16,marginTop:22}}>{sorted.map(o => <OrderCard key={o.id} order={o} onOpen={(id)=>router.push(`/customer-order-live?order=${encodeURIComponent(id)}`)} />)}</div>}
    </div>
  </main>
}

function OrderCard({ order, onOpen }: { order: OrderSummary; onOpen: (orderId: string) => void }) {
  const status = orderStatus(order)
  const title = order.serviceTitle || order.estimate?.serviceTitle || 'Professional Service'
  const orderNo = (order as { order_no?: string }).order_no || (order as { orderNumber?: string }).orderNumber || order.id.slice(0, 8).toUpperCase()
  const amount = order.estimate?.amount ?? order.amount
  const hasEstimate = typeof amount === 'number' && amount > 0
  const updated = order.updatedAt ? new Date(order.updatedAt).toLocaleString('en-US') : '—'
  const invoiceAvailable = Boolean(order.invoice)
  const invoiceStatus = order.invoice?.status || ''

  return <section style={card}>
    <div style={{display:'flex',justifyContent:'space-between',gap:20,alignItems:'flex-start',flexWrap:'wrap'}}>
      <div style={{minWidth:0}}>
        <div style={{fontSize:12,color:'#7c3aed',fontWeight:800,letterSpacing:'.04em'}}>SERVICE ORDER #{orderNo}</div>
        <h2 style={{margin:'8px 0 6px',fontSize:19}}>{title}</h2>
        <div style={{display:'flex',gap:8,flexWrap:'wrap',alignItems:'center',marginTop:2}}>
          <span style={{...statusPill,color: status === 'Completed' ? '#166534' : '#5b21b6', background: status === 'Completed' ? '#ecfdf5' : '#f5f3ff'}}>{status}</span>
        </div>
      </div>
      <div style={{textAlign:'right',flexShrink:0}}>
        {hasEstimate
          ? <><div style={{fontSize:28,fontWeight:850}}>${Number(amount).toFixed(2)}</div><div style={{fontSize:12,color:'#71717a'}}>Professional Service Fee</div></>
          : <><div style={{fontSize:16,fontWeight:750,color:'#71717a'}}>Estimate pending</div><div style={{fontSize:12,color:'#71717a'}}>Professional Service Fee</div></>}
      </div>
    </div>

    <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))',gap:10,marginTop:16}}>
      <Info label="Service Order ID" value={orderNo} />
      <Info label="Last Updated" value={updated} />
      <Info label="Invoice" value={invoiceAvailable ? (invoiceStatus === 'paid' ? 'Available · Paid' : 'Available') : 'Not generated yet'} />
    </div>

    <div style={{display:'flex',gap:10,marginTop:18,flexWrap:'wrap'}}>
      <button style={primary} onClick={()=>onOpen(order.id)}>Open Service Workspace</button>
    </div>
  </section>
}

function Info({ label, value }: { label: string; value: string }) {
  return <div><div style={{fontSize:11,color:'#a8a29e',letterSpacing:'.05em',textTransform:'uppercase'}}>{label}</div><div style={{fontSize:13,color:'#3f3f46',marginTop:3}}>{value}</div></div>
}

const card = {background:'#fff',border:'1px solid #e7e5e4',borderRadius:18,padding:22,boxShadow:'0 1px 4px rgba(0,0,0,.04)'} as const
const primary = {border:0,borderRadius:10,background:'#18181b',color:'#fff',padding:'11px 16px',fontWeight:750,cursor:'pointer'} as const
const secondary = {border:'1px solid #d6d3d1',borderRadius:10,background:'#fff',color:'#3f3f46',padding:'10px 14px',fontWeight:650,cursor:'pointer'} as const
const statusPill = {display:'inline-block',padding:'4px 10px',borderRadius:20,fontSize:12,fontWeight:750} as const
