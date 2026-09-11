"use client"

/**
 * GoldenSessionBridge — mounts the golden business session on the pages the
 * golden AI Butler surface already owns, without changing any of them.
 *
 * It renders nothing. Everything it does is a side effect, so the golden
 * layout, styles and business flow are untouched: no wrapper element, no DOM
 * node, no CSS, no z-index, no re-render of the page tree. The only visible
 * difference on a golden page is that a business session exists when Clerk says
 * the visitor is signed in.
 *
 * Two things happen here, and nothing else:
 *   1. signed in (Clerk)  -> resume the business session if it is still live,
 *                            otherwise start it once;
 *   2. signed out (Clerk) -> revoke whatever business credential is left.
 *
 * (1) is a *read first*: a page refresh, a client-side navigation or a second
 * tab must not rotate the credential out from under a working session.
 *
 * (2) is the safety net, not the happy path. The happy path is the sign-out
 * button asking this bridge to end the session *before* Clerk clears it, via:
 *
 *     window.dispatchEvent(new CustomEvent('goaa:golden-session-signout',
 *       { detail: { redirectUrl: '/client-login' } }))
 *
 * which revokes first and only then signs out of Clerk, reporting `failed`
 * (and stopping) if the revocation could not be confirmed. This listener covers
 * the other order — Clerk already gone, credential still present — and uses the
 * token-based revoke path, which exists for exactly this case.
 *
 * Failure is never silent: it is broadcast on `goaa:golden-session-error` and
 * kept on `window.__goaaGoldenSession.lastError`, and both the browser-side
 * marker and the credential itself are left in place, so the state is visibly
 * inconsistent rather than invisibly dangerous.
 *
 * THE CREDENTIAL'S HOME: the golden surface's own slot — `localStorage` key
 * `client_token`, sent back as `Authorization: Bearer`. This component is what
 * writes it (after the server minted it) and the only thing that deletes it
 * (after the server confirmed revocation).
 *
 * ISOLATION: this component is candidate-only code running against the isolated
 * test stack. It issues no order, no checkout and no payment call.
 */

import { useEffect, useRef } from 'react'
import { useAuth } from "@clerk/nextjs"
import {
  SIGN_OUT_FAILED_MESSAGE,
  SIGN_OUT_LOADING_MESSAGE,
  clerkSignOutOf,
} from "@/app/lib/agent-loop/signout"
import {
  bootstrapBusinessSession,
  clearGoldenCredential,
  clearMarker,
  endBusinessSession,
  GOLDEN_SESSION_UNAVAILABLE,
  readGoldenCredential,
  readMarker,
  revokeBusinessSession,
  startBusinessSession,
  writeMarker,
  type GoldenSession,
} from "@/app/lib/golden-session"

export const GOLDEN_SESSION_READY_EVENT = 'goaa:golden-session'
export const GOLDEN_SESSION_SIGN_OUT_EVENT = 'goaa:golden-session-signout'
export const GOLDEN_SESSION_ERROR_EVENT = 'goaa:golden-session-error'

export type GoldenSessionSignOutDetail = { redirectUrl?: string }

/** The one function a golden page may call to sign out in the safe order. */
export type GoldenSessionHandle = {
  session: GoldenSession | null
  lastError: string | null
  /** Revoke, then clear, then sign out of Clerk — in that order, or not at all. */
  signOut: (redirectUrl?: string) => Promise<'ended' | 'not-started' | 'failed'>
}

declare global {
  interface Window {
    __goaaGoldenSession?: GoldenSessionHandle
  }
}

/** Same-origin fetch. Cookie, no cache, no credential in the body. */
function bridgeFetch(target: string, init?: RequestInit): Promise<Response> {
  return fetch(target, { ...init, credentials: 'same-origin', cache: 'no-store' })
}

function announce(name: string, detail: unknown): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(name, { detail }))
}

function ClerkSessionBridge() {
  const { isLoaded, isSignedIn } = useAuth()
  const started = useRef(false)
  const handle = useRef<GoldenSessionHandle>({ session: null, lastError: null, signOut: async () => 'failed' })

  // The handle a golden page can call, and the event it can dispatch. Both do
  // the same thing: revoke, clear, then let Clerk sign out — and stop if the
  // revocation could not be confirmed.
  useEffect(() => {
    const session = isSignedIn ? readMarker(window.sessionStorage) : null
    handle.current = {
      session,
      lastError: null,
      signOut: async (redirectUrl?: string) => {
        const result = await endBusinessSession({
          fetch: bridgeFetch,
          // Order matters: the server revokes first, and only then is the
          // credential removed from the browser. On failure nothing is
          // cleared, so the page cannot look signed out while a credential the
          // API still accepts sits in storage.
          clearClient: () => {
            clearMarker(window.sessionStorage)
            clearGoldenCredential(window.localStorage)
            handle.current.session = null
          },
          hadSession: Boolean(isSignedIn),
          credential: readGoldenCredential(window.localStorage),
        })
        if (result.status === 'failed') {
          handle.current.lastError = result.message
          announce(GOLDEN_SESSION_ERROR_EVENT, { message: result.message })
          return 'failed'
        }
        // Only now the Clerk half — and the Clerk client is what navigates, so
        // a missing one is a refusal to claim anything, not a fallback to some
        // other logout that would leave the Clerk session alive.
        const clerkSignOut = clerkSignOutOf(window)
        if (!clerkSignOut) {
          handle.current.lastError = SIGN_OUT_LOADING_MESSAGE
          announce(GOLDEN_SESSION_ERROR_EVENT, { message: SIGN_OUT_LOADING_MESSAGE })
          return 'failed'
        }
        try {
          await clerkSignOut(redirectUrl ? { redirectUrl } : undefined)
        } catch {
          handle.current.lastError = SIGN_OUT_FAILED_MESSAGE
          announce(GOLDEN_SESSION_ERROR_EVENT, { message: SIGN_OUT_FAILED_MESSAGE })
          return 'failed'
        }
        announce(GOLDEN_SESSION_READY_EVENT, { session: null })
        return result.status
      },
    }
    window.__goaaGoldenSession = handle.current
  }, [isSignedIn])

  // A golden page asks for the safe order.
  useEffect(() => {
    const onSignOut = (event: Event) => {
      const detail = (event as CustomEvent<GoldenSessionSignOutDetail>).detail
      void handle.current.signOut(detail?.redirectUrl)
    }
    window.addEventListener(GOLDEN_SESSION_SIGN_OUT_EVENT, onSignOut)
    return () => window.removeEventListener(GOLDEN_SESSION_SIGN_OUT_EVENT, onSignOut)
  }, [])

  // (1) resume or start; (2) revoke what is left after Clerk is gone.
  useEffect(() => {
    if (!isLoaded) return undefined
    let cancelled = false

    if (isSignedIn) {
      if (started.current) return undefined
      started.current = true
      void (async () => {
        const result = await startBusinessSession(bridgeFetch, {
          credential: readGoldenCredential(window.localStorage),
          storage: window.localStorage,
        })
        if (cancelled) return
        if (result.state === 'live') {
          writeMarker(window.sessionStorage, result.session)
          handle.current.session = result.session
          announce(GOLDEN_SESSION_READY_EVENT, { session: result.session, created: result.created })
          return
        }
        const message = result.state === 'unavailable' ? GOLDEN_SESSION_UNAVAILABLE : result.message
        handle.current.lastError = message
        announce(GOLDEN_SESSION_ERROR_EVENT, { message })
      })()
      return () => {
        cancelled = true
      }
    }

    // Clerk says signed out. If this browser still has a business credential,
    // it has to go now — that is the whole point of the token-based path.
    const leftover = readMarker(window.sessionStorage)
    if (!leftover) return undefined
    void (async () => {
      try {
        await revokeBusinessSession(bridgeFetch, readGoldenCredential(window.localStorage))
        clearMarker(window.sessionStorage)
        clearGoldenCredential(window.localStorage)
        handle.current.session = null
        announce(GOLDEN_SESSION_READY_EVENT, { session: null })
      } catch (error) {
        const message = error instanceof Error ? error.message : GOLDEN_SESSION_UNAVAILABLE
        handle.current.lastError = message
        announce(GOLDEN_SESSION_ERROR_EVENT, { message })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [isLoaded, isSignedIn])

  return null
}

/**
 * Mounted from the root layout, inside `<ClerkProvider>`, only when a server
 * component decided that Clerk is the identity authority for this deployment.
 * With Clerk off there is no bridge to mount and this is a no-op — the legacy
 * session keeps working exactly as it shipped.
 */
export default function GoldenSessionBridge({ clerkAuth }: { clerkAuth: boolean }) {
  if (!clerkAuth) return null
  return <ClerkSessionBridge />
}

/** Re-exported for the isolated test page. */
export { bootstrapBusinessSession, startBusinessSession }
