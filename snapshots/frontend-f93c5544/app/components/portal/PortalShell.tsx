'use client';

/**
 * PortalShell — the one layout every portal page uses (customer / agent / admin).
 * Visual spec = planning.goaa.ai workspace: rounded header card with logo +
 * brand text + account menu (ghost), left rail card, main card, optional aside.
 * Brand text follows the portal: customer "AI Butler", agent "AI Agent", admin "AI Admin".
 *
 * Requires goaa-tokens.css loaded once in app/layout.tsx.
 * Does not import anything from /portal-preview or the golden ChatComponent.
 */

import Link from 'next/link';
import type { ReactNode } from 'react';
import LoginMenu from '@/app/components/LoginMenu';

export type RailItem = {
  id: string;
  label: string;
  href?: string;          // link item
  onSelect?: () => void;  // in-page item
  isNew?: boolean;
  dividerAbove?: boolean;
  disabled?: boolean;
};

export type RailSection = { title?: string; items: RailItem[] };

export type PortalShellProps = {
  /** Which portal this is; only affects data-attrs and the switch link. */
  portal: 'customer' | 'agent' | 'admin';
  brandHref?: string;                     // default '/planning'
  signedIn: boolean;
  onLogout?: () => void;
  /** Optional primary CTA at the top of the rail (e.g. "+ New"). */
  railCta?: { label: string; onClick: () => void };
  sections: RailSection[];
  activeId: string;
  /** Rendered at the bottom of the rail: role switch / gate hint. */
  railFooter?: ReactNode;
  eyebrow?: string;
  title?: ReactNode;
  headerRight?: ReactNode;                // e.g. status pill next to title
  aside?: ReactNode;                      // right column (blueprint, help)
  children: ReactNode;
};

export const PORTAL_BRAND: Record<PortalShellProps['portal'], string> = {
  customer: 'AI Butler',
  agent: 'AI Agent',
  admin: 'AI Admin',
};

export default function PortalShell(p: PortalShellProps) {
  const withAside = Boolean(p.aside);
  const brand = PORTAL_BRAND[p.portal];
  return (
    <div className="goaa-portal" data-portal={p.portal}>
      <header className="goaa-header">
        <Link className="goaa-brand" href={p.brandHref ?? '/planning'} aria-label={`${brand} home`}>
          <img src="/goaa-logo.svg" alt="" />
          <span className="goaa-brand-text">{brand}</span>
        </Link>
        <LoginMenu variant="ghost" signedIn={p.signedIn} onLogout={p.onLogout} />
      </header>

      <div className={`goaa-layout${withAside ? ' goaa-with-aside' : ''}`}>
        <nav className="goaa-rail" aria-label="main navigation">
          {p.railCta ? (
            <button type="button" className="goaa-rail-cta" onClick={p.railCta.onClick}>
              + {p.railCta.label}
            </button>
          ) : null}

          {p.sections.map((s, si) => (
            <div key={si}>
              {s.title ? <div className="goaa-rail-section">{s.title}</div> : null}
              {s.items.map((it) => {
                const current = it.id === p.activeId;
                const body = (
                  <>
                    <span>{it.label}</span>
                    {it.isNew ? <span className="goaa-rail-tag">NEW</span> : null}
                  </>
                );
                return (
                  <div key={it.id}>
                    {it.dividerAbove ? <div className="goaa-rail-divider" /> : null}
                    {it.href ? (
                      <Link
                        className="goaa-rail-item"
                        href={it.href}
                        aria-current={current ? 'page' : undefined}
                        aria-disabled={it.disabled || undefined}
                        data-testid={`rail-${it.id}`}
                      >
                        {body}
                      </Link>
                    ) : (
                      <button
                        type="button"
                        className="goaa-rail-item"
                        aria-current={current ? 'page' : undefined}
                        disabled={it.disabled}
                        onClick={it.onSelect}
                        data-testid={`rail-${it.id}`}
                      >
                        {body}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          ))}

          {p.railFooter ? (
            <>
              <div className="goaa-rail-divider" />
              {p.railFooter}
            </>
          ) : null}
        </nav>

        <main className="goaa-main">
          {(p.eyebrow || p.title) && (
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, marginBottom: 20 }}>
              <div>
                {p.eyebrow ? <div className="goaa-eyebrow">{p.eyebrow}</div> : null}
                {p.title ? <h1 className="goaa-h1">{p.title}</h1> : null}
              </div>
              {p.headerRight}
            </div>
          )}
          {p.children}
        </main>

        {withAside ? <aside className="goaa-aside">{p.aside}</aside> : null}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Rail presets — the only place the three menus are defined.          */
/* ------------------------------------------------------------------ */

export const CUSTOMER_RAIL: RailSection[] = [
  {
    title: 'My AI Butler',
    items: [
      { id: 'chat', label: 'Chat', href: '/planning' },
      { id: 'matters', label: 'Matters', href: '/planning?view=matters' },
      { id: 'skills', label: 'Skills Marketplace', href: '/agent-loop/customer/skills' },
      { id: 'licensed', label: 'Get Licensed', href: '/agent-loop/customer/get-licensed', isNew: true, dividerAbove: true },
      { id: 'earning', label: 'Earning Paths', href: '/agent-loop/customer/earning', isNew: true },
      // Plan Result and Professional Execution are intentionally absent:
      // capabilities remain reachable from Matters cards and the order flow.
    ],
  },
];

export const AGENT_RAIL: RailSection[] = [
  {
    title: 'Agent Portal',
    items: [
      { id: 'overview', label: 'Overview', href: '/agent-loop/agent' },
      { id: 'opportunities', label: 'Opportunities', href: '/agent-loop/agent/opportunities' },
      { id: 'orders', label: 'Service Orders', href: '/agent-loop/agent/orders' },
      { id: 'knowledge', label: 'Knowledge Base', href: '/agent-loop/agent/knowledge' },
      { id: 'my-ai', label: 'My AI', href: '/agent-loop/agent/my-ai' },
    ],
  },
];

export const ADMIN_RAIL: RailSection[] = [
  {
    title: 'Admin',
    items: [
      { id: 'overview', label: 'Overview', href: '/agent-loop/admin' },
      { id: 'applications', label: 'Applications', href: '/agent-loop/admin/applications' },
      { id: 'content', label: 'Content', href: '/agent-loop/admin/content' },
      { id: 'finance', label: 'Finance', href: '/agent-loop/admin/finance' },
      { id: 'system', label: 'System', href: '/agent-loop/admin/system' },
      { id: 'support', label: 'Support', href: '/agent-loop/admin/support' },
    ],
  },
];
