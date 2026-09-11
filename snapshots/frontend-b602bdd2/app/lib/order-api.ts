export type OrderRole='customer'|'agent'|'admin'
export type OrderStage='estimate'|'accepted'|'paid'|'processing'|'waiting_customer'|'delivered'|'completed'
export type DeliveryCategory='final'|'receipt'|'policy_contract'|'tax'|'approval_notice'|'report'|'other'
export type SupplementType='text'|'date'|'amount'|'choice'|'image'|'pdf'|'file'
export type OrderEvent={id:string;type:string;createdAt:string;actorRole?:OrderRole;data?:unknown}
export type OrderMessage={id:string;senderRole:OrderRole;content:string;createdAt:string}
export type SupplementItem={id:string;label:string;type:SupplementType;required:boolean;status:string;answer?:string;files?:Array<{id:string;name:string;downloadUrl?:string}>}
export type SupplementRequest={id:string;status:'draft'|'collecting'|'complete';items:SupplementItem[]}
export type DeliveryFile={id:string;name:string;category:DeliveryCategory;version:number;size?:number;mimeType?:string;downloadUrl?:string;createdAt?:string}
export type DeliveryPackage={id:string;orderId:string;version:number;status:'draft'|'submitted'|'superseded';note?:string;files:DeliveryFile[];submittedAt?:string}
export type EstimateLine={label:string;amount?:number;description?:string}
export type ServiceEstimate={id?:string;serviceTitle:string;amount:number;currency?:string;scope?:string;lines?:EstimateLine[];status?:'draft'|'sent'|'accepted'|'paid';createdAt?:string}
export type InvoiceRecord={id:string;invoiceNumber:string;orderId:string;serviceTitle:string;amount:number;currency:string;status:'open'|'paid'|'void';downloadUrl?:string;createdAt?:string}
export type CheckoutSession={checkoutUrl:string;sessionId?:string;status?:string}
export type HandoffContext={matterId:string;title:string;category?:string;summary?:string;organization?:string|null;dueDate?:string|null;amount?:string|null;urgency?:'low'|'normal'|'high'|'urgent';risks?:string[];ownerActions?:string[];agentNextSteps?:string[];missingInformation?:string[];reviewedAt?:string|null;source:'customer_butler'}
export type OrderSummary={id:string;serviceTitle:string;amount:number;stage:OrderStage;dbStage?:string;settlement?:'locked'|'ready'|'paid';supplement?:SupplementRequest;deliveryPackage?:DeliveryPackage;estimate?:ServiceEstimate;connectPaid?:boolean;matched?:boolean;invoice?:InvoiceRecord|null;updatedAt?:string;handoffContext?:HandoffContext;handoff_context?:HandoffContext}
export type AdminOrderAction='flag'|'unflag'|'reassign'
type RequestOptions=RequestInit&{token?:string}
const API_BASE=(process.env.NEXT_PUBLIC_GOAA_ORDER_API_BASE||'https://api.goaa.ai/api/v1/order').replace(/\/$/,'')
export function orderApiConfigured(){return Boolean(API_BASE)}
async function request<T>(path:string,options:RequestOptions={}):Promise<T>{if(!API_BASE)throw new Error('GOAA Order API is not configured');const{token,headers,...rest}=options;const response=await fetch(`${API_BASE}${path}`,{...rest,headers:{...(rest.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(token?{Authorization:`Bearer ${token}`}:{}) ,...headers},cache:'no-store'});if(!response.ok){const detail=await response.text().catch(()=>'');throw new Error(detail||`GOAA Order API ${response.status}`)}if(response.status===204)return undefined as T;return response.json() as Promise<T>}
export const orderApi={
 createOrder:(payload:{need:string;category?:string;serviceTitle?:string},token?:string)=>request<OrderSummary>('/orders',{method:'POST',body:JSON.stringify(payload),token}),
 getOrder:(orderId:string,token?:string)=>request<OrderSummary>(`/orders/${encodeURIComponent(orderId)}`,{token}),
 saveHandoffContext:(orderId:string,payload:HandoffContext,token?:string)=>request<{status:'success';handoffContext:HandoffContext}>(`/orders/${encodeURIComponent(orderId)}/handoff-context`,{method:'POST',body:JSON.stringify(payload),token}),
 listOrders:(token?:string)=>request<{orders:Array<Record<string,unknown>>}>(`/orders`,{token}),
 getTimeline:(orderId:string,token?:string)=>request<OrderEvent[]>(`/orders/${encodeURIComponent(orderId)}/events`,{token}),
 createConnectCheckout:(orderId:string,token?:string)=>request<CheckoutSession>(`/orders/${encodeURIComponent(orderId)}/connect/checkout`,{method:'POST',token}),
 requestMatch:(orderId:string,token?:string)=>request<OrderSummary>(`/orders/${encodeURIComponent(orderId)}/match`,{method:'POST',token}),
 createEstimate:(orderId:string,payload:{serviceTitle:string;amount:number;scope?:string;lines?:EstimateLine[]},token?:string)=>request<ServiceEstimate>(`/orders/${encodeURIComponent(orderId)}/estimate`,{method:'POST',body:JSON.stringify(payload),token}),
 acceptEstimate:(orderId:string,token?:string)=>request<OrderSummary>(`/orders/${encodeURIComponent(orderId)}/estimate/accept`,{method:'POST',token}),
 createServiceCheckout:(orderId:string,token?:string)=>request<CheckoutSession>(`/orders/${encodeURIComponent(orderId)}/payments/service/checkout`,{method:'POST',token}),
 startService:(orderId:string,token?:string)=>request<OrderSummary>(`/orders/${encodeURIComponent(orderId)}/start`,{method:'POST',token}),
 confirmCompletion:(orderId:string,token?:string)=>request<OrderSummary>(`/orders/${encodeURIComponent(orderId)}/confirm`,{method:'POST',body:JSON.stringify({}),token}),
 getInvoice:(orderId:string,token?:string)=>request<InvoiceRecord|null>(`/orders/${encodeURIComponent(orderId)}/invoice`,{token}),
 generateInvoice:(orderId:string,token?:string)=>request<InvoiceRecord>(`/orders/${encodeURIComponent(orderId)}/invoice`,{method:'POST',token}),
 getMessages:(orderId:string,token?:string)=>request<OrderMessage[]>(`/orders/${encodeURIComponent(orderId)}/messages`,{token}),
 sendMessage:(orderId:string,content:string,token?:string)=>request<OrderMessage>(`/orders/${encodeURIComponent(orderId)}/messages`,{method:'POST',body:JSON.stringify({content}),token}),
 getSupplement:(orderId:string,token?:string)=>request<SupplementRequest|null>(`/orders/${encodeURIComponent(orderId)}/supplement`,{token}),
 createSupplement:(orderId:string,items:Array<{label:string;type:SupplementType;required:boolean}>,token?:string)=>request<SupplementRequest>(`/orders/${encodeURIComponent(orderId)}/supplement`,{method:'POST',body:JSON.stringify({items}),token}),
 answerSupplement:(orderId:string,itemId:string,answer:string,token?:string)=>request<SupplementItem>(`/orders/${encodeURIComponent(orderId)}/supplement/items/${encodeURIComponent(itemId)}`,{method:'PATCH',body:JSON.stringify({answer}),token}),
 uploadSupplementFile:(orderId:string,itemId:string,file:File,token?:string)=>{const body=new FormData();body.append('file',file);return request<SupplementItem>(`/orders/${encodeURIComponent(orderId)}/supplement/items/${encodeURIComponent(itemId)}/files`,{method:'POST',body,token})},
 completeSupplements:(orderId:string,token?:string)=>request<OrderSummary>(`/orders/${encodeURIComponent(orderId)}/supplements/complete`,{method:'POST',token}),
 getDeliveryPackage:(orderId:string,token?:string)=>request<DeliveryPackage|null>(`/orders/${encodeURIComponent(orderId)}/delivery-package`,{token}),
 createDeliveryPackage:(orderId:string,payload:{note?:string},token?:string)=>request<DeliveryPackage>(`/orders/${encodeURIComponent(orderId)}/delivery-package`,{method:'POST',body:JSON.stringify(payload),token}),
 uploadDeliveryFile:(orderId:string,packageId:string,file:File,category:DeliveryCategory,token?:string)=>{const body=new FormData();body.append('file',file);body.append('category',category);return request<DeliveryFile>(`/orders/${encodeURIComponent(orderId)}/delivery-package/${encodeURIComponent(packageId)}/files`,{method:'POST',body,token})},
 submitDeliveryPackage:(orderId:string,packageId:string,token?:string)=>request<DeliveryPackage>(`/orders/${encodeURIComponent(orderId)}/delivery-package/${encodeURIComponent(packageId)}/submit`,{method:'POST',token}),
 packageDownloadUrl:(orderId:string,packageId:string)=>API_BASE?`${API_BASE}/orders/${encodeURIComponent(orderId)}/delivery-package/${encodeURIComponent(packageId)}/download`:'#',
 invoicePdfUrl:(orderId:string)=>API_BASE?`${API_BASE}/orders/${encodeURIComponent(orderId)}/invoice/pdf`:'#',
 adminGetOrder:(orderId:string,token?:string)=>request<OrderSummary>(`/admin/orders/${encodeURIComponent(orderId)}`,{token}),
 adminAction:(orderId:string,action:AdminOrderAction,reason:string,token?:string)=>request<{ok:boolean}>(`/admin/orders/${encodeURIComponent(orderId)}/actions`,{method:'POST',body:JSON.stringify({action,reason}),token}),
 adminPayments:(orderId:string,token?:string)=>request<unknown[]>(`/admin/orders/${encodeURIComponent(orderId)}/payments`,{token}),
 adminAudit:(orderId:string,token?:string)=>request<OrderEvent[]>(`/admin/orders/${encodeURIComponent(orderId)}/audit`,{token}),
}
