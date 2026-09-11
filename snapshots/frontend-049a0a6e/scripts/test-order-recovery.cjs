// Offline component tests: actual React hooks + react-test-renderer, fake API/storage/clock.
// No live browser/session, network, database, payment or production service is used.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const ts = require('typescript');
const React = require('react');
const {create, act} = require('react-test-renderer');
const root = path.resolve(__dirname, '..');
const fixtures = [];
const WORKSPACE = 'goaa_planning_workspace_v1';
const JOURNEY = 'goaa_customer_e2e_journey_v1';
const GUARD = 'goaa_connect_attempt_pending_v1';
function deferred() { let resolve, reject; const promise = new Promise((a,b) => {resolve=a;reject=b}); return {promise,resolve,reject}; }
function storage(seed={}) {const data=new Map(Object.entries(seed));return {getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,String(v)),removeItem:k=>data.delete(k),data};}
function fixture({saved=false,token='offline-test-identity',api={},session={},search='?source=planning',runtime={}}={}) {
  let now=0,id=0; const timers=new Map(), calls=[], navigations=[];
  const setTimer=(fn,ms)=>{timers.set(++id,{fn,at:now+ms});return id;};
  const clearTimer=i=>timers.delete(i);
  const local=storage({client_token:token,[WORKSPACE]:JSON.stringify({sessionId:'offline-session',displayTitle:'Insurance',intent:'insurance_planning',thread:[{role:'user',content:'Insurance for myself'}]}),...(saved?{[JOURNEY]:JSON.stringify({orderId:'order-offline',planningSessionId:'offline-session',step:'order_created'}),goaa_active_order_id:'order-offline'}:{})});
  const browser={localStorage:local,sessionStorage:storage(session),setTimeout:setTimer,clearTimeout:clearTimer,location:{search,pathname:'/connect-pass',assign:u=>navigations.push(u),replace:u=>navigations.push(u)},history:{replaceState:(_a,_b,u)=>{browser.location.search=u.includes('?')?'?'+u.split('?')[1]:''}}};
  const snapshot={id:'order-offline',serviceTitle:'Insurance',amount:0,stage:'estimate',connectPaid:false,matched:false};
  const orderApi={};
  for(const name of ['getOrder','createOrder','createConnectCheckout','requestMatch'])orderApi[name]=(...args)=>{
    calls.push({name,args}); if(api[name])return api[name](...args);
    if(name==='createConnectCheckout')return Promise.resolve({checkoutUrl:'https://checkout.invalid/offline'});
    if(name==='requestMatch')throw new Error('Unexpected matching mutation');
    return Promise.resolve({...snapshot});
  };
  const rt={data:null,loading:true,error:'',orderId:'order-offline',token,refresh:async()=>{calls.push({name:'refresh'});},...runtime};
  const cache=new Map();
  function load(relative) {
    const absolute=path.resolve(root,relative);
    if(cache.has(absolute))return cache.get(absolute);
    const source=fs.readFileSync(absolute,'utf8');
    const result=ts.transpileModule(source,{fileName:absolute,reportDiagnostics:true,compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}});
    assert.equal((result.diagnostics||[]).filter(d=>d.category===ts.DiagnosticCategory.Error).length,0,relative);
    const exports={};cache.set(absolute,exports);
    vm.runInNewContext(result.outputText,{exports,console,window:browser,localStorage:local,URLSearchParams,setTimeout:setTimer,clearTimeout:clearTimer,fetch:()=>{throw new Error('NETWORK FORBIDDEN')},require:spec=>{
      if(spec==='react'||spec==='react/jsx-runtime')return require(spec);
      if(spec.endsWith('/order-api'))return {orderApi};
      if(spec.endsWith('/OrderRuntimeBridge'))return {useOrderRuntime:()=>rt,RuntimeBadge:()=>null};
      if(spec.endsWith('/order-runtime'))return {runtimeActions:new Proxy({}, {get:()=>()=>{throw new Error('MUTATION FORBIDDEN')}})};
      if(spec.endsWith('/personal-agent-order-sync'))return {syncMatterMatched:()=>{throw new Error('Unexpected match sync')}};
      if(spec.endsWith('/personal-agent-handoff-persist'))return {ensureStructuredHandoff:async()=>{calls.push({name:'handoff'})}};
      const file=path.resolve(path.dirname(absolute),spec);
      const found=['.ts','.tsx'].map(ext=>file+ext).find(p=>fs.existsSync(p));
      assert.ok(found,`Unexpected import ${spec}`);return load(path.relative(root,found));
    }},{filename:relative});
    return exports;
  }
  let renderer,Component;
  const f={calls,navigations,local,browser,rt,snapshot,load,
    async mount(file='app/connect-pass/page.tsx'){Component=load(file).default;await act(async()=>{renderer=create(React.createElement(Component));});},
    async rerender(){await act(async()=>renderer.update(React.createElement(Component)));},
    async tick(ms){await act(async()=>{now+=ms;for(const [key,t] of [...timers])if(t.at<=now){timers.delete(key);t.fn();}});},
    async click(button){await act(async()=>{void button.props.onClick();});},
    buttons(){return renderer.root.findAllByType('button');},
    buy(){return f.buttons().find(b=>b.props.style?.width==='100%');},
    recheck(){return f.buttons().find(b=>String(b.props.children).includes('重新查询'));},
    text(){return JSON.stringify(renderer.toJSON());},
    links(){return renderer.root.findAllByType('a').map(a=>a.props.href);},
    async stop(){if(renderer)await act(async()=>renderer.unmount());timers.clear();},
  };
  fixtures.push(f);return f;
}
const flush=async()=>act(async()=>{});
let passed=0;
async function test(name,fn){try{await fn();passed++;console.log(`PASS ${name}`)}finally{for(const f of fixtures.splice(0))await f.stop();}}
(async()=>{
  await test('pending existing-order read disables purchase and keeps return link',async()=>{
    const d=deferred(),f=fixture({saved:true,api:{getOrder:()=>d.promise}});await f.mount();assert.equal(f.buy().props.disabled,true);await f.click(f.buy());assert.equal(f.calls.length,1);assert.ok(f.links().includes('/planning'));
  });
  await test('initial GET timeout shows recovery; late result cannot unlock purchase',async()=>{
    const d=deferred(),f=fixture({saved:true,api:{getOrder:()=>d.promise}});await f.mount();await f.tick(20001);assert.match(f.text(),/原订单未能加载/);d.resolve(f.snapshot);await flush();assert.equal(f.buy().props.disabled,true);assert.equal(f.calls.filter(c=>c.name==='createOrder').length,0);
  });
  await test('failed existing-order read never falls through to creating another order',async()=>{
    const f=fixture({saved:true,api:{getOrder:async()=>{throw new Error('403')}}});await f.mount();await f.click(f.buy());assert.match(f.text(),/原订单未能加载/);assert.equal(f.calls.filter(c=>c.name==='createOrder').length,0);
  });
  await test('recovery is GET only; confirmed paid state exposes original-order link',async()=>{
    let n=0;const f=fixture({saved:true,api:{getOrder:async()=>{if(++n===1)throw new Error('timeout');return {...f.snapshot,connectPaid:true,matched:true};}}});await f.mount();await f.click(f.recheck());assert.deepEqual(f.calls.map(c=>c.name),['getOrder','getOrder']);assert.equal(f.navigations.length,0);assert.match(f.text(),/服务器已确认/);assert.ok(f.links().includes('/customer-order-live?order=order-offline'));assert.equal(f.buy().props.disabled,true);
  });
  await test('unpaid recovery does not declare payment failure or reopen purchase',async()=>{
    let n=0;const f=fixture({saved:true,api:{getOrder:async()=>{if(++n===1)throw new Error('timeout');return f.snapshot;}}});await f.mount();await f.click(f.recheck());assert.match(f.text(),/这不是付款失败证明/);assert.equal(f.buy().props.disabled,true);assert.equal(f.navigations.length,0);
  });
  await test('wrong-order or malformed GET cannot unlock purchase',async()=>{
    for(const response of [{id:'different',connectPaid:true},{id:'order-offline'}]){const f=fixture({saved:true,api:{getOrder:async()=>response}});await f.mount();assert.equal(f.buy().props.disabled,true);assert.match(f.text(),/原订单未能加载/);}
  });
  await test('guest keeps original purchase login destination and no order requests',async()=>{
    const f=fixture({token:''});await f.mount();assert.equal(f.navigations[0],'/client-login?resume=1&reason=purchase');assert.equal(f.calls.length,0);assert.ok(f.links().includes('/planning'));
  });
  await test('fresh healthy request uses original order + checkout sequence once',async()=>{
    const f=fixture();await f.mount();assert.equal(f.buy().props.disabled,false);const button=f.buy();await act(async()=>{void button.props.onClick();void button.props.onClick();});assert.deepEqual(f.calls.map(c=>c.name),['createOrder','createConnectCheckout']);assert.equal(f.navigations[0],'https://checkout.invalid/offline');assert.equal(f.browser.sessionStorage.getItem(GUARD),'offline-session');
  });
  await test('hanging create keeps purchase disabled and shows outcome-unknown warning',async()=>{
    const d=deferred(),f=fixture({api:{createOrder:()=>d.promise}});await f.mount();await f.click(f.buy());await f.tick(20001);assert.match(f.text(),/操作结果尚未确定/);assert.equal(f.buy().props.disabled,true);await f.click(f.buy());assert.deepEqual(f.calls.map(c=>c.name),['createOrder']);assert.ok(f.links().includes('/planning'));
  });
  await test('reload guard with no known order prevents duplicate creation',async()=>{
    const f=fixture({session:{[GUARD]:'offline-session'}});await f.mount();assert.match(f.text(),/本地没有可核对的订单号/);await f.click(f.buy());assert.equal(f.calls.length,0);assert.equal(f.buy().props.disabled,true);
  });
  await test('guard from another planning context does not prevent a fresh request',async()=>{
    const f=fixture({session:{[GUARD]:'different-session'}});await f.mount();assert.equal(f.buy().props.disabled,false);
  });
  await test('storage failure blocks purchase instead of losing recovery marker',async()=>{
    const f=fixture();await f.mount();f.browser.sessionStorage.setItem=()=>{throw new Error('Quota')};await f.click(f.buy());assert.equal(f.calls.length,0);assert.match(f.text(),/已暂停购买/);
  });
  await test('cancelled return provides GET recovery, no automatic checkout or match',async()=>{
    const f=fixture({saved:true,search:'?payment=cancelled&order=order-offline'});await f.mount();assert.equal(f.calls.length,0);await f.click(f.recheck());assert.deepEqual(f.calls.map(c=>c.name),['getOrder']);assert.equal(f.buy().props.disabled,true);
  });
  await test('previous checkout journey locks purchase while state is queried',async()=>{
    const f=fixture({saved:true});f.local.setItem(JOURNEY,JSON.stringify({orderId:'order-offline',planningSessionId:'offline-session',step:'connect_checkout_started'}));await f.mount();assert.equal(f.buy().props.disabled,true);assert.deepEqual(f.calls.map(c=>c.name),['getOrder']);
  });
  await test('healthy existing unpaid order reuses original order, never creates another',async()=>{
    const f=fixture({saved:true});await f.mount();assert.equal(f.buy().props.disabled,false);await f.click(f.buy());assert.deepEqual(f.calls.map(c=>c.name),['getOrder','createConnectCheckout']);
  });
  await test('already-paid matched order keeps existing destination and performs no checkout',async()=>{
    const f=fixture({saved:true,api:{getOrder:async()=>({...f.snapshot,connectPaid:true,matched:true})}});await f.mount();assert.deepEqual(f.calls.map(c=>c.name),['getOrder']);assert.deepEqual(f.navigations,['/customer-order-live?order=order-offline']);
  });
  await test('session change during a recovery read does not expose or accept its result',async()=>{
    const d=deferred();let n=0;const f=fixture({saved:true,api:{getOrder:async()=>{if(++n===1)throw new Error('initial failure');return d.promise;}}});await f.mount();await f.click(f.recheck());f.local.setItem('client_token','different-offline-identity');d.resolve({...f.snapshot,connectPaid:true});await flush();assert.match(f.text(),/无法确认原订单状态/);assert.ok(!f.text().includes('服务器已确认'));assert.equal(f.navigations.length,0);
  });
  await test('query timeout can be retried without any business mutations',async()=>{
    let n=0;const d=deferred();const f=fixture({saved:true,api:{getOrder:async()=>{n++;if(n===1)throw new Error('initial failure');if(n===2)return d.promise;return f.snapshot;}}});await f.mount();await f.click(f.recheck());await f.tick(20001);assert.match(f.text(),/无法确认原订单状态/);await f.click(f.recheck());assert.equal(f.calls.length,3);assert.ok(f.calls.every(c=>c.name==='getOrder'));assert.equal(f.buy().props.disabled,true);
  });
  await test('page return navigation is sticky, same-origin, and has no mutation handler',async()=>{
    const f=fixture();await f.mount('app/components/CustomerRecoveryNav.tsx');assert.deepEqual(f.links(),['/planning']);assert.match(f.text(),/sticky/);assert.equal(f.calls.length,0);
  });
  await test('order page missing data hides fake zero price, progress, and transaction controls',async()=>{
    const f=fixture();await f.mount('app/customer-order-live/page.tsx');assert.match(f.text(),/正在查询订单/);assert.ok(!f.text().includes('Professional Service Fee'));assert.ok(!f.text().includes('Confirm Completion'));assert.ok(f.links().includes('/planning'));await f.tick(20001);assert.match(f.text(),/订单暂未加载/);
  });
  await test('order page read-only retry timeout is visible and re-enables query',async()=>{
    const f=fixture({runtime:{refresh:()=>new Promise(()=>{})}});await f.mount('app/customer-order-live/page.tsx');await f.click(f.recheck());await f.tick(20001);assert.match(f.text(),/状态查询仍未完成/);assert.equal(f.recheck().props.disabled,false);
  });
  await test('loaded matched order awaiting estimate does not present zero as a quote',async()=>{
    const f=fixture();f.rt.data={mode:'api',order:{...f.snapshot,matched:true}};f.rt.loading=false;await f.mount('app/customer-order-live/page.tsx');assert.match(f.text(),/Awaiting estimate/);assert.match(f.text(),/Matched with a Professional/);
  });
  await test('payment return query alone does not announce successful payment',async()=>{
    const f=fixture({search:'?payment=success&order=order-offline'});await f.mount('app/customer-order-live/page.tsx');f.rt.data={mode:'api',order:f.snapshot};await f.rerender();assert.match(f.text(),/a redirect alone does not confirm payment/);assert.ok(!f.text().includes('Payment successful.'));
  });
  await test('order runtime refresh error has visible query action without writes',async()=>{
    const f=fixture();f.rt.data={mode:'api',order:f.snapshot};f.rt.error='offline error';await f.mount('app/customer-order-live/page.tsx');assert.match(f.text(),/上次加载的订单信息/);await f.click(f.recheck());assert.deepEqual(f.calls.map(c=>c.name),['refresh']);
  });
  await test('protected business handlers are byte-identical to approved parent',()=>{
    const expected=JSON.parse(fs.readFileSync(path.join(root,'scripts/order-recovery-protected.json'),'utf8'));
    for(const [file,names] of Object.entries(expected)){
      const source=fs.readFileSync(path.join(root,file),'utf8'),sf=ts.createSourceFile(file,source,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX),found={};
      function visit(node){if(ts.isFunctionDeclaration(node)&&node.name&&node.name.text in names)found[node.name.text]=crypto.createHash('sha256').update(node.getText(sf)).digest('hex');ts.forEachChild(node,visit);}
      visit(sf);assert.deepEqual(found,names,file);
    }
  });
  console.log(`${passed} offline recovery tests passed. No live browser/API/payment acceptance claimed.`);
})().catch(error=>{console.error(error);process.exitCode=1;});
