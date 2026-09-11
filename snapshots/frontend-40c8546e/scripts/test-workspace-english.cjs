// planning workspace English copy tests (2026-09-07, Round 12).
// Butler workspace sidebar + conversation title:
//   - "+ New" (was "＋ 新事项"), "Chat" (was "对话 · Chat"), "Matters" (was "事项 · Matters")
//   - eyebrow "Current planning task" kept; title = "AI Butler · <matter>" when a
//     matter is selected (user-entered name kept as-is, may be CJK) or just "AI Butler".
// Offline static render of the real ChatComponent TSX via transpile + JSX doubles;
// no browser / network / API / DB / payment.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'app/components/ChatComponent.tsx'), 'utf8');
const stateNames = [...source.matchAll(/const \[(\w+),\s*\w+\] = useState/g)].map(m => m[1]);

function transpile(text, name) {
  const result = ts.transpileModule(text, { fileName: name, reportDiagnostics: true, compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX,
  }});
  assert.equal((result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error).length, 0);
  return result.outputText;
}
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
let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log(`PASS ${name}`); }

(async () => {
  let index = 0;
  const storage = new Map();
  const state = {};
  const jsx = { jsx: (type, props) => ({ type, props }), jsxs: (type, props) => ({ type, props }), Fragment: 'Fragment' };
  const imports = {
    react: { useMemo: fn => fn(), useEffect: () => {}, useState: value => {
      const key = stateNames[index++];
      if (!(key in state)) state[key] = typeof value === 'function' ? value() : value;
      return [state[key], next => { state[key] = typeof next === 'function' ? next(state[key]) : next; }];
    } },
    'react/jsx-runtime': jsx,
    '../lib/openclaw': { chat: async () => ({ sessionId: 's', stage: 'intake', intent: 'tax_planning', knownFacts: {}, displayTitle: '保险保障规划', subIntent: null, response: 'x', connectionReady: false, productAction: null }) },
    '../lib/personal-agent-matter': { LEGACY_WORKSPACE_KEY: 'goaa_planning_workspace_v1', MATTER_RESTORE_EVENT: 'restore' },
    '../lib/customer-signout': { clearCustomerSession: () => ({}) },
    '../lib/golden-signout': { decideGoldenSignOut: async () => ({ status: 'legacy' }) },
  };
  for (const name of ['ProfessionalHandoffCard', 'ButlerMattersView', 'ButlerWelcome', 'PersonalAgentInbox', 'PersonalAgentKnowledge', 'AgentProblemSolvingModel', 'AgentMattersOverview', 'LoginMenu']) imports[`./${name}`] = { default: name };
  const browser = {
    localStorage: { getItem: k => storage.get(k) || null, setItem: (k, v) => storage.set(k, v), removeItem: k => storage.delete(k) },
    location: { assign: () => {} },
  };
  const out = {};
  vm.runInNewContext(transpile(source, 'ChatComponent.tsx'), {
    exports: out, require: id => { assert.ok(id in imports, `Unexpected import: ${id}`); return imports[id]; },
    console, window: browser,
  }, { filename: 'ChatComponent.tsx' });
  const ChatComponent = out.default;
  const render = () => { index = 0; return ChatComponent({ butlerMode: true }); };

  await test('sidebar: + New / Chat / Matters with old CJK strings gone', () => {
    const tree = render();
    const rail = walk(tree, n => n.type === 'aside' && n.props && n.props.className === 'workspace-rail');
    assert.equal(rail.length, 1);
    const buttons = walk(rail[0], n => n.type === 'button').map(b => textOf(b).trim());
    assert.ok(buttons.includes('+ New'), `+ New present (got ${JSON.stringify(buttons)})`);
    assert.ok(buttons.includes('Chat'), 'Chat present');
    assert.ok(buttons.includes('Matters'), 'Matters present');
    const whole = textOf(rail[0]);
    assert.ok(!whole.includes('新事项'), 'no 新事项 in sidebar');
    assert.ok(!whole.includes('对话'), 'no 对话 in sidebar');
    assert.ok(!whole.includes('事项 ·'), 'no 事项 · in sidebar');
  });

  await test('workspace title without selected matter shows New Matter', () => {
    state.displayTitle = 'GOAA Plan';
    state.intent = null;
    const tree = render();
    const head = walk(tree, n => n.type === 'div' && n.props && n.props.className === 'workspace-section-head');
    assert.equal(head.length, 1);
    const kicker = walk(head[0], n => n.type === 'span' && n.props && n.props.className === 'workspace-kicker');
    assert.equal(kicker.length, 1);
    assert.equal(textOf(kicker[0]), 'Current planning task', 'eyebrow kept');
    const h2 = walk(head[0], n => n.type === 'h2');
    assert.equal(textOf(h2[0]), 'New Matter');
    assert.ok(!textOf(head[0]).includes('AI Butler'), 'no AI Butler prefix without a matter');
    assert.ok(!textOf(head[0]).includes('Continuing Your Plan'));
    assert.ok(!textOf(head[0]).includes('Understanding Your Goals'));
  });

  await test('workspace title with a selected matter shows the matter name only (CJK kept)', () => {
    state.displayTitle = '保险保障规划';
    const tree = render();
    const head = walk(tree, n => n.type === 'div' && n.props && n.props.className === 'workspace-section-head');
    const h2 = walk(head[0], n => n.type === 'h2');
    assert.equal(textOf(h2[0]), '保险保障规划');
    assert.ok(!textOf(head[0]).includes('AI Butler ·'), 'matter name is not prefixed');
  });

  await test('source no longer contains the old CJK sidebar literals; non-butler New Plan kept', () => {
    assert.ok(!source.includes('＋ 新事项'));
    assert.ok(!source.includes('对话 · Chat'));
    assert.ok(!source.includes('事项 · Matters'));
    assert.ok(source.includes('＋ New Plan'), 'non-butler copy untouched');
  });

  if (passed === 0) throw new Error('no tests ran');
  console.log(`\nOK ${passed}/${passed} workspace-english tests passed.`);
})().catch(err => { console.error(err); process.exit(1); });
