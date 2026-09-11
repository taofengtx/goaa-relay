/**
 * signout.ts — the sign-out decision, in one place and free of React.
 *
 * The rule it encodes: never report a sign-out that did not happen.
 *
 * With Clerk in charge the session is what authenticates, and only the official
 * Clerk sign-out revokes it. So:
 *   * Clerk present            -> official `signOut({ redirectUrl })`;
 *   * Clerk still loading      -> blocked: say so, stay put, do NOT fall back to
 *                                 the legacy endpoint (which would leave the
 *                                 Clerk session alive);
 *   * Clerk sign-out threw     -> failed: say so, stay put;
 *   * Clerk not in charge      -> the legacy flow, exactly as it shipped.
 *
 * Keeping it here (instead of inside the component) is what makes the three
 * cases testable without a browser.
 */

/** The official sign-out entry point of the Clerk browser client. */
export type ClerkSignOut = (options?: { redirectUrl?: string }) => Promise<void>

type ClerkClient = { signOut?: ClerkSignOut }

/** After a Clerk sign-out the visitor returns to the one public entry. */
export const CLERK_SIGN_OUT_REDIRECT = '/client-login?next=/agent-loop/customer'
/** The legacy flow keeps its own destination. */
export const LEGACY_SIGN_OUT_REDIRECT = '/agent-loop/login'

export const SIGN_OUT_LOADING_MESSAGE = 'The sign-in service is still loading — please try again.'
export const SIGN_OUT_FAILED_MESSAGE = 'Sign-out did not complete — you are still signed in.'

export type SignOutResult =
  | { status: 'redirected'; via: 'clerk' | 'legacy' }
  | { status: 'failed'; message: string }
  | { status: 'blocked'; message: string }

/**
 * The official Clerk sign-out, or `null` when this page does not run on Clerk.
 * `<ClerkProvider>` is what publishes the client, so its presence is the runtime
 * truth about whether Clerk owns the session here — not a guess. The member is
 * checked and returned as a value, so no caller has to assert anything.
 */
export function clerkSignOutOf(browser: unknown): ClerkSignOut | null {
  if (!browser || typeof browser !== 'object') return null
  const clerk = (browser as { Clerk?: ClerkClient }).Clerk
  const signOut = clerk?.signOut
  return typeof signOut === 'function' ? signOut : null
}

export async function performSignOut(options: {
  /** Server-decided: this deployment signs people in through Clerk. */
  clerkAuth: boolean
  /** The browser global (injected so the decision stays testable). */
  browser: unknown
  /** The legacy sign-out call; only ever used when Clerk is not in charge. */
  legacy: () => Promise<void>
  /** Used by the legacy branch only; the SDK navigates itself for Clerk. */
  navigate: (url: string) => void
}): Promise<SignOutResult> {
  const { clerkAuth, browser, legacy, navigate } = options

  if (clerkAuth) {
    const clerkSignOut = clerkSignOutOf(browser)
    if (!clerkSignOut) {
      return { status: 'blocked', message: SIGN_OUT_LOADING_MESSAGE }
    }
    try {
      await clerkSignOut({ redirectUrl: CLERK_SIGN_OUT_REDIRECT })
      return { status: 'redirected', via: 'clerk' }
    } catch {
      return { status: 'failed', message: SIGN_OUT_FAILED_MESSAGE }
    }
  }

  await legacy()
  navigate(LEGACY_SIGN_OUT_REDIRECT)
  return { status: 'redirected', via: 'legacy' }
}
