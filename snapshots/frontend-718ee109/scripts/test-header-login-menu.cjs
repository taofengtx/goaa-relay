// planning header LoginMenu offline tests (2026-09-06).
// Covers the Round 11 header change:
//   - ChatComponent: wordmark "GOAA.ai" removed (round mark only), the
//     For Professionals / Sign in anchors are gone, and the signed-in/out
//     branches render <LoginMenu variant="ghost" signedIn=... onLogout=.../>.
//   - LoginMenu itself (mounted with react-test-renderer, real component):
//       * ghost variant renders a transparent text-only trigger
//       * signed-out opens a dark dropdown with exactly three <a>:
//         CUSTOMERS -> /client-login, AGENTS -> /agent-login,
//         Register Now -> /client-login  (plus a non-link CUSTOMERS label)
//       * signed-in with onLogout renders MY ACCOUNT -> /planning (link) and
//         LOG OUT as a button that invokes onLogout
//       * signed-in without onLogout renders LOG OUT as
//         /client-logout?return=home
// No browser, no network, no API / DB / payment is touched.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const { create, act } = require('react-test-renderer');
const root = path.resolve(__dirname, '..');

function transpile(text, name) {
  const result = ts.transpileModule(text, { fileName: name, reportDiagnostics: true, compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX,
  }});
  assert.equal((result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error).length, 0);
  return result.outputText;
}
function loadModule(relative, imports, globals = {}) {
  const absolute = path.resolve(root, relative);
  const source = fs.readFileSync(absolute, 'utf8');
  const exports = {};
  const module = { exports };
  vm.runInNewContext(transpile(source, relative), {
    exports, module, require: id => {
      assert.ok(id in imports, `Unexpected import in ${relative}: ${id}`);
      return imports[id];
    }, console, ...globals,
  }, { filename: relative });
  return exports;
}
function json(renderer) { return renderer.toJSON(); }
function walk(node, pred, found = []) {
  if (!node || typeof node !== 'object') return found;
  if (Array.isArray(node)) { node.forEach(n => walk(n, pred, found)); return found; }
  if (pred(node)) found.push(node);
  if (node.children) walk(node.children, pred, found);
  if (node.props && node.props.children) walk(node.props.children, pred, found);
  return found;
}
function textOf(node) {
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (Array.isArray(node)) return node.map(textOf).join('');
  if (node && typeof node === 'object') {
    const kids = node.children || (node.props && node.props.children);
    return kids ? textOf(kids) : '';
  }
  return '';
}
function buttonWith(tree, text) {
  const b = walk(tree, n => n.type === 'button' && textOf(n).includes(text))[0];
  assert.ok(b, `expected button containing ${text}`);
  return b;
}
let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log(`PASS ${name}`); }

(async () => {
  // ---------- Part 1: LoginMenu real mount ----------
  const jsxRuntime = require('react/jsx-runtime');
  const docListeners = {};
  const sandboxDocument = {
    listeners: docListeners,
    addEventListener: (type, fn) => { (docListeners[type] = docListeners[type] || []).push(fn); },
    removeEventListener: (type, fn) => { if (docListeners[type]) docListeners[type] = docListeners[type].filter(f => f !== fn); },
  };
  const loginImports = { 'react': React, 'react/jsx-runtime': jsxRuntime };
  function mountLogin(props) {
    const Menu = loadModule('app/components/LoginMenu.tsx', loginImports, { document: sandboxDocument }).default;
    let renderer;
    act(() => { renderer = create(React.createElement(Menu, props)); });
    return renderer;
  }

  await test('signed-out ghost trigger shows LOGIN / REGISTER with down caret and transparent background', () => {
    const r = mountLogin({ signedIn: false, variant: 'ghost' });
    const tree = json(r);
    assert.equal(walk(tree, n => n.props && n.props['data-testid'] === 'login-menu').length, 1);
    const trigger = buttonWith(tree, 'LOGIN / REGISTER');
    assert.equal(trigger.props['aria-haspopup'], 'menu');
    assert.equal(trigger.props['aria-expanded'], false);
    assert.equal(trigger.props.style.background, 'transparent', 'ghost must be transparent (no purple button)');
    assert.equal(trigger.props.style.minWidth, 0);
    act(() => { r.unmount(); });
  });

  await test('signed-out opens dark menu with exactly three <a>: /client-login, /agent-login, /client-login', () => {
    const r = mountLogin({ signedIn: false, variant: 'ghost' });
    let tree = json(r);
    const trigger = buttonWith(tree, 'LOGIN / REGISTER');
    act(() => { trigger.props.onClick(); });
    tree = json(r);
    assert.equal(buttonWith(tree, 'LOGIN / REGISTER').props['aria-expanded'], true);
    const menu = walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu');
    assert.equal(menu.length, 1);
    assert.equal(menu[0].props.style.background, '#17143a', 'dropdown must stay dark');
    const anchors = walk(menu[0], n => n.type === 'a' && n.props.href);
    assert.equal(anchors.length, 3);
    assert.deepEqual(anchors.map(a => a.props.href), ['/client-login', '/agent-login', '/client-login']);
    assert.deepEqual(anchors.map(a => a.children.join('')), ['CUSTOMERS', 'AGENTS', 'Register Now']);
    // Non-link CUSTOMERS small label is a div, not an anchor.
    const label = walk(menu[0], n => n.type === 'div' && Array.isArray(n.children) && n.children.join('') === 'CUSTOMERS' && n.props.style && String(n.props.style.color).includes('rgba'));
    assert.ok(label.length >= 1, 'expected a non-link CUSTOMERS label row');
    act(() => { r.unmount(); });
  });

  await test('Escape closes the signed-out menu', () => {
    const r = mountLogin({ signedIn: false, variant: 'ghost' });
    let tree = json(r);
    const trigger = buttonWith(tree, 'LOGIN / REGISTER');
    act(() => { trigger.props.onClick(); });
    tree = json(r);
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 1);
    const escHandlers = docListeners.keydown || [];
    assert.ok(escHandlers.length >= 1, 'expected Escape keydown listener while open');
    act(() => { for (const fn of escHandlers) fn({ key: 'Escape' }); });
    tree = json(r);
    assert.equal(walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu').length, 0);
    assert.equal(buttonWith(tree, 'LOGIN / REGISTER').props['aria-expanded'], false);
    act(() => { r.unmount(); });
  });

  await test('signed-in with onLogout shows MY ACCOUNT (/planning) and LOG OUT button invoking onLogout', () => {
    let signedOut = 0;
    const r = mountLogin({ signedIn: true, variant: 'ghost', onLogout: () => { signedOut++; } });
    let tree = json(r);
    const trigger = buttonWith(tree, 'MY ACCOUNT');
    assert.equal(trigger.props.style.background, 'transparent');
    act(() => { trigger.props.onClick(); });
    tree = json(r);
    const menu = walk(tree, n => n.type === 'div' && n.props && n.props.role === 'menu');
    assert.equal(menu.length, 1);
    const acct = walk(menu[0], n => n.type === 'a' && n.props.href === '/planning');
    assert.equal(acct.length, 1);
    assert.equal(acct[0].children.join(''), 'MY ACCOUNT');
    const out = walk(menu[0], n => n.type === 'button' && Array.isArray(n.children) && n.children.join('').includes('LOG OUT'));
    assert.equal(out.length, 1);
    act(() => { out[0].props.onClick(); });
    assert.equal(signedOut, 1);
    act(() => { r.unmount(); });
  });

  await test('signed-in without onLogout renders LOG OUT as /client-logout?return=home link', () => {
    const r = mountLogin({ signedIn: true, variant: 'ghost' });
    let tree = json(r);
    const trigger = buttonWith(tree, 'MY ACCOUNT');
    act(() => { trigger.props.onClick(); });
    tree = json(r);
    const out = walk(tree, n => n.type === 'a' && n.props.href === '/client-logout?return=home');
    assert.equal(out.length, 1);
    assert.equal(out[0].children.join(''), 'LOG OUT');
    act(() => { r.unmount(); });
  });

  // ---------- Part 2: ChatComponent header integration ----------
  const sourceChat = fs.readFileSync(path.join(root, 'app/components/ChatComponent.tsx'), 'utf8');
  const stateNames = [...sourceChat.matchAll(/const \[(\w+),\s*\w+\] = useState/g)].map(m => m[1]);
  let index = 0;
  const storage = new Map();
  const navigations = [];
  const requests = [];
  const state = {};
  const jsx = { jsx: (type, props) => ({ type, props }), jsxs: (type, props) => ({ type, props }), Fragment: 'Fragment' };
  const imports = {
    react: { useMemo: fn => fn(), useEffect: () => {}, useState: value => {
      const key = stateNames[index++];
      if (!(key in state)) state[key] = typeof value === 'function' ? value() : value;
      return [state[key], next => { state[key] = typeof next === 'function' ? next(state[key]) : next; }];
    } },
    'react/jsx-runtime': jsx,
    '../lib/openclaw': { chat: async (...args) => { requests.push(args); return {
      sessionId: 's', stage: 'intake', intent: 'tax_planning', knownFacts: {},
      displayTitle: 'Tax', subIntent: null, response: 'x', connectionReady: false, productAction: null,
    }; } },
    '../lib/personal-agent-matter': { LEGACY_WORKSPACE_KEY: 'goaa_planning_workspace_v1', MATTER_RESTORE_EVENT: 'restore' },
    '../lib/customer-signout': { clearCustomerSession: () => ({}) },
    '../lib/golden-signout': { decideGoldenSignOut: async () => ({ status: 'legacy' }) },
  };
  for (const name of ['ProfessionalHandoffCard', 'ButlerMattersView', 'ButlerWelcome', 'PersonalAgentInbox', 'PersonalAgentKnowledge', 'AgentProblemSolvingModel', 'AgentMattersOverview', 'LoginMenu']) imports[`./${name}`] = { default: name };
  const browser = {
    localStorage: { getItem: k => storage.get(k) || null, setItem: (k, v) => storage.set(k, v), removeItem: k => storage.delete(k) },
    location: { assign: url => navigations.push(url) },
  };
  const exports = {};
  vm.runInNewContext(transpile(sourceChat, 'ChatComponent.tsx'), {
    exports, require: id => { assert.ok(id in imports, `Unexpected import: ${id}`); return imports[id]; },
    console, window: browser,
  }, { filename: 'ChatComponent.tsx' });
  const ChatComponent = exports.default;
  const render = () => { index = 0; return ChatComponent({ butlerMode: true }); };

  await test('header has no GOAA.ai text; round mark stays', () => {
    const tree = render();
    const brand = walk(tree, n => n.type === 'a' && n.props && n.props.className === 'goaa-brand');
    assert.equal(brand.length, 1);
    const text = JSON.stringify(brand[0].props.children);
    assert.ok(text.includes('goaa-mark'), 'round mark still present');
    assert.ok(!text.includes('GOAA.ai'), 'GOAA.ai wordmark text removed');
    // The whole rendered header must not contain visible GOAA.ai text.
    const headerNode = walk(tree, n => n.type === 'header' && n.props && n.props.className === 'goaa-nav');
    assert.equal(headerNode.length, 1);
    assert.ok(!textOf(headerNode[0]).includes('GOAA.ai'), 'no GOAA.ai text anywhere in the header');
    assert.ok(textOf(brand[0]).includes('G'), 'round mark letter G is present');
  });

  await test('brand shows AI Butler text next to round mark (goaa-brand-text; aria-label AI Butler home)', () => {
    const tree = render();
    const brand = walk(tree, n => n.type === 'a' && n.props && n.props.className === 'goaa-brand');
    assert.equal(brand.length, 1);
    const text = JSON.stringify(brand[0].props.children);
    assert.ok(text.includes('goaa-brand-text'), 'brand-text span present again');
    assert.ok(text.includes('AI Butler'), 'wordmark text is AI Butler');
    assert.equal(brand[0].props['aria-label'], 'AI Butler home');
    assert.equal(textOf(brand[0]).trim(), 'GAI Butler', 'visible brand content = round G + AI Butler');
    assert.ok(!textOf(brand[0]).includes('GOAA'));
  });

  await test('For Professionals and Sign in anchors are gone; LoginMenu ghost is used with sessionVisible + onLogout', () => {
    const tree = render();
    assert.equal(walk(tree, n => n.type === 'a' && n.props && n.props.href === '/agent-login').length, 0);
    assert.equal(walk(tree, n => n.type === 'a' && n.props && n.props.href === '/client-login').length, 0);
    const menus = walk(tree, n => n.type === 'LoginMenu');
    assert.equal(menus.length, 1);
    assert.equal(menus[0].props.variant, 'ghost');
    assert.equal(menus[0].props.signedIn, false, 'signedIn bound to sessionVisible (false when logged out)');
    assert.equal(typeof menus[0].props.onLogout, 'function', 'onLogout bound to app sign-out');
  });

  await test('ChatComponent source keeps AccountMenu out and LoginMenu import in', () => {
    assert.ok(sourceChat.includes("import LoginMenu from './LoginMenu'"));
    assert.ok(!sourceChat.includes("import AccountMenu from './AccountMenu'"));
    assert.ok(!sourceChat.includes('For Professionals'));
    assert.ok(!/Sign in/.test(sourceChat));
  });

  if (passed === 0) throw new Error('no tests ran');
  console.log(`\nOK ${passed}/${passed} header-login-menu tests passed.`);
})().catch(err => { console.error(err); process.exit(1); });
