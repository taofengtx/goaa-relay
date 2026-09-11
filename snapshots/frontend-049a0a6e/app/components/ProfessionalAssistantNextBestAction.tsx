'use client'

import { useOrderRuntime } from './OrderRuntimeBridge'
import { deriveCoordinationState } from '../lib/agent-coordination-state'

export default function ProfessionalAssistantNextBestAction(){
 const runtime=useOrderRuntime('agent',4200)
 const order=runtime.data?.order
 if(!order)return null
 const state=deriveCoordinationState(order,runtime.data?.supplement,runtime.data?.deliveryPackage)
 const label=state.owner==='professional'?'YOUR MOVE':state.owner==='customer'?'WAITING ON CUSTOMER':state.owner==='system'?'SYSTEM / MATCHING':'ORDER STATE'
 return <section style={{maxWidth:1180,margin:'12px auto 0',padding:'0 18px',fontFamily:'Inter,Arial,sans-serif'}}><div style={{border:'1px solid rgba(251,191,36,.22)',borderRadius:18,padding:16,background:'#1c170d',color:'#fffbeb'}}><div style={{fontSize:11,fontWeight:850,letterSpacing:'.08em',color:'#fcd34d'}}>PROFESSIONAL AI ASSISTANT · NEXT BEST ACTION</div><div style={{display:'flex',justifyContent:'space-between',gap:12,flexWrap:'wrap',marginTop:6}}><strong style={{fontSize:16}}>{state.title}</strong><span style={{fontSize:10,fontWeight:800,color:'#fde68a'}}>{label}</span></div><p style={{fontSize:11,lineHeight:1.55,color:'#d6c9a6',margin:'8px 0 0'}}>{state.professionalView}</p><div style={{marginTop:9,paddingTop:9,borderTop:'1px solid rgba(255,255,255,.07)',fontSize:10,lineHeight:1.5,color:'#9f936f'}}>Why: {state.reason} Completion allowed: {state.completionAllowed?'yes':'no'}.</div></div></section>
}
