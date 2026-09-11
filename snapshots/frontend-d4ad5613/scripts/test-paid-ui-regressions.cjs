// Focused regressions; fixture harness copied unchanged from test-order-recovery.cjs.
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
let passed=0,failed=0;
async function test(name,fn){
  try{await fn();passed++;console.log('PASS '+name);}
  catch(error){failed++;console.error('FAIL '+name+'\n'+error.stack);}
  finally{for(const f of fixtures.splice(0))await f.stop();}
}
function counts(f){return Object.fromEntries(['getOrder','requestMatch','createOrder','createConnectCheckout'].map(name=>[name,f.calls.filter(c=>c.name===name).length]));}
function flat(node){if(node==null)return '';if(typeof node==='string')return node;if(Array.isArray(node))return node.map(flat).join('');return flat(node.children);}
function findNode(node,predicate){
  if(!node||typeof node==='string')return null;
  if(Array.isArray(node)){for(const child of node){const found=findNode(child,predicate);if(found)return found;}return null;}
  return predicate(node)?node:findNode(node.children,predicate);
}
async function paidFixture({matched=true,matchMode='success'}={}){
  let current;
  const pending=deferred();
  const f=fixture({saved:true,api:{
    getOrder:async()=>({...current}),
    requestMatch:async()=>{
      if(matchMode==='pending')return pending.promise;
      if(matchMode==='failure')throw new Error('offline match unavailable');
      current={...current,matched:true};return {...current};
    },
  }});
  current={...f.snapshot,connectPaid:true,matched};
  // Retain the old order_created journey and keep the renderer mounted even
  // after location.replace. Do not assume navigation makes clicks impossible.
  await f.mount();await flush();
  return f;
}
function noNewCalls(f,before){assert.deepEqual(counts(f),before);assert.equal(f.calls.filter(c=>/create/.test(c.name)).length,0);}
(async()=>{
  await test('paid matched saved order disables purchase while navigation has not unloaded page',async()=>{
    const f=await paidFixture();assert.equal(f.navigations.length,1);
    assert.equal(f.buy().props.disabled,true);
    assert.equal(f.buy().props.style.opacity,0.6);
  });
  await test('paid matched purchase handler refuses direct/repeated invocation',async()=>{
    const f=await paidFixture(),before=counts(f),nav=f.navigations.length;
    // Direct invocation intentionally tests the handler guard independently
    // of native disabled-button behavior.
    const handler=f.buy().props.onClick;
    await act(async()=>{void handler();void handler();});await flush();
    noNewCalls(f,before);assert.equal(f.navigations.length,nav);
    assert.equal(f.browser.sessionStorage.getItem(GUARD),null);
  });
  await test('paid unmatched auto-match remains once; completed match cannot reopen purchase',async()=>{
    const f=await paidFixture({matched:false});
    assert.deepEqual(counts(f),{getOrder:2,requestMatch:1,createOrder:0,createConnectCheckout:0});
    assert.equal(f.buy().props.disabled,true);assert.equal(f.navigations.length,1);
  });
  await test('after auto-match completes, purchase handler cannot start a second verification',async()=>{
    const f=await paidFixture({matched:false}),before=counts(f),nav=f.navigations.length;
    await f.click(f.buy());await f.click(f.buy());noNewCalls(f,before);
    assert.equal(f.navigations.length,nav);
  });
  for(const matchMode of ['pending','failure']){
    await test('paid unmatched '+matchMode+' match keeps purchase blocked',async()=>{
      const f=await paidFixture({matched:false,matchMode}),before=counts(f);
      assert.equal(f.buy().props.disabled,true);await f.click(f.buy());noNewCalls(f,before);
      assert.equal(f.navigations.length,0);assert.equal(before.requestMatch,1);
    });
  }
  for(const invoiceStatus of ['unpaid','pending','paid',undefined,null,'unrecognized']){
    await test('invoice Payment Status reflects '+String(invoiceStatus)+' independently of connectPaid and success URL',async()=>{
      const f=fixture({search:'?payment=success&order=order-offline'});
      f.rt.data={mode:'api',order:{...f.snapshot,amount:500,stage:'accepted',connectPaid:true,matched:true,
        invoice:{id:'invoice-offline',invoiceNumber:'OFFLINE-1',serviceTitle:'Insurance',amount:500,status:invoiceStatus}}};
      f.rt.loading=false;await f.mount('app/customer-order-live/page.tsx');
      const tree=JSON.parse(f.text());
      const statusRow=findNode(tree,n=>n.type==='div'&&n.children?.some(c=>c?.type==='span'&&flat(c)==='Payment Status'));
      assert.ok(statusRow,'Payment Status row must exist');
      const statusValue=statusRow.children.find(c=>c?.type==='b');
      const paid=invoiceStatus==='paid';
      assert.equal(flat(statusValue),paid?'✓ Paid':'Pending');
      assert.equal(statusValue.props.style.color,paid?'#86efac':'#8a8494');
      const progressRow=findNode(tree,n=>n.type==='div'&&n.children?.some(c=>c?.type==='b'&&flat(c)==='Professional Service Fee Paid'));
      assert.ok(progressRow,'service payment progress row must exist');
      assert.equal(flat(progressRow.children.find(c=>c?.type==='span')),paid?'✓':'');
      assert.match(flat(tree),/a redirect alone does not confirm payment/);
      assert.ok(f.calls.every(c=>c.name==='refresh'),'render/return must not mutate');
    });
  }
  await test('healthy unpaid saved order can still create one Checkout via original handler',async()=>{
    const f=fixture({saved:true});await f.mount();assert.equal(f.buy().props.disabled,false);
    const handler=f.buy().props.onClick;await act(async()=>{void handler();void handler();});
    assert.deepEqual(counts(f),{getOrder:1,requestMatch:0,createOrder:0,createConnectCheckout:1});
    assert.deepEqual(f.navigations,['https://checkout.invalid/offline']);
  });
  console.log(passed+' passed / '+failed+' failed. Offline paid-UI regressions only.');
  if(failed)process.exitCode=1;
})().catch(error=>{console.error(error);process.exitCode=1;});

