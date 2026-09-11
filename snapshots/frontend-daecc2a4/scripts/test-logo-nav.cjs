// Customer home-logo navigation tests (2026-09-04).
// The top-left GOAA.ai brand must be a real <a> to https://goaa.ai/ opening in
// the SAME tab, with an explicit accessible name, native keyboard activation,
// no storage cleanup, no navigation handler side effects, and zero
// order/match/checkout/payment requests.
// Static render of the actual ChatComponent TSX via transpile + JSX doubles;
// no browser, no network, no API / DB / payment.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
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
function walk(node, predicate, found = []) {
  if (!node || typeof node !== 'object') return found;
  if (Array.isArray(node)) {node.forEach(n => walk(n, predicate, found)); return found;}
  if (predicate(node)) found.push(node);
  walk(node.props?.children, predicate, found);
  return found;
}
function brandLink(node) {
  return walk(node, n => n.type === 'a' && n.props?.className === 'goaa-brand');
}
let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log(`PASS ${name}`); }

(async () => {
  let index = 0;
  const storage = new Map();
  const navigations = [];
  const requests = [];
  const state = {};
  const jsx = {jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props}), Fragment: 'Fragment'};
  const imports = {
    react: {useMemo: fn => fn(), useEffect: () => {}, useState: value => {
      const key = stateNames[index++];
      if (!(key in state)) state[key] = typeof value === 'function' ? value() : value;
      return [state[key], next => {state[key] = typeof next === 'function' ? next(state[key]) : next;}];
    }},
    'react/jsx-runtime': jsx,
    '../lib/openclaw': {chat: async (...args) => {requests.push(args); return {
      sessionId: 's', stage: 'intake', intent: 'tax_planning', knownFacts: {},
      displayTitle: 'Tax', subIntent: null, response: 'x', connectionReady: false, productAction: null,
    };}},
    '../lib/personal-agent-matter': {LEGACY_WORKSPACE_KEY: 'goaa_planning_workspace_v1', MATTER_RESTORE_EVENT: 'restore'},
    '../lib/customer-signout': {clearCustomerSession: () => ({})},
  };
  for (const name of ['ProfessionalHandoffCard','ButlerMattersView','ButlerWelcome','PersonalAgentInbox','PersonalAgentKnowledge','AgentProblemSolvingModel','AgentMattersOverview','LoginMenu']) imports[`./${name}`] = {default: name};
  const browser = {
    localStorage: {getItem: k => storage.get(k) || null, setItem: (k, v) => storage.set(k, v), removeItem: k => storage.delete(k)},
    location: {assign: url => navigations.push(url)},
  };
  const exports = {};
  vm.runInNewContext(transpile(source, 'ChatComponent.tsx'), {
    exports, require: id => { assert.ok(id in imports, `Unexpected import: ${id}`); return imports[id]; },
    console, window: browser,
  }, {filename: 'ChatComponent.tsx'});
  const ChatComponent = exports.default;
  const render = () => { index = 0; return ChatComponent({butlerMode: true}); };

  await test('brand is an <a> link, not a button', () => {
    const links = brandLink(render());
    assert.equal(links.length, 1);
    assert.equal(links[0].props.href, 'https://goaa.ai/');
    assert.equal(links[0].props['aria-label'], 'AI Butler home');
  });
  await test('opens in current tab (no target=_blank, no external window props)', () => {
    const link = brandLink(render())[0];
    assert.equal(link.props.target, undefined);
    assert.equal(link.props.rel, undefined);
    assert.equal(link.props.onClick, undefined);
  });
  await test('keyboard accessible native link (focusable, not disabled, no tabIndex trap)', () => {
    const link = brandLink(render())[0];
    assert.equal(link.props.disabled, undefined);
    assert.equal(link.props.tabIndex, undefined);
    assert.equal(link.props['aria-hidden'], undefined);
  });
  await test('brand content = round mark + AI Butler wordmark (no GOAA.ai)', () => {
    const text = JSON.stringify(brandLink(render())[0].props.children);
    assert.ok(text.includes('goaa-mark'));
    assert.ok(text.includes('goaa-brand-text'), 'brand-text span present');
    assert.ok(text.includes('AI Butler'));
    assert.ok(text.includes('"G"') || text.includes('>G<') || text.includes('children:"G"'));
    assert.ok(!text.includes('GOAA.ai'));
  });
  await test('no onClick handler -> click does not clear draft/nickname/storage or navigate by JS', () => {
    const link = brandLink(render())[0];
    assert.equal(link.props.onClick, undefined);
    assert.equal(storage.size, 0);
    assert.equal(navigations.length, 0);
    assert.equal(requests.length, 0);
  });
  await test('render issues zero order/match/checkout/payment requests', () => {
    render();
    assert.equal(requests.length, 0);
    assert.equal(navigations.length, 0);
    assert.equal(storage.size, 0);
  });
  await test('For Professionals/Sign in direct anchors replaced by LoginMenu ghost', () => {
    const tree = render();
    assert.equal(walk(tree, n => n.type === 'a' && n.props.href === '/client-login').length, 0);
    assert.equal(walk(tree, n => n.type === 'a' && n.props.href === '/agent-login').length, 0);
    const menus = walk(tree, n => n.type === 'LoginMenu');
    assert.equal(menus.length, 1);
    assert.equal(menus[0].props.variant, 'ghost');
    assert.equal(menus[0].props.signedIn, false);
    assert.equal(typeof menus[0].props.onLogout, 'function');
  });
  console.log(`OK ${passed}/${passed} logo-navigation tests passed.`);
})().catch(err => { console.error(err); process.exit(1); });
