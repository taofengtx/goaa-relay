// Mock tests for sign-out (app/lib/agent-loop/signout.ts).
//
// The point of these three cases is a promise the UI must keep: never report a
// sign-out that did not happen. Clerk owns the session when it is on, so a
// missing or failing Clerk client must show an error and leave the visitor on
// the page — falling back to the legacy endpoint would say "signed out" while
// the Clerk session was still alive.
import { assert, assertEqual, load, summary, test } from './harness.mjs'

const signout = await load('app/lib/agent-loop/signout.ts')
const {
  CLERK_SIGN_OUT_REDIRECT,
  LEGACY_SIGN_OUT_REDIRECT,
  SIGN_OUT_LOADING_MESSAGE,
  clerkSignOutOf,
  performSignOut,
} = signout

function browserWith(signOut) {
  return { Clerk: signOut ? { signOut } : {} }
}

const settle = (result) => result

/* -------------------------------------------------------------- success */

await test('clerk loaded: the official sign-out runs and carries the return path', async () => {
  const seen = []
  const result = await performSignOut({
    clerkAuth: true,
    browser: browserWith(async (options) => {
      seen.push(options)
    }),
    legacy: async () => {
      throw new Error('the legacy endpoint must not be called while Clerk is on')
    },
    navigate: () => {
      throw new Error('the SDK navigates; the page must not')
    },
  })
  assertEqual(result.status, 'redirected')
  assertEqual(result.via, 'clerk')
  assertEqual(seen.length, 1)
  assertEqual(seen[0].redirectUrl, CLERK_SIGN_OUT_REDIRECT)
})

await test('clerk loaded: a client that reports no session at all is still no error', async () => {
  // The SDK's sign-out is idempotent: a browser whose session already expired
  // must not be told the sign-out failed.
  const result = await performSignOut({
    clerkAuth: true,
    browser: browserWith(async () => {}),
    legacy: async () => {},
    navigate: () => {},
  })
  assertEqual(result.status, 'redirected')
})

/* -------------------------------------------------------- clerk missing */

await test('clerk not loaded yet: blocked, with an error, and no fallback', async () => {
  let legacyCalled = false
  let navigated = null
  const result = await performSignOut({
    clerkAuth: true,
    browser: {},
    legacy: async () => {
      legacyCalled = true
    },
    navigate: (url) => {
      navigated = url
    },
  })
  assertEqual(result.status, 'blocked')
  assertEqual(result.message, SIGN_OUT_LOADING_MESSAGE)
  assertEqual(legacyCalled, false, 'the legacy endpoint must never stand in for a live Clerk session')
  assertEqual(navigated, null, 'the visitor stays on the page')
})

await test('clerk not loaded yet: the missing client is reported, never guessed at', async () => {
  for (const browser of [undefined, null, {}, { Clerk: {} }, { Clerk: { signOut: 'not a function' } }, 'window']) {
    assertEqual(clerkSignOutOf(browser), null, `unexpected client for ${JSON.stringify(browser)}`)
  }
  const fn = async () => {}
  assertEqual(clerkSignOutOf({ Clerk: { signOut: fn } }), fn)
})

/* ------------------------------------------------------------- failure */

await test('clerk reports a failure: failed, with an error, and no fallback', async () => {
  let legacyCalled = false
  let navigated = null
  const result = await performSignOut({
    clerkAuth: true,
    browser: browserWith(async () => {
      throw new Error('network down')
    }),
    legacy: async () => {
      legacyCalled = true
    },
    navigate: (url) => {
      navigated = url
    },
  })
  assertEqual(result.status, 'failed')
  assert(result.message.length > 0, 'a failure must explain itself')
  assertEqual(legacyCalled, false, 'a failed Clerk sign-out must not be re-tried as legacy')
  assertEqual(navigated, null, 'the visitor stays on the page')
})

/* --------------------------------------------------------- clerck off */

await test('clerk off: the legacy sign-out runs exactly as it shipped', async () => {
  let legacyCalled = false
  let navigated = null
  const result = await performSignOut({
    clerkAuth: false,
    browser: { Clerk: { signOut: async () => {} } },
    legacy: async () => {
      legacyCalled = true
    },
    navigate: (url) => {
      navigated = url
    },
  })
  assertEqual(result.status, 'redirected')
  assertEqual(result.via, 'legacy')
  assertEqual(legacyCalled, true)
  assertEqual(navigated, LEGACY_SIGN_OUT_REDIRECT)
})

/* ------------------------------------------------------------- wiring */

await test('the shell shows the error and stays put when sign-out is refused', async () => {
  // The component is a thin caller of the decisions above; assert the shape it
  // depends on: only a refusal produces a message, and only on a refusal does
  // the page stay where it is.
  const fs = await import('node:fs')
  const shell = fs.readFileSync(`${process.cwd()}/app/components/agent-loop/Shell.tsx`, 'utf8')
  assert(shell.includes('performSignOut'), 'the shell must use the tested decision')
  assert(shell.includes('setSignOutError(result.message)'), 'a refusal must surface its message')
  assert(shell.includes("result.status !== 'redirected'"), 'the page must only act when Clerk redirected')
  assert(shell.includes('signOutError'), 'the error must be rendered')
  assert(!shell.includes('officialClerkSignOut'), 'the shell must not keep a second copy of the decision')
})

summary('c2 clerk sign-out')
