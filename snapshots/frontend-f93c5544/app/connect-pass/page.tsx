'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import CustomerRecoveryNav from '../components/CustomerRecoveryNav'
import { CUSTOMER_READ_DEADLINE_MS, withReadDeadline } from '../lib/customer-read-recovery'
import { orderApi, type OrderSummary } from '../lib/order-api'
import {
  CUSTOMER_JOURNEY_KEYS,
  customerOrderId,
  customerToken,
  prepareCustomerAuthReturn,
  readCustomerJourney,
  writeCustomerJourney,
} from '../lib/customer-journey'
import { syncMatterMatched } from '../lib/personal-agent-order-sync'
import { ensureStructuredHandoff } from '../lib/personal-agent-handoff-persist'

type Workspace = {
  thread?: Array<{ role?: string; content?: string }>
  sessionId?: string
  intent?: string | null
  knownFacts?: Record<string, unknown>
  displayTitle?: string
  subIntent?: string | null
}

type PendingHandoff = {
  matterId?: string
  title?: string
  category?: string | null
  summary?: string | null
  organization?: string | null
  dueDate?: string | null
  amount?: string | null
  urgency?: 'low'|'normal'|'high'|'urgent'|null
  risks?: string[]
  ownerActions?: string[]
  agentNextSteps?: string[]
  missingInformation?: string[]
  reviewedAt?: string | null
  source?: 'customer_butler'
  boundary?: string
}

const PAYMENT_POLL_ATTEMPTS = 20
const PAYMENT_POLL_MS = 1500
const HANDOFF_PACKAGE_KEY = 'goaa_pending_professional_handoff_v1'
// A tab-local safety latch, not a payment record or server idempotency key.
const ATTEMPT_GUARD_KEY = 'goaa_connect_attempt_pending_v1'

function readWorkspace(): Workspace | null {
  try { const raw = window.localStorage.getItem(CUSTOMER_JOURNEY_KEYS.workspace); return raw ? JSON.parse(raw) as Workspace : null } catch { return null }
}
function readHandoff(): PendingHandoff | null {
  try { const raw = window.localStorage.getItem(HANDOFF_PACKAGE_KEY); return raw ? JSON.parse(raw) as PendingHandoff : null } catch { return null }
}
function buildNeed(workspace: Workspace | null, handoff: PendingHandoff | null) {
  if (handoff?.matterId) {
    return [handoff.title ? `Matter: ${handoff.title}` : '', handoff.summary ? `Reviewed summary: ${handoff.summary}` : '', handoff.organization ? `Organization: ${handoff.organization}` : '', handoff.dueDate ? `Due date: ${handoff.dueDate}` : '', handoff.amount ? `Amount: ${handoff.amount}` : '', handoff.urgency ? `Urgency: ${handoff.urgency}` : ''].filter(Boolean).join('\n')
  }
  if (!workspace) return ''
  const firstUser = workspace.thread?.find(x => x.role === 'user')?.content || ''
  const latestAssistant = [...(workspace.thread || [])].reverse().find(x => x.role === 'assistant')?.content || ''
  const facts = Object.entries(workspace.knownFacts || {}).slice(0, 8).map(([k, v]) => `${k}: ${String(v)}`).join('；')
  return [workspace.displayTitle ? `Topic: ${workspace.displayTitle}` : '', firstUser ? `Initial request: ${firstUser}` : '', workspace.intent ? `Intent: ${workspace.intent}` : '', workspace.subIntent ? `Sub-need: ${workspace.subIntent}` : '', facts ? `Known info: ${facts}` : '', latestAssistant ? `GOAA AI summary: ${latestAssistant}` : ''].filter(Boolean).join('\n')
}
function sleep(ms:number){ return new Promise(resolve => window.setTimeout(resolve, ms)) }

export default function ConnectPassPage() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [handoff, setHandoff] = useState<PendingHandoff | null>(null)
  const [order, setOrder] = useState<OrderSummary | null>(null)
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [initialLoading, setInitialLoading] = useState(true)
  const [lookupError, setLookupError] = useState('')
  const [lookupId, setLookupId] = useState('')
  const [queryBusy, setQueryBusy] = useState(false)
  const [recoveryOnly, setRecoveryOnly] = useState(false)
  const [busySlow, setBusySlow] = useState(false)
  const querySequence = useRef(0)
  const purchaseInFlight = useRef(false)
  const mounted = useRef(false)
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; querySequence.current += 1 } }, [])
  useEffect(() => {
    setBusySlow(false)
    if (!busy && !initialLoading) return
    const timer = window.setTimeout(() => setBusySlow(true), CUSTOMER_READ_DEADLINE_MS)
    return () => window.clearTimeout(timer)
  }, [busy, initialLoading])
  const need = useMemo(() => buildNeed(workspace, handoff), [workspace, handoff])

  async function recheckSavedOrder() {
    // GET only. Never call ensureOrder, checkout or requestMatch from recovery.
    const id = order?.id || lookupId
    const token = customerToken()
    if (!id || !token) { setLookupError('无法核对原订单。请返回 AI 管家并保留当前会话，不要再次激活或付款。'); return }
    const sequence = ++querySequence.current
    setQueryBusy(true); setLookupError(''); setRecoveryOnly(true)
    try {
      const current = await withReadDeadline(orderApi.getOrder(id, token))
      if (!mounted.current || sequence !== querySequence.current) return
      if (customerToken() !== token) throw new Error('Session changed')
      if (current.id !== id || typeof current.connectPaid !== 'boolean') throw new Error('Invalid order response')
      setOrder(current); setError('')
      setStatus(current.connectPaid
        ? '服务器已确认此订单连接费到账。请查看原订单；不要重复购买。'
        : '服务器当前未确认此订单连接费到账。这不是付款失败证明；请稍后重新查询，不要重复支付。')
    } catch {
      if (mounted.current && sequence === querySequence.current) setLookupError('无法确认原订单状态，可能是请求超时、登录失效或无权访问。请保留订单号，不要重复下单或付款。')
    } finally {
      if (mounted.current && sequence === querySequence.current) { setQueryBusy(false); setInitialLoading(false) }
    }
  }

  async function guardedBuyPass() {
    if (purchaseInFlight.current || initialLoading || queryBusy || busy || recoveryOnly || lookupError || error || order?.connectPaid || !need) return
    purchaseInFlight.current = true
    try {
      const context = handoff?.matterId || workspace?.sessionId || 'unscoped'
      window.sessionStorage.setItem(ATTEMPT_GUARD_KEY, context)
    } catch {
      setLookupError('浏览器无法保存本次操作标记，已暂停购买。请返回 AI 管家。')
      purchaseInFlight.current = false
      return
    }
    setRecoveryOnly(true)
    try { await buyPass() }
    finally { purchaseInFlight.current = false }
  }

  useEffect(() => {
    let disposed = false
    const ws = readWorkspace(); const hf = readHandoff(); setWorkspace(ws); setHandoff(hf)
    const token = customerToken()
    if (!token) {
      const currentTarget = `${window.location.pathname}${window.location.search}`
      prepareCustomerAuthReturn(currentTarget || '/connect-pass?source=planning')
      window.location.replace('/client-login?resume=1&reason=purchase')
      return
    }
    const params = new URLSearchParams(window.location.search)
    const checkoutState = params.get('checkout'); const paymentState = params.get('payment'); const returnOrderId = params.get('order') || ''
    const isCancelled = checkoutState === 'cancelled' || paymentState === 'cancelled'
    const isReturn = checkoutState === 'return' || paymentState === 'success'
    if (isCancelled) {
      setLookupId(returnOrderId || customerOrderId()); setInitialLoading(false); setRecoveryOnly(true)
      setStatus('已收到取消结账返回。事项仍保留，请先查询原订单状态，不要直接重复付款。')
      return
    }
    if (isReturn && returnOrderId) {
      setLookupId(returnOrderId); setInitialLoading(false); setRecoveryOnly(true)
      void verifyConnectPaymentAndMatch(returnOrderId, token, ws, hf); return
    }
    const journey = readCustomerJourney()
    const planningSession = hf?.matterId ? undefined : ws?.sessionId
    const samePlanningSession = !planningSession || !journey?.planningSessionId || journey.planningSessionId === planningSession
    let pendingAttempt = false
    try { pendingAttempt = window.sessionStorage.getItem(ATTEMPT_GUARD_KEY) === (hf?.matterId || ws?.sessionId || 'unscoped') }
    catch { setLookupError('无法读取浏览器操作记录，请返回 AI 管家核对，暂不发起购买。'); setRecoveryOnly(true) }
    const previousCheckout = samePlanningSession && ['connect_checkout_started','connect_payment_verifying','connect_paid','matching','matched','order_workspace'].includes(journey?.step || '')
    if (pendingAttempt || previousCheckout) setRecoveryOnly(true)
    if (planningSession) writeCustomerJourney({ step: 'need_ready', planningSessionId: planningSession })
    const savedId = samePlanningSession ? customerOrderId() : ''
    setLookupId(savedId)
    if (savedId) {
      withReadDeadline(orderApi.getOrder(savedId, token)).then(async current => {
        if (disposed || customerToken() !== token) return
        if (current.id !== savedId || typeof current.connectPaid !== 'boolean') throw new Error('Invalid order response')
        if (hf?.matterId) await ensureStructuredHandoff(current.id, hf, token)
        if (disposed || customerToken() !== token) return
        setOrder(current)
        setInitialLoading(false)
        writeCustomerJourney({ orderId: current.id, step: current.connectPaid ? (current.matched ? 'matched' : 'connect_paid') : 'order_created', planningSessionId: planningSession })
        if (current.connectPaid) {
          if (current.matched) { if (hf?.matterId) syncMatterMatched(hf.matterId, current.id); window.location.replace(`/customer-order-live?order=${encodeURIComponent(current.id)}`) }
          else void verifyConnectPaymentAndMatch(current.id, token, ws, hf)
        }
      }).catch(() => {
        if (!disposed) { setLookupError('原订单未能加载，请重新查询状态。无法确认前不会再次创建订单或付款。'); setInitialLoading(false); setRecoveryOnly(true) }
      })
    } else {
      setInitialLoading(false)
      if (pendingAttempt || previousCheckout) setLookupError('此前操作结果尚不明确，且本地没有可核对的订单号。请返回 AI 管家联系支持核查，不要重复激活。')
    }
    return () => { disposed = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function verifyConnectPaymentAndMatch(orderId:string, token:string, ws:Workspace|null, hf:PendingHandoff|null) {
    setBusy(true); setError(''); setStatus('Confirming your 30-day Personal AI Agent access…')
    writeCustomerJourney({ orderId, step: 'connect_payment_verifying', planningSessionId: hf?.matterId ? undefined : ws?.sessionId })
    try {
      if (hf?.matterId) await ensureStructuredHandoff(orderId, hf, token)
      let current: OrderSummary | null = null
      for (let attempt = 0; attempt < PAYMENT_POLL_ATTEMPTS; attempt += 1) { current = await orderApi.getOrder(orderId, token); setOrder(current); if (current.connectPaid) break; await sleep(PAYMENT_POLL_MS) }
      if (!current?.connectPaid) { setStatus('Payment return received, but server confirmation is still in progress — click "Re-check Payment" shortly.'); return }
      writeCustomerJourney({ orderId, step: 'connect_paid', planningSessionId: hf?.matterId ? undefined : ws?.sessionId })
      setStatus(current.matched ? 'Access confirmed. Opening your service order…' : 'Access confirmed. Matching you with a licensed professional…')
      let matchedOrder = current
      if (!current.matched) {
        writeCustomerJourney({ orderId, step: 'matching', planningSessionId: hf?.matterId ? undefined : ws?.sessionId })
        try { matchedOrder = await orderApi.requestMatch(orderId, token) }
        catch { const refreshed = await orderApi.getOrder(orderId, token); if (!refreshed.matched) throw new Error('Your access is confirmed. We are still matching you with a professional — please try again shortly.'); matchedOrder = refreshed }
      }
      setOrder(matchedOrder)
      writeCustomerJourney({ orderId, step: 'matched', planningSessionId: hf?.matterId ? undefined : ws?.sessionId })
      window.localStorage.setItem(CUSTOMER_JOURNEY_KEYS.orderId, orderId)
      if (hf?.matterId) syncMatterMatched(hf.matterId, orderId)
      window.location.replace(`/customer-order-live?order=${encodeURIComponent(orderId)}`)
    } catch {
      setError('We could not verify the protected connection flow yet. No completion state was fabricated.')
      setStatus('Your Matter remains with your AI Agent while confirmation or matching is still pending.')
    } finally { setBusy(false) }
  }

  async function ensureOrder() {
    const token = customerToken(); if (!token) throw new Error('We could not verify your account. Please sign in again and try again.')
    if (order) { if (handoff?.matterId) await ensureStructuredHandoff(order.id, handoff, token); return order }
    if (!need) throw new Error('No reviewed Matter or consultation found.')
    setStatus('Preparing your protected service request…')
    const created = await orderApi.createOrder({ need, category: handoff?.category || workspace?.intent || 'general', serviceTitle: handoff?.title || workspace?.displayTitle || 'GOAA Professional Service Request' }, token)
    if (handoff?.matterId) await ensureStructuredHandoff(created.id, handoff, token)
    setOrder(created)
    writeCustomerJourney({ orderId: created.id, step: 'order_created', planningSessionId: handoff?.matterId ? undefined : workspace?.sessionId })
    return created
  }

  async function buyPass() {
    setBusy(true); setError('')
    try {
      const token = customerToken(); const current = await ensureOrder()
      if (current.connectPaid) { await verifyConnectPaymentAndMatch(current.id, token, workspace, handoff); return }
      setStatus(handoff?.matterId ? 'Reviewed Matter saved. Taking you to Stripe Test Mode secure payment…' : 'Taking you to Stripe Test Mode secure payment…')
      writeCustomerJourney({ orderId: current.id, step: 'connect_checkout_started', planningSessionId: handoff?.matterId ? undefined : workspace?.sessionId })
      const checkout = await orderApi.createConnectCheckout(current.id, token); window.location.assign(checkout.checkoutUrl)
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e)
      if (/401|403|unauthor|forbidden/i.test(message)) { setError('We could not verify your account. Please sign in again and try again.'); setStatus('') }
      else setError('Something went wrong. Please try again.')
    } finally { setBusy(false) }
  }

  async function retryPaymentVerification() { const token = customerToken(); const orderId = order?.id || customerOrderId(); if (!token || !orderId) return; await verifyConnectPaymentAndMatch(orderId, token, workspace, handoff) }

  return <><CustomerRecoveryNav /><main style={{minHeight:'100vh',background:'#0b0b10',color:'#fff',fontFamily:'system-ui,-apple-system,sans-serif',padding:'34px 18px 70px'}}><div style={{maxWidth:920,margin:'0 auto'}}>
    <div style={{marginTop:24,fontSize:12,color:'#9d7cff',fontWeight:850,letterSpacing:'.08em'}}>GOAA · PERSONAL AI AGENT ACCESS</div>
    <h1 style={{fontSize:34,margin:'8px 0 10px'}}>Activate 30 Days of Your Personal AI Agent</h1>
    <p style={{color:'#aaa4b1',lineHeight:1.75,maxWidth:720}}>Your AI Agent keeps the Matter organized, prepares the professional handoff when needed, and continues tracking the work. Professional services remain separate and are provided by the licensed professional.</p>
    <section style={card}><div style={{fontSize:12,color:'#9d7cff',fontWeight:800}}>Reviewed Matter</div><h2 style={{margin:'8px 0 12px'}}>{handoff?.title || workspace?.displayTitle || 'Professional Service Request'}</h2><pre style={{whiteSpace:'pre-wrap',fontFamily:'inherit',color:'#d8d3dd',lineHeight:1.65,margin:0,fontSize:14}}>{need || 'No reviewed Matter found yet.'}</pre></section>
    <section style={{...card,borderColor:'#6d4aff',boxShadow:'0 20px 70px rgba(109,74,255,.12)'}}><div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:20,flexWrap:'wrap'}}><div><div style={{fontSize:12,color:'#9d7cff',fontWeight:800}}>GOAA 30-Day Personal AI Agent Access</div><h2 style={{margin:'8px 0 6px'}}>30-Day Personal AI Agent Access</h2><p style={{margin:0,color:'#aaa4b1',lineHeight:1.65}}>One-time payment. No auto-renewal. Your same Personal AI Agent stays with you; this purchase activates 30 days of service and professional connection access when a licensed expert is needed.</p></div><div style={{fontSize:38,fontWeight:900}}>$39.90</div></div>
      <div style={{marginTop:18,padding:14,borderRadius:12,background:'#15121d',color:'#cfc7da',fontSize:13,lineHeight:1.65}}>Professional service fees are separate. Your AI Agent does not represent the professional, and the Professional AI Assistant does not replace your customer-side AI Agent.</div>
      <button onClick={guardedBuyPass} disabled={busy || initialLoading || queryBusy || recoveryOnly || !!lookupError || !!error || !!order?.connectPaid || !need} style={{marginTop:18,width:'100%',minHeight:52,border:0,borderRadius:14,background:'#6d4aff',color:'#fff',fontWeight:850,fontSize:16,cursor:'pointer',opacity:(busy || initialLoading || queryBusy || recoveryOnly || !!lookupError || !!error || !!order?.connectPaid || !need)?0.6:1}}>{busy?'正在处理 · Processing…':initialLoading?'正在核对已有订单…':order?.connectPaid?'此订单连接费已确认，请查看原订单':recoveryOnly||lookupError||error?'请先核对原订单状态':'Activate My 30-Day AI Agent'}</button>
      {(lookupError || busySlow || recoveryOnly) && <section aria-label="订单状态恢复" style={{marginTop:16,border:'1px solid #65507e',borderRadius:12,padding:14}}>
        <p role="status" style={{color:'#ded2ef',fontSize:13,lineHeight:1.7}}>{lookupError || (busySlow ? '等待时间较长，本次操作结果尚未确定。超时不代表失败，后台仍可能正在处理；不要重复下单或付款。' : '本事项已有操作记录，请先核对原订单状态。仅服务器确认付款后才可确认连接费到账。')}</p>
        {(order?.id || lookupId) ? <>
          <button onClick={recheckSavedOrder} disabled={queryBusy} style={{padding:10,borderRadius:8,border:'1px solid #87729e',background:'transparent',color:'#fff'}}>{queryBusy?'正在查询…':'重新查询状态（不下单、不付款）'}</button>
          <a href={`/customer-order-live?order=${encodeURIComponent(order?.id || lookupId)}`} style={{display:'inline-block',margin:12,color:'#c7b6ff'}}>查看原订单 · View existing order</a>
          <div style={{fontSize:12}}>Order #{order?.id || lookupId}</div>
        </> : <p style={{fontSize:12}}>请保留当前会话与截图，由支持人员核查原请求。</p>}
      </section>}
      {status&&<div style={{marginTop:14,color:'#c7bed2',fontSize:13,lineHeight:1.6}}>{status}</div>}
      {status.includes('Re-check Payment')&&<button onClick={recheckSavedOrder} disabled={queryBusy} style={{marginTop:12,border:'1px solid #4c435a',borderRadius:10,background:'transparent',color:'#ddd5e7',padding:'9px 12px',cursor:'pointer'}}>Re-check status (read only)</button>}
      {error&&<div style={{marginTop:12,padding:12,borderRadius:10,background:'#3a1720',color:'#fecdd3',fontSize:12,lineHeight:1.55}}>Error: {error}</div>}
      {order&&<div style={{marginTop:12,color:'#77717f',fontSize:11}}>Service Order ID: {order.id}</div>}
    </section>
  </div></main></>
}
const card={marginTop:18,background:'#15131b',border:'1px solid #2d2934',borderRadius:20,padding:22} as const
