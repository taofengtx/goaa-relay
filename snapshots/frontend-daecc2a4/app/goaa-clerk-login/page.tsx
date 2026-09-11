import { headers } from "next/headers"
import { redirect } from "next/navigation"
import { SignIn } from "@clerk/nextjs"

import {
  CLERK_ENTRY_MARKER,
  CLERK_ENTRY_MARKER_VALUE,
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

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "48px 16px",
        background: "#07070b",
      }}
    >
      <div style={{ width: "100%", maxWidth: 420 }}>
        <SignIn
          withSignUp
          routing="hash"
          forceRedirectUrl={next}
          fallbackRedirectUrl={next}
          appearance={{ variables: { colorPrimary: "#6d5efc" } }}
        />
      </div>
    </main>
  )
}
