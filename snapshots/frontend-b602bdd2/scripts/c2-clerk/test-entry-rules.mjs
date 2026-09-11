// Mock tests for the Clerk entry rules (no build, no server, no session).
//
// These pin the two halves of the transition that are pure decisions:
//   * which switch state the app is in, and
//   * whether a `next` target may steer the internal rewrite.
import { assert, assertEqual, load, summary, test } from './harness.mjs'

const source = (await import('node:fs')).readFileSync
const entrySourcePath = 'app/lib/clerk-entry.ts'
const entry = await load(entrySourcePath)
const {
  AGENT_NEXT_PREFIX,
  CLERK_ENTRY_PATH,
  CLERK_SWITCH,
  DEFAULT_AGENT_NEXT,
  MATCHED_ENTRY_PATHS,
  RETIRED_LOGIN_PATHS,
  UNIFIED_LOGIN_PATH,
  clerkAuthState,
  clerkMisconfiguredDetail,
  isUnifiedLoginPath,
  retiredEntryRedirect,
  safeNextTarget,
  validateNextTarget,
} = entry

const PK = 'pk_test_abcdefghijklmnopqrstuvwx.abcdefghijklmnopqrstuv'
const SK = 'sk_test_FIXTURE_REDACTED'

/* ------------------------------------------------------------ switch state */

await test('switch absent (or explicitly off) leaves the app on the legacy flow', async () => {
  assertEqual(clerkAuthState({}), 'disabled')
  assertEqual(clerkAuthState({ [CLERK_SWITCH]: '' }), 'disabled')
  assertEqual(clerkAuthState({ [CLERK_SWITCH]: '0' }), 'disabled')
  assertEqual(clerkAuthState({ [CLERK_SWITCH]: 'false' }), 'disabled')
  assertEqual(clerkAuthState({ [CLERK_SWITCH]: 'OFF' }), 'disabled')
  // A publishable key on its own must not switch the site over.
  assertEqual(clerkAuthState({ NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: PK }), 'disabled')
})

await test('switch on without a complete configuration refuses instead of falling back', async () => {
  assertEqual(clerkAuthState({ [CLERK_SWITCH]: 'true' }), 'misconfigured')
  assertEqual(clerkAuthState({ [CLERK_SWITCH]: 'true', NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: PK }), 'misconfigured')
  assertEqual(clerkAuthState({ [CLERK_SWITCH]: 'true', CLERK_SECRET_KEY: SK }), 'misconfigured')
})

await test('an unreadable switch value refuses rather than guessing', async () => {
  assertEqual(clerkAuthState({ [CLERK_SWITCH]: 'maybe', NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: PK, CLERK_SECRET_KEY: SK }), 'misconfigured')
})

await test('switch on with a non-test key refuses', async () => {
  const live = 'pk_live_abcdefghijklmnopqrstuvwx.abcdefghijklmnopqrstuv'
  assertEqual(
    clerkAuthState({ [CLERK_SWITCH]: 'true', NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: live, CLERK_SECRET_KEY: SK }),
    'misconfigured',
  )
})

await test('switch on with a complete test configuration is the only enabled state', async () => {
  assertEqual(
    clerkAuthState({ [CLERK_SWITCH]: 'true', NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: PK, CLERK_SECRET_KEY: SK }),
    'enabled',
  )
  // CLERK_PUBLISHABLE_KEY is the server-side spelling of the same value.
  assertEqual(
    clerkAuthState({ [CLERK_SWITCH]: 'true', CLERK_PUBLISHABLE_KEY: PK, CLERK_SECRET_KEY: SK }),
    'enabled',
  )
})

await test('a misconfigured state names the missing variables but never their values', async () => {
  const detail = clerkMisconfiguredDetail({ [CLERK_SWITCH]: 'true' }).join(' ')
  assert(detail.includes('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY'), detail)
  assert(detail.includes('CLERK_SECRET_KEY'), detail)
  assert(!detail.includes('pk_') && !detail.includes('sk_'), `detail leaked a key: ${detail}`)
})

/* ------------------------------------------------------------------- next */

await test('next accepts the agent-loop paths it was designed for', async () => {
  for (const target of [
    '/agent-loop',
    '/agent-loop/customer',
    '/agent-loop/agent',
    '/agent-loop/apply',
    '/agent-loop/admin',
    DEFAULT_AGENT_NEXT,
  ]) {
    const result = validateNextTarget(target)
    assert(result.ok, `${target} should be accepted (${result.reason || ''})`)
    assertEqual(result.value, target)
  }
  assertEqual(DEFAULT_AGENT_NEXT.startsWith(`${AGENT_NEXT_PREFIX}/`), true)
})

await test('next rejects every shape that could leave the site or loop back', async () => {
  const cases = [
    [null, 'missing'],
    ['', 'missing'],
    ['/agent-loop/customer ', 'padded'],
    ['/agent-loop/customer\n', 'padded'],
    ['  /agent-loop/customer', 'padded'],
    ['/agent-loop/customer\u0000', 'control-character'],
    ['/agent-loop/customer\u007f', 'control-character'],
    ['/\\evil.example/agent-loop', 'backslash'],
    ['/agent-loop/%2f%2fevil.example', 'encoded-separator'],
    ['/agent-loop/%2F%2Fevil.example', 'encoded-separator'],
    ['/agent-loop/%5cevil.example', 'encoded-separator'],
    ['/agent-loop/%00', 'encoded-separator'],
    ['/agent-loop/%2e%2e/admin', 'encoded-dot-segment'],
    ['/agent-loop/%2E/admin', 'encoded-dot-segment'],
    ['agent-loop/customer', 'not-root-relative'],
    ['https://evil.example/agent-loop', 'not-root-relative'],
    ['//evil.example/agent-loop', 'protocol-relative'],
    ['/agent-loop/./../admin', 'dot-segment'],
    ['/agent-loop/../admin', 'dot-segment'],
    ['/agent-loop/customer?tab=roles', 'query-or-fragment'],
    ['/agent-loop/customer#x', 'query-or-fragment'],
    ['/admin-dashboard', 'outside-agent-loop'],
    ['/api/agent-loop/health', 'outside-agent-loop'],
    ['/agent-loop/login', 'login-loop'],
    // The public and internal login entries sit outside the agent area, so they
    // are refused before the loop check even runs. Refused either way.
    ['/client-login', 'outside-agent-loop'],
    ['/goaa-clerk-login', 'outside-agent-loop'],
    ['/agent-login', 'outside-agent-loop'],
  ]
  for (const [target, reason] of cases) {
    const result = validateNextTarget(target)
    assertEqual(result.ok, false, `${JSON.stringify(target)} must be refused`)
    assertEqual(result.reason, reason, `reason for ${JSON.stringify(target)}`)
  }
})

await test('a refused next carries no value at all', async () => {
  for (const target of ['//evil.example', '/agent-loop/../admin', 'https://evil.example', '/client-login']) {
    const result = validateNextTarget(target)
    assert(result.value === undefined, `${target} leaked a value: ${result.value}`)
  }
})

await test('safeNextTarget falls back to the default and never returns a refused value', async () => {
  assertEqual(safeNextTarget('/agent-loop/agent'), '/agent-loop/agent')
  assertEqual(safeNextTarget('//evil.example'), DEFAULT_AGENT_NEXT)
  assertEqual(safeNextTarget(null), DEFAULT_AGENT_NEXT)
  assertEqual(safeNextTarget(undefined), DEFAULT_AGENT_NEXT)
})

/* --------------------------------------------------------------- topology */

await test('the internal Clerk page is at a routable path (Next skips underscore segments)', async () => {
  assertEqual(CLERK_ENTRY_PATH, '/goaa-clerk-login')
  for (const segment of CLERK_ENTRY_PATH.split('/').filter(Boolean)) {
    assert(!segment.startsWith('_'), `segment ${segment} would be skipped by Next`)
  }
  // The retired private folder must be gone for good.
  const fs = await import('node:fs')
  assert(!fs.existsSync(`${process.cwd()}/app/__goaa`), 'app/__goaa still exists')
  assert(fs.existsSync(`${process.cwd()}/app/goaa-clerk-login/page.tsx`), 'internal page missing')
})

await test('the unified entry stays the one public login path', async () => {
  assertEqual(UNIFIED_LOGIN_PATH, '/client-login')
  assertEqual(isUnifiedLoginPath('/client-login'), true)
  assertEqual(isUnifiedLoginPath('/client-login/'), true)
  assertEqual(isUnifiedLoginPath('/agent-login'), false)
})

await test('the golden sign-in route is preserved and is NOT a retired entry', async () => {
  const { GOLDEN_LOGIN_PATH } = entry
  assertEqual(GOLDEN_LOGIN_PATH, '/agent-login')
  assert(
    !RETIRED_LOGIN_PATHS.includes('/agent-login'),
    'the golden /agent-login route must never be treated as a retired alias'
  )
  // ...including its trailing-slash spelling, which is the same route.
  assertEqual(retiredEntryRedirect('/agent-login'), null)
  assertEqual(retiredEntryRedirect('/agent-login/'), null)
  // a `next` can never bounce back into the golden route either
  assertEqual(validateNextTarget('/agent-login').ok, false)
})

await test('only the test-only alias redirects, and only into the test namespace', async () => {
  assert(RETIRED_LOGIN_PATHS.includes('/agent-loop/login'), 'agent-loop/login must be retired')
  assertEqual(RETIRED_LOGIN_PATHS.length, 1, 'the golden route must not be retired')
  for (const path of ['/agent-loop/login', '/agent-loop/login/']) {
    const target = retiredEntryRedirect(path)
    assertEqual(target, `/client-login?next=${encodeURIComponent(DEFAULT_AGENT_NEXT)}`, `redirect for ${path}`)
  }
  assertEqual(retiredEntryRedirect('/agent-loop/customer'), null)
  // the default landing is the test namespace, never a golden destination
  assertEqual(DEFAULT_AGENT_NEXT.startsWith(`${AGENT_NEXT_PREFIX}/`), true)
  for (const golden of ['/client-dashboard/orders', '/agent-dashboard', '/planning']) {
    assert(DEFAULT_AGENT_NEXT !== golden, `${golden} must not be the test landing point`)
  }
})

await test('the matcher covers both entries, the internal page and the agent loop', async () => {
  for (const required of [
    UNIFIED_LOGIN_PATH,
    CLERK_ENTRY_PATH,
    '/agent-login',
    '/agent-loop/login',
    '/agent-loop/:path*',
    '/api/agent-loop/:path*',
  ]) {
    assert(MATCHED_ENTRY_PATHS.includes(required), `matcher misses ${required}`)
  }
  assert(!MATCHED_ENTRY_PATHS.some((p) => p.includes('logout')), 'no logout route was added')
})

await test('the candidate still has exactly one switch', async () => {
  const fs = await import('node:fs')
  const files = ['middleware.ts', 'app/lib/clerk-entry.ts', 'app/lib/agent-loop/server.ts']
  const text = files.map((f) => fs.readFileSync(`${process.cwd()}/${f}`, 'utf8')).join('\n')
  assert(text.includes(CLERK_SWITCH), 'the shared switch is missing')
  assert(!text.includes('GOAA_C2_CLERK_ENTRY'), 'the retired second switch is still referenced')
})

summary('c2 clerk entry rules')
