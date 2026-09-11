'use client'

import { useOrderRuntime } from './OrderRuntimeBridge'
import { deriveCoordinationState } from '../lib/agent-coordination-state'

export default function ButlerBlockerDetector(){
 const runtime=useOrderRuntime('customer',3600)
 const order=runtime.data?.order
 if(!order||order.stage==='completed')return null
 const state=deriveCoordinationState(order,runtime.data?.supplement,runtime.data?.deliveryPackage)
 const owner=state.owner==='customer'?'You':state.owner==='professional'?'Professional':state.owner==='system'?'GOAA system':'No one'
 return <section style={{maxWidth:1180,margin:'10px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><div style={{border:'1px solid rgba(45,212,191,.18)',borderRadius:16,padding:14,background:'#0d1c1b',color:'#ecfeff'}}><div style={{fontSize:10,fontWeight:850,letterSpacing:'.08em',color:'#5eead4'}}>AI BUTLER · WHAT IS HOLDING THIS UP?</div><div style={{fontSize:12,lineHeight:1.55,marginTop:6,color:'#ccfbf1'}}>{state.title}</div><div style={{fontSize:11,lineHeight:1.55,marginTop:5,color:'#a7d8d1'}}>{state.customerView}</div><div style={{display:'flex',gap:8,flexWrap:'wrap',marginTop:8,fontSize:10}}><span style={pill}>Current owner: {owner}</span><span style={pill}>Phase: {state.phase}</span></div><div style={{marginTop:7,fontSize:10,color:'#699b93'}}>Why: {state.reason}</div></div></section>
}
const pill={padding:'5px 8px',borderRadius:999,border:'1px solid rgba(94,234,212,.16)',color:'#99f6e4'} as const
