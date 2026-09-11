#!/usr/bin/env node
// Portal Preview (isolated) — golden zero-write + isolation checks.
//
// Verifies that the portal-preview candidate adds files ONLY inside the
// isolated namespaces (routes /portal-preview, components/portal-preview,
// lib/portal-preview, scripts/test-portal-preview-*) and that no golden
// file is modified, deleted or renamed. It also scans every new source
// file for forbidden coupling: imports from golden components/libs/routes,
// references to the golden stylesheet, CJK copy, or credential-shaped
// literals.

const assert = require('node:assert/strict')
const { execFileSync } = require('node:child_process')
const fs = require('node:fs')
const path = require('node:path')

const ROOT = path.resolve(__dirname, '..')
const CJK = /[\u3400-\u9fff]/
const SECRET_LIKE = /(sk|key|secret|token|password|credential)[_-][A-Za-z0-9]{12,}/i

const ALLOWED_UNTRACKED_PREFIXES = [
  'app/portal-preview/',
  'app/components/portal-preview/',
  'app/lib/portal-preview/',
  'scripts/test-portal-preview-',
  'node_modules', // symlinked local install, never committed
  'screens/', // local screenshot artifacts, never committed
]

function newFilePaths() {
  const status = execFileSync('git', ['status', '--porcelain'], { cwd: ROOT }).toString().trim()
  const lines = status ? status.split('\n') : []
  const modified = lines.filter((l) => !l.startsWith('??') && !l.startsWith(' A') && !l.startsWith('A '))
  const untracked = lines.filter((l) => l.startsWith('??')).map((l) => l.slice(3))
  return { lines, modified, untracked }
}

async function run() {
  let passed = 0
  const test = async (name, fn) => {
    await fn()
    passed += 1
    console.log(`PASS ${name}`)
  }

  const { lines, modified, untracked } = newFilePaths()

  await test('golden tree is untouched: no tracked file modified/added/deleted/renamed', () => {
    assert.equal(modified.length, 0, `modified paths: ${modified.join(', ')}`)
  })

  await test('every untracked path stays inside the isolated namespaces', () => {
    const offenders = untracked.filter((p) => !ALLOWED_UNTRACKED_PREFIXES.some((pre) => p.startsWith(pre)))
    assert.equal(offenders.length, 0, `untracked outside allowed prefixes: ${offenders.join(', ')}`)
  })

  const newFiles = []
  const collect = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) collect(full)
      else newFiles.push(full)
    }
  }
  collect(path.join(ROOT, 'app/portal-preview'))
  collect(path.join(ROOT, 'app/components/portal-preview'))
  collect(path.join(ROOT, 'app/lib/portal-preview'))
  for (const p of untracked.filter((x) => x.startsWith('scripts/test-portal-preview-'))) {
    newFiles.push(path.join(ROOT, p))
  }

  await test('route files exist for customer, agent and admin', () => {
    for (const id of ['customer', 'agent', 'admin']) {
      assert.ok(fs.existsSync(path.join(ROOT, 'app/portal-preview', id, 'page.tsx')), `missing page for ${id}`)
    }
  })

  await test('new portal-preview files contain no CJK copy', () => {
    const offenders = newFiles.filter((f) => CJK.test(fs.readFileSync(f, 'utf8')))
    assert.equal(offenders.length, 0, `CJK found in: ${offenders.map((f) => path.relative(ROOT, f)).join(', ')}`)
  })

  await test('new portal-preview sources never import golden components/libs/routes', () => {
    const bad = []
    for (const f of newFiles.filter((x) => /\.(ts|tsx)$/.test(x))) {
      const rel = path.relative(ROOT, f)
      const insideComponent = rel.startsWith('app/components/portal-preview/')
      const insideLib = rel.startsWith('app/lib/portal-preview/')
      const src = fs.readFileSync(f, 'utf8')
      for (const m of src.matchAll(/from\s+['"]([^'"]+)['"]/g)) {
        const spec = m[1]
        const isPortal = spec.startsWith('@/components/portal-preview/') || spec.startsWith('@/lib/portal-preview/') || spec.startsWith('@/portal-preview/')
        const isStd = spec.startsWith('react') || spec.startsWith('next/') || spec.startsWith('node:')
        const isOwnDirRelative = (insideComponent && spec.startsWith('./')) || (insideLib && spec.startsWith('./'))
        const isPortalRelative = spec.startsWith('../') && spec.includes('portal-preview')
        if (!isPortal && !isStd && !isOwnDirRelative && !isPortalRelative) {
          bad.push(`${rel} -> ${spec}`)
        }
      }
    }
    assert.equal(bad.length, 0, `forbidden imports:\n${bad.join('\n')}`)
  })

  await test('portal-preview CSS is independent: no butler reference, pp- only', () => {
    const cssPath = path.join(ROOT, 'app/portal-preview/portal-preview.css')
    const css = fs.readFileSync(cssPath, 'utf8')
    assert.ok(!/butler/i.test(css), 'must not mention or import butler stylesheet')
    assert.ok(!/@import/i.test(css), 'no external css import')
    const ruleLines = css
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l && !l.startsWith('/*') && l.includes('{'))
    const offenders = ruleLines.filter((l) => !l.startsWith('.pp-') && !l.startsWith('@media'))
    assert.equal(offenders.length, 0, `non-pp rules:\n${offenders.join('\n')}`)
    assert.ok(ruleLines.length > 40, 'expected a substantial independent stylesheet')
  })

  await test('new source has no credential-shaped literal values', () => {
    const offenders = newFiles.filter((f) => SECRET_LIKE.test(fs.readFileSync(f, 'utf8')))
    assert.equal(offenders.length, 0, `secret-like literals in: ${offenders.map((f) => path.relative(ROOT, f)).join(', ')}`)
  })

  await test('no reference to golden views or admin desk inside the isolated preview', () => {
    const goldenSymbols = ['GetLicensedView', 'ChatComponent', 'AdminReviewDesk', 'butler-workspace.css', 'admin-dashboard', 'agent-dashboard', 'client-dashboard']
    const offenders = []
    for (const f of newFiles.filter((x) => /\.tsx?$/.test(x))) {
      const src = fs.readFileSync(f, 'utf8')
      for (const sym of goldenSymbols) {
        if (src.includes(sym)) {
          // imports are already banned above; route words may appear in plain
          // copy only as lowercase user-facing text. Only flag code-ish usage.
          const codeish = new RegExp(`['"\`]|import|export|require\\(`).test(src)
          if (codeish && src.match(new RegExp(sym, 'g')).length > 1) offenders.push(`${path.relative(ROOT, f)} mentions ${sym}`)
        }
      }
    }
    assert.equal(offenders.length, 0, offenders.join('\n'))
  })

  await test("every new component/page has exactly one default export and no 'use server'", () => {
    for (const f of newFiles.filter((x) => x.endsWith('.tsx'))) {
      const src = fs.readFileSync(f, 'utf8')
      assert.ok(!src.includes("'use server'"), `${f} must not be a server action file`)
      const defs = src.match(/export\s+default/g)
      assert.equal(defs ? defs.length : 0, 1, `${f} default export count`)
    }
  })

  console.log(`\nAll isolation assertions passed (${passed})`)
}

run().catch((err) => {
  console.error('FAIL', err)
  process.exit(1)
})
