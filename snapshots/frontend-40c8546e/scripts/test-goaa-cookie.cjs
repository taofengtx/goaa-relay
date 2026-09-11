// GOAA signed-in cookie mirror offline tests (2026-09-04).
// Pure node: verifies host gating, flag-only content, set/clear strings,
// parsing, browser no-ops on dev hosts, and central clear inside
// clearCustomerSession. No network / browser / credentials.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
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
let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log(`PASS ${name}`); }

(async () => {
  const cookie = loadModule('app/lib/goaa-cookie.ts', {});

  await test('goaa hosts map to .goaa.ai domain', () => {
    for (const h of ['goaa.ai', 'planning.goaa.ai', 'www.goaa.ai', 'api.goaa.ai']) {
      assert.equal(cookie.cookieDomainForHost(h), '.goaa.ai', h);
    }
    for (const h of ['localhost', '127.0.0.1', 'preview-abc.example', 'notgoaa.ai', '', null, undefined]) {
      assert.equal(cookie.cookieDomainForHost(h), null, String(h));
    }
  });

  await test('set cookie is flag-only with exact domain/path/max-age/flags', () => {
    const s = cookie.buildSignedInSetCookie('.goaa.ai');
    assert.ok(s.startsWith('goaa_signed_in=1; Path=/; Domain=.goaa.ai; Max-Age=2592000; Secure; SameSite=Lax'), s);
    assert.ok(!/token|username|email|@|order/i.test(s), 'cookie must not contain identity content: ' + s);
    const dev = cookie.buildSignedInSetCookie(null);
    assert.ok(!dev.includes('Domain='), 'dev cookie must not include Domain: ' + dev);
  });

  await test('clear cookie has empty value + Max-Age=0 on same domain/path', () => {
    const c = cookie.buildSignedInClearCookie('.goaa.ai');
    assert.ok(c.startsWith('goaa_signed_in=; Path=/; Domain=.goaa.ai; Max-Age=0'), c);
  });

  await test('hasSignedInCookie parses cookie headers only for the flag', () => {
    assert.equal(cookie.hasSignedInCookie('goaa_signed_in=1; other=a'), true);
    assert.equal(cookie.hasSignedInCookie('goaa_signed_in=; Max-Age=0'), false);
    assert.equal(cookie.hasSignedInCookie('session=abc; pref=1'), false);
    assert.equal(cookie.hasSignedInCookie(null), false);
    assert.equal(cookie.hasSignedInCookie(''), false);
  });

  await test('browser write/clear are no-ops without DOM', () => {
    cookie.writeSignedInCookieToDocument();
    cookie.clearSignedInCookieFromDocument();
  });

  await test('browser helpers skip non-goaa hosts entirely', () => {
    const assignments = [];
    const windowStub = {
      location: { hostname: 'localhost' },
      document: { set cookie(v) { assignments.push(v); }, get cookie() { return assignments.join('; '); } },
    };
    const domCookie = loadModule('app/lib/goaa-cookie.ts', {}, { window: windowStub });
    domCookie.writeSignedInCookieToDocument();
    domCookie.clearSignedInCookieFromDocument();
    assert.equal(assignments.length, 0, 'no cookie writes on dev host');
  });

  await test('browser write emits flag cookie on goaa host', () => {
    const assignments = [];
    const windowStub = {
      location: { hostname: 'planning.goaa.ai' },
      document: { set cookie(v) { assignments.push(v); }, get cookie() { return assignments.join('; '); } },
    };
    const domCookie = loadModule('app/lib/goaa-cookie.ts', {}, { window: windowStub });
    domCookie.writeSignedInCookieToDocument();
    assert.equal(assignments.length, 1);
    assert.ok(assignments[0].startsWith('goaa_signed_in=1; Path=/; Domain=.goaa.ai;'));
    assert.ok(!/token|username/i.test(assignments[0]));
  });

  // clearCustomerSession keeps working offline and clears the cookie through
  // its central path when a goaa-host DOM is present.
  await test('clearCustomerSession central path clears cookie on goaa host', () => {
    const assignments = [];
    const windowStub = {
      location: { hostname: 'planning.goaa.ai' },
      document: { set cookie(v) { assignments.push(v); }, get cookie() { return assignments.join('; '); } },
    };
    const signout = loadModule('app/lib/customer-signout.ts',
      { './goaa-cookie': loadModule('app/lib/goaa-cookie.ts', {}, { window: windowStub }) },
      { window: windowStub });
    const local = storage({ client_token: 'tok', client_username: 'u', goaa_active_order_id: 'o' });
    const session = storage({ goaa_connect_attempt_pending_v1: 'x' });
    const migration = signout.clearCustomerSession(local, session);
    assert.equal(local.getItem('client_token'), null);
    assert.equal(local.getItem('goaa_active_order_id'), null);
    assert.equal(migration.username, 'u');
    assert.equal(assignments.length, 1, 'cookie clear should run once');
    assert.ok(assignments[0].startsWith('goaa_signed_in=; Path=/; Domain=.goaa.ai; Max-Age=0'));
  });

  await test('clearCustomerSession offline without DOM does not throw', () => {
    const signout = loadModule('app/lib/customer-signout.ts',
      { './goaa-cookie': loadModule('app/lib/goaa-cookie.ts', {}) });
    const local = storage({ client_token: 'tok' });
    signout.clearCustomerSession(local, storage());
    assert.equal(local.getItem('client_token'), null);
  });

  console.log(`\nOK ${passed} passed`);
  if (passed < 8) process.exit(1);
})().catch((err) => { console.error(err); process.exit(1); });
