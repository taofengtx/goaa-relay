// /client-login legal footer links (2026-09-06).
//
// Covers:
//   - bottom legal sentence points to real GOAA legal pages
//     (https://www.goaa.ai/terms, https://www.goaa.ai/privacy) as two true
//     <a href> links opened in a new tab (target=_blank, rel=noopener
//     noreferrer) - no fake anchors / no onClick interception;
//   - links render in both sign-in mode and the register mode;
//   - native link semantics: real anchors, focusable, no JS navigation
//     handlers, no login-state side effects on the link element itself;
//   - source-level guard that the old unlinked merged sentence is gone.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const {create, act} = require('react-test-renderer');
const root = path.resolve(__dirname, '..');
const pageSrc = fs.readFileSync(path.join(root, 'app/client-login/page.tsx'), 'utf8');

function transpile(text, name) {
  const result = ts.transpileModule(text, {fileName: name, reportDiagnostics: true, compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX,
  }});
  assert.equal((result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error).length, 0);
  return result.outputText;
}

let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log(`PASS ${name}`); }

function loadLib() {
  const libMod = {};
  vm.runInNewContext(transpile(
    fs.readFileSync(path.join(root, 'app/lib/client-login-dismiss.ts'), 'utf8'),
    'lib/client-login-dismiss.ts'
  ), {exports: libMod, URL, console}, {filename: 'lib/client-login-dismiss.ts'});
  return libMod;
}

function makeWindow(seed = {}, search = '') {
  const data = new Map(Object.entries(seed));
  const navs = [];
  const listeners = {};
  return {
    cookieWrites: 0,
    navs,
    data,
    listeners,
    localStorage: {
      getItem: k => data.has(k) ? data.get(k) : null,
      setItem: (k, v) => data.set(k, String(v)),
      removeItem: k => data.delete(k),
    },
    location: {search, origin: 'https://planning.goaa.ai', assign: u => navs.push(String(u))},
    setTimeout: cb => { cb(); return 1; },
    clearTimeout: () => {},
    setInterval: () => 1,
    clearInterval: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
  };
}

async function okFetchStub(url) {
  if (String(url).includes('/api/v1/auth/status')) {
    return {ok: true, status: 200, json: async () => ({google: true, email_code: true})};
  }
  return {ok: true, status: 200, json: async () => ({status: 'success'})};
}

async function mountPage(seed = {}) {
  const win = makeWindow(seed);
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
    console, process: { env: {} }, window: win, fetch: okFetchStub, URLSearchParams,
  }, {filename: 'client-login/page.tsx'});
  let renderer;
  await act(async () => { renderer = create(React.createElement(exports.default)); });
  return {win, renderer};
}

function links(renderer) {
  return renderer.root.findAll(n => n.type === 'a');
}

(async () => {
  // ---------- static source contracts ----------
  await test('source: two real anchors point to goaa.ai/terms and goaa.ai/privacy, new tab', () => {
    assert.match(pageSrc, /<a href="https:\/\/www\.goaa\.ai\/terms" target="_blank" rel="noopener noreferrer"[^>]*>Terms of Service<\/a>/);
    assert.match(pageSrc, /<a href="https:\/\/www\.goaa\.ai\/privacy" target="_blank" rel="noopener noreferrer"[^>]*>Privacy Policy<\/a>/);
  });
  await test('source: old unlinked merged legal sentence is gone', () => {
    assert.doesNotMatch(pageSrc, /Terms of Service and Privacy Policy\.<\/p>/);
    assert.doesNotMatch(pageSrc, /GOAA&apos;s Terms of Service/);
  });
  await test('source: legal links have no JS navigation or login side effects', () => {
    const snippet = pageSrc.match(/<p style=\{\{ margin: "22px 0 0", textAlign: "center"[^}]*\}\}>\s*By continuing[\s\S]*?<\/p>/);
    assert.ok(snippet, 'legal paragraph not found');
    assert.doesNotMatch(snippet[0], /onClick|onSubmit|fetch\(|localStorage|cookie|setItem|removeItem/);
  });

  // ---------- behavior ----------
  await test('behavior: sign-in mode renders both legal links with new-tab attributes', async () => {
    const {renderer} = await mountPage();
    const found = links(renderer);
    assert.equal(found.length, 2);
    const terms = found.find(n => n.props.href === 'https://www.goaa.ai/terms');
    const privacy = found.find(n => n.props.href === 'https://www.goaa.ai/privacy');
    assert.ok(terms && privacy, 'both legal hrefs present');
    assert.ok(found.every(n => n.props.target === '_blank'));
    assert.ok(found.every(n => n.props.rel === 'noopener noreferrer'));
    assert.ok(found.every(n => !n.props.onClick), 'no JS click interception');
    const text = found.map(n => String(n.children && n.children.join(''))).sort().join('|');
    assert.equal(text, 'Privacy Policy|Terms of Service');
  });
  await test('behavior: register mode keeps the same two legal links', async () => {
    const {renderer} = await mountPage();
    await act(async () => { await new Promise(r => setTimeout(r, 0)); }); // caps probe
    const createBtns = renderer.root.findAll(n => n.type === 'button' && n.children && n.children.join('') === 'Create an account');
    assert.equal(createBtns.length, 1);
    await act(async () => { createBtns[0].props.onClick(); });
    const found = links(renderer);
    assert.equal(found.length, 2);
    assert.ok(found.every(n => n.props.target === '_blank' && n.props.rel === 'noopener noreferrer'));
  });

  console.log(`\n${passed} legal-links checks passed`);
})().catch(err => { console.error(err); process.exit(1); });
