// Mock tests for the same-origin BFF (app/api/agent-loop/[...path]/route.ts).
//
// No build, no server, no database, no real session: `fetch` is replaced with a
// recorder, so every assertion is about what this tier would send, never about
// what a live API would answer. The Clerk SDK's single `auth()` call is doubled
// for this run (stub-clerk-server.mjs) so the four answers it can give — a
// session, no session, no token, a throw — can each be pinned.
process.env.GOAA_AGENT_LOOP_UPSTREAM = 'http://127.0.0.1:3103'
process.env.GOAA_C2_CLERK_AUTH_ENABLED = 'true'
process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY =
  'pk_test_YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4LmNsZXJrLmFjY291bnRzLmRldiQ'
process.env.CLERK_PUBLISHABLE_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
process.env.CLERK_SECRET_KEY = 'sk_test_FIXTURE_REDACTED'
import { assert, assertEqual, load, summary, test } from './harness.mjs'
import { register } from 'node:module'
import { pathToFileURL } from 'node:url'

// Registered here, not in the harness: this extra hook is what points the BFF's
// Clerk import at the double, and it must be in place before the route module
// is loaded. See stub-clerk-server.mjs for why the double is sound and where
// the real SDK still runs.
register(new URL('./resolve-hook-stub.mjs', import.meta.url).href)

const { NextRequest } = await import('next/server.js')
const route = await load('app/api/agent-loop/[...path]/route.ts')
const { SESSION_COOKIE } = await load('app/lib/agent-loop/server.ts')

const ORIGIN = 'http://127.0.0.1:3102'
const HOST_HEADERS = { host: '127.0.0.1:3102' }

/** Replace global fetch with a recorder; returns the call log. */
function stubFetch(handler) {
  const calls = []
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url: String(url), init })
    return handler ? handler(String(url), init) : json({ ok: true })
  }
  return calls
}

function json(payload, status = 200, headers = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'content-type': 'application/json', ...headers },
  })
}

function call(path, { method = 'GET', headers = {}, body } = {}) {
  const request = new NextRequest(`${ORIGIN}/api/agent-loop/${path}`, {
    method,
    headers: { ...HOST_HEADERS, ...headers },
    body,
  })
  return route[method](request, { params: { path: path.split('/') } })
}

function setState(state) {
  if (state === 'enabled') {
    process.env.GOAA_C2_CLERK_AUTH_ENABLED = 'true'
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY =
      'pk_test_YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4LmNsZXJrLmFjY291bnRzLmRldiQ'
    process.env.CLERK_PUBLISHABLE_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
    process.env.CLERK_SECRET_KEY = 'sk_test_FIXTURE_REDACTED'
  } else if (state === 'disabled') {
    delete process.env.GOAA_C2_CLERK_AUTH_ENABLED
  } else {
    process.env.GOAA_C2_CLERK_AUTH_ENABLED = 'true'
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
    delete process.env.CLERK_PUBLISHABLE_KEY
    delete process.env.CLERK_SECRET_KEY
  }
}

function session({ userId = 'user_2abc', token = 'session-token-abc' } = {}) {
  globalThis.__c2ClerkAuth = async () => ({ userId, getToken: async () => token })
}

function noSession() {
  globalThis.__c2ClerkAuth = async () => ({ userId: null, getToken: async () => null })
}

/* ------------------------------------------------------- the real SDK edge */

await test('the real SDK refuses to answer outside a request (the fail-closed source)', async () => {
  const real = await import(
    pathToFileURL(`${process.cwd()}/node_modules/@clerk/nextjs/dist/cjs/server/index.js`).href
  )
  assertEqual(typeof real.auth, 'function')
  let threw = false
  try {
    await real.auth()
  } catch {
    threw = true
  }
  assert(threw, 'auth() outside a request must not fabricate a session')
})

/* -------------------------------------------------------------- no session */

await test('clerk on: no session, no upstream call, 401 from this tier', async () => {
  setState('enabled')
  noSession()
  const calls = stubFetch()
  const response = await call('auth/me')
  assertEqual(response.status, 401)
  assertEqual((await response.json()).error.code, 'clerk_session_required')
  assertEqual(calls.length, 0, 'the upstream must not be asked to guess')
})

await test('clerk on: a leftover GOAA session cookie authenticates nobody', async () => {
  setState('enabled')
  noSession()
  const calls = stubFetch()
  const response = await call('auth/me', { headers: { cookie: `${SESSION_COOKIE}=leftover-legacy-token` } })
  assertEqual(response.status, 401)
  assertEqual(calls.length, 0, 'the legacy cookie must not be forwarded while Clerk is on')
})

await test('clerk on: a session without a token is still unauthenticated', async () => {
  setState('enabled')
  globalThis.__c2ClerkAuth = async () => ({ userId: 'user_2abc', getToken: async () => null })
  const calls = stubFetch()
  const response = await call('auth/me')
  assertEqual(response.status, 401)
  assertEqual(calls.length, 0)
})

await test('clerk on: a failing auth() is refused, never retried as legacy', async () => {
  setState('enabled')
  globalThis.__c2ClerkAuth = async () => {
    throw new Error('clerk unavailable')
  }
  const calls = stubFetch()
  const response = await call('auth/me', { headers: { cookie: `${SESSION_COOKIE}=leftover-legacy-token` } })
  assertEqual(response.status, 401)
  assertEqual(calls.length, 0, 'a throw must not fall back to the legacy cookie')
})

/* --------------------------------------------------------- session present */

await test('clerk on: the Clerk session token is forwarded as a Bearer credential', async () => {
  setState('enabled')
  session({ token: 'clerk-session-token' })
  const calls = stubFetch(() => json({ id: 'user_2abc', roles: ['user'] }))
  const response = await call('auth/me')
  assertEqual(response.status, 200)
  assertEqual(calls.length, 1)
  assertEqual(calls[0].url, 'http://127.0.0.1:3103/api/v1/agent-loop/auth/me')
  assertEqual(calls[0].init.headers.get('authorization'), 'Bearer clerk-session-token')
})

await test('clerk on: no identity is asserted by this tier and no legacy cookie is sent', async () => {
  setState('enabled')
  session()
  const calls = stubFetch(() => json({ ok: true }))
  await call('auth/me', {
    headers: {
      cookie: `${SESSION_COOKIE}=leftover-legacy-token`,
      'x-goaa-user-id': 'attacker',
      'x-goaa-role': 'admin',
      'x-user-email': 'attacker@example.test',
      authorization: 'Bearer attacker-supplied',
    },
  })
  assertEqual(calls.length, 1)
  const sent = calls[0].init.headers
  assertEqual(sent.get('cookie'), null, 'no cookie may travel upstream')
  assertEqual(sent.get('x-goaa-user-id'), null)
  assertEqual(sent.get('x-goaa-role'), null)
  assertEqual(sent.get('x-user-email'), null)
  assertEqual(sent.get('authorization'), 'Bearer session-token-abc', 'a client-supplied credential must be replaced')
})

await test('clerk on: the public health probe is the only route served without a credential', async () => {
  setState('enabled')
  noSession()
  const calls = stubFetch(() => json({ database: { name: 'goaa_c2test' }, status: 'ok' }))
  const response = await call('health')
  assertEqual(response.status, 200)
  assertEqual(calls.length, 1)
  assertEqual(calls[0].init.headers.get('authorization'), null, 'health carries no credential')
})

/* ------------------------------------------------------- half configured */

await test('clerk half configured: 503 from this tier, no upstream call', async () => {
  setState('misconfigured')
  const calls = stubFetch()
  for (const path of ['auth/me', 'health']) {
    const response = await call(path)
    assertEqual(response.status, 503, `${path} must refuse`)
    assertEqual((await response.json()).error.code, 'clerk_misconfigured')
  }
  assertEqual(calls.length, 0)
})

/* ------------------------------------------------------------- clerk off */

await test('clerk off: the legacy cookie flows upstream exactly as it shipped', async () => {
  setState('disabled')
  const calls = stubFetch(() => json({ id: 'legacy-user' }))
  const response = await call('auth/me', { headers: { cookie: `${SESSION_COOKIE}=legacy-session-token` } })
  assertEqual(response.status, 200)
  assertEqual(calls.length, 1)
  assertEqual(calls[0].init.headers.get('authorization'), 'Bearer legacy-session-token')
})

await test('clerk off: without a cookie the upstream is still called (legacy has no local gate)', async () => {
  setState('disabled')
  const calls = stubFetch(() => json({ error: 'unauthenticated' }, 401))
  const response = await call('auth/me')
  assertEqual(response.status, 401)
  assertEqual(calls.length, 1, 'the legacy flow leaves the decision to the API')
})

await test('clerk off: login keeps the token server-side in the httpOnly cookie', async () => {
  setState('disabled')
  stubFetch(() => json({ access_token: 'issued-token', user: { id: 'u1' } }, 200))
  const response = await call('auth/login', {
    method: 'POST',
    headers: { origin: ORIGIN, 'content-type': 'application/json' },
    body: JSON.stringify({ email: 'someone@example.test', password: 'x'.repeat(12) }),
  })
  assertEqual(response.status, 200)
  const payload = await response.json()
  assertEqual(payload.access_token, undefined, 'the token must never reach the browser')
  const cookie = response.cookies.get(SESSION_COOKIE)
  assert(cookie, 'the session cookie must be issued')
  assertEqual(cookie.httpOnly, true)
  assertEqual(cookie.sameSite, 'lax')
})

await test('clerk on: login issues no legacy cookie at all', async () => {
  setState('enabled')
  session()
  stubFetch(() => json({ access_token: 'issued-token', user: { id: 'u1' } }, 200))
  const response = await call('auth/login', {
    method: 'POST',
    headers: { origin: ORIGIN, 'content-type': 'application/json' },
    body: JSON.stringify({ email: 'someone@example.test', password: 'x'.repeat(12) }),
  })
  assertEqual(response.status, 200)
  assertEqual(response.cookies.get(SESSION_COOKIE), undefined, 'Clerk is the only credential while it is on')
})

await test('a cross-origin request is refused before anything else happens', async () => {
  setState('disabled')
  const calls = stubFetch()
  const response = await call('auth/login', {
    method: 'POST',
    headers: { origin: 'https://evil.example', 'content-type': 'application/json' },
    body: JSON.stringify({ email: 'someone@example.test', password: 'x'.repeat(12) }),
  })
  assertEqual(response.status, 403)
  assertEqual(calls.length, 0)
})

summary('c2 clerk bff')
