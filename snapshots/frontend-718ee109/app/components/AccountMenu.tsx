'use client'

// Account menu for the signed-in customer planning header (2026-09-04).
// Replaces the static "已登录 · Signed in" status span with an accessible
// disclosure menu: trigger button → popover with "退出登录 · Sign out".
// "For Professionals" stays as its own separate nav item (rendered by the
// caller, never inside this menu).
//
// Behavior:
//   - click trigger toggles; second click closes
//   - pointerdown outside closes
//   - Escape closes and returns focus to the trigger
//   - ArrowDown on the trigger focuses the menu item when the menu is open
//   - focus moves into the menu when it opens
//   - menuitem activates sign-out via keyboard (Enter/Space natively)
import { useEffect, useRef, useState } from 'react'

type Props = {
  onSignOut: () => void
}

export default function AccountMenu({ onSignOut }: Props) {
  const [open, setOpen] = useState(false)
  const wrapRef = useRef<HTMLDivElement | null>(null)
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const itemRef = useRef<HTMLButtonElement | null>(null)

  // Move focus to the only menuitem when the menu opens.
  useEffect(() => {
    if (!open) return
    const first = itemRef.current
    if (first && typeof first.focus === 'function') first.focus()
  }, [open])

  // Outside click / Escape listeners live for the whole open period.
  useEffect(() => {
    if (typeof window === 'undefined') return
    if (!open) return
    function onPointerDown(event: PointerEvent) {
      const wrap = wrapRef.current
      // In browsers wrap.contains is a DOM Node method; if for any reason it
      // is unavailable we treat the pointer as outside to fail closed.
      if (!wrap || typeof wrap.contains !== 'function' || !wrap.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault()
        setOpen(false)
        const trigger = triggerRef.current
        if (trigger && typeof trigger.focus === 'function') trigger.focus()
      }
    }
    window.addEventListener('pointerdown', onPointerDown)
    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('pointerdown', onPointerDown)
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  function toggle() {
    setOpen(prev => !prev)
  }

  function handleTriggerKeyDown(event: React.KeyboardEvent<HTMLButtonElement>) {
    if (event.key === 'ArrowDown' && open) {
      event.preventDefault()
      const item = itemRef.current
      if (item && typeof item.focus === 'function') item.focus()
    }
  }

  return (
    <div className="goaa-account-menu" ref={wrapRef}>
      <button
        type="button"
        ref={triggerRef}
        className="goaa-link goaa-account-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? 'goaa-account-menu-popover' : undefined}
        onClick={toggle}
        onKeyDown={handleTriggerKeyDown}
      >
        已登录 · Signed in <span aria-hidden="true">▾</span>
      </button>
      {open && (
        <div
          id="goaa-account-menu-popover"
          role="menu"
          aria-label="Account menu"
          className="goaa-account-popover"
        >
          <button
            type="button"
            ref={itemRef}
            role="menuitem"
            className="goaa-account-item"
            onClick={() => { setOpen(false); onSignOut() }}
          >
            退出登录 · Sign out
          </button>
        </div>
      )}
    </div>
  )
}
