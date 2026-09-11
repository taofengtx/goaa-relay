// ChatComponent (homepage / planner workspace) footer legal links (2026-09-06).
//
// Covers:
//   - footer Privacy anchor -> https://www.goaa.ai/privacy (target=_blank,
//     rel=noopener noreferrer), visible text "Privacy" unchanged;
//   - footer Terms anchor -> https://www.goaa.ai/terms (target=_blank,
//     rel=noopener noreferrer), visible text "Terms" unchanged;
//   - no leftover self-referencing <a href="/"> for Privacy/Terms;
//   - Security anchor intentionally untouched (out of legal-link scope).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'app/components/ChatComponent.tsx'), 'utf8');

let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log(`PASS ${name}`); }

(async () => {
  await test('source: footer Privacy anchor points to www.goaa.ai/privacy in new tab', () => {
    assert.match(src, /<a href="https:\/\/www\.goaa\.ai\/privacy" target="_blank" rel="noopener noreferrer">Privacy<\/a>/);
  });
  await test('source: footer Terms anchor points to www.goaa.ai/terms in new tab', () => {
    assert.match(src, /<a href="https:\/\/www\.goaa\.ai\/terms" target="_blank" rel="noopener noreferrer">Terms<\/a>/);
  });
  await test('source: no leftover self-referencing Privacy/Terms footer anchors', () => {
    const footer = src.match(/<footer className="goaa-footer">[\s\S]*?<\/footer>/);
    assert.ok(footer, 'goaa-footer not found');
    assert.doesNotMatch(footer[0], /<a href="\/">(Privacy|Terms)<\/a>/);
  });
  await test('source: footer keeps only the three original legal labels, Security untouched', () => {
    const footer = src.match(/<footer className="goaa-footer">[\s\S]*?<\/footer>/);
    const labels = [...footer[0].matchAll(/<a [^>]*>([^<]+)<\/a>/g)].map(m => m[1]);
    assert.deepEqual(labels, ['Privacy', 'Terms', 'Security']);
    assert.match(footer[0], /<a href="\/">Security<\/a>/);
  });

  console.log(`\n${passed} chat-footer legal-links checks passed`);
})().catch(err => { console.error(err); process.exit(1); });
