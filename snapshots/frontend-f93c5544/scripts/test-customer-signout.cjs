// Customer sign-out offline tests (2026-09-04).
// Covers: nav signed-in/out states, account menu open/close / outside click /
// Esc / keyboard, whitelist cleanup, unrelated-storage retention, planning
// draft retention, butler nickname → guest migration, refresh stays signed
// out, and zero order/match/checkout/payment requests.
// No browser, no network, no real API / DB / payment is touched.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const {create, act} = require('react-test-renderer');
const root = path.resolve(__dirname, '..');

function transpile(text, name) {
  const result = ts.transpileModule(text, {fileName: name, reportDiagnostics: true, compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX,
  }});
  assert.equal((result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error).length, 0);
  return result.outputText;
}
function loadModule(relative, imports, globals = {}) {
  const absolute = path.resolve(root, relative);
  const source = fs.readFileSync(absolute, 'utf8');
  const exports = {};
  const module = {exports};
  vm.runInNewContext(transpile(source, relative), {
    exports, module, require: id => {
      assert.ok(id in imports, `Unexpected import in ${relative}: ${id}`);
      return imports[id];
    }, console, ...globals,
  }, {filename: relative});
  return exports;
}

// ---------- pure storage helpers ----------
function storage(seed = {}) {
  const data = new Map(Object.entries(seed));
  return {
    data,
    getItem: k => data.has(k) ? data.get(k) : null,
    setItem: (k, v) => data.set(k, String(v)),
    removeItem: k => data.delete(k),
    dump: () => Object.fromEntries(data),
  };
}
const LOCAL_EXPECTED = [
  'client_token', 'client_username', 'customer_token', 'goaa_order_customer_token',
  'goaa_active_order_id', 'goaa_customer_e2e_journey_v1',
  'goaa_pending_purchase_v1', 'goaa_auth_return_v1', 'goaa_auth_reason_v1', 'goaa_after_auth_action_v1',
  'goaa_pending_prompt_v1', 'goaa_pending_professional_handoff_v1', 'goaa_matter_order_links_v1',
  'goaa_connect_attempt_pending_v1',
];
const SESSION_EXPECTED = ['goaa_connect_attempt_pending_v1'];
let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log(`PASS ${name}`); }

(async () => {
  const cookieMod = loadModule('app/lib/goaa-cookie.ts', {});
  const lib = loadModule('app/lib/customer-signout.ts', { './goaa-cookie': cookieMod });
  const {clearCustomerSession, isCustomerSignedIn, readCustomerOrderContext,
    CLIENT_LOCAL_KEYS_TO_REMOVE, CLIENT_SESSION_KEYS_TO_REMOVE,
    migrateButlerNicknameToGuest, butlerNickKeyFor} = lib;

  await test('whitelist inventory matches login/journey source inventory exactly', () => {
    assert.deepEqual([...CLIENT_LOCAL_KEYS_TO_REMOVE].sort(), [...LOCAL_EXPECTED].sort());
    assert.deepEqual([...CLIENT_SESSION_KEYS_TO_REMOVE].sort(), [...SESSION_EXPECTED].sort());
    // Protected keys must NEVER appear in the removal lists.
    const protectedKeys = ['goaa_planning_workspace_v1', 'goaa_butler_display_name_v1:guest', 'goaa_butler_display_name_v1:x', 'agent_token', 'agent_username', 'goaa_order_agent_token', 'goaa_order_demo_v1', 'goaa_personal_agent_current_matter_v1', 'goaa_personal_agent_matter_history_v1', 'theme'];
    for (const p of protectedKeys) {
      assert.equal(CLIENT_LOCAL_KEYS_TO_REMOVE.includes(p), false, `must not clear ${p}`);
    }
  });

  await test('planning draft + unrelated prefs survive; whitelist removed', () => {
    const draft = JSON.stringify({thread: [{role: 'user', content: 'Insurance'}], sessionId: 's1'});
    const local = storage({
      client_token: 'tok', client_username: 'u@example.com', customer_token: 'ctok',
      goaa_order_customer_token: 'octok', goaa_active_order_id: 'o1',
      goaa_customer_e2e_journey_v1: JSON.stringify({orderId: 'o1', step: 'order_created'}),
      goaa_pending_purchase_v1: '/connect-pass', goaa_auth_return_v1: '/x', goaa_auth_reason_v1: 'purchase',
      goaa_after_auth_action_v1: 'new_plan', goaa_pending_prompt_v1: 'p', 
      goaa_pending_professional_handoff_v1: 'h', goaa_matter_order_links_v1: '{}',
      goaa_connect_attempt_pending_v1: 'ctx',
      [butlerNickKeyFor('u@example.com')]: '小安',
      goaa_planning_workspace_v1: draft,
      agent_token: 'agent-tok', agent_username: 'agent-name',
      goaa_order_agent_token: 'aotok', goaa_order_demo_v1: '{}',
      goaa_personal_agent_current_matter_v1: '{"schemaVersion":1}', goaa_personal_agent_matter_history_v1: '[]',
      theme: 'dark',
    });
    const session = storage({'goaa_connect_attempt_pending_v1': 'ctx'});
    clearCustomerSession(local, session);
    const dump = local.dump();
    for (const k of LOCAL_EXPECTED) assert.equal(k in dump, false, `should remove ${k}`);
    for (const k of SESSION_EXPECTED) assert.equal(k in session.dump(), false, `session ${k}`);
    assert.equal(dump.goaa_planning_workspace_v1, draft, 'draft retained unchanged');
    assert.equal(dump['goaa_butler_display_name_v1:guest'], '小安', 'nickname migrated to guest');
    assert.equal(dump['goaa_butler_display_name_v1:u@example.com'], '小安', 'butler nickname keys are preserved (not identity)');
    assert.equal(dump.client_username, undefined, 'client_username identity key removed');
    assert.equal(dump.agent_token, 'agent-tok');
    assert.equal(dump.agent_username, 'agent-name');
    assert.equal(dump.goaa_order_agent_token, 'aotok');
    assert.equal(dump.goaa_order_demo_v1, '{}');
    assert.equal(dump.theme, 'dark');
    assert.equal(dump.goaa_personal_agent_current_matter_v1, '{"schemaVersion":1}');
    assert.equal(dump.goaa_personal_agent_matter_history_v1, '[]');
  });

  await test('refresh after sign-out cannot restore token or order', () => {
    const local = storage({
      client_token: 'tok', goaa_active_order_id: 'o1',
      goaa_customer_e2e_journey_v1: JSON.stringify({orderId: 'o1', step: 'order_created'}),
    });
    clearCustomerSession(local, storage());
    assert.equal(isCustomerSignedIn(local), false);
    assert.equal(JSON.stringify(readCustomerOrderContext(local)), JSON.stringify({orderId: null, journey: null}));
    // Simulate a planning refresh: no token, no active order, no journey.
    assert.equal(local.getItem('client_token'), null);
    assert.equal(local.getItem('goaa_active_order_id'), null);
  });

  await test('guest nickname kept when both signed-in and guest values exist', () => {
    const local = storage({
      client_username: 'bob@example.com',
      'goaa_butler_display_name_v1:bob@example.com': '鲍勃的管家',
      'goaa_butler_display_name_v1:guest': '小安',
      client_token: 'tok',
    });
    clearCustomerSession(local, storage());
    assert.equal(local.getItem('goaa_butler_display_name_v1:guest'), '小安');
    assert.equal(local.getItem('client_username'), null);
  });

  await test('sign-out with no username leaves guest untouched', () => {
    const local = storage({'goaa_butler_display_name_v1:guest': '小安', client_token: 'tok'});
    clearCustomerSession(local, storage());
    assert.equal(local.getItem('goaa_butler_display_name_v1:guest'), '小安');
    assert.equal(local.getItem('client_token'), null);
  });

  await test('nickname migration never stores the username value', () => {
    const local = storage({client_username: 'real-user@example.com'});
    const m = migrateButlerNicknameToGuest(local);
    assert.equal(m.migratedValue, null);
    assert.equal(local.getItem('goaa_butler_display_name_v1:guest'), null);
    assert.equal(local.getItem('goaa_butler_display_name_v1:real-user@example.com'), null);
  });

  await test('empty local/session storage clears cleanly', () => {
    const local = storage(); const session = storage();
    clearCustomerSession(local, session);
    assert.deepEqual(local.dump(), {});
    assert.deepEqual(session.dump(), {});
  });

  // ---------- UI: AccountMenu ----------
  const makeWindow = () => {
    const listeners = {};
    return {
      listeners,
      addEventListener: (type, fn) => { (listeners[type] = listeners[type] || []).push(fn); },
      removeEventListener: (type, fn) => { if (listeners[type]) listeners[type] = listeners[type].filter(f => f !== fn); },
    };
  };
  const jsxRuntime = require('react/jsx-runtime');
  const menuImports = {'react': React, 'react/jsx-runtime': jsxRuntime};
  function mountMenu(sandboxWindow, onSignOut = () => {}) {
    const Menu = loadModule('app/components/AccountMenu.tsx', menuImports, {window: sandboxWindow}).default;
    let renderer;
    act(() => { renderer = create(React.createElement(Menu, {onSignOut})); });
    return renderer;
  }
  function json(root) { return root.toJSON(); }
  function walk(node, pred, found = []) {
    if (!node || typeof node !== 'object') return found;
    if (Array.isArray(node)) { node.forEach(n => walk(n, pred, found)); return found; }
    if (pred(node)) found.push(node);
    walk(node.children, pred, found);
    return found;
  }
  const hasTextIn = n => n && typeof n === 'object' && Array.isArray(n.children) && n.children.join('');
  function buttonWith(tree, text) {
    const b = walk(tree, n => n.type === 'button' && Array.isArray(n.children) && n.children.join('').includes(text))[0];
    assert.ok(b, `expected button containing ${text}`);
    return b;
  }
  function dispatch(window, type, event) {
    assert.ok(window.listeners[type] && window.listeners[type].length, `expected ${type} listeners`);
    for (const fn of window.listeners[type]) fn(event);
  }

  await test('signed-in nav shows account trigger with caret and no Sign in link', () => {
    const w = makeWindow();
    const r = mountMenu(w);
    const tree = json(r);
    const trigger = buttonWith(tree, '已登录 · Signed in');
    assert.ok(trigger.props['aria-haspopup'] === 'menu');
    assert.equal(trigger.props['aria-expanded'], false);
    assert.equal(walk(tree, n => n.type === 'a' && n.children && n.children.join('').includes('Sign in')).length, 0);
    // For Professionals anchor is a separate caller-side nav item; not in menu.
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 0);
    act(() => { r.unmount(); });
  });

  await test('click trigger opens menu with sign-out item; second click closes', () => {
    const w = makeWindow();
    const r = mountMenu(w);
    let tree = json(r);
    const trigger = buttonWith(tree, '已登录 · Signed in');
    act(() => { trigger.props.onClick(); });
    tree = json(r);
    assert.equal(buttonWith(tree, '已登录 · Signed in').props['aria-expanded'], true);
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 1);
    buttonWith(tree, '退出登录 · Sign out');
    const menu = walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu')[0];
    assert.equal(menu.props['aria-label'], 'Account menu');
    assert.equal(walk(tree, n => n.type === 'button' && n.props && n.props.role === 'menuitem').length, 1);
    act(() => { trigger.props.onClick(); });
    tree = json(r);
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 0);
    act(() => { r.unmount(); });
  });

  await test('Escape closes menu', () => {
    const w = makeWindow();
    const r = mountMenu(w);
    let tree = json(r);
    act(() => { buttonWith(tree, '已登录 · Signed in').props.onClick(); });
    tree = json(r);
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 1);
    act(() => { dispatch(w, 'keydown', {key: 'Escape', preventDefault() {}}); });
    tree = json(r);
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 0);
    act(() => { r.unmount(); });
  });

  await test('pointerdown outside closes menu (fail-closed when contains unavailable)', () => {
    const w = makeWindow();
    const r = mountMenu(w);
    let tree = json(r);
    act(() => { buttonWith(tree, '已登录 · Signed in').props.onClick(); });
    tree = json(r);
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 1);
    act(() => { dispatch(w, 'pointerdown', {target: {}}); });
    tree = json(r);
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 0);
    act(() => { r.unmount(); });
  });

  await test('ArrowDown on trigger keeps menu open (keyboard nav does not crash)', () => {
    const w = makeWindow();
    const r = mountMenu(w);
    let tree = json(r);
    const trigger = buttonWith(tree, '已登录 · Signed in');
    act(() => { trigger.props.onClick(); });
    tree = json(r);
    act(() => { buttonWith(tree, '已登录 · Signed in').props.onKeyDown({key: 'ArrowDown', preventDefault() {}}); });
    tree = json(r);
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 1);
    act(() => { r.unmount(); });
  });

  await test('clicking Sign out fires exactly once and closes menu', () => {
    const w = makeWindow();
    let calls = 0;
    const r = mountMenu(w, () => calls++);
    let tree = json(r);
    act(() => { buttonWith(tree, '已登录 · Signed in').props.onClick(); });
    tree = json(r);
    act(() => { buttonWith(tree, '退出登录 · Sign out').props.onClick(); });
    assert.equal(calls, 1);
    tree = json(r);
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 0);
    act(() => { r.unmount(); });
  });

  await test('AccountMenu contains zero network touchpoints (no fetch/XMLHttpRequest/WebSocket literals)', () => {
    const source = fs.readFileSync(path.join(root, 'app/components/AccountMenu.tsx'), 'utf8');
    assert.equal(/fetch\(/.test(source), false);
    assert.equal(/XMLHttpRequest/.test(source), false);
    assert.equal(/WebSocket/.test(source), false);
    const libSource = fs.readFileSync(path.join(root, 'app/lib/customer-signout.ts'), 'utf8');
    assert.equal(/fetch\(|XMLHttpRequest|WebSocket/.test(libSource), false);
  });

  await test('ChatComponent header: LoginMenu ghost with sessionVisible + onLogout; For Professionals/Sign in removed', () => {
    const src = fs.readFileSync(path.join(root, 'app/components/ChatComponent.tsx'), 'utf8');
    const navStart = src.indexOf('aria-label="Primary navigation"');
    const navEnd = src.indexOf('</nav>', navStart);
    const nav = src.slice(navStart, navEnd);
    assert.ok(nav.includes('<LoginMenu variant="ghost" signedIn={sessionVisible} onLogout={handleCustomerSignOut} error={signOutError} />'), 'LoginMenu receives sessionVisible + sign-out handler + error slot');
    assert.ok(nav.includes('<a href="#start" className="goaa-start-link">Start Planning'), 'Start Planning link remains');
    assert.ok(nav.includes('For Professionals') === false, 'For Professionals removed');
    assert.ok(nav.includes('Sign in') === false, 'standalone Sign in removed');
    assert.ok(src.includes("import LoginMenu from './LoginMenu'"), 'LoginMenu imported');
    assert.ok(src.includes('AccountMenu') === false, 'AccountMenu no longer referenced');
    assert.ok(src.includes('<span className="goaa-brand-text">AI Butler</span>'), 'brand text = AI Butler');
    assert.ok(src.includes('aria-label="AI Butler home"'), 'brand aria = AI Butler home');
    assert.ok(nav.includes('goaa_signout') === false);
  });

  await test('one-time notice: only on logged_out=1 and then param cleaned', () => {
    const src = fs.readFileSync(path.join(root, 'app/components/ChatComponent.tsx'), 'utf8');
    assert.ok(src.includes('logged_out') === true);
    assert.ok(src.includes('已退出登录；此浏览器中的规划草稿仍保留。'));
    assert.ok(src.includes("history.replaceState(window.history.state, '', window.location.pathname)"));
  });

  if (passed === 0) throw new Error('no tests ran');
  console.log(`\nALL ${passed} CUSTOMER SIGNOUT TESTS PASSED`);
})().catch(err => { console.error(err); process.exit(1); });
