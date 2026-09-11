/**
 * Test double for the `@clerk/nextjs/server` module, used ONLY by the BFF test
 * run (the resolve hook swaps it in when C2_STUB_CLERK_SERVER is set).
 *
 * Why a double is acceptable here: the BFF's contract with Clerk is a single
 * `auth()` call, and what this tier must get right is what it does with each
 * possible answer — a session, no session, no token, or a throw. Every one of
 * those is exercised. The real SDK is exercised elsewhere: middleware.ts runs
 * against the genuine `clerkMiddleware` in test-middleware.mjs, and
 * test-bff.mjs also imports the real CJS build directly to show that a call
 * outside a request context throws (which is the fail-closed path in the wild).
 */
export async function auth() {
  const impl = globalThis.__c2ClerkAuth
  if (typeof impl !== 'function') return { userId: null, getToken: async () => null }
  return impl()
}

export function clerkMiddleware() {
  throw new Error('clerkMiddleware is not used in this test run')
}
