// /client-login password show/hide toggles (2026-09-06).
//
// Covers:
//   - three reveal controls exist: email-login password, register Password,
//     register Confirm password — each a real <button type="button"> so it is
//     Tab-focusable and Enter/Space activate it via native button semantics;
//   - default state hides every password (type="password") and every toggle
//     says aria-label "Show password" with aria-pressed="false";
//   - clicking a toggle flips ONLY that field type password<->text, flips its
//     own icon/label to Hide/Show and keeps aria-pressed in sync;
//   - register Password and Confirm password toggles are independent;
//   - value state is untouched by toggling (no submit/validation change);
//   - static guards: exactly 3 reveal buttons, all type="button", no
//     preventDefault/stopPropagation/submit side effects inside them.
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
  const requests = [];
  const listeners = {};
  return {
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
    location: {search, origin: 'https://planning.goaa.ai', assign: u => navs.push(String(u)), href: 'https://planning.goaa.ai/client-login'},
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
}

// fetch stub: auth/status advertises google+emailCode so the register entry
// is visible; email-code/send succeeds so the register card advances to its
// password+confirm step without network/DB.
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

function inputByLabel(renderer, label) {
  const found = renderer.root.findAll(n => n.type === 'input' && n.props['aria-label'] === label);
  assert.equal(found.length, 1, `expected exactly one input labelled "${label}"`);
  return found[0];
}

function revealButtons(renderer) {
  return renderer.root.findAll(n => n.type === 'button' && (
    n.props['aria-label'] === 'Show password' || n.props['aria-label'] === 'Hide password'
  ));
}

function revealFor(renderer, label) {
  const found = revealButtons(renderer).filter(n => n.props['aria-label'] === label);
  return found;
}

function buttonWithText(renderer, text) {
  const found = renderer.root.findAll(n => n.type === 'button' && n.children && n.children.join('') === text);
  assert.equal(found.length, 1, `expected one button "${text}"`);
  return found[0];
}

function forms(renderer) {
  return renderer.root.findAll(n => n.type === 'form');
}

function flush() { return new Promise(r => setTimeout(r, 0)); }

// Helper: advance classic login to its password step (email -> Continue).
async function advanceLoginToPassword(renderer) {
  const emailInput = inputByLabel(renderer, 'Email');
  await act(async () => { emailInput.props.onChange({target: {value: 'aika@example.com'}}); });
  const form = forms(renderer)[0];
  await act(async () => { form.props.onSubmit(undefined); });
}

// Helper: open register code step (Create an account -> send code -> code form).
async function advanceRegisterToPasswords(renderer) {
  await act(async () => { await flush(); }); // let /auth/status capability probe settle
  await act(async () => { buttonWithText(renderer, 'Create an account').props.onClick(); });
  const emailInput = inputByLabel(renderer, 'Registration email');
  await act(async () => { emailInput.props.onChange({target: {value: 'new@example.com'}}); });
  const form = forms(renderer)[0];
  await act(async () => { form.props.onSubmit({preventDefault() {}}); await flush(); });
}

(async () => {
  // ---------- static page contracts ----------
  await test('page defines exactly three password reveal toggles wired to separate state', () => {
    const uses = (pageSrc.match(/<PasswordRevealButton\b/g) || []).length;
    assert.equal(uses, 3);
    assert.equal((pageSrc.match(/<PasswordRevealButton\s+visible=\{loginPwVisible\}\s+onToggle=\{\(\) => setLoginPwVisible/g) || []).length, 1);
    assert.equal((pageSrc.match(/<PasswordRevealButton\s+visible=\{regPwVisible\}\s+onToggle=\{\(\) => setRegPwVisible/g) || []).length, 1);
    assert.equal((pageSrc.match(/<PasswordRevealButton\s+visible=\{regPw2Visible\}\s+onToggle=\{\(\) => setRegPw2Visible/g) || []).length, 1);
    assert.match(pageSrc, /loginPwVisible/);
    assert.match(pageSrc, /regPwVisible/);
    assert.match(pageSrc, /regPw2Visible/);
  });
  await test('every reveal button is a real type=button with aria-label/aria-pressed/title', () => {
    const snippet = pageSrc.match(/function PasswordRevealButton[\s\S]*?\n\}/)[0];
    assert.match(snippet, /type="button"/);
    assert.match(snippet, /aria-label=\{label\}/);
    assert.match(snippet, /aria-pressed=\{visible\}/);
    assert.match(snippet, /title=\{label\}/);
    assert.match(snippet, /onClick=\{onToggle\}/);
    assert.doesNotMatch(snippet, /onKeyDown|onKeyUp/); // native Enter/Space activation preserved
  });
  await test('reveal toggle never blocks submit or changes validation/value handling', () => {
    // The button only flips a boolean; the surrounding form handlers are
    // untouched (no new submits, no preventDefault/stopPropagation in button).
    const snippet = pageSrc.match(/function PasswordRevealButton[\s\S]*?\n\}/)[0];
    assert.doesNotMatch(snippet, /preventDefault|stopPropagation|type="submit"/);
    assert.match(pageSrc, /onSubmit=\{handleLogin\}/);
    assert.match(pageSrc, /onSubmit=\{handleRegister\}/);
    // Fields keep their original validation-relevant attrs.
    const pwInputs = pageSrc.match(/aria-label="Password"/g) || [];
    const cfInputs = pageSrc.match(/aria-label="Confirm password"/g) || [];
    assert.equal(pwInputs.length, 2); // login + register Password
    assert.equal(cfInputs.length, 1); // register Confirm password
    assert.match(pageSrc, /autoComplete="current-password"/);
    assert.match(pageSrc, /autoComplete="new-password"/g);
  });

  // ---------- behavior: classic email login password ----------
  await test('login: password hidden by default; toggle reveals text and flips a11y attrs', async () => {
    const {renderer} = await mountPage();
    await advanceLoginToPassword(renderer);
    const pw = inputByLabel(renderer, 'Password');
    assert.equal(pw.props.type, 'password');
    assert.equal(revealButtons(renderer).length, 1);
    const btn = revealButtons(renderer)[0];
    assert.equal(btn.props['aria-label'], 'Show password');
    assert.equal(btn.props['aria-pressed'], false);
    assert.equal(btn.props.type, 'button');
    await act(async () => { btn.props.onClick(); });
    assert.equal(inputByLabel(renderer, 'Password').props.type, 'text');
    const hide = revealButtons(renderer)[0];
    assert.equal(hide.props['aria-label'], 'Hide password');
    assert.equal(hide.props['aria-pressed'], true);
    await act(async () => { hide.props.onClick(); });
    assert.equal(inputByLabel(renderer, 'Password').props.type, 'password');
    assert.equal(revealButtons(renderer)[0].props['aria-label'], 'Show password');
  });
  await test('login: toggling never mutates the password value', async () => {
    const {renderer} = await mountPage();
    await advanceLoginToPassword(renderer);
    const pw = inputByLabel(renderer, 'Password');
    await act(async () => { pw.props.onChange({target: {value: 'hunter2secret'}}); });
    const btn = revealButtons(renderer)[0];
    await act(async () => { btn.props.onClick(); });
    assert.equal(inputByLabel(renderer, 'Password').props.type, 'text');
    assert.equal(inputByLabel(renderer, 'Password').props.value, 'hunter2secret');
    assert.equal(inputByLabel(renderer, 'Password').props.name, 'password'); // login uses name for autofill fallback
  });

  // ---------- behavior: register Password + Confirm password ----------
  await test('register: both password fields start hidden with Show buttons', async () => {
    const {renderer} = await mountPage();
    await advanceRegisterToPasswords(renderer);
    const pw = inputByLabel(renderer, 'Password');
    const cf = inputByLabel(renderer, 'Confirm password');
    assert.equal(pw.props.type, 'password');
    assert.equal(cf.props.type, 'password');
    const buttons = revealButtons(renderer);
    assert.equal(buttons.length, 2);
    assert.ok(buttons.every(b => b.props['aria-label'] === 'Show password' && b.props['aria-pressed'] === false));
  });
  await test('register: Password and Confirm toggles are independent', async () => {
    const {renderer} = await mountPage();
    await advanceRegisterToPasswords(renderer);
    // Show Password only
    const showAll = revealButtons(renderer);
    await act(async () => { showAll[0].props.onClick(); });
    assert.equal(inputByLabel(renderer, 'Password').props.type, 'text');
    assert.equal(inputByLabel(renderer, 'Confirm password').props.type, 'password');
    let labels = revealButtons(renderer).map(b => b.props['aria-label']);
    assert.ok(labels.includes('Hide password') && labels.includes('Show password'));
    assert.equal(revealButtons(renderer).find(b => b.props['aria-label'] === 'Hide password').props['aria-pressed'], true);
    assert.equal(revealButtons(renderer).find(b => b.props['aria-label'] === 'Show password').props['aria-pressed'], false);
    // Show Confirm too
    const showRemaining = revealButtons(renderer).filter(b => b.props['aria-label'] === 'Show password');
    assert.equal(showRemaining.length, 1);
    await act(async () => { showRemaining[0].props.onClick(); });
    assert.equal(inputByLabel(renderer, 'Confirm password').props.type, 'text');
    assert.ok(revealButtons(renderer).every(b => b.props['aria-label'] === 'Hide password' && b.props['aria-pressed'] === true));
    // Hide Password only (Confirm stays visible)
    const hidePw = revealButtons(renderer)[0];
    await act(async () => { hidePw.props.onClick(); });
    assert.equal(inputByLabel(renderer, 'Password').props.type, 'password');
    assert.equal(inputByLabel(renderer, 'Confirm password').props.type, 'text');
  });
  await test('register: typed values survive toggling on both fields', async () => {
    const {renderer} = await mountPage();
    await advanceRegisterToPasswords(renderer);
    const pw = inputByLabel(renderer, 'Password');
    const cf = inputByLabel(renderer, 'Confirm password');
    await act(async () => { pw.props.onChange({target: {value: 'longpass123'}}); });
    await act(async () => { cf.props.onChange({target: {value: 'longpass123'}}); });
    for (const b of revealButtons(renderer)) {
      await act(async () => { b.props.onClick(); });
    }
    assert.equal(inputByLabel(renderer, 'Password').props.type, 'text');
    assert.equal(inputByLabel(renderer, 'Confirm password').props.type, 'text');
    assert.equal(inputByLabel(renderer, 'Password').props.value, 'longpass123');
    assert.equal(inputByLabel(renderer, 'Confirm password').props.value, 'longpass123');
  });
  await test('behavior: no password toggle exists before the login password step is reached', async () => {
    const {renderer} = await mountPage();
    assert.equal(revealButtons(renderer).length, 0);
    assert.equal(renderer.root.findAll(n => n.type === 'input' && n.props['aria-label'] === 'Password').length, 0);
  });

  console.log(`\n${passed} password-toggle checks passed`);
})().catch(err => { console.error(err); process.exit(1); });
