// Shape tests: the invariants that must hold in the *source*, independent of
// any runtime path. These are the ones a reviewer would otherwise have to check
// by hand — above all that the production login page was not touched.
//
// Read-only: this file runs `git diff`/`git status` and reads files. It changes
// nothing, builds nothing and talks to nothing.
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import { assert, assertEqual, summary, test } from './harness.mjs'

const ROOT = process.cwd()

function git(...args) {
  return execFileSync('git', args, { cwd: ROOT, encoding: 'utf8' })
}

function read(path) {
  return fs.readFileSync(`${ROOT}/${path}`, 'utf8')
}

function exists(path) {
  return fs.existsSync(`${ROOT}/${path}`)
}

/* ------------------------------------------------- the production page */

await test('/client-login/page.tsx is byte-identical to the committed file', async () => {
  const page = 'app/client-login/page.tsx'
  assertEqual(git('diff', '--name-only', '--', page).trim(), '', `${page} has uncommitted changes`)
  assertEqual(git('status', '--porcelain', '--', page).trim(), '', `${page} is modified`)
  assertEqual(git('diff', 'HEAD', '--', page).trim(), '', `${page} differs from HEAD`)
  // It is the real production sign-in page, not a shell of one.
  const source = read(page)
  assert(source.includes('api.goaa.ai'), 'the production page must still be the production page')
  assert(source.length > 20000, `unexpected size: ${source.length}`)
})

await test('the retired entries are untouched — the middleware redirects them, not the pages', async () => {
  for (const page of ['app/agent-login/page.tsx', 'app/agent-loop/login/page.tsx']) {
    if (!exists(page)) continue
    let tracked = true
    try {
      git('ls-files', '--error-unmatch', page)
    } catch {
      tracked = false
    }
    // app/agent-loop/login is itself part of the candidate; a page that was
    // already committed must not have moved.
    if (!tracked) continue
    assertEqual(git('status', '--porcelain', '--', page).trim(), '', `${page} is modified`)
    assertEqual(git('diff', 'HEAD', '--', page).trim(), '', `${page} differs from HEAD`)
  }
})

/* ------------------------------------------------------ the internal page */

await test('the internal sign-in page exists at a routable path and guards itself', async () => {
  const page = 'app/goaa-clerk-login/page.tsx'
  assert(exists(page), `${page} is missing`)
  assert(!exists('app/__goaa'), 'the unroutable app/__goaa folder is back')
  const source = read(page)
  assert(/dynamic = ["']force-dynamic["']/.test(source), 'the page must not be cached')
  assert(source.includes('clerkAuthState'), 'the page must consult the switch')
  assert(source.includes("!== 'enabled'") || source.includes("!== \"enabled\""), 'the page must refuse when off')
  assert(source.includes('CLERK_ENTRY_MARKER'), 'the page must check the middleware marker')
  assert(source.includes('CLERK_ENTRY_MARKER_VALUE'), 'the page must compare the marker value')
  assert(source.includes('safeNextTarget'), 'the page must not trust a raw next')
  assert(!/referer/i.test(source), 'the gate must not depend on the Referer header')
})

/* ---------------------------------------------------------- the middleware */

await test('the middleware uses the official Clerk middleware, and refuses without swallowing', async () => {
  const source = read('middleware.ts')
  assert(source.includes("clerkMiddleware"), 'clerkMiddleware must be used')
  assert(/from ["']@clerk\/nextjs\/server["']/.test(source), 'it must come from the official package')
  assert(source.includes('clerkAuthState()'), 'the switch must gate it')
  // The three branches, in order: off -> legacy, half configured -> refuse,
  // otherwise the official middleware. A configuration error must not be caught
  // and turned into a quiet legacy response.
  const disabled = source.indexOf('state === "disabled"')
  const misconfigured = source.indexOf('state === "misconfigured"')
  const official = source.indexOf('clerkHandler(')
  assert(disabled !== -1 && misconfigured !== -1 && official !== -1, 'a branch is missing')
  assert(disabled < official && misconfigured < official, 'the refusals must come before the SDK call')
  const catchBlock = source.slice(source.indexOf('} catch'))
  assert(catchBlock.includes('misconfigured(request)'), 'a broken Clerk must refuse, not fall back')
})

await test('the middleware never verifies a token itself', async () => {
  for (const file of ['middleware.ts', 'app/lib/clerk-entry.ts']) {
    const source = read(file)
    for (const banned of ['jwt', 'jose', 'createHmac', 'verifySignature', 'decodeJwt']) {
      assert(!source.toLowerCase().includes(banned.toLowerCase()), `${file} looks like it verifies tokens (${banned})`)
    }
  }
})

/* ------------------------------------------------------------- the layout */

await test('ClerkProvider is only mounted when Clerk is actually in charge', async () => {
  const source = read('app/layout.tsx')
  assert(source.includes('ClerkProvider'), 'the provider is missing')
  // The gate is the switch *and* the public configuration, and the provider must
  // sit behind it: the page markup is built first and returned bare when the
  // gate is false, so the provider is only ever reached past the early return.
  assert(
    source.includes('clerkAuthState()') && /clerkState === ["']enabled["']/.test(source),
    'the provider must be gated by the switch',
  )
  assert(
    /const clerkAuth = .*clerkState === ["']enabled["'] && Boolean\(publishableKey\)/.test(source),
    'the gate must require both the switch and a publishable key',
  )
  const gateAt = source.indexOf('if (!clerkAuth) return page')
  const providerAt = source.indexOf('<ClerkProvider')
  assert(gateAt !== -1, 'the bare page must be returned when the gate is false')
  assert(providerAt > gateAt, 'the provider must be unreachable when the gate is false')
  assert(!source.includes('CLERK_SECRET_KEY'), 'the layout must never see the secret key')
})

/* -------------------------------------------------------------- one switch */

await test('there is exactly one switch across the candidate', async () => {
  const files = [
    'middleware.ts',
    'app/lib/clerk-entry.ts',
    'app/lib/agent-loop/server.ts',
    'app/api/agent-loop/[...path]/route.ts',
    'app/goaa-clerk-login/page.tsx',
  ]
  for (const file of files) {
    assert(!read(file).includes('GOAA_C2_CLERK_ENTRY'), `${file} still references the retired second switch`)
  }
  // clerk-entry.ts is allowed to look for the secret's presence (that is what
  // "configured" means); nothing else may touch it, and nothing may read it to
  // sign or verify anything.
  for (const file of files.filter((f) => f !== 'app/lib/clerk-entry.ts')) {
    assert(!read(file).includes('CLERK_SECRET_KEY'), `${file} must not read the secret key`)
  }
  const entry = read('app/lib/clerk-entry.ts')
  const usesSecret = entry
    .split('\n')
    .filter((line) => line.includes('CLERK_SECRET_KEY'))
  assert(usesSecret.length > 0, 'the switch cannot be evaluated without probing for the secret')
  for (const line of usesSecret) {
    assert(/readEnv\(["']CLERK_SECRET_KEY["']/.test(line), `unexpected use: ${line}`)
  }
})

await test('the internal page is the only new route the transition adds', async () => {
  const added = git('status', '--porcelain')
    .split('\n')
    .filter((line) => line.trim().startsWith('??') || /^ ?A/.test(line))
    .map((line) => line.slice(2).trim())
    .filter((path) => path.startsWith('app/'))
  for (const path of added) {
    assert(
      path.startsWith('app/agent-loop/') ||
        path.startsWith('app/api/') ||
        path.startsWith('app/components/agent-loop/') ||
        path === 'app/components/GoldenSessionBridge.tsx' ||
        path.startsWith('app/lib/') ||
        path === 'app/goaa-clerk-login/',
      `unexpected new app path: ${path}`,
    )
  }
})

summary('c2 clerk candidate shape')
