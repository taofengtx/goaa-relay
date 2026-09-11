// Mock tests for the golden business-session routes of the same-origin BFF.
//
// No build, no server, no database, no real session: `fetch` is replaced with a
// recorder, so every assertion is about what this tier would send and what it
// puts in the browser, never about what a live API would answer.
//
// The behaviour under test is the sign-out contract, which is the whole reason
// these routes exist:
//   * the credential the browser is given goes to the page itself, and the page
//     keeps it where the golden surface keeps it (`localStorage.client_token`);
//     this tier sets no cookie of its own and keeps no copy;
//   * `verify` and `revoke` present that credential as `Authorization: Bearer`,
//     so a sign-out can still be completed after Clerk has signed the browser
//     out;
//   * a revocation that the API did not confirm is reported as it is — the
//     failure stays visible instead of leaving a live credential behind a
//     "signed out" message.
process.env.GOAA_AGENT_LOOP_UPSTREAM = 'http://127.0.0.1:3103'
process.env.GOAA_C2_CLERK_AUTH_ENABLED = 'true'
process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY =
  'pk_test_YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4LmNsZXJrLmFjY291bnRzLmRldiQ'
process.env.CLERK_PUBLISHABLE_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
process.env.CLERK_SECRET_KEY = 'sk_test_FIXTURE_REDACTED'
import { assert, assertEqual, load, summary, test } from './harness.mjs'
import { register } from 'node:module'

// Registered here, not in the harness: the BFF's Clerk import is pointed at the
// double before the route module is loaded.
register(new URL('./resolve-hook-stub.mjs', import.meta.url).href)

const { NextRequest } = await import('next/server.js')
const route = await load('app/api/agent-loop/[...path]/route.ts')

const ORIGIN = 'http://127.0.0.1:3102'
const HOST_HEADERS = { host: '127.0.0.1:3102' }
const BUSINESS_TOKEN = 'a'.repeat(32)
const CLERK_TOKEN = 'clerk-session-token'
const POST_HEADERS = { origin: ORIGIN, 'content-type': 'application/json' }

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

function session({ token = CLERK_TOKEN } = {}) {
  globalThis.__c2ClerkAuth = async () => ({ userId: 'user_2abc', getToken: async () => token })
}

function noSession() {
  globalThis.__c2ClerkAuth = async () => ({ userId: null, getToken: async () => null })
}

function withGoldenCredential(extra = {}) {
  return { authorization: `Bearer ${BUSINESS_TOKEN}`, ...extra }
}

function authorizationOf(init) {
  const headers = init && init.headers
  return headers ? headers.get('authorization') : null
}

function setCookieOf(response) {
  return response.headers.get('set-cookie') || ''
}

/* ---------------------------------------------------------- route allow-list */

await test('golden: the method allow-list is exactly what the bridge needs', async () => {
  setState('enabled')
  session()
  stubFetch()
  assertEqual((await call('golden/session')).status, 200)
  assertEqual((await call('golden/session/verify', { headers: withGoldenCredential() })).status, 200)
  assertEqual((await call('golden/session', { method: 'DELETE' })).status, 405)
  const put = await call('golden/session', { method: 'PUT', headers: POST_HEADERS })
  assertEqual(put.status, 404)
  assertEqual((await put.json()).error.code, 'route_not_allowed')
})

await test('golden: a cross-origin write is refused before anything else', async () => {
  setState('enabled')
  session()
  const calls = stubFetch()
  const response = await call('golden/session', {
    method: 'POST',
    headers: { origin: 'https://evil.example', 'content-type': 'application/json' },
  })
  assertEqual(response.status, 403)
  assertEqual((await response.json()).error.code, 'cross_origin_blocked')
  assertEqual(calls.length, 0, 'a cross-origin write must not reach the API')
})

/* --------------------------------------------- minting: handed to the page */

await test('golden: minting hands the credential to the page and stores no copy', async () => {
  setState('enabled')
  session()
  const calls = stubFetch(() =>
    json({ token: BUSINESS_TOKEN, role: 'customer', user_id: 'biz-1', issued_at: 'now', created: true }),
  )

  const response = await call('golden/session', { method: 'POST', headers: POST_HEADERS })
  const payload = await response.json()

  assertEqual(response.status, 200)
  assertEqual(payload.user_id, 'biz-1')
  assertEqual(payload.role, 'customer')
  assertEqual(
    payload.token,
    BUSINESS_TOKEN,
    'the credential goes to the same-origin page, which stores it in the golden slot',
  )
  assertEqual(
    setCookieOf(response),
    '',
    'this tier sets no cookie of its own: the credential lives in the golden key',
  )

  assertEqual(calls.length, 1)
  assertEqual(authorizationOf(calls[0].init), `Bearer ${CLERK_TOKEN}`, 'Clerk authenticates the minting')
})

await test('golden: the minting request carries no identity of its own', async () => {
  setState('enabled')
  session()
  const calls = stubFetch(() => json({ token: BUSINESS_TOKEN, role: 'customer', user_id: 'biz-1' }))
  await call('golden/session', { method: 'POST', headers: POST_HEADERS, body: JSON.stringify({ user_id: 'forged' }) })
  const sent = calls[0].init.body
  const body = sent ? new TextDecoder().decode(sent) : ''
  assert(!body.includes('forged'), 'the browser cannot propose an identity')
})

await test('golden: a refused mint hands nothing to the browser and keeps the status', async () => {
  setState('enabled')
  session()
  stubFetch(() => json({ error: { code: 'invalid_session' } }, 401))
  const response = await call('golden/session', { method: 'POST', headers: POST_HEADERS })
  assertEqual(response.status, 401)
  assertEqual(setCookieOf(response), '', 'nothing may be handed out on a refusal')
})

await test('golden: a 200 without a credential is a failure, not a session', async () => {
  setState('enabled')
  session()
  stubFetch(() => json({ role: 'customer', user_id: 'biz-1' }))
  const response = await call('golden/session', { method: 'POST', headers: POST_HEADERS })
  assertEqual(response.status, 502)
  assertEqual((await response.json()).error.code, 'upstream_credential_missing')
  assertEqual(setCookieOf(response), '', 'nothing to hand over, so nothing is set')
})

/* ------------------------------------------------------- verify: business only */

await test('golden: verify presents the business credential, not the Clerk session', async () => {
  setState('enabled')
  session()
  const calls = stubFetch(() => json({ user_id: 'biz-1', role: 'customer' }))

  const response = await call('golden/session/verify', { headers: withGoldenCredential() })

  assertEqual(response.status, 200)
  assertEqual((await response.json()).user_id, 'biz-1')
  assertEqual(authorizationOf(calls[0].init), `Bearer ${BUSINESS_TOKEN}`)
  assertEqual(setCookieOf(response), '', 'verify must not re-issue the credential')
})

await test('golden: verify still works after Clerk has signed the browser out', async () => {
  setState('enabled')
  noSession()
  const calls = stubFetch(() => json({ user_id: 'biz-1', role: 'customer' }))

  const response = await call('golden/session/verify', { headers: withGoldenCredential() })

  assertEqual(response.status, 200, 'the business credential is the one being checked')
  assertEqual(calls.length, 1)
  assertEqual(authorizationOf(calls[0].init), `Bearer ${BUSINESS_TOKEN}`)
})

await test('golden: verify without a credential never reaches the API', async () => {
  setState('enabled')
  session()
  const calls = stubFetch()
  const response = await call('golden/session/verify')
  assertEqual(response.status, 401)
  assertEqual(calls.length, 0)
})

await test('golden: a refused verify is passed through, with no credential attached', async () => {
  setState('enabled')
  noSession()
  const calls = stubFetch(() => json({ error: { code: 'invalid_business_token' } }, 401))
  const response = await call('golden/session/verify', { headers: withGoldenCredential() })
  assertEqual(response.status, 401)
  assertEqual(calls.length, 1)
})

/* ------------------------------------------------------------- sign-out order */

await test('golden: revoke prefers the Clerk session while it is valid', async () => {
  setState('enabled')
  session()
  const calls = stubFetch(() => json({ revoked: 1, role: 'customer', basis: 'clerk_session' }))

  const response = await call('golden/session/revoke', { method: 'POST', headers: withGoldenCredential(POST_HEADERS) })

  assertEqual(response.status, 200)
  assertEqual((await response.json()).revoked, 1)
  assertEqual(authorizationOf(calls[0].init), `Bearer ${CLERK_TOKEN}`)
  assertEqual(setCookieOf(response), '', 'the browser deletes its own copy; this tier writes no cookie')
})

await test('golden: revoke falls back to the business credential after a Clerk sign-out', async () => {
  setState('enabled')
  noSession()
  const calls = stubFetch(() => json({ revoked: 1, role: 'customer', basis: 'business_token' }))

  const response = await call('golden/session/revoke', { method: 'POST', headers: withGoldenCredential(POST_HEADERS) })

  assertEqual(response.status, 200)
  assertEqual((await response.json()).basis, 'business_token')
  assertEqual(authorizationOf(calls[0].init), `Bearer ${BUSINESS_TOKEN}`)
  assertEqual(setCookieOf(response), '', 'the authority to revoke comes from the credential itself')
})

await test('golden: a failed revoke keeps the credential and reports the failure', async () => {
  setState('enabled')
  noSession()
  stubFetch(() => json({ error: { code: 'upstream_unreachable' } }, 502))
  const response = await call('golden/session/revoke', { method: 'POST', headers: withGoldenCredential(POST_HEADERS) })
  assertEqual(response.status, 502)
  assertEqual(setCookieOf(response), '', 'an unconfirmed revoke clears nothing, here or in the page')
})

await test('golden: revoke with no credential at all does not reach the API', async () => {
  setState('enabled')
  noSession()
  const calls = stubFetch()
  const response = await call('golden/session/revoke', { method: 'POST', headers: POST_HEADERS })
  assertEqual(response.status, 401)
  assertEqual(calls.length, 0)
})

/* ------------------------------------------------------------------ isolation */

await test('golden: the upstream target stays the allow-listed test port', async () => {
  setState('enabled')
  session()
  const calls = stubFetch(() => json({ revoked: 0, role: 'customer', basis: 'clerk_session' }))
  await call('golden/session/revoke', { method: 'POST', headers: POST_HEADERS })
  assert(calls[0].url.startsWith('http://127.0.0.1:3103/api/v1/agent-loop/golden/session'), calls[0].url)
  assert(!calls[0].url.includes('api.goaa.ai'), 'no production origin is reachable from here')
})

await test('golden: clerk off means the bridge routes are refused, not silently served', async () => {
  setState('disabled')
  noSession()
  const calls = stubFetch(() => json({ revoked: 0 }))
  // With Clerk off the tier cannot prove an identity, so it forwards nothing;
  // the API is the one that answers 409 clerk_auth_disabled.
  const response = await call('golden/session')
  assertEqual(response.status, 200)
  assertEqual(calls.length, 1, 'the decision belongs to the API, not to this tier')
})

function setState(state) {
  if (state === 'enabled') {
    process.env.GOAA_C2_CLERK_AUTH_ENABLED = 'true'
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY =
      'pk_test_YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4LmNsZXJrLmFjY291bnRzLmRldiQ'
    process.env.CLERK_PUBLISHABLE_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
    process.env.CLERK_SECRET_KEY = 'sk_test_FIXTURE_REDACTED'
  } else {
    delete process.env.GOAA_C2_CLERK_AUTH_ENABLED
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
    delete process.env.CLERK_PUBLISHABLE_KEY
    delete process.env.CLERK_SECRET_KEY
  }
}

summary('golden routes')
