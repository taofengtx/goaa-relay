'use client'

import { orderApi, orderApiConfigured, OrderSummary, DeliveryPackage, SupplementRequest, OrderRole, SupplementType, DeliveryCategory, AdminOrderAction } from './order-api'

const DEMO_KEY='goaa_order_demo_v1'
// Demo fallback is an explicit opt-in for local/dev/test tooling only.
// Production formal flows (customer-order-live / agent-order-live / admin-order-live)
// FAIL CLOSED unless NEXT_PUBLIC_GOAA_ALLOW_DEMO_FALLBACK === 'true'.
const demoAllowed = () => process.env.NEXT_PUBLIC_GOAA_ALLOW_DEMO_FALLBACK === 'true'
export type RuntimeMode='api'|'demo'
export type RuntimeOrder={mode:RuntimeMode;order:OrderSummary;deliveryPackage?:DeliveryPackage|null;supplement?:SupplementRequest|null}

function readDemo():any{if(typeof window==='undefined')return{};try{return JSON.parse(localStorage.getItem(DEMO_KEY)||'{}')}catch{return{}}}
function writeDemo(patch:any){if(typeof window==='undefined')return;const next={...readDemo(),...patch,updatedAt:new Date().toISOString()};localStorage.setItem(DEMO_KEY,JSON.stringify(next));window.dispatchEvent(new Event('goaa-order-demo-updated'))}
function demoOrderFromStorage():OrderSummary{const d=readDemo();return{id:'GOAA-DEMO-001',serviceTitle:d.serviceTitle||'Life Protection Planning Service',amount:Number(d.amount||600),stage:d.stage||'estimate',settlement:d.settlement==='paid'?'paid':d.stage==='completed'?'ready':'locked',updatedAt:d.updatedAt,deliveryPackage:(d.deliveryFiles||[]).length?{id:'demo-package-v1',orderId:'GOAA-DEMO-001',version:1,status:d.deliverySubmittedAt?'submitted':'draft',note:d.deliveryNote,submittedAt:d.deliverySubmittedAt,files:(d.deliveryFiles||[]).map((f:any)=>({id:f.id,name:f.name,category:'other',version:f.version||1,size:f.size,mimeType:f.type}))}:undefined}}
export async function loadRuntimeOrder(orderId:string,token?:string):Promise<RuntimeOrder>{if(orderApiConfigured()){try{const order=await orderApi.getOrder(orderId,token);const[deliveryPackage,supplement]=await Promise.all([orderApi.getDeliveryPackage(orderId,token).catch(()=>null),orderApi.getSupplement(orderId,token).catch(()=>null)]);return{mode:'api',order:{...order,deliveryPackage:deliveryPackage||order.deliveryPackage},deliveryPackage,supplement}}catch(err){if(!demoAllowed())throw err}}else if(!demoAllowed()){throw new Error('Order API is not configured and demo fallback is disabled')}const order=demoOrderFromStorage();return{mode:'demo',order,deliveryPackage:order.deliveryPackage||null,supplement:null}}
export function runtimeToken(role:OrderRole){
 if(typeof window==='undefined')return''
 if(role==='customer')return localStorage.getItem('client_token')||localStorage.getItem('goaa_order_customer_token')||localStorage.getItem('customer_token')||''
 return localStorage.getItem(`goaa_order_${role}_token`)||localStorage.getItem(`${role}_token`)||''
}
export function runtimeOrderId(){if(typeof window==='undefined')return'GOAA-DEMO-001';return new URLSearchParams(window.location.search).get('order')||localStorage.getItem('goaa_active_order_id')||'GOAA-DEMO-001'}
export function shouldUseApi(){return orderApiConfigured()}
async function apiOrDemo<T>(api:()=>Promise<T>,demo:()=>T|Promise<T>):Promise<T>{if(orderApiConfigured()){try{return await api()}catch(err){if(!demoAllowed())throw err}}else if(!demoAllowed()){throw new Error('Order API is not configured and demo fallback is disabled')}return demo()}
export const runtimeActions={
 acceptEstimate:(orderId:string,token?:string)=>apiOrDemo(()=>orderApi.acceptEstimate(orderId,token),()=>{writeDemo({stage:'accepted'});return demoOrderFromStorage()}),
 startService:(orderId:string,token?:string)=>apiOrDemo(()=>orderApi.startService(orderId,token),()=>{writeDemo({stage:'processing'});return demoOrderFromStorage()}),
 confirmCompletion:(orderId:string,token?:string)=>apiOrDemo(()=>orderApi.confirmCompletion(orderId,token),()=>{writeDemo({stage:'completed'});return demoOrderFromStorage()}),
 sendMessage:(orderId:string,role:OrderRole,content:string,token?:string)=>apiOrDemo(()=>orderApi.sendMessage(orderId,content,token),()=>{const d=readDemo();const key=role==='customer'?'customerMessages':'agentMessages';writeDemo({[key]:[...(d[key]||[]),content]});return{id:`demo-msg-${Date.now()}`,senderRole:role,content,createdAt:new Date().toISOString()}}),
 createSupplement:(orderId:string,items:Array<{label:string;type:SupplementType;required:boolean}>,token?:string)=>apiOrDemo(()=>orderApi.createSupplement(orderId,items,token),()=>{const mapped=items.map((x,i)=>({...x,id:`demo-s-${Date.now()}-${i}`,complete:false}));writeDemo({supplementItems:mapped,supplementStatus:'collecting'});return{id:'demo-supplement',status:'collecting',items:[]} as SupplementRequest}),
 answerSupplement:(orderId:string,itemId:string,answer:string,token?:string)=>apiOrDemo(()=>orderApi.answerSupplement(orderId,itemId,answer,token),()=>{const d=readDemo();const items=(d.supplementItems||[]).map((x:any)=>x.id===itemId?{...x,answer,complete:true}:x);writeDemo({supplementItems:items,supplementStatus:items.length&&items.every((x:any)=>x.complete)?'complete':'collecting'});return items.find((x:any)=>x.id===itemId)}),
 uploadSupplementFile:(orderId:string,itemId:string,file:File,token?:string)=>apiOrDemo(()=>orderApi.uploadSupplementFile(orderId,itemId,file,token),()=>{const d=readDemo();const items=(d.supplementItems||[]).map((x:any)=>x.id===itemId?{...x,attachments:[...(x.attachments||[]),{name:file.name,size:file.size,type:file.type}],complete:true}:x);writeDemo({supplementItems:items});return items.find((x:any)=>x.id===itemId)}),
 completeSupplements:(orderId:string,token?:string)=>apiOrDemo(()=>orderApi.completeSupplements(orderId,token),()=>{writeDemo({supplementStatus:'complete'});return demoOrderFromStorage()}),
 createDeliveryPackage:(orderId:string,note:string,token?:string)=>apiOrDemo(()=>orderApi.createDeliveryPackage(orderId,{note},token),()=>{writeDemo({deliveryNote:note,deliveryFiles:[]});return{id:'demo-package-v1',orderId,version:1,status:'draft',note,files:[]} as DeliveryPackage}),
 uploadDeliveryFile:(orderId:string,packageId:string,file:File,category:DeliveryCategory,token?:string)=>apiOrDemo(()=>orderApi.uploadDeliveryFile(orderId,packageId,file,category,token),()=>{const d=readDemo();const item={id:`df-${Date.now()}`,name:file.name,size:file.size,mimeType:file.type,category,version:1};writeDemo({deliveryFiles:[...(d.deliveryFiles||[]),{...item,type:file.type}]});return item}),
 submitDeliveryPackage:(orderId:string,packageId:string,token?:string)=>apiOrDemo(()=>orderApi.submitDeliveryPackage(orderId,packageId,token),()=>{writeDemo({stage:'delivered',deliverySubmittedAt:new Date().toISOString()});return demoOrderFromStorage().deliveryPackage as DeliveryPackage}),
 adminAction:(orderId:string,action:AdminOrderAction,reason:string,token?:string)=>apiOrDemo(()=>orderApi.adminAction(orderId,action,reason,token),()=>({ok:true})),
}
