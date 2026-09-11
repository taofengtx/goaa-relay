'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { AgentLead, listAgentLeads } from '../../lib/agent-console'

const DEMO_KEY = 'goaa_order_demo_v1'

type DemoState = { stage?: string; amount?: number; serviceTitle?: string; updatedAt?: string }

export default function AgentServiceOrdersPage() {
  const router = useRouter()
  const [leads, setLeads] = useState<AgentLead[]>([])
  const [demo, setDemo] = useState<DemoState>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!localStorage.getItem('agent_token')) { router.replace('/agent-login'); return }
    const readDemo = () => { try { setDemo(JSON.parse(localStorage.getItem(DEMO_KEY) || '{}')) } catch { setDemo({}) } }
    readDemo()
    const onStorage = (e: StorageEvent) => { if (e.key === DEMO_KEY) readDemo() }
    window.addEventListener('storage', onStorage)
    void (async () => {
      try {
        const result = await listAgentLeads() as { leads: AgentLead[] }
        setLeads((result.leads || []).filter((x: AgentLead) => x.status === 'accepted' || x.status === 'closed'))
      } catch {
        setError('Service orders are temporarily unavailable. Please try again later.')
      } finally {
        setLoading(false)
      }
    })()
    return () => window.removeEventListener('storage', onStorage)
  }, [router])

  const hasPrototypeOrder = Boolean(demo.stage)
  const totalCount = leads.length + (hasPrototypeOrder ? 1 : 0)
  const statusLabel = useMemo(() => ({ estimate:'Preparing Quote', accepted:'Customer Accepted', paid:'Paid', processing:'Service in Progress', delivered:'Awaiting Customer Confirmation', completed:'Completed' } as Record<string,string>)[demo.stage || ''] || 'Preparing Quote', [demo.stage])
  const processingCount = leads.filter((x: AgentLead) => x.status === 'accepted').length + (demo.stage === 'processing' ? 1 : 0)
  const completedCount = leads.filter((x: AgentLead) => x.status === 'closed').length + (demo.stage === 'completed' ? 1 : 0)

  return <main style={{minHeight:'100vh',background:'#0d0b12',color:'#f7f5fb',fontFamily:'Inter,system-ui,sans-serif',padding:'30px 18px 70px'}}>
    <div style={{maxWidth:1100,margin:'0 auto'}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:16,flexWrap:'wrap'}}>
        <div><div style={{color:'#9d7cff',fontSize:12,fontWeight:800}}>GOAA.ai My Agent</div><h1 style={{margin:'7px 0 4px',fontSize:30}}>Service Orders</h1><p style={{margin:0,color:'#9993a4'}}>Estimates, payments, fulfillment, AI chat, delivery, and settlement all happen in one order workspace.</p></div>
        <div style={{display:'flex',gap:8,flexWrap:'wrap'}}><button onClick={()=>router.push('/agent-dashboard')} style={secondary}>Back to Agent Home</button><button onClick={()=>router.push('/agent-dashboard')} style={primary}>Accept Opportunities</button></div>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(210px,1fr))',gap:12,marginTop:18}}>
        <Metric label="Service Orders" value={String(totalCount)} />
        <Metric label="In Progress" value={String(processingCount)} />
        <Metric label="Completed" value={String(completedCount)} />
      </div>

      {error && <div style={{...card,marginTop:18,color:'#fca5a5'}}>{error}</div>}
      {loading && <div style={{...card,marginTop:18,color:'#9993a4'}}>Loading service orders…</div>}
      {!loading && !error && totalCount === 0 && <div style={{...card,marginTop:18,textAlign:'center',padding:38}}><h2 style={{marginTop:0}}>No Service Orders Yet</h2><p style={{color:'#9993a4'}}>Accept an opportunity first, agree on scope, then the formal order will appear here.</p><button style={primary} onClick={()=>router.push('/agent-dashboard')}>Back to Opportunities</button></div>}

      <div style={{display:'grid',gap:14,marginTop:18}}>
        {hasPrototypeOrder && <article style={{...card,borderColor:'#5b46a0'}}>
          <div style={{display:'flex',justifyContent:'space-between',gap:18,alignItems:'center',flexWrap:'wrap'}}>
            <div style={{minWidth:0,flex:1}}><div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}><span style={{color:'#a88af7',fontSize:12,fontWeight:800}}>Service Order</span><span style={{fontSize:11,padding:'4px 8px',borderRadius:20,background:'#2b2146',color:'#cbb9ff'}}>{statusLabel}</span></div><div style={{marginTop:9,fontSize:18,fontWeight:750}}>{demo.serviceTitle || 'Professional Service'}</div><div style={{marginTop:8,color:'#928c9d',fontSize:12}}>${demo.amount || 600} · contact hidden · AI-relayed chat</div></div>
            <button style={primary} onClick={()=>router.push('/agent-order-demo')}>Open Service Workspace</button>
          </div>
        </article>}

        {leads.map((lead: AgentLead)=> <article key={lead.id} style={card}>
          <div style={{display:'flex',justifyContent:'space-between',gap:18,alignItems:'center',flexWrap:'wrap'}}>
            <div style={{minWidth:0,flex:1}}><div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}><span style={{color:'#a88af7',fontSize:12,fontWeight:800}}>{lead.category === 'insurance' ? 'Financial Planning' : lead.category || 'Professional Service'}</span><span style={{fontSize:11,padding:'4px 8px',borderRadius:20,background:lead.status==='closed'?'#193523':'#18334b',color:lead.status==='closed'?'#86efac':'#93c5fd'}}>{lead.status==='closed'?'Completed':'Awaiting Service Order'}</span></div><div style={{marginTop:9,fontSize:18,fontWeight:750,lineHeight:1.5}}>{clean(lead.summary)}</div><div style={{marginTop:8,color:'#928c9d',fontSize:12}}>{lead.client_region || 'Region TBD'} · contact hidden</div></div>
            <button style={primary} onClick={()=>router.push(`/agent-dashboard/order-workspace?order=${encodeURIComponent(lead.id)}`)}>Open Service Workspace</button>
          </div>
        </article>)}
      </div>
    </div>
  </main>
}

function Metric({label,value}:{label:string;value:string}) { return <div style={{...card,padding:16}}><div style={{color:'#8f8999',fontSize:11}}>{label}</div><div style={{fontSize:24,fontWeight:850,marginTop:5}}>{value}</div></div> }
function clean(value:string){return value.replace(/^life\s*/i,'Life ').replace(/available|accepted|matched|declined|closed/gi,'').replace(/\s+/g,' ').trim()}
const card = {background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:20} as const
const primary = {border:0,borderRadius:10,background:'#7655df',color:'#fff',padding:'10px 14px',fontWeight:750,cursor:'pointer'} as const
const secondary = {border:'1px solid #3b3545',borderRadius:10,background:'transparent',color:'#c7c0cf',padding:'9px 13px',cursor:'pointer'} as const
