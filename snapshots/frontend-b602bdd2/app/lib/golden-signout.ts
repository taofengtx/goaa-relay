/**
 * golden-signout.ts — one place that decides how the account menu's LOG OUT
 * behaves on golden pages.
 *
 * Contract (see FILE-DIVISION-AND-INTERFACE.md §3): when the golden session
 * bridge is mounted it exposes window.__goaaGoldenSession.signOut(redirectUrl)
 * resolving to 'ended' | 'not-started' | 'failed'. Order is fixed by the
 * bridge: revoke business credential -> clear browser state -> Clerk sign-out.
 *   'ended' / 'not-started' -> safe to navigate.
 *   'failed'                -> do NOT navigate, do NOT clear local state,
 *                              surface lastError so the user can retry.
 * When the bridge is absent (Clerk off / older build) the caller falls back to
 * the legacy local sign-out, exactly as before.
 */

export type GoldenSignOutStatus = 'ended' | 'not-started' | 'failed'

export type GoldenSessionApi = {
  signOut: (redirectUrl?: string) => Promise<GoldenSignOutStatus>
  session: { user_id: string; role: string } | null
  lastError: string | null
}

export const GOLDEN_SIGN_OUT_FAILED = 'Sign-out did not complete — you are still signed in. Please try again.'

export function goldenSessionOf(browser: unknown): GoldenSessionApi | null {
  if (!browser || typeof browser !== 'object') return null
  const api = (browser as { __goaaGoldenSession?: Partial<GoldenSessionApi> }).__goaaGoldenSession
  return api && typeof api.signOut === 'function' ? (api as GoldenSessionApi) : null
}

export type GoldenSignOutOutcome =
  | { status: 'navigate' }
  | { status: 'legacy' }
  | { status: 'failed'; message: string }

/**
 * Decide what the LOG OUT button should do next. Pure: no navigation, no
 * storage access — the caller performs the side effects.
 */
export async function decideGoldenSignOut(browser: unknown, redirectUrl: string): Promise<GoldenSignOutOutcome> {
  const golden = goldenSessionOf(browser)
  if (!golden) return { status: 'legacy' }
  let result: GoldenSignOutStatus
  try {
    result = await golden.signOut(redirectUrl)
  } catch {
    return { status: 'failed', message: golden.lastError || GOLDEN_SIGN_OUT_FAILED }
  }
  if (result === 'ended' || result === 'not-started') return { status: 'navigate' }
  return { status: 'failed', message: golden.lastError || GOLDEN_SIGN_OUT_FAILED }
}
