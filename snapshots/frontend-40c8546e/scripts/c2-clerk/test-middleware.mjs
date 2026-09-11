// Mock tests for middleware.ts (no build, no server, no session, no OTP).
//
// The middleware is exercised through the real, official `clerkMiddleware()`
// from @clerk/nextjs@6.39.6 — nothing about Clerk is stubbed. Only the switch
// and the key material in process.env are varied, which is exactly the axis the
// deployment moves along.
//
// Set the credentials BEFORE importing the module: the SDK reads them when it
// builds the middleware.
import { assert, assertEqual, load, summary, test } from './harness.mjs'

process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY =
  'pk_test_YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4LmNsZXJrLmFjY291bnRzLmRldiQ'
process.env.CLERK_PUBLISHABLE_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
process.env.CLERK_SECRET_KEY = 'sk_test_FIXTURE_REDACTED'
process.env.GOAA_C2_CLERK_AUTH_ENABLED = 'true'

// The service's own advertised origin, exactly as the systemd unit supplies it
// (HOSTNAME/PORT on the 3102 unit). Next builds its internal `initUrl` from
// these two values, so the middleware can only recognise "itself" when the test
// harness configures the same origin the deployment does.
process.env.HOSTNAME = 'localhost'
process.env.PORT = '3102'

const { NextRequest } = await import('next/server.js')
const middleware = (await load('middleware.ts')).default
const { CLERK_ENTRY_PATH, CLERK_ENTRY_MARKER, CLERK_ENTRY_MARKER_VALUE } = await load('app/lib/clerk-entry.ts')

const ORIGIN = 'http://127.0.0.1:3102'
const event = { waitUntil() {}, passThroughOnException() {} }

function request(path, headers = {}) {
  return new NextRequest(`${ORIGIN}${path}`, { headers })
}

function rewrittenTo(response) {
  const value = response.headers.get('x-middleware-rewrite')
  // Next's middleware sandbox parses this header with `new NextURL(value)`
  // before the response leaves it, so the header must be an absolute URL: a
  // path-only value throws ERR_INVALID_URL. Parsing without a base proves it.
  return value ? new URL(value) : null
}

/** A request whose URL is not the deployment's own spelling (tunnel, alias...). */
function requestUrl(url) {
  return new NextRequest(url)
}

function passesThrough(response) {
  return response.headers.get('x-middleware-next') === '1'
}

/**
 * With Clerk in charge, a signed-out request is delivered through a same-URL
 * rewrite (that is how the SDK attaches its request headers), so "served the
 * page that was asked for" must be read from the rewrite target rather than
 * from `x-middleware-next`.
 */
function served(requestPath, response) {
  const target = rewrittenTo(response)
  if (!target) return passesThrough(response)
  const asked = new URL(ORIGIN + requestPath)
  return (
    target.pathname === asked.pathname && target.searchParams.toString() === asked.searchParams.toString()
  )
}

/** The path the response ultimately serves, whether by pass-through or rewrite. */
function servedPath(response) {
  const target = rewrittenTo(response)
  return target ? target.pathname : null
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

/* --------------------------------------------------------- switch disabled */

await test('clerk off: every path keeps the legacy behaviour (no rewrite, no redirect)', async () => {
  setState('disabled')
  for (const path of [
    '/agent-loop/customer',
    '/api/agent-loop/health',
    '/client-login?next=%2Fagent-loop%2Fcustomer',
    '/client-login',
    '/agent-login',
    '/agent-loop/login',
    '/goaa-clerk-login',
  ]) {
    const response = await middleware(request(path), event)
    assertEqual(response.status, 200, `${path} should pass through untouched`)
    assert(passesThrough(response), `${path} should not be rewritten or redirected`)
    assertEqual(response.headers.get('location'), null, `${path} must not redirect while Clerk is off`)
  }
})

await test('clerk off: the production exposure guard still blocks internal routes', async () => {
  setState('disabled')
  process.env.VERCEL_ENV = 'production'
  try {
    for (const path of ['/admin-dashboard', '/customer-order', '/order-live', '/agent-skill-engine']) {
      const response = await middleware(request(path), events())
      assertEqual(response.status, 404, `${path} must stay hidden in production`)
    }
    // Exact-only entries must not swallow the formal product route.
    for (const path of ['/customer-order-live', '/agent-dashboard/overview']) {
      const response = await middleware(request(path), events())
      assertEqual(response.status, 200, `${path} must stay reachable`)
    }
  } finally {
    delete process.env.VERCEL_ENV
  }
})

function events() {
  return { waitUntil() {}, passThroughOnException() {} }
}

/* ---------------------------------------------------------- switch enabled */

await test('clerk on: /agent-login redirects, server-side, to the Clerk card and the AI Agent portal', async () => {
  setState('enabled')
  // Round C1.8 (Tao): with Clerk in charge the golden agent sign-in form is
  // retired like /client-login's; its page file is untouched and still served
  // while Clerk is off (see the clerk-off test above).
  for (const path of ['/agent-login', '/agent-login/', '/agent-login?resume=1&reason=order&order=abc']) {
    const response = await middleware(request(path), event)
    assertEqual(response.status, 307, `${path} should redirect`)
    const target = new URL(response.headers.get('location'))
    assertEqual(`${target.pathname}${target.search}`, '/client-login?next=%2Fagent-loop%2Fagent', `redirect for ${path}`)
  }
})

await test('clerk on: the old /agent-loop/login alias redirects, keeping a valid next', async () => {
  setState('enabled')
  for (const path of ['/agent-loop/login', '/agent-loop/login/', '/agent-loop/login?next=%2F%2Fevil.example']) {
    const response = await middleware(request(path), event)
    assertEqual(response.status, 307, `${path} should redirect`)
    const target = new URL(response.headers.get('location'))
    assertEqual(`${target.pathname}${target.search}`, '/client-login?next=%2Fagent-loop%2Fcustomer', `redirect for ${path}`)
  }
  // The agent page's own bounce for a signed-out visitor returns to the agent page.
  const bounce = await middleware(request('/agent-loop/login?next=%2Fagent-loop%2Fagent'), event)
  assertEqual(bounce.status, 307)
  const target = new URL(bounce.headers.get('location'))
  assertEqual(`${target.pathname}${target.search}`, '/client-login?next=%2Fagent-loop%2Fagent')
})

await test('clerk on: a valid next rewrites /client-login to the internal page and marks it', async () => {
  setState('enabled')
  const response = await middleware(request('/client-login?next=%2Fagent-loop%2Fcustomer'), event)
  const target = rewrittenTo(response)
  assert(target, 'expected an internal rewrite')
  assertEqual(target.pathname, CLERK_ENTRY_PATH)
  assertEqual(target.searchParams.get('next'), '/agent-loop/customer')
  assertEqual(response.headers.get('x-middleware-request-x-goaa-clerk-entry'), CLERK_ENTRY_MARKER_VALUE)
})

await test('clerk on: /client-login without a valid next opens the card and lands on /planning', async () => {
  setState('enabled')
  // Round C1.7: the legacy form is retired while Clerk is in charge. A missing
  // or refused next is replaced by /planning, and no other query parameter
  // (the retired form's resume/reason/order/google) is carried along.
  for (const path of [
    '/client-login',
    '/client-login/',
    '/client-login?next=',
    '/client-login?next=//evil.example',
    '/client-login?next=https%3A%2F%2Fevil.example',
    '/client-login?next=%2Fagent-loop%2F..%2Fadmin',
    '/client-login?next=%2Fagent-loop%2Flogin',
    '/client-login?next=%2Fadmin-dashboard',
    '/client-login?resume=1&reason=purchase',
    '/client-login?google=done',
    '/client-login?order=abc&next=%2Fplanning%2Fx',
  ]) {
    const response = await middleware(request(path), event)
    assertEqual(response.status, 200, `${path} should serve a page`)
    assertEqual(response.headers.get('location'), null, `${path} must not redirect`)
    const target = rewrittenTo(response)
    assert(target, `${path}: expected an internal rewrite`)
    assertEqual(target.pathname, CLERK_ENTRY_PATH, `${path} must reach the card`)
    assertEqual(target.searchParams.get('next'), '/planning', `${path} must land on /planning`)
    for (const dropped of ['resume', 'reason', 'order', 'google']) {
      assertEqual(target.searchParams.has(dropped), false, `${path} carried ${dropped}`)
    }
    assertEqual(response.headers.get('x-middleware-request-x-goaa-clerk-entry'), CLERK_ENTRY_MARKER_VALUE)
  }
})

await test('clerk on: next=/planning is kept as it is', async () => {
  setState('enabled')
  const response = await middleware(request('/client-login?next=%2Fplanning&resume=1'), event)
  const target = rewrittenTo(response)
  assert(target, 'expected an internal rewrite')
  assertEqual(target.pathname, CLERK_ENTRY_PATH)
  assertEqual(target.searchParams.get('next'), '/planning')
  assertEqual(target.searchParams.has('resume'), false)
})

await test('clerk on: a client-supplied marker never survives the middleware', async () => {
  setState('enabled')
  const browser = { host: '127.0.0.1:3102', 'user-agent': 'c2-clerk-mock' }
  const forged = await middleware(
    request('/agent-loop/customer', { ...browser, [CLERK_ENTRY_MARKER]: CLERK_ENTRY_MARKER_VALUE }),
    event,
  )
  assert(served('/agent-loop/customer', forged), 'expected the asked-for page')
  assertEqual(forged.headers.get('x-middleware-request-x-goaa-clerk-entry'), null, 'a forged marker reached the page')
  const overrides = (forged.headers.get('x-middleware-override-headers') || '').split(',').map((s) => s.trim())
  assert(!overrides.includes(CLERK_ENTRY_MARKER), `marker survived in the override list: ${overrides.join(',')}`)
  assert(overrides.includes('host'), 'the override list was rebuilt from scratch')

  // ...and on the one page that acts on the marker, the middleware's own value
  // is what the page sees.
  const internal = await middleware(
    request('/client-login?next=%2Fagent-loop%2Fcustomer', { ...browser, [CLERK_ENTRY_MARKER]: 'forged' }),
    event,
  )
  assertEqual(internal.headers.get('x-middleware-request-x-goaa-clerk-entry'), CLERK_ENTRY_MARKER_VALUE)
})

await test('clerk on: a loopback rewrite stays absolute and carries this service origin', async () => {
  setState('enabled')
  // Next normalises 127.0.0.1 to its own `localhost` spelling, so a rewrite it
  // hands back can no longer match a service that advertises 127.0.0.1; the
  // middleware puts both on the service's configured origin instead.
  const response = await middleware(request('/agent-loop/customer', { host: '127.0.0.1:3102' }), event)
  const raw = response.headers.get('x-middleware-rewrite')
  assert(raw !== null, 'the decorated request must still carry its rewrite')
  const target = rewrittenTo(response)
  assertEqual(target.origin, 'http://localhost:3102')
  assertEqual(target.pathname, '/agent-loop/customer')
  assert(served('/agent-loop/customer', response), 'the rewrite must still serve the asked-for page')
})

await test('clerk on: another loopback port names a different service and is left untouched', async () => {
  setState('enabled')
  // A rewrite aimed at another local port (3103, a stub, ...) must never be
  // retargeted onto this service.
  const forwarded = await middleware(requestUrl('http://localhost:13102/api/agent-loop/health'), event)
  assertEqual(forwarded.headers.get('x-middleware-rewrite'), 'http://localhost:13102/api/agent-loop/health')

  const entry = await middleware(
    requestUrl('http://localhost:13102/client-login?next=%2Fagent-loop%2Fcustomer'),
    event,
  )
  assertEqual(
    entry.headers.get('x-middleware-rewrite'),
    'http://localhost:13102/goaa-clerk-login?next=%2Fagent-loop%2Fcustomer',
  )
  assertEqual(entry.headers.get('x-middleware-request-x-goaa-clerk-entry'), CLERK_ENTRY_MARKER_VALUE)
})

await test('clerk on: an https target on this host and port is left untouched', async () => {
  setState('enabled')
  // This service speaks http; an https rewrite is not this service's own URL.
  const response = await middleware(requestUrl('https://localhost:3102/agent-loop/customer'), event)
  const raw = response.headers.get('x-middleware-rewrite')
  assert(raw && raw.startsWith('https://localhost:3102/'), `https rewrite was modified: ${raw}`)
})

await test('clerk on: a rewrite that leaves loopback is left untouched', async () => {
  setState('enabled')
  const response = await middleware(requestUrl('https://app.example.test/agent-loop/customer'), event)
  const raw = response.headers.get('x-middleware-rewrite')
  assert(raw && raw.startsWith('https://app.example.test/'), `non-loopback rewrite was modified: ${raw}`)
})

await test('clerk on: without a configured PORT the rewrite is left untouched', async () => {
  setState('enabled')
  const port = process.env.PORT
  delete process.env.PORT
  try {
    // Guard only: the SDK already emits the request URL, so this case cannot
    // be told apart from "unified to the same value"; it exists to prove the
    // middleware neither throws nor invents an origin without a configured
    // PORT. The discriminating checks are the port/protocol/host cases above.
    const response = await middleware(requestUrl('http://localhost:3102/api/agent-loop/health'), event)
    assertEqual(response.headers.get('x-middleware-rewrite'), 'http://localhost:3102/api/agent-loop/health')
  } finally {
    process.env.PORT = port
  }
})

await test('clerk on: forged forwarding headers cannot move the rewrite origin', async () => {
  setState('enabled')
  // The origin comes from this service's own configuration, so a client
  // supplied Host / X-Forwarded-* / Forwarded header must not change it.
  const clean = await middleware(request('/client-login?next=%2Fagent-loop%2Fcustomer'), event)
  const forged = await middleware(
    request('/client-login?next=%2Fagent-loop%2Fcustomer', {
      host: 'evil.example:3102',
      'x-forwarded-host': 'evil.example',
      'x-forwarded-proto': 'https',
      forwarded: 'host=evil.example;proto=https',
    }),
    event,
  )
  const cleanRaw = clean.headers.get('x-middleware-rewrite')
  assert(cleanRaw !== null && cleanRaw.startsWith('http://localhost:3102/'), `unexpected rewrite: ${cleanRaw}`)
  assertEqual(forged.headers.get('x-middleware-rewrite'), cleanRaw)
  assertEqual(rewrittenTo(forged).origin, 'http://localhost:3102')
})

await test('clerk on: the official middleware decorates the response', async () => {
  setState('enabled')
  const response = await middleware(request('/agent-loop/customer'), event)
  const headers = {}
  response.headers.forEach((value, key) => {
    headers[key] = value
  })
  const probe = Object.keys(headers).filter((key) => key.includes('clerk') || key.includes('auth'))
  assert(probe.length > 0, `no Clerk decoration found on the response: ${JSON.stringify(headers)}`)
})

/* ----------------------------------------------------- switch misconfigured */

await test('clerk on but incomplete: Clerk-dependent paths refuse, the rest of the site is untouched', async () => {
  setState('misconfigured')
  for (const path of [
    '/agent-loop/customer',
    '/api/agent-loop/health',
    '/client-login?next=%2Fagent-loop%2Fcustomer',
    // Round C1.7: every /client-login visit is the Clerk card, so a half
    // configured deployment refuses it too instead of showing the retired form.
    '/client-login',
    '/client-login?resume=1&reason=purchase',
    '/agent-loop/login',
    // Round C1.8: the golden agent sign-in is retired too while Clerk is on.
    '/agent-login',
    '/goaa-clerk-login',
  ]) {
    const response = await middleware(request(path), event)
    assertEqual(response.status, 503, `${path} must refuse rather than serve stale auth`)
    const body = await response.text()
    assert(!body.includes('pk_') && !body.includes('sk_'), 'the refusal leaked a key')
  }
  // A half-configured deployment must not take the marketing site or any other
  // existing page down with it.
  for (const path of ['/', '/pricing', '/planning', '/agent-dashboard/overview']) {
    const response = await middleware(request(path), event)
    assertEqual(response.status, 200, `${path} must not be affected`)
    assert(passesThrough(response), `${path} should pass through`)
  }
})

summary('c2 clerk middleware')
