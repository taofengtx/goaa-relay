// Resolve hook for the C2 Clerk mock tests.
//
// Two resolution gaps stand between plain Node and this repo's modules:
//   * Next and Clerk publish sub-path entries without an extension Node's ESM
//     resolver will guess, and Clerk's ESM build uses bundler-style directory
//     imports (with an `exports` map that refuses the deep CommonJS subpath, so
//     the hook maps it to an absolute file path);
//   * the repo's TypeScript sources import each other without extensions.
//
// Nothing here changes what the code under test does; it only lets Node find
// the same files a bundle step would.
import { existsSync } from 'node:fs'
import { fileURLToPath, pathToFileURL } from 'node:url'

const REWRITE = {
  'next/server': 'next/server.js',
  'next/navigation': 'next/navigation.js',
  'next/headers': 'next/headers.js',
  'next/cache': 'next/cache.js',
  'next/link': 'next/link.js',
  // The ESM build uses bundler-style directory imports that plain Node cannot
  // resolve, and the package's `exports` map refuses the deep subpath; an
  // absolute file path sidesteps both. The CommonJS build is equivalent.
  '@clerk/nextjs/server': new URL(
    './node_modules/@clerk/nextjs/dist/cjs/server/index.js',
    pathToFileURL(process.cwd() + '/'),
  ).href,
}

export async function resolve(specifier, context, nextResolve) {
  const mapped = REWRITE[specifier]
  if (mapped) {
    try {
      return await nextResolve(mapped, context)
    } catch {
      /* fall through to the original specifier */
    }
  }
  // The repo imports its own modules through the `@/*` tsconfig alias.
  if (specifier.startsWith('@/')) {
    const target = pathToFileURL(`${process.cwd()}/${specifier.slice(2)}`).href
    for (const candidate of [target, `${target}.ts`, `${target}.tsx`, `${target}/index.ts`, `${target}/index.tsx`]) {
      try {
        return await nextResolve(candidate, context)
      } catch {
        /* try the next candidate */
      }
    }
  }
  if ((specifier.startsWith('./') || specifier.startsWith('../')) && !/\.[a-z]+$/i.test(specifier)) {
    for (const ext of ['.ts', '.tsx', '.js', '.mjs']) {
      try {
        const resolved = await nextResolve(specifier + ext, context)
        if (resolved?.url && existsSync(fileURLToPath(resolved.url))) return resolved
      } catch {
        /* try the next extension */
      }
    }
  }
  return nextResolve(specifier, context)
}
