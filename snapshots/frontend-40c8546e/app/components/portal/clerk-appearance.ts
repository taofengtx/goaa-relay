/**
 * clerk-appearance.ts — makes Clerk's <SignIn withSignUp /> look like the
 * approved /client-login card (dark gradient card, pill buttons, white primary,
 * "Welcome to GOAA" heading). Pass as `appearance={goaaClerkAppearance}`.
 *
 * Only presentation. No auth logic, no routing, no env.
 */

import type { Appearance } from '@clerk/types';

export const goaaClerkAppearance: Appearance = {
  variables: {
    colorPrimary: '#f4f4f5',
    colorText: '#ffffff',
    colorTextSecondary: 'rgba(255,255,255,.62)',
    colorBackground: 'transparent',
    colorInputBackground: 'rgba(255,255,255,.055)',
    colorInputText: '#ffffff',
    colorDanger: '#fca5a5',
    borderRadius: '15px',
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontSize: '15px',
  },
  elements: {
    rootBox: { width: '100%' },
    cardBox: { width: '100%', boxShadow: 'none' },
    card: {
      width: 'min(100%, 470px)',
      padding: '34px 34px 30px',
      border: '1px solid rgba(255,255,255,.12)',
      background: 'linear-gradient(180deg, rgba(30,30,38,.98), rgba(18,18,24,.98))',
      borderRadius: '28px',
      boxShadow: '0 30px 90px rgba(0,0,0,.45)',
    },
    logoBox: { justifyContent: 'center', marginBottom: '16px' },
    logoImage: { width: '48px', height: '48px', borderRadius: '50%' },
    headerTitle: { fontSize: '28px', letterSpacing: '-.03em', textAlign: 'center' },
    headerSubtitle: { color: 'rgba(255,255,255,.62)', fontSize: '14px', lineHeight: 1.6, textAlign: 'center' },
    socialButtonsBlockButton: {
      height: '52px',
      borderRadius: '999px',
      border: '1px solid rgba(255,255,255,.28)',
      background: 'rgba(255,255,255,.035)',
      color: '#fff',
      fontWeight: 700,
      fontSize: '15px',
    },
    socialButtonsBlockButtonText: { color: '#fff', fontWeight: 700 },
    dividerLine: { background: 'rgba(255,255,255,.14)' },
    dividerText: { color: 'rgba(255,255,255,.46)', fontSize: '13px' },
    formFieldLabel: { display: 'none' },
    formFieldInput: {
      height: '52px',
      padding: '0 16px',
      borderRadius: '15px',
      border: '1px solid rgba(255,255,255,.16)',
      background: 'rgba(255,255,255,.055)',
      color: '#fff',
      boxShadow: 'none',
    },
    formButtonPrimary: {
      height: '52px',
      borderRadius: '999px',
      border: 0,
      background: '#f4f4f5',
      color: '#111116',
      fontWeight: 700,
      fontSize: '16px',
      textTransform: 'none',
      boxShadow: 'none',
      '&:hover': { background: '#ffffff' },
    },
    footerAction: { justifyContent: 'center' },
    footerActionText: { color: 'rgba(255,255,255,.62)', fontSize: '14px' },
    footerActionLink: { color: '#fff', textDecoration: 'underline', textUnderlineOffset: '3px', fontWeight: 400 },
    footer: { background: 'transparent' },
    identityPreview: { background: 'rgba(255,255,255,.055)', borderRadius: '15px' },
    otpCodeFieldInput: { borderRadius: '12px', background: 'rgba(255,255,255,.055)', color: '#fff', border: '1px solid rgba(255,255,255,.16)' },
    alert: { background: 'rgba(252,165,165,.08)', border: '1px solid rgba(252,165,165,.3)', borderRadius: '12px' },
    alertText: { color: '#fca5a5' },
  },
  layout: {
    logoImageUrl: '/goaa-logo.svg',
    logoPlacement: 'inside',
    socialButtonsPlacement: 'top',
    socialButtonsVariant: 'blockButton',
    showOptionalFields: false,
    shimmer: false,
  },
};

/** Page wrapper style for goaa-clerk-login (mirrors /client-login <main>). */
export const goaaClerkPageStyle = {
  minHeight: '100vh',
  display: 'grid',
  placeItems: 'center',
  padding: '24px',
  background: '#08080c',
} as const;
