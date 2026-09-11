'use client';

/**
 * LoginMenu — header account dropdown for planning.goaa.ai.
 * Mirrors the www.goaa.ai navbar Embed (LOGIN / REGISTER ▾ → dark dropdown).
 *
 * Usage:
 *   <LoginMenu signedIn={isSignedIn} />
 *   <LoginMenu signedIn={isSignedIn} onLogout={signOut} />   // if the app has its own signOut()
 *
 * No external deps. All text is English. Same-tab navigation.
 */

import { useCallback, useEffect, useId, useRef, useState } from 'react';

type LoginMenuProps = {
  signedIn: boolean;
  /** 'solid' = purple button (www.goaa.ai style). 'ghost' = transparent, text only (planning header). */
  variant?: 'solid' | 'ghost';
  /** Where MY ACCOUNT goes when signed in. */
  accountHref?: string;
  /** Where LOG OUT goes when signed in (used when onLogout is not provided). */
  logoutHref?: string;
  /** Optional app-native logout. If provided, LOG OUT calls this instead of navigating. */
  onLogout?: () => void;
  customerLoginHref?: string;
  agentLoginHref?: string;
  registerHref?: string;
  /** Shown under the menu when a sign-out could not complete. */
  error?: string | null;
};

const PURPLE = '#512FEB';
const PURPLE_LIGHT = '#8B7BFF';
const MENU_BG = '#17143a';
const FONT = "600 15px/1 Outfit, Arial, sans-serif";

const styles = {
  wrap: { position: 'relative', display: 'inline-block' } as React.CSSProperties,
  button: {
    boxSizing: 'border-box',
    minWidth: 166,
    height: 38,
    padding: '0 12px',
    border: 0,
    borderRadius: 8,
    background: PURPLE,
    color: '#fff',
    font: FONT,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    whiteSpace: 'nowrap',
    cursor: 'pointer',
    outline: 'none',
  } as React.CSSProperties,
  buttonGhost: {
    minWidth: 0,
    padding: '0 8px',
    background: 'transparent',
    color: '#fff',
    font: '500 15px/1 Outfit, Arial, sans-serif',
  } as React.CSSProperties,
  buttonGhostHover: { background: 'rgba(255,255,255,.08)' } as React.CSSProperties,
  arrow: { fontSize: 10, transform: 'translateY(1px)' } as React.CSSProperties,
  menu: {
    position: 'absolute',
    top: 'calc(100% + 6px)',
    right: 0,
    boxSizing: 'border-box',
    minWidth: 220,
    padding: 6,
    background: MENU_BG,
    border: '1px solid rgba(255,255,255,.12)',
    borderRadius: 12,
    boxShadow: '0 10px 34px rgba(20,10,80,.16)',
    color: '#fff',
    font: '600 14px/1 Outfit, Arial, sans-serif',
    zIndex: 1000,
  } as React.CSSProperties,
  item: {
    display: 'flex',
    alignItems: 'center',
    boxSizing: 'border-box',
    width: '100%',
    height: 44,
    padding: '0 20px',
    borderRadius: 8,
    color: '#fff',
    textDecoration: 'none',
    letterSpacing: '.04em',
    outline: 'none',
    background: 'transparent',
    border: 0,
    font: 'inherit',
    cursor: 'pointer',
    textAlign: 'left',
  } as React.CSSProperties,
  itemHover: { background: 'rgba(255,255,255,.08)' } as React.CSSProperties,
  divider: { height: 1, background: 'rgba(255,255,255,.15)', margin: '6px 0' } as React.CSSProperties,
  label: {
    boxSizing: 'border-box',
    padding: '12px 20px 2px',
    color: 'rgba(255,255,255,.55)',
    font: '600 12px/1.2 Outfit, Arial, sans-serif',
    letterSpacing: '.04em',
  } as React.CSSProperties,
};

function MenuLink({
  href,
  children,
  color,
  weight,
  onClick,
}: {
  href?: string;
  children: React.ReactNode;
  color?: string;
  weight?: number;
  onClick?: () => void;
}) {
  const [hover, setHover] = useState(false);
  const style: React.CSSProperties = {
    ...styles.item,
    ...(hover ? styles.itemHover : null),
    ...(color ? { color } : null),
    ...(weight ? { fontWeight: weight } : null),
  };
  const common = {
    role: 'menuitem' as const,
    style,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
  };
  if (onClick) {
    return (
      <button type="button" {...common} onClick={onClick}>
        {children}
      </button>
    );
  }
  return (
    <a href={href} {...common}>
      {children}
    </a>
  );
}

export default function LoginMenu({
  signedIn,
  variant = 'solid',
  accountHref = '/planning',
  logoutHref = '/client-logout?return=home',
  onLogout,
  error = null,
  customerLoginHref = '/client-login',
  agentLoginHref = '/agent-login',
  registerHref = '/client-login',
}: LoginMenuProps) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: PointerEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) close();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
    };
    document.addEventListener('pointerdown', onDown, true);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('pointerdown', onDown, true);
      document.removeEventListener('keydown', onKey);
    };
  }, [open, close]);

  const label = signedIn ? 'MY ACCOUNT' : 'LOGIN / REGISTER';
  const [btnHover, setBtnHover] = useState(false);
  const buttonStyle: React.CSSProperties =
    variant === 'ghost'
      ? { ...styles.button, ...styles.buttonGhost, ...(btnHover || open ? styles.buttonGhostHover : null) }
      : styles.button;

  return (
    <div ref={wrapRef} style={styles.wrap} data-testid="login-menu">
      <button
        type="button"
        style={buttonStyle}
        onMouseEnter={() => setBtnHover(true)}
        onMouseLeave={() => setBtnHover(false)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((v) => !v)}
      >
        {label}
        <span style={styles.arrow} aria-hidden="true">
          {open ? '\u25B4' : '\u25BE'}
        </span>
      </button>

      {open && (
        <div id={menuId} role="menu" style={styles.menu}>
          {signedIn ? (
            <>
              <MenuLink href={accountHref}>MY ACCOUNT</MenuLink>
              {onLogout ? (
                <MenuLink onClick={onLogout}>LOG OUT</MenuLink>
              ) : (
                <MenuLink href={logoutHref}>LOG OUT</MenuLink>
              )}
              {error ? (
                <div role="alert" data-testid="sign-out-error" style={{ padding: '10px 20px 6px', fontSize: 13, color: '#fca5a5', letterSpacing: 0 }}>
                  {error}
                </div>
              ) : null}
            </>
          ) : (
            <>
              <MenuLink href={customerLoginHref}>CUSTOMERS</MenuLink>
              <MenuLink href={agentLoginHref}>AGENTS</MenuLink>
              <div style={styles.divider} aria-hidden="true" />
              <div style={styles.label}>CUSTOMERS</div>
              <MenuLink href={registerHref} color={PURPLE_LIGHT} weight={700}>
                Register Now
              </MenuLink>
            </>
          )}
        </div>
      )}
    </div>
  );
}
