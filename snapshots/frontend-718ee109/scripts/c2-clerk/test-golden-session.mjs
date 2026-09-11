// Mock tests for the golden business-session client (app/lib/golden-session.ts).
//
// No build, no server, no Clerk, no database: `fetch` is injected, so every
// assertion is about what this layer would do and in what order. The order is
// the point — a sign-out that revokes *after* clearing, or that reports success
// when revocation failed, is the exact bug this file exists to catch.
//
// The last block runs a whole lifecycle against a small in-memory model of the
// API, where the credential is held the way a cookie is (invisibly to the
// module): login, refresh, re-login, sign-out, and the check that the previous
// credential is refused afterwards.
import { assert, assertEqual, load, summary, test } from './harness.mjs'

const mod = await load('app/lib/golden-session.ts')
const {
  GoldenSessionError,
  GOLDEN_SESSION_PATH,
  assertGoldenTokenShape,
  clearGoldenCredential,
  GOLDEN_CLIENT_TOKEN_KEY,
  readGoldenCredential,
  storeGoldenCredential,
  assertTestOnlyTarget,
  bootstrapBusinessSession,
  checkBusinessSession,
  clearMarker,
  endBusinessSession,
  isTestOnlyTarget,
  readMarker,
  revokeBusinessSession,
  signOutGoldenSession,
  startBusinessSession,
  writeMarker,
} = mod

const BUSINESS_ID = '385a3acc-1f3d-4a93-b3db-325ea351959c'
const TOKEN = 'a'.repeat(32)

function json(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'content-type': 'application/json' },
  })
}

function recorder(handler) {
  const calls = []
  const fetcher = async (target, init = {}) => {
    calls.push({ target, method: (init.method || 'GET').toUpperCase(), init })
    return handler(target, init)
  }
  return { fetcher, calls }
}

/* --------------------------------------------------------------- the target */

await test('only this origin\u2019s agent-loop routes are acceptable targets', () => {
  assert(isTestOnlyTarget(GOLDEN_SESSION_PATH), 'the session path must be allowed')
  assert(isTestOnlyTarget(`${GOLDEN_SESSION_PATH}/verify`))
  assert(isTestOnlyTarget(`${GOLDEN_SESSION_PATH}/revoke`))
})

await test('no production origin can be reached, however it is spelled', () => {
  for (const bad of [
    'https://api.goaa.ai/api/v1/order',
    'https://planning.goaa.ai/agent-login',
    '//api.goaa.ai/api/v1/order',
    'http://127.0.0.1:3100/api/agent-loop/golden/session',
    'http://127.0.0.1:3101/api/agent-loop/golden/session',
    'javascript:alert(1)',
    '/api/agent-loop/../../etc/passwd',
    '/api/agent-loop/golden/session\u0000',
    '/api/agent-loop/golden/session\\..\\x',
    '/other/api/agent-loop/golden/session',
    '',
    null,
    undefined,
  ]) {
    assert(!isTestOnlyTarget(bad), `must be refused: ${String(bad)}`)
  }
  assertEqual(assertTestOnlyTarget(GOLDEN_SESSION_PATH), GOLDEN_SESSION_PATH)
  let threw = false
  try {
    assertTestOnlyTarget('https://api.goaa.ai/api/v1/order')
  } catch (error) {
    threw = error instanceof GoldenSessionError && error.code === 'target_not_allowed'
  }
  assert(threw, 'a production target must throw, not be quietly rewritten')
})

await test('only a well-formed business credential is ever accepted', () => {
  assertEqual(assertGoldenTokenShape(TOKEN), TOKEN)
  for (const bad of [
    'not-a-token',
    TOKEN.toUpperCase(),
    `${TOKEN}0`,
    TOKEN.slice(0, 31),
    '',
    null,
    undefined,
    42,
    { token: TOKEN },
  ]) {
    let threw = false
    try {
      assertGoldenTokenShape(bad)
    } catch (error) {
      threw = error instanceof GoldenSessionError && error.code === 'credential_malformed'
    }
    assert(threw, `must be refused as a credential: ${JSON.stringify(bad)}`)
  }
})

await test('the credential is kept in the golden slot and can be deleted again', () => {
  const storage = memoryStorage()
  storeGoldenCredential(storage, TOKEN)
  assertEqual(readGoldenCredential(storage), TOKEN)
  assertEqual(
    storage.getItem(GOLDEN_CLIENT_TOKEN_KEY),
    TOKEN,
    'the golden surface reads this exact key',
  )
  // A value that is not a credential must not reach storage at all.
  let threw = false
  try {
    storeGoldenCredential(storage, 'nope')
  } catch (error) {
    threw = error instanceof GoldenSessionError && error.code === 'credential_malformed'
  }
  assert(threw, 'nothing but a well-formed credential may be written')
  assertEqual(readGoldenCredential(storage), TOKEN, 'the bad write changed nothing')
  clearGoldenCredential(storage)
  assertEqual(readGoldenCredential(storage), null)
})

/* -------------------------------------------------------------- the reads */

await test('a live business session is reported with its principal', async () => {
  const { fetcher, calls } = recorder(() => json({ user_id: BUSINESS_ID, role: 'customer' }))
  const result = await checkBusinessSession(fetcher)
  assertEqual(result.state, 'live')
  assertEqual(result.session.user_id, BUSINESS_ID)
  assertEqual(result.session.role, 'customer')
  assertEqual(calls[0].method, 'GET', 'checking must be a read')
  assertEqual(calls[0].target, `${GOLDEN_SESSION_PATH}/verify`)
})

await test('a refused credential is absent, not an error', async () => {
  for (const status of [401, 403, 404]) {
    const { fetcher } = recorder(() => json({ error: { code: 'invalid_business_token' } }, status))
    assertEqual((await checkBusinessSession(fetcher)).state, 'absent', `status ${status}`)
  }
})

await test('a service that cannot be asked is unknown, not "absent"', async () => {
  const failing = async () => {
    throw new TypeError('fetch failed')
  }
  assertEqual((await checkBusinessSession(failing)).state, 'unavailable')
  const { fetcher } = recorder(() => json({ error: {} }, 502))
  assertEqual((await checkBusinessSession(fetcher)).state, 'unavailable')
  const { fetcher: empty } = recorder(() => json({ role: 'customer' }))
  assertEqual((await checkBusinessSession(empty)).state, 'unavailable')
})

/* ------------------------------------------------------------- the start-up */

await test('starting resumes a live session and mints nothing', async () => {
  const { fetcher, calls } = recorder(() => json({ user_id: BUSINESS_ID, role: 'customer' }))
  const result = await startBusinessSession(fetcher)
  assertEqual(result.state, 'live')
  assertEqual(result.created, false, 'a refresh must not rotate the credential')
  assertEqual(calls.length, 1, 'exactly one read, no write')
  assertEqual(calls[0].method, 'GET')
})

await test('starting mints only when the credential is absent', async () => {
  const storage = memoryStorage()
  const { fetcher, calls } = recorder((target, init) => {
    if ((init.method || 'GET').toUpperCase() === 'POST') {
      return json({ user_id: BUSINESS_ID, role: 'customer', created: true, token: TOKEN })
    }
    return json({ error: { code: 'invalid_business_token' } }, 401)
  })
  const result = await startBusinessSession(fetcher, { credential: null, storage })
  assertEqual(result.state, 'live')
  assertEqual(result.created, true)
  assertEqual(calls.map((c) => c.method).join(','), 'GET,POST', 'read first, then write')
  assertEqual(calls[1].target, GOLDEN_SESSION_PATH)
  assertEqual(
    readGoldenCredential(storage),
    TOKEN,
    'the minted credential lands in the golden slot the browser reads',
  )
})

await test('an unreachable service is not papered over with a fresh credential', async () => {
  const failing = async () => {
    throw new TypeError('fetch failed')
  }
  const result = await startBusinessSession(failing)
  assertEqual(result.state, 'unavailable')
})

await test('a refused mint is a failure with a message, never a silent success', async () => {
  const { fetcher } = recorder((target, init) =>
    (init.method || 'GET').toUpperCase() === 'POST'
      ? json({ error: { code: 'clerk_session_required' } }, 401)
      : json({ error: {} }, 401),
  )
  const result = await startBusinessSession(fetcher)
  assertEqual(result.state, 'failed')
  assert(result.message.includes('401'), result.message)
})

await test('a mint that returns no customer principal is refused', async () => {
  const bootstrap = (payload) =>
    recorder((target, init) =>
      (init.method || 'GET').toUpperCase() === 'POST' ? json(payload) : json({}, 401),
    ).fetcher

  let threw = false
  try {
    await bootstrapBusinessSession(bootstrap({ user_id: BUSINESS_ID, role: 'agent' }))
  } catch (error) {
    threw = error instanceof GoldenSessionError && error.code === 'bootstrap_invalid'
  }
  assert(threw, 'an agent role must not be accepted through this path')

  threw = false
  try {
    await bootstrapBusinessSession(bootstrap({ role: 'customer' }))
  } catch (error) {
    threw = error instanceof GoldenSessionError && error.code === 'bootstrap_invalid'
  }
  assert(threw, 'a missing principal must not be accepted')

  threw = false
  const storage = memoryStorage()
  try {
    await bootstrapBusinessSession(
      recorder((target, init) =>
        (init.method || 'GET').toUpperCase() === 'POST'
          ? json({ user_id: BUSINESS_ID, role: 'customer', token: 'not-a-credential' })
          : json({}, 401),
      ).fetcher,
      storage,
    )
  } catch (error) {
    threw = error instanceof GoldenSessionError && error.code === 'credential_malformed'
  }
  assert(threw, 'a malformed credential is refused, not stored')
  assertEqual(readGoldenCredential(storage), null, 'and nothing was written to the golden slot')

  // A well-formed one, on the other hand, is exactly what gets stored.
  const good = memoryStorage()
  const stored = await bootstrapBusinessSession(
    recorder((target, init) =>
      (init.method || 'GET').toUpperCase() === 'POST'
        ? json({ user_id: BUSINESS_ID, role: 'customer', token: TOKEN })
        : json({}, 401),
    ).fetcher,
    good,
  )
  assertEqual(stored.user_id, BUSINESS_ID)
  assertEqual(readGoldenCredential(good), TOKEN)
})

/* ------------------------------------------------------------- the sign-out */

await test('ending a session revokes first, then clears the browser marker', async () => {
  const order = []
  const { fetcher } = recorder(() => json({ revoked: 1, role: 'customer', basis: 'clerk_session' }))
  const result = await endBusinessSession({
    fetch: async (target, init) => {
      order.push('revoke')
      return fetcher(target, init)
    },
    clearClient: () => order.push('clear'),
    hadSession: true,
  })
  assertEqual(result.status, 'ended')
  assertEqual(result.revoked, 1)
  assertEqual(order.join(','), 'revoke,clear', 'the marker is cleared only after the server confirmed')
})

await test('a revoke that fails is reported and the marker is left in place', async () => {
  const order = []
  const storage = memoryStorage()
  storeGoldenCredential(storage, TOKEN)
  const result = await endBusinessSession({
    fetch: async () => {
      order.push('revoke')
      return json({ error: { code: 'upstream_unreachable' } }, 502)
    },
    clearClient: () => {
      order.push('clear')
      clearGoldenCredential(storage)
    },
    hadSession: true,
    credential: readGoldenCredential(storage),
  })
  assertEqual(result.status, 'failed')
  assertEqual(order.join(','), 'revoke', 'nothing may be cleared over a live credential')
  assertEqual(
    readGoldenCredential(storage),
    TOKEN,
    'an unconfirmed sign-out must leave the credential visible, not silently delete it',
  )
  assert(result.message.includes('502'), result.message)
})

await test('a revoke that cannot be reached at all is also a failure', async () => {
  const result = await endBusinessSession({
    fetch: async () => {
      throw new TypeError('fetch failed')
    },
    clearClient: () => {
      throw new Error('clearClient must not be called')
    },
    hadSession: true,
  })
  assertEqual(result.status, 'failed')
})

await test('a browser that never started a session hears "not started"', async () => {
  const result = await endBusinessSession({
    fetch: async () => json({ error: { code: 'clerk_session_required' } }, 401),
    clearClient: () => {
      throw new Error('clearClient must not be called')
    },
    hadSession: false,
  })
  assertEqual(result.status, 'not-started')
})

await test('sign-out of Clerk happens last, and only after a confirmed revoke', async () => {
  const order = []
  const ended = await signOutGoldenSession({
    fetch: async (target, init) => {
      order.push('revoke')
      return json({ revoked: 1, role: 'customer', basis: 'business_token' })
    },
    clearClient: () => order.push('clear'),
    hadSession: true,
    signOutClerk: async () => {
      order.push('clerk')
    },
  })
  assertEqual(ended.status, 'ended')
  assertEqual(order.join(','), 'revoke,clear,clerk')
})

await test('an unconfirmed revoke stops the Clerk sign-out instead of hiding it', async () => {
  const order = []
  const result = await signOutGoldenSession({
    fetch: async () => {
      order.push('revoke')
      return json({ error: {} }, 502)
    },
    clearClient: () => order.push('clear'),
    hadSession: true,
    signOutClerk: async () => {
      order.push('clerk')
    },
  })
  assertEqual(result.status, 'failed')
  assertEqual(order.join(','), 'revoke', 'the Clerk half must not run over a live business credential')
})

await test('nothing to revoke still signs the person out of Clerk', async () => {
  const order = []
  const result = await signOutGoldenSession({
    fetch: async () => {
      order.push('revoke')
      return json({ error: {} }, 401)
    },
    clearClient: () => order.push('clear'),
    hadSession: false,
    signOutClerk: async () => {
      order.push('clerk')
    },
  })
  assertEqual(result.status, 'not-started')
  assertEqual(order.join(','), 'revoke,clerk')
})

/* --------------------------------------------------------- the tab marker */

function memoryStorage() {
  const map = new Map()
  return {
    getItem: (key) => (map.has(key) ? map.get(key) : null),
    setItem: (key, value) => map.set(key, value),
    removeItem: (key) => map.delete(key),
    size: () => map.size,
  }
}

await test('the marker carries a principal and a role, and clears cleanly', () => {
  const storage = memoryStorage()
  assertEqual(readMarker(storage), null)
  writeMarker(storage, { user_id: BUSINESS_ID, role: 'customer' })
  const read = readMarker(storage)
  assertEqual(read.user_id, BUSINESS_ID)
  assertEqual(read.role, 'customer')
  assertEqual(Object.keys(read).sort().join(','), 'role,user_id', 'only these two fields, ever')
  assert(
    !/[0-9a-f]{32}/.test(JSON.stringify(read)),
    'a 32-hex credential must never be written client-side',
  )
  clearMarker(storage)
  assertEqual(readMarker(storage), null)
  assertEqual(storage.size(), 0)
})

await test('a tampered or unknown marker is treated as no session', () => {
  const storage = memoryStorage()
  storage.setItem('goaa_golden_business_session', '{not json')
  assertEqual(readMarker(storage), null)
  storage.setItem('goaa_golden_business_session', JSON.stringify({ user_id: BUSINESS_ID, role: 'agent' }))
  assertEqual(readMarker(storage), null, 'a role this bridge cannot issue must not be trusted')
  storage.setItem('goaa_golden_business_session', JSON.stringify({ user_id: 42, role: 'customer' }))
  assertEqual(readMarker(storage), null)
})

/* --------------------------------------------------------------- lifecycle */

/**
 * A small model of the API with the credential where the golden contract puts
 * it: in the browser's own storage (`localStorage.client_token`), presented on
 * every request as `Authorization: Bearer`.
 *
 * The server keeps only the set of credentials it still accepts; the browser
 * keeps the value. "The old credential is refused afterwards" is therefore a
 * statement about a real value travelling and a real lookup failing, not a
 * restatement of the module's own code.
 */
function fakeServer() {
  const state = { live: new Set(), revoked: 0, log: [] }
  const presented = (init) => {
    const header = init.headers && (init.headers.authorization || init.headers.Authorization)
    const match = /^Bearer ([0-9a-f]{32})$/.exec(String(header || '').trim())
    return match ? match[1] : null
  }
  const fetcher = async (target, init = {}) => {
    const method = (init.method || 'GET').toUpperCase()
    state.log.push(`${method} ${target}`)
    const credential = presented(init)
    if (target === `${GOLDEN_SESSION_PATH}/verify`) {
      if (!credential || !state.live.has(credential)) {
        return json({ error: { code: 'invalid_business_token' } }, 401)
      }
      return json({ user_id: BUSINESS_ID, role: 'customer' })
    }
    if (target === `${GOLDEN_SESSION_PATH}` && method === 'POST') {
      const created = state.live.size === 0
      const issued = `${Math.random()}`.replace('0.', 'b').padEnd(32, 'c').slice(0, 32)
      state.live.add(issued)
      return json({ user_id: BUSINESS_ID, role: 'customer', created, token: issued })
    }
    if (target === `${GOLDEN_SESSION_PATH}/revoke` && method === 'POST') {
      if (!credential) return json({ error: { code: 'clerk_session_required' } }, 401)
      if (!state.live.has(credential)) {
        return json({ error: { code: 'invalid_business_token' } }, 401)
      }
      state.live.delete(credential)
      state.revoked += 1
      return json({ revoked: 1, role: 'customer', basis: 'business_token' })
    }
    return json({ error: { code: 'route_not_allowed' } }, 404)
  }
  return { fetcher, state }
}

await test('a full lifecycle: login, refresh, re-login, sign-out, refusal', async () => {
  const { fetcher, state } = fakeServer()
  const storage = memoryStorage()

  // 1. first sign-in: nothing yet, so one mint, and the credential lands in
  //    the golden slot the golden surface itself reads
  const first = await startBusinessSession(fetcher, {
    credential: readGoldenCredential(storage),
    storage,
  })
  assertEqual(first.state, 'live')
  assertEqual(first.created, true)
  writeMarker(storage, first.session)
  const afterLogin = readGoldenCredential(storage)
  assert(/^[0-9a-f]{32}$/.test(String(afterLogin)), 'a real credential must be stored')
  assertEqual(state.log.join(' | '), `GET ${GOLDEN_SESSION_PATH}/verify | POST ${GOLDEN_SESSION_PATH}`)

  // 2. refresh: a read, and the credential is the same one afterwards
  state.log.length = 0
  const refreshed = await startBusinessSession(fetcher, {
    credential: readGoldenCredential(storage),
    storage,
  })
  assertEqual(refreshed.created, false)
  assertEqual(readGoldenCredential(storage), afterLogin, 'a refresh must not rotate the credential')
  assertEqual(state.log.join(' | '), `GET ${GOLDEN_SESSION_PATH}/verify`)

  // 3. sign-out: confirmed revocation, then the browser deletes its copy
  const ended = await endBusinessSession({
    fetch: fetcher,
    clearClient: () => {
      clearMarker(storage)
      clearGoldenCredential(storage)
    },
    hadSession: true,
    credential: readGoldenCredential(storage),
  })
  assertEqual(ended.status, 'ended')
  assertEqual(ended.revoked, 1)
  assertEqual(readMarker(storage), null)
  assertEqual(readGoldenCredential(storage), null, 'no credential may survive a confirmed sign-out')
  assertEqual(
    (await checkBusinessSession(fetcher, afterLogin)).state,
    'absent',
    'the old credential is refused by the API',
  )
  assertEqual(
    state.log[state.log.length - 1],
    `GET ${GOLDEN_SESSION_PATH}/verify`,
  )

  // 4. signing in again mints a new credential rather than reusing a dead one
  const again = await startBusinessSession(fetcher, {
    credential: readGoldenCredential(storage),
    storage,
  })
  assertEqual(again.created, true)
  assertEqual(again.session.user_id, BUSINESS_ID, 'the same identity maps to the same principal')
  assert(
    readGoldenCredential(storage) !== afterLogin,
    'the new credential must not be the revoked one',
  )
})

await test('a sign-out after Clerk is already gone still revokes', async () => {
  const { fetcher, state } = fakeServer()
  const storage = memoryStorage()
  const started = await startBusinessSession(fetcher, { credential: null, storage })
  writeMarker(storage, started.session)
  const credential = readGoldenCredential(storage)

  // Clerk has signed the browser out; only the business credential remains, and
  // that is exactly what the revoke route accepts.
  const result = await endBusinessSession({
    fetch: fetcher,
    clearClient: () => {
      clearMarker(storage)
      clearGoldenCredential(storage)
    },
    hadSession: true,
    credential,
  })
  assertEqual(result.status, 'ended')
  assertEqual(readGoldenCredential(storage), null)
  assertEqual(state.live.size, 0, 'the API no longer accepts that credential')
  assertEqual((await checkBusinessSession(fetcher, credential)).state, 'absent')
})

summary('golden session')
