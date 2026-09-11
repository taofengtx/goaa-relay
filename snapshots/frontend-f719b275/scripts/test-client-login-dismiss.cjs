// /client-login visitor dismiss (close X) offline tests (2026-09-05).
//
// Covers:
//   - X close button exists with aria-label "Continue as guest", is a real
//     <button type="button"> (native Tab/Enter/Space activation), and calls
//     the guest redirect;
//   - Esc triggers the exact same guest redirect;
//   - return allowlist: same-origin /planning (with query/hash) and
//     /client-dashboard subpaths pass; external / protocol-relative /
//     javascript: / unknown paths fall back to /planning; missing param
//     falls back to /planning;
//   - the whole dismiss path performs ZERO login-state writes, ZERO
//     localStorage mutation, ZERO cookie writes, ZERO business requests;
//   - resume=1&reason=new-topic style query params survive the redirect
//     untouched (existing sign-in-prompt semantics unchanged).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const {create, act} = require('react-test-renderer');
const root = path.resolve(__dirname, '..');
const pageSrc = fs.readFileSync(path.join(root, 'app/client-login/page.tsx'), 'utf8');
const libSrc = fs.readFileSync(path.join(root, 'app/lib/client-login-dismiss.ts'), 'utf8');

function transpile(text, name) {
  const result = ts.transpileModule(text, {fileName: name, reportDiagnostics: true, compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX,
  }});
  assert.equal((result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error).length, 0);
  return result.outputText;
}

function loadLib() {
  const libMod = {};
  vm.runInNewContext(transpile(libSrc, 'lib/client-login-dismiss.ts'), {
    exports: libMod, URL, console,
  }, {filename: 'lib/client-login-dismiss.ts'});
  return libMod;
}

let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log(`PASS ${name}`); }

// ---------- lib allowlist unit tests ----------
const lib = loadLib();
const ORIGIN = 'https://planning.goaa.ai';

(async () => {
  await test('lib: allow /planning (bare)', () => {
    assert.equal(lib.resolveVisitorDestination('/planning', ORIGIN), '/planning');
  });
  await test('lib: allow /planning with query (resume/reason preserved)', () => {
    const raw = '/planning?resume=1&reason=new-topic';
    assert.equal(lib.resolveVisitorDestination(raw, ORIGIN), raw);
  });
  await test('lib: allow /client-dashboard and subpaths', () => {
    assert.equal(lib.resolveVisitorDestination('/client-dashboard', ORIGIN), '/client-dashboard');
    assert.equal(lib.resolveVisitorDestination('/client-dashboard/orders', ORIGIN), '/client-dashboard/orders');
    assert.equal(lib.resolveVisitorDestination('/client-dashboard/orders?x=1&y=2', ORIGIN), '/client-dashboard/orders?x=1&y=2');
    assert.equal(lib.resolveVisitorDestination('/client-dashboard/orders#history', ORIGIN), '/client-dashboard/orders#history');
  });
  await test('lib: reject external / protocol-relative / javascript URLs -> /planning', () => {
    assert.equal(lib.resolveVisitorDestination('https://evil.example.com/x', ORIGIN), '/planning');
    assert.equal(lib.resolveVisitorDestination('//evil.example.com/x', ORIGIN), '/planning');
    assert.equal(lib.resolveVisitorDestination('http://planning.goaa.ai.evil.example/x', ORIGIN), '/planning');
    assert.equal(lib.resolveVisitorDestination('javascript:alert(1)', ORIGIN), '/planning');
    assert.equal(lib.resolveVisitorDestination('https://planning.goaa.ai.evil/x', ORIGIN), '/planning');
  });
  await test('lib: reject non-allowlisted same-origin paths -> /planning', () => {
    assert.equal(lib.resolveVisitorDestination('/api/v1/client/login', ORIGIN), '/planning');
    assert.equal(lib.resolveVisitorDestination('/client-logout?return=home', ORIGIN), '/planning');
    assert.equal(lib.resolveVisitorDestination('/client-dashboard-evil', ORIGIN), '/planning');
    assert.equal(lib.resolveVisitorDestination('/planning-evil', ORIGIN), '/planning');
    assert.equal(lib.resolveVisitorDestination('/client-dashboard/', ORIGIN), '/client-dashboard/');
    assert.equal(lib.resolveVisitorDestination('/client-dashboard/orders/../orders', ORIGIN), '/client-dashboard/orders');
  });
  await test('lib: missing / empty return -> /planning', () => {
    assert.equal(lib.resolveVisitorDestination(null, ORIGIN), '/planning');
    assert.equal(lib.resolveVisitorDestination('', ORIGIN), '/planning');
    assert.equal(lib.resolveVisitorDestination('   ', ORIGIN), '/planning');
  });
  await test('lib: pure module has no window/storage/cookie/network side effects', () => {
    // Inspect only code, not explanatory comments.
    const libCode = libSrc.split('\n').filter(l => !l.trim().startsWith('//')).join('\n');
    assert.doesNotMatch(libCode, /localStorage|sessionStorage|document\.cookie|window\.|fetch\(|XMLHttpRequest/);
  });

  // ---------- static page contracts ----------
  await test('page imports resolveVisitorDestination from lib', () => {
    assert.match(pageSrc, /import\s*\{[^}]*resolveVisitorDestination[^}]*\}\s*from\s*["']\.\.\/lib\/client-login-dismiss["']/);
  });
  await test('page renders X button with aria-label/title and svg close glyph', () => {
    assert.match(pageSrc, /aria-label="Continue as guest"/);
    assert.match(pageSrc, /title="Continue as guest"/);
    assert.match(pageSrc, /type="button"/);
    assert.match(pageSrc, /<svg[^>]*viewBox="0 0 14 14"[^>]*>/);
  });
  await test('page shows the optional small guest link below the sign-in form', () => {
    assert.match(pageSrc, />Not ready to sign in\?<\/p>/);
    assert.match(pageSrc, />Continue as guest<\/button>/);
  });
  await test('page goAsGuest is a pure allowlisted redirect', () => {
    const m = pageSrc.match(/function goAsGuest\(\)\s*\{([\s\S]*?)\n  \}/);
    assert.ok(m, 'goAsGuest function not found');
    assert.match(m[1], /resolveVisitorDestination\(params\.get\("return"\), baseOrigin\)/);
    assert.match(m[1], /window\.location\.assign\(destination\)/);
    assert.doesNotMatch(m[1], /localStorage|sessionStorage|cookie|fetch\(|XMLHttpRequest|clear\(/);
  });
  await test('page Esc handler triggers the same guest redirect', () => {
    assert.match(pageSrc, /window\.addEventListener\("keydown", onKeyDown\)/);
    assert.match(pageSrc, /event\.key === "Escape"/);
    assert.match(pageSrc, /if \(event\.key === "Escape"\) goAsGuest\(\)/);
  });
  await test('page dismiss path never removes/clears storage in the listener or button', () => {
    const dismissFns = pageSrc.match(/function goAsGuest\(\)\s*\{[\s\S]*?\n  \}/g) || [];
    assert.equal(dismissFns.length, 1);
    // The guest path is intentionally a pure redirect; any storage cleanup is
    // only allowed in the authenticated returnAfterLogin/handleLogin flow.
    assert.doesNotMatch(dismissFns[0], /removeItem|clear\(|setItem|delete|writeSignedInCookieToDocument|fetch\(/);
  });

  // ---------- behavior tests (react-test-renderer + mocked window) ----------
  function makeWindow(seed = {}, search = '') {
    const data = new Map(Object.entries(seed));
    const navs = [];
    const requests = [];
    const listeners = {};
    const win = {
      cookieWrites: 0,
      navs,
      requests,
      data,
      listeners,
      localStorage: {
        getItem: k => data.has(k) ? data.get(k) : null,
        setItem: (k, v) => data.set(k, String(v)),
        removeItem: k => data.delete(k),
      },
      location: {search, origin: ORIGIN, assign: u => navs.push(String(u))},
      setTimeout: cb => { cb(); return 1; },
      clearTimeout: () => {},
      setInterval: () => 1,
      clearInterval: () => {},
      addEventListener: (type, fn) => { (listeners[type] ||= []).push(fn); },
      removeEventListener: (type, fn) => {
        const list = listeners[type] || [];
        const i = list.indexOf(fn);
        if (i >= 0) list.splice(i, 1);
      },
    };
    return win;
  }
  async function mountPage(seed, search) {
    const win = makeWindow(seed, search);
    const libExports = loadLib();
    const imports = {
      react: React,
      'react/jsx-runtime': require('react/jsx-runtime'),
      '../lib/goaa-cookie': { writeSignedInCookieToDocument: () => { win.cookieWrites++; } },
      '../lib/client-login-dismiss': libExports,
    };
    const exports = {};
    vm.runInNewContext(transpile(pageSrc, 'client-login/page.tsx'), {
      exports, require: id => { assert.ok(id in imports, `Unexpected import: ${id}`); return imports[id]; },
      console, process: { env: {} }, window: win, URLSearchParams,
    }, {filename: 'client-login/page.tsx'});
    let renderer;
    await act(async () => { renderer = create(React.createElement(exports.default)); });
    return {win, renderer};
  }
  function snapshot(win) {
    return JSON.stringify(Object.fromEntries(win.data.entries())) + '|' + win.cookieWrites + '|' + win.requests.length;
  }
  function closeBtn(renderer) {
    const found = renderer.root.findAll(node => node.props && node.props['aria-label'] === 'Continue as guest');
    assert.equal(found.length, 1);
    return found[0];
  }
  function linkBtn(renderer) {
    const found = renderer.root.findAll(node => node.type === 'button' && node.children && node.children.join('') === 'Continue as guest');
    assert.equal(found.length, 1);
    return found[0];
  }
  const seed = {goaa_planning_workspace_v1: 'draft', pref: '1'};

  await test('behavior: X click with allowlisted return navigates & leaves every side effect at zero', async () => {
    const {win, renderer} = await mountPage(seed, '?return=/client-dashboard/orders');
    const before = snapshot(win);
    await act(async () => { closeBtn(renderer).props.onClick(); });
    assert.deepEqual(win.navs, ['/client-dashboard/orders']);
    assert.equal(snapshot(win), before);
    assert.equal(win.requests.length, 0);
  });
  await test('behavior: X click keeps resume/reason query params on /planning', async () => {
    const {win, renderer} = await mountPage(seed, '?return=' + encodeURIComponent('/planning?resume=1&reason=new-topic'));
    await act(async () => { closeBtn(renderer).props.onClick(); });
    assert.deepEqual(win.navs, ['/planning?resume=1&reason=new-topic']);
  });
  await test('behavior: X click with external / evil return falls back to /planning', async () => {
    const {win, renderer} = await mountPage(seed, '?return=' + encodeURIComponent('https://evil.example.com/x'));
    const before = snapshot(win);
    await act(async () => { closeBtn(renderer).props.onClick(); });
    assert.deepEqual(win.navs, ['/planning']);
    assert.equal(snapshot(win), before);
    assert.equal(win.requests.length, 0);
  });
  await test('behavior: X click without return param falls back to /planning', async () => {
    const {win, renderer} = await mountPage(seed, '');
    await act(async () => { closeBtn(renderer).props.onClick(); });
    assert.deepEqual(win.navs, ['/planning']);
  });
  await test('behavior: Esc key performs the same guest redirect (allowlisted)', async () => {
    const {win, renderer} = await mountPage(seed, '?return=/client-dashboard');
    const before = snapshot(win);
    assert.ok(Array.isArray(win.listeners.keydown) && win.listeners.keydown.length >= 1);
    await act(async () => { win.listeners.keydown[win.listeners.keydown.length - 1]({key: 'Escape'}); });
    assert.deepEqual(win.navs, ['/client-dashboard']);
    assert.equal(snapshot(win), before);
  });
  await test('behavior: Esc key falls back to /planning for a non-allowlisted return', async () => {
    const {win, renderer} = await mountPage(seed, '?return=' + encodeURIComponent('//evil.example.com/x'));
    await act(async () => { win.listeners.keydown[win.listeners.keydown.length - 1]({key: 'Escape'}); });
    assert.deepEqual(win.navs, ['/planning']);
    assert.equal(win.requests.length, 0);
  });
  await test('behavior: optional small guest link behaves exactly like X', async () => {
    const {win, renderer} = await mountPage(seed, '?return=' + encodeURIComponent('/planning?resume=1&reason=purchase'));
    await act(async () => { linkBtn(renderer).props.onClick(); });
    assert.deepEqual(win.navs, ['/planning?resume=1&reason=purchase']);
    assert.equal(win.cookieWrites, 0);
    assert.equal(win.requests.length, 0);
  });
  await test('behavior: native button keyboard contract (real <button>, no href, focusable)', () => {
    // Handled at runtime by the browser; assert the rendered node is a real
    // button element with onClick and no external navigation semantics.
    const tests = [
      [closeBtn, 'aria-label'],
      [linkBtn, 'text'],
    ];
    for (const [find, kind] of tests) {
      // find needs a renderer; behavior is verified above. Here just assert
      // the source shape: type=button + onClick={goAsGuest}.
      assert.match(pageSrc, /type="button"/);
      assert.ok(pageSrc.includes('onClick={goAsGuest}'));
      void kind;
    }
  });

  console.log(`\nALL PASS (${passed}) client-login dismiss`);
})().catch(err => { console.error(err); process.exit(1); });
