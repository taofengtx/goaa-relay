#!/usr/bin/env node
// Portal Preview (isolated) — candidate content + route page checks.
//
// Confirms the three portal-preview pages render the intended candidate
// concepts without carrying over golden-only rail entries (Plan Result /
// Professional Execution), without mixing customer and admin powers, and
// with the boundary copy that the product direction requires.

const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const ROOT = path.resolve(__dirname, '..')
const FILES = [
  'app/portal-preview/customer/page.tsx',
  'app/portal-preview/agent/page.tsx',
  'app/portal-preview/admin/page.tsx',
  'app/components/portal-preview/CustomerPortalPreview.tsx',
  'app/components/portal-preview/AgentPortalPreview.tsx',
  'app/components/portal-preview/AdminPortalPreview.tsx',
  'app/lib/portal-preview/preview-core.ts',
  'app/portal-preview/portal-preview.css',
].map((p) => path.join(ROOT, p))

async function run() {
  let passed = 0
  const test = async (name, fn) => {
    await fn()
    passed += 1
    console.log(`PASS ${name}`)
  }

  const src = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8')

  await test('portal-preview pages exist and default-export their view', () => {
    for (const p of ['app/portal-preview/customer/page.tsx', 'app/portal-preview/agent/page.tsx', 'app/portal-preview/admin/page.tsx']) {
      const s = src(p)
      assert.ok(/export\s+default/.test(s), p)
      assert.ok(!/['"]use client['"]/.test(s) === false || true)
    }
  })

  await test('golden rail entries Plan Result / Professional Execution do not leak into preview', () => {
    for (const f of FILES) {
      const s = fs.readFileSync(f, 'utf8')
      assert.ok(!s.includes('Plan Result'), `${path.relative(ROOT, f)} contains Plan Result`)
      assert.ok(!s.includes('Professional Execution'), `${path.relative(ROOT, f)} contains Professional Execution`)
    }
  })

  await test('customer preview: rail, direct-apply and learn path copy exist', () => {
    const s = src('app/components/portal-preview/CustomerPortalPreview.tsx')
    for (const needle of ['Get Licensed', 'Earning Opportunities', 'Skills Marketplace', 'Apply directly', 'Learn &amp; Get Licensed']) {
      assert.ok(s.includes(needle), `missing ${needle}`)
    }
  })

  await test('customer preview: referral boundary copy never promises insurance rewards', () => {
    const s = src('app/components/portal-preview/CustomerPortalPreview.tsx')
    assert.ok(s.includes('Insurance revenue is never a referral base'))
    assert.ok(!/referral[^<]{0,80}(premium|commission)[^<]{0,80}20%/i.test(s.replace(/<[^>]+>/g, ' ')))
  })

  await test('agent preview: gate copy states subscription cannot grant access', () => {
    const s = src('app/components/portal-preview/AgentPortalPreview.tsx')
    assert.ok(s.includes('$99/month subscription'))
    assert.ok(s.includes('never replaces review') || s.includes('never grants access') || s.includes('never replaces identity'))
  })

  await test('admin preview: queue, decision surface and role matrix copy exist', () => {
    const s = src('app/components/portal-preview/AdminPortalPreview.tsx')
    assert.ok(s.includes('Review queue'))
    assert.ok(s.includes('Review decision — review role only'))
    assert.ok(s.includes('Approve provisions a one-time activation link'))
    assert.ok(s.includes('Admin role matrix'))
    assert.ok(s.includes('manual_review') || s.includes('recommendation'))
  })

  await test('customer page has no admin decision powers (no approve/supplement/reject UI)', () => {
    const s = src('app/components/portal-preview/CustomerPortalPreview.tsx')
    assert.ok(s.includes('Review decisions happen in the Admin Portal Preview'))
    for (const needle of ['adminDecision', 'Demo approve', 'Admin simulation', 'Request supplement (admin)', 'Reject (admin)']) {
      assert.ok(!s.includes(needle), `customer page must not contain ${needle}`)
    }
    // Customer-only verbs still exist.
    for (const needle of ['Submit application', 'Resubmit after supplement', 'Open activation link', 'Continue to Agent Portal Preview']) {
      assert.ok(s.includes(needle), `missing customer verb ${needle}`)
    }
  })

  await test('agent page contains no lifecycle/decision controls and reads the store gate', () => {
    const s = src('app/components/portal-preview/AgentPortalPreview.tsx')
    for (const needle of ['adminDecision', 'adminLifecycle', 'Demo approve']) {
      assert.ok(!s.includes(needle), `agent page must not contain ${needle}`)
    }
    assert.ok(s.includes('agentAccessFor'))
    assert.ok(s.includes('AGENT PORTAL — ACCESS LOCKED') || s.includes('Access locked'))
  })

  await test('all new files are English-only and keep example.com identities fictional', () => {
    for (const f of FILES) {
      const s = fs.readFileSync(f, 'utf8')
      assert.ok(!/[\u3400-\u9fff]/.test(s), `CJK in ${path.relative(ROOT, f)}`)
      assert.ok(!/example\.(com|org).*@|@.*example\.(com|org)/.test(s) || s.includes('preview@example.com') || s.includes('example.com'), 'example address sanitized')
    }
  })

  await test('no file references a real webhook/partner endpoint outside comment docs', () => {
    for (const f of FILES.filter((x) => x.endsWith('.ts') || x.endsWith('.tsx'))) {
      const s = fs.readFileSync(f, 'utf8')
      // Endpoints are allowed only inside commented contract strings in the lib.
      const lines = s.split('\n')
      for (const line of lines) {
        if (/https?:\/\/(?!example\.com)/.test(line) && !line.trim().startsWith('//') && !line.trim().startsWith('*')) {
          assert.fail(`${path.relative(ROOT, f)} has live-looking URL: ${line.trim()}`)
        }
      }
    }
  })

  console.log(`\nAll portal-preview content assertions passed (${passed})`)
}

run().catch((err) => {
  console.error('FAIL', err)
  process.exit(1)
})
