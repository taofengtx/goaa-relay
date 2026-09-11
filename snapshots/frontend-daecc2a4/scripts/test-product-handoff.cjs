// Offline tests: transpile actual TSX and execute it with hook/JSX test doubles.
// No browser, real API, payment or application startup. Not full UI acceptance.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'app/components/ChatComponent.tsx'), 'utf8');
const stateNames = [...source.matchAll(/const \[(\w+),\s*\w+\] = useState/g)].map(m => m[1]);
function transpile(text, name) {
  const result = ts.transpileModule(text, {fileName: name, reportDiagnostics: true, compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX,
  }});
  assert.equal((result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error).length, 0);
  return result.outputText;
}
function load(text, name, imports, globals = {}) {
  const exports = {};
  vm.runInNewContext(transpile(text, name), {exports, require: id => {
    assert.ok(id in imports, `Unexpected import: ${id}`); return imports[id];
  }, console, ...globals}, {filename: name});
  return exports;
}
const jsx = {jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props}), Fragment: 'Fragment'};
function walk(node, predicate, found = []) {
  if (!node || typeof node !== 'object') return found;
  if (Array.isArray(node)) {node.forEach(n => walk(n, predicate, found)); return found;}
  if (predicate(node)) found.push(node);
  walk(node.props?.children, predicate, found);
  return found;
}
function fixture(initial = {}, reply = {}) {
  let index = 0;
  const state = {...initial};
  const storage = new Map();
  const navigations = [];
  const requests = [];
  const imports = {
    react: {useMemo: fn => fn(), useEffect: () => {}, useState: value => {
      const key = stateNames[index++];
      if (!(key in state)) state[key] = typeof value === 'function' ? value() : value;
      return [state[key], next => {state[key] = typeof next === 'function' ? next(state[key]) : next;}];
    }},
    'react/jsx-runtime': jsx,
    '../lib/openclaw': {chat: async (...args) => {requests.push(args); return {
      sessionId: 'offline-session', stage: 'intake', intent: 'tax_planning', knownFacts: {}, displayTitle: 'Tax',
      subIntent: null, response: 'Offline test response', connectionReady: false, productAction: null, ...reply,
    };}},
    '../lib/personal-agent-matter': {LEGACY_WORKSPACE_KEY: 'goaa_planning_workspace_v1', MATTER_RESTORE_EVENT: 'restore'},
    '../lib/customer-signout': {clearCustomerSession: () => ({})},
  };
  for (const name of ['ProfessionalHandoffCard','ButlerMattersView','ButlerWelcome','PersonalAgentInbox','PersonalAgentKnowledge','AgentProblemSolvingModel','AgentMattersOverview','LoginMenu']) imports[`./${name}`] = {default: name};
  const browser = {localStorage: {getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key)}, location: {assign: url => navigations.push(url)}};
  const component = load(source, 'ChatComponent.tsx', imports, {window: browser}).default;
  const render = () => {index = 0; return component({butlerMode: true});};
  const cards = tree => walk(tree, n => n.type === 'ProfessionalHandoffCard');
  return {state, storage, navigations, requests, render, cards};
}
let passed = 0;
async function test(name, fn) {await fn(); passed++; console.log(`PASS ${name}`);}
(async () => {
  await test('explicit server signal shows card with zero facts and no intent', () => {
    const f = fixture({connectionReady: true}); assert.equal(f.cards(f.render()).length, 1);
    assert.equal(f.navigations.length, 0);
  });
  await test('old backend stage also reveals card', () => {
    const f = fixture({stage: 'connection_ready'}); assert.equal(f.cards(f.render()).length, 1);
  });
  await test('ordinary low-fact chat does not offer pass', () => {
    const f = fixture({intent: 'tax_planning'}); assert.equal(f.cards(f.render()).length, 0);
  });
  await test('declined offer stays dismissed', () => {
    const f = fixture({connectionReady: true, handoffDismissed: true}); assert.equal(f.cards(f.render()).length, 0);
  });
  await test('actual submitPrompt consumes ready signal without navigating', async () => {
    const f = fixture({message: '可以对接经纪人了', handoffDismissed: true}, {connectionReady: true, stage: 'connection_ready'});
    const form = walk(f.render(), n => n.type === 'form' && n.props.className === 'workspace-composer')[0];
    await form.props.onSubmit({preventDefault(){}});
    assert.equal(f.requests.length, 1); assert.equal(f.requests[0][1], '可以对接经纪人了');
    assert.equal(f.cards(f.render()).length, 1); assert.equal(f.navigations.length, 0);
  });
  await test('fee response alone does not create a card or navigate', async () => {
    const f = fixture({message: '39.9是干什么的'}, {productAction: 'fee_info'});
    const form = walk(f.render(), n => n.type === 'form' && n.props.className === 'workspace-composer')[0];
    await form.props.onSubmit({preventDefault(){}});
    assert.equal(f.cards(f.render()).length, 0); assert.equal(f.navigations.length, 0);
  });
  await test('explicit decline hides previously offered card', async () => {
    const f = fixture({message: '不要对接', connectionReady: true}, {productAction: 'decline'});
    const form = walk(f.render(), n => n.type === 'form' && n.props.className === 'workspace-composer')[0];
    await form.props.onSubmit({preventDefault(){}});
    assert.equal(f.cards(f.render()).length, 0); assert.equal(f.navigations.length, 0);
  });
  await test('fee question does not reopen a dismissed connection offer', async () => {
    const f = fixture({message: '39.9能做什么', connectionReady: true, handoffDismissed: true}, {productAction: 'fee_info', connectionReady: true, stage: 'connection_ready'});
    const form = walk(f.render(), n => n.type === 'form' && n.props.className === 'workspace-composer')[0];
    await form.props.onSubmit({preventDefault(){}});
    assert.equal(f.cards(f.render()).length, 0); assert.equal(f.navigations.length, 0);
  });
  await test('logged-in click uses existing connect-pass route', () => {
    const f = fixture({connectionReady: true}); f.storage.set('client_token', 'offline-display-token');
    f.cards(f.render())[0].props.onConnect();
    assert.equal(f.navigations[0], '/connect-pass?source=planning');
    assert.equal(f.requests.length, 0);
  });
  await test('guest click preserves existing auth return', () => {
    const f = fixture({connectionReady: true}); f.cards(f.render())[0].props.onConnect();
    assert.equal(f.navigations[0], '/client-login?resume=1&reason=purchase');
    assert.equal(f.storage.get('goaa_auth_return_v1'), '/connect-pass?source=planning');
  });
  await test('API decoder preserves actual boolean readiness and old payload defaults', async () => {
    const text = fs.readFileSync(path.join(root, 'app/lib/openclaw.ts'), 'utf8');
    for (const [payload, expected] of [[{connection_ready: true, product_action: 'fee_info'}, true], [{connection_ready: 'true'}, false], [{}, false]]) {
      const api = load(text, 'openclaw.ts', {}, {process: {env: {}}, fetch: async (url, options) => {
        assert.equal(url, 'https://api.goaa.ai/api/v1/chat');
        assert.deepEqual(JSON.parse(options.body), {user_id: 'offline', message: 'test', session_id: 'session'});
        return {ok: true, json: async () => payload};
      }});
      assert.equal((await api.chat('offline', 'test', 'session')).connectionReady, expected);
    }
  });
  await test('fee copy separates platform and professional charges', () => {
    const text = fs.readFileSync(path.join(root, 'app/components/ProfessionalHandoffCard.tsx'), 'utf8');
    const card = load(text, 'ProfessionalHandoffCard.tsx', {'react/jsx-runtime': jsx}).default;
    const tree = JSON.stringify(card({lang: 'zh', facts: {}, onConnect(){}, onContinue(){}}));
    for (const value of ['$39.90', '美元', '30 天', '不自动续费', '不包含报税', '经您确认']) assert.ok(tree.includes(value));
  });
  await test('auth and purchase handlers match baseline hashes', () => {
    const expected = JSON.parse(fs.readFileSync(path.join(root, 'scripts/product-handoff-protected.json')));
    const sf = ts.createSourceFile('ChatComponent.tsx', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const found = {};
    function visit(node) {
      if (ts.isFunctionDeclaration(node) && node.name && node.name.text in expected) found[node.name.text] = crypto.createHash('sha256').update(node.getText(sf)).digest('hex');
      ts.forEachChild(node, visit);
    }
    visit(sf); assert.deepEqual(found, expected);
  });
  console.log(`${passed} offline frontend checks passed; no browser/API/payment acceptance claimed.`);
})().catch(error => {console.error(error); process.exitCode = 1;});
