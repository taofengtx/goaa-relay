export default function CustomerRecoveryNav() {
  return <nav aria-label="客户工作区导航" style={{position:'sticky',top:0,zIndex:30,background:'#0b0b10',borderBottom:'1px solid #302a39',padding:'14px 18px'}}>
    <div style={{maxWidth:1080,margin:'0 auto'}}>
      <a href="/planning" style={{color:'#c7b6ff',fontWeight:750,textDecoration:'none'}}>← 返回 AI 管家 · Back to AI Butler</a>
      <span style={{display:'block',color:'#aaa4b1',fontSize:12,marginTop:5}}>返回不会取消订单或重新付款。Return without cancelling your order or starting another payment.</span>
    </div>
  </nav>
}
