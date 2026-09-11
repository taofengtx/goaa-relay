// Extra resolve hook, registered by test-bff.mjs, that points the BFF's single
// Clerk SDK import at the test double. It is a separate hook (rather than a flag
// on the shared one) because the shared hook is loaded by the harness—and the
// loader runs on its own thread, which keeps the process.env it started with, so
// a switch set later in the test body would never be seen.
import { fileURLToPath, pathToFileURL } from 'node:url'
import { existsSync } from 'node:fs'

const STUB = pathToFileURL(
  fileURLToPath(new URL('./stub-clerk-server.mjs', import.meta.url)),
).href

export async function resolve(specifier, context, nextResolve) {
  if (specifier === '@clerk/nextjs/server' && existsSync(fileURLToPath(STUB))) {
    return { url: STUB, shortCircuit: true }
  }
  return nextResolve(specifier, context)
}
