// client-logout + Cal.com card offline tests (2026-09-04).
// Static source contracts for /client-logout (fixed destination, enum-only
// return, reuses lib clearCustomerSession, no storage.clear, zero business
// endpoints), RTR behavior in signed-in / signed-out / repeated entry,
// Cal.com card exact URL/new-tab/keyboard/no-side-effects, and homepage
// account-menu constraints (no cross-origin login read) are covered.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const {create, act} = require('react-test-renderer');
const root = path.resolve(__dirname, '..');
const sourceChat = fs.readFileSync(path.join(root, 'app/components/ChatComponent.tsx'), 'utf8');
const stateNames = [...sourceChat.matchAll(/const \[(\w+),\s*\w+\] = useState/g)].map(m => m[1]);

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
let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log(`PASS ${name}`); }

// ---------- /client-logout static contracts ----------
const pageSrc = fs.readFileSync(path.join(root, 'app/client-logout/page.tsx'), 'utf8');
const libSrc = fs.readFileSync(path.join(root, 'app/lib/customer-signout.ts'), 'utf8');
const cookieSrc = fs.readFileSync(path.join(root, 'app/lib/goaa-cookie.ts'), 'utf8');
function loadCookieMod() {
  const cookieMod = {};
  vm.runInNewContext(transpile(cookieSrc, 'goaa-cookie.ts'), {
    exports: cookieMod, require: () => { throw new Error('cookie has no imports'); }, console,
  }, {filename: 'goaa-cookie.ts'});
  return cookieMod;
}

(async () => {
  await test('logout page reuses lib clearCustomerSession, no duplicate logic', () => {
    assert.match(pageSrc, /import\s*\{[^}]*clearCustomerSession[^}]*\}\s*from\s*'\.\.\/lib\/customer-signout'/);
    assert.doesNotMatch(pageSrc, /removeItem\s*\(/);  // removal stays in the lib
    assert.doesNotMatch(pageSrc, /localStorage\.clear|sessionStorage\.clear/);
    assert.doesNotMatch(libSrc, /localStorage\.clear|sessionStorage\.clear/);
  });
  await test('fixed destination only and no open redirect', () => {
    assert.match(pageSrc, /https:\/\/goaa\.ai\/\?logged_out=1/);
    assert.match(pageSrc, /window\.location\.assign\(HOME_AFTER_LOGOUT\)/);
    assert.doesNotMatch(pageSrc, /assign\([^)]*params/);
    assert.doesNotMatch(pageSrc, /assign\([^)]*requested/);
    assert.match(pageSrc, /ALLOWED_RETURN_VALUES/);
    assert.match(pageSrc, /'home'/);
  });
  await test('logout page never calls business endpoints', () => {
    for (const token of ['/orders/', '/match', '/checkout', '/payments', '/webhook', 'fetch(', 'openclaw']) {
      assert.ok(!pageSrc.includes(token), `unexpected ${token} in client-logout`);
    }
  });
  await test('status message + accessible role present', () => {
    assert.match(pageSrc, /正在安全退出/);
    assert.match(pageSrc, /role="status"/);
  });

  // ---------- behavior via real RTR mount (isolated react 18.3.1) ----------
  function makeWindow(seed = {}) {
    const data = new Map(Object.entries(seed));
    const navs = [];
    const requests = [];
    const session = new Map();
    const local = {
      getItem: k => data.has(k) ? data.get(k) : null,
      setItem: (k, v) => data.set(k, String(v)),
      removeItem: k => data.delete(k),
    };
    const sess = {
      getItem: k => session.has(k) ? session.get(k) : null,
      setItem: (k, v) => session.set(k, String(v)),
      removeItem: k => session.delete(k),
    };
    return {
      data, session, navs, requests,
      localStorage: local, sessionStorage: sess,
      location: {search: '?return=home', assign: u => navs.push(u)},
      setTimeout: cb => { cb(); return 1; },
      clearTimeout: () => {},
    };
  }
  async function mountPage(seed) {
    const win = makeWindow(seed);
    const libExports = {};
    vm.runInNewContext(transpile(libSrc, 'lib/customer-signout.ts'), {
      exports: libExports, require: id => { assert.equal(id, './goaa-cookie'); return loadCookieMod(); }, console,
    }, {filename: 'lib/customer-signout.ts'});
    const imports = {
      react: React,
      'react/jsx-runtime': require('react/jsx-runtime'),
      '../lib/customer-signout': libExports,
      '../lib/golden-signout': { decideGoldenSignOut: async () => ({ status: 'legacy' }) },
    };
    const exports = {};
    vm.runInNewContext(transpile(pageSrc, 'client-logout/page.tsx'), {
      exports, require: id => { assert.ok(id in imports, `Unexpected import: ${id}`); return imports[id]; },
      console, window: win, URLSearchParams,
    }, {filename: 'client-logout/page.tsx'});
    let renderer;
    await act(async () => { renderer = create(React.createElement(exports.default)); });
    return {win, renderer};
  }
  const seedIdentity = {
    client_token: 'tk', client_username: 'user@test', goaa_active_order_id: 'o1',
    goaa_customer_e2e_journey_v1: '{"x":1}', goaa_planning_workspace_v1: 'draft',
    'goaa_butler_display_name_v1:user@test': '管家甲', pref: '1',
  };

  await test('signed-in logout clears identity/order, keeps draft+nick, migrates to guest, fixed nav', async () => {
    const {win} = await mountPage(seedIdentity);
    assert.equal(win.data.get('client_token'), undefined);
    assert.equal(win.data.get('client_username'), undefined);
    assert.equal(win.data.get('goaa_active_order_id'), undefined);
    assert.equal(win.data.get('goaa_customer_e2e_journey_v1'), undefined);
    assert.equal(win.data.get('goaa_planning_workspace_v1'), 'draft');
    assert.equal(win.data.get('pref'), '1');
    assert.equal(win.data.get('goaa_butler_display_name_v1:guest'), '管家甲');
    assert.deepEqual(win.navs, ['https://goaa.ai/?logged_out=1']);
    assert.equal(win.requests.length, 0);
  });
  await test('signed-out (guest) entry is safe and still returns home', async () => {
    const {win} = await mountPage({goaa_planning_workspace_v1: 'draft', pref: '1'});
    assert.equal(win.data.get('goaa_planning_workspace_v1'), 'draft');
    assert.equal(win.data.get('pref'), '1');
    assert.deepEqual(win.navs, ['https://goaa.ai/?logged_out=1']);
  });
  await test('repeated entry is idempotent', async () => {
    const a = await mountPage(seedIdentity);
    const b = await mountPage(Object.fromEntries(a.win.data.entries()));
    assert.equal(b.win.data.get('client_token'), undefined);
    assert.equal(b.win.data.get('goaa_planning_workspace_v1'), 'draft');
    assert.equal(b.win.data.get('goaa_butler_display_name_v1:guest'), '管家甲');
    assert.deepEqual(b.win.navs, ['https://goaa.ai/?logged_out=1']);
  });
  await test('invalid return value ignored (no external navigation)', async () => {
    const win = makeWindow(seedIdentity);
    win.location.search = '?return=https://evil.example';
    const libExports2 = {};
    vm.runInNewContext(transpile(libSrc, 'lib/customer-signout.ts'), {
      exports: libExports2, require: id => { assert.equal(id, './goaa-cookie'); return loadCookieMod(); }, console,
    }, {filename: 'lib/customer-signout.ts'});
    const imports = {
      react: React,
      'react/jsx-runtime': require('react/jsx-runtime'),
      '../lib/customer-signout': libExports2,
      '../lib/golden-signout': { decideGoldenSignOut: async () => ({ status: 'legacy' }) },
    };
    const exports = {};
    vm.runInNewContext(transpile(pageSrc, 'client-logout/page.tsx'), {
      exports, require: id => { assert.ok(id in imports); return imports[id]; }, console, window: win, URLSearchParams,
    }, {filename: 'client-logout/page.tsx'});
    await act(async () => { create(React.createElement(exports.default)); });
    assert.deepEqual(win.navs, ['https://goaa.ai/?logged_out=1']);
  });

  // ---------- Cal.com card (static render of real ChatComponent) ----------
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
      sessionId: 's', stage: 'intake', intent: 'tax_planning', knownFacts: {}, displayTitle: 'Tax',
      subIntent: null, response: 'x', connectionReady: false, productAction: null,
    };}},
    '../lib/personal-agent-matter': {LEGACY_WORKSPACE_KEY: 'goaa_planning_workspace_v1', MATTER_RESTORE_EVENT: 'restore'},
    '../lib/customer-signout': {clearCustomerSession: () => ({})},
    '../lib/golden-signout': { decideGoldenSignOut: async () => ({ status: 'legacy' }) },
  };
  for (const name of ['ProfessionalHandoffCard','ButlerMattersView','ButlerWelcome','PersonalAgentInbox','PersonalAgentKnowledge','AgentProblemSolvingModel','AgentMattersOverview','LoginMenu']) imports[`./${name}`] = {default: name};
  const browser = {
    localStorage: {getItem: k => storage.get(k) || null, setItem: (k, v) => storage.set(k, v), removeItem: k => storage.delete(k)},
    location: {assign: url => navigations.push(url)},
  };
  const exportsChat = {};
  vm.runInNewContext(transpile(sourceChat, 'ChatComponent.tsx'), {
    exports: exportsChat, require: id => { assert.ok(id in imports, `Unexpected import: ${id}`); return imports[id]; },
    console, window: browser,
  }, {filename: 'ChatComponent.tsx'});
  const ChatComponent = exportsChat.default;
  const renderChat = () => { index = 0; return ChatComponent({butlerMode: true}); };

  await test('Cal card href exact, new tab, noopener noreferrer', () => {
    const card = walk(renderChat(), n => n.type === 'a' && n.props.className === 'cal-card');
    assert.equal(card.length, 1);
    assert.equal(card[0].props.href, 'https://cal.com/goaa.ai/30min');
    assert.equal(card[0].props.target, '_blank');
    assert.equal(card[0].props.rel, 'noopener noreferrer');
  });
  await test('Cal card keyboard accessible and has no side-effect handler', () => {
    const card = walk(renderChat(), n => n.type === 'a' && n.props.className === 'cal-card')[0];
    assert.equal(card.props.onClick, undefined);
    assert.equal(card.props.disabled, undefined);
    assert.equal(card.props.tabIndex, undefined);
  });
  await test('Cal card text/copy present', () => {
    const text = JSON.stringify(walk(renderChat(), n => n.type === 'a' && n.props.className === 'cal-card')[0].props.children);
    for (const s of ['预约 30 分钟评估', '与 GOAA 团队进一步梳理目标和下一步', '预约时间 ↗', '预约不会自动购买 GOAA $39.90 专业人士连接服务，也不会触发平台扣款。']) assert.ok(text.includes(s), s);
  });
  await test('Cal card sits AFTER Professional Connection card in same column', () => {
    const tree = renderChat();
    const order = walk(tree, n => (n.type === 'button' && n.props.className && n.props.className.includes('professional-card')) || (n.type === 'a' && n.props.className === 'cal-card'));
    const classes = order.map(n => n.props.className);
    const prof = classes.findIndex(c => c.includes('professional-card'));
    const cal = classes.findIndex(c => c === 'cal-card');
    assert.ok(prof >= 0 && cal >= 0 && cal > prof);
  });
  await test('rendering Cal card performs zero writes/navigations/requests', () => {
    renderChat();
    assert.equal(storage.size, 0); assert.equal(navigations.length, 0); assert.equal(requests.length, 0);
  });
  console.log(`OK ${passed}/${passed} client-logout/cal tests passed.`);
})().catch(err => { console.error(err); process.exit(1); });
