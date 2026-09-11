/**
 * preview-business-store.ts — browser persistence adapter for the
 * business-loop demo (accounts, agent order loop, admin console).
 *
 * Like the license-preview store, this key is demo-only. It plays the role
 * the server + database play in production. SSR never reads it: pages
 * render from `defaultBusinessState()` first and hydrate the persisted
 * value inside `useEffect`.
 */

import {
  type BusinessSeedKind,
  type BusinessState,
  defaultBusinessState,
  seedBusinessState,
} from './preview-business'

export const BUSINESS_STORE_KEY = 'goaa_portal_preview_business_v1'

export interface BusinessStorageLike {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

class MemoryBusinessStorage implements BusinessStorageLike {
  private map = new Map<string, string>()
  getItem(key: string) { return this.map.has(key) ? this.map.get(key)! : null }
  setItem(key: string, value: string) { this.map.set(key, value) }
  removeItem(key: string) { this.map.delete(key) }
}

let injectedStorage: BusinessStorageLike | null = null

/** Test seam: inject an in-memory backend so node can exercise the store. */
export function setBusinessStorageForTests(storage: BusinessStorageLike | null): void {
  injectedStorage = storage
}

function effectiveStorage(): BusinessStorageLike | null {
  if (injectedStorage) return injectedStorage
  if (typeof window !== 'undefined' && window.localStorage) return window.localStorage
  return null
}

/** Hydration-safe read: returns the demo default when nothing is stored or
 *  the stored payload does not parse (browser-only). */
export function readBusinessState(): BusinessState {
  const storage = effectiveStorage()
  if (!storage) return defaultBusinessState()
  try {
    const raw = storage.getItem(BUSINESS_STORE_KEY)
    if (!raw) return defaultBusinessState()
    const parsed = JSON.parse(raw) as BusinessState
    if (!parsed || parsed.version !== 1 || !Array.isArray(parsed.accounts)) return defaultBusinessState()
    return parsed
  } catch {
    return defaultBusinessState()
  }
}

export function writeBusinessState(state: BusinessState): BusinessState {
  const storage = effectiveStorage()
  if (storage) {
    try {
      storage.setItem(BUSINESS_STORE_KEY, JSON.stringify(state))
    } catch {
      // Prototype storage is best-effort; state still drives the UI.
    }
  }
  return state
}

/** Replaces the persisted demo world with a fixture seed. */
export function applyBusinessSeed(kind: BusinessSeedKind): BusinessState {
  return writeBusinessState(seedBusinessState(kind))
}
