import { headers } from "next/headers"
import { redirect } from "next/navigation"
import { SignIn } from "@clerk/nextjs"
import { goaaClerkAppearance, goaaClerkPageStyle } from "../components/portal/clerk-appearance"

import {
  CLERK_ENTRY_MARKER,
  CLERK_ENTRY_MARKER_VALUE,
  DEFAULT_LOGIN_NEXT,
  UNIFIED_LOGIN_PATH,
  clerkAuthState,
  safeNextTarget,
} from "../lib/clerk-entry"

/**
 * Internal sign-in surface. It is never linked to and never reachable by typing
 * a URL: the middleware rewrites the unified entry here and stamps a marker
 * header on the rewritten request, after stripping any client-supplied copy.
 * Without that marker the request bounces back to the public entry.
 *
 * The folder name carries no leading underscore on purpose — Next.js ignores
 * every path segment starting with "_".
 */
export const dynamic = "force-dynamic"

type SearchParams = { next?: string | string[] }

export default function ClerkLoginPage({ searchParams }: { searchParams: SearchParams }) {
  if (clerkAuthState() !== "enabled") {
    redirect(UNIFIED_LOGIN_PATH)
  }
  if (headers().get(CLERK_ENTRY_MARKER) !== CLERK_ENTRY_MARKER_VALUE) {
    redirect(UNIFIED_LOGIN_PATH)
  }

  const raw = Array.isArray(searchParams.next) ? searchParams.next[0] : searchParams.next
  // Already validated by the middleware; validated again so that even a direct
  // hit can never turn into an open redirect.
  const next = safeNextTarget(raw)
  // A first-time visitor finishes on the sign-up branch of this same card;
  // without the signUp* redirect props Clerk sends them to "/" and the
  // validated `next` is lost (Round T3: every new account landed on "/").
  // Round C1.7: this card is now the only sign-in page, so it carries the
  // retired form's "Continue as guest" exit: a plain link to AI Butler that
  // signs nothing in and writes nothing.

  return (
    <main style={goaaClerkPageStyle}>
      <div style={{ width: "100%", maxWidth: 470 }}>
        <SignIn
          withSignUp
          routing="hash"
          forceRedirectUrl={next}
          fallbackRedirectUrl={next}
          signUpForceRedirectUrl={next}
          signUpFallbackRedirectUrl={next}
          appearance={goaaClerkAppearance}
        />
        <p style={{ margin: "18px 0 0", textAlign: "center" }}>
          <a
            href={DEFAULT_LOGIN_NEXT}
            data-testid="clerk-continue-as-guest"
            style={{ color: "rgba(255,255,255,.72)", fontSize: 14, textDecoration: "underline", textUnderlineOffset: 3 }}
          >
            Continue as guest
          </a>
        </p>
      </div>
    </main>
  )
}
