'use client'

export default function OrderDemoCenter() {
  return <main style={{ minHeight:'100vh',background:'#0d0b12',color:'#f7f5fb',fontFamily:'Inter,Arial,sans-serif',padding:'40px 18px' }}>
    <div style={{ maxWidth:1080,margin:'0 auto' }}>
      <div style={{ color:'#9d7cff',fontSize:12,fontWeight:800 }}>GOAA ORDER FLOW V1</div>
      <h1 style={{ fontSize:34,margin:'8px 0' }}>Three-Role Order Test Center</h1>
      <p style={{ color:'#aaa4b5',lineHeight:1.7 }}>Open Customer, Agent, and Admin windows on the same demo order to verify the full flow: quote, payment, fulfillment, supplements, delivery, platform management, and settlement.</p>

      <div style={{ display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))',gap:16,marginTop:24 }}>
        <RoleCard title="Customer" copy="Accept the estimate, simulate Stripe payment, view progress, provide information, reply to messages, and confirm completion." href="/customer-order" action="Open Customer Window" />
        <RoleCard title="Agent" copy="Set the quote, wait for acceptance, start service, chat with the customer, request supplements, submit delivery, and review settlement." href="/agent-order-demo" action="Open Agent Window" />
        <RoleCard title="Admin" copy="View platform overview, order status, customers and Agents, payments and settlement, flags, and audit log." href="/admin-dashboard" action="Open Admin Window" />
      </div>

      <section style={{ marginTop:20,background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:22 }}>
        <h2 style={{ marginTop:0,fontSize:20 }}>Three-Role Integration Test Sequence</h2>
        <div style={{ display:'grid',gap:10,color:'#c5becb',fontSize:14,lineHeight:1.6 }}>
          <div>1. Agent confirms the service name, scope, and $600 estimated fee.</div>
          <div>2. Customer accepts the estimate and completes simulated Stripe payment.</div>
          <div>3. Admin reviews the order payment and current status.</div>
          <div>4. Agent starts service and requests additional information.</div>
          <div>5. Customer completes the requested information and attachments.</div>
          <div>6. Agent reviews the full information package and continues service.</div>
          <div>7. Agent submits final delivery; customer confirms completion.</div>
          <div>8. Admin reviews completion and settlement; Agent reviews the settlement condition.</div>
        </div>
      </section>
    </div>
  </main>
}

function RoleCard({title,copy,href,action}:{title:string;copy:string;href:string;action:string}) {
  return <article style={{ background:'#17151e',border:'1px solid #2b2734',borderRadius:18,padding:22 }}><h2 style={{ margin:'0 0 8px' }}>{title}</h2><p style={{ color:'#aaa4b5',lineHeight:1.65,minHeight:88 }}>{copy}</p><a href={href} target="_blank" rel="noreferrer" style={{ display:'inline-block',background:'#7655df',color:'#fff',textDecoration:'none',borderRadius:10,padding:'11px 15px',fontWeight:750 }}>{action}</a></article>
}
