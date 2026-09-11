import type { Metadata } from "next"
import { ClerkProvider } from "@clerk/nextjs"
import "./globals.css"
import "./logo.css"
import "./styles/goaa-tokens.css"
import "./styles/goaa-pp-compat.css"
import ProfessionalConnectBar from "./components/ProfessionalConnectBar"
import SignedInCookieSync from "./components/SignedInCookieSync"
import GoldenSessionBridge from "./components/GoldenSessionBridge"
import { clerkAuthState } from "./lib/clerk-entry"

export const metadata: Metadata = {
  title: "GOAA.ai",
  description: "AI planning and professional execution platform",
}

/**
 * The Clerk provider is mounted only when BOTH hold: the single switch
 * `GOAA_C2_CLERK_AUTH_ENABLED` says so, and the public configuration is
 * actually present.
 *
 * A publishable key on its own is not enough — that only means someone exported
 * a key, not that this deployment opted into Clerk, and mounting the provider
 * would ship Clerk's client runtime and its sign-in state to every page. No
 * secret key is read here; the value is public by design.
 *
 * This file differs from the golden baseline in one further way: the golden
 * business-session bridge is mounted as a sibling of the existing children. It
 * renders nothing and holds no layout, so golden pages keep their structure,
 * styles and behaviour. See `components/GoldenSessionBridge.tsx`; with Clerk off
 * it is a no-op.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const clerkState = clerkAuthState()
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  const clerkAuth = clerkState === "enabled" && Boolean(publishableKey)

  const page = (
    <html lang="en">
      <body>
        {children}
        <ProfessionalConnectBar />
        <SignedInCookieSync />
        <GoldenSessionBridge clerkAuth={clerkAuth} />
      </body>
    </html>
  )

  if (!clerkAuth) return page

  return <ClerkProvider publishableKey={publishableKey}>{page}</ClerkProvider>
}
