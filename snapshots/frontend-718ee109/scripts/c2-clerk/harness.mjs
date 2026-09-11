// Minimal harness for the C2 Clerk mock tests.
//
// It does three things and nothing clever:
//   1. registers resolve-hook.mjs so Node can load the repo's TypeScript;
//   2. counts PASS/FAIL and exits non-zero if anything failed;
//   3. blocks outbound network calls, so a test that silently tried to reach
//      Clerk (or anything else) fails loudly instead of passing on a stale
//      answer. These are mock tests: no build, no server, no session, no OTP.
import { createRequire, register } from 'node:module'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
register(pathToFileURL(path.join(here, 'resolve-hook.mjs')).href)

export const ROOT = path.resolve(here, '..', '..')

/** Load a repo file by path, e.g. load('app/lib/clerk-entry.ts'). */
export async function load(relative) {
  return import(pathToFileURL(path.join(ROOT, relative)).href)
}

/* ---------------------------------------------------------------- network */

export const networkAttempts = []

function blockNetwork() {
  const http = require('node:http')
  const https = require('node:https')
  const net = require('node:net')
  const tls = require('node:tls')

  const record = (label) => (...args) => {
    networkAttempts.push(label)
    throw new Error(`network access is not allowed in mock tests (${label})`)
  }

  http.request = record('http.request')
  http.get = record('http.get')
  https.request = record('https.request')
  https.get = record('https.get')
  net.connect = record('net.connect')
  net.createConnection = record('net.createConnection')
  net.Socket.prototype.connect = record('net.Socket#connect')
  tls.connect = record('tls.connect')
}

const require = createRequire(import.meta.url)
blockNetwork()

/* ----------------------------------------------------------------- runner */

let passed = 0
let failed = 0

export async function test(name, fn) {
  try {
    await fn()
    passed += 1
    console.log(`PASS ${name}`)
  } catch (error) {
    failed += 1
    console.log(`FAIL ${name}: ${error && error.message ? error.message : error}`)
  }
}

export function assert(condition, message) {
  if (!condition) throw new Error(message || 'assertion failed')
}

export function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message || 'values differ'}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`)
  }
}

export function summary(label) {
  for (const attempt of networkAttempts) console.log(`FAIL outbound network call blocked: ${attempt}`)
  failed += networkAttempts.length
  console.log(`\n${label}: ${passed} passed, ${failed} failed`)
  process.exit(failed === 0 ? 0 : 1)
}
