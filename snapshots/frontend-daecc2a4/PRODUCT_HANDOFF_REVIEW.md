# GOAA product handoff — frontend review

Status: source-only candidate. No C1 deployment, service restart, merge or Framer publish is authorized by this document.

Base: `86bbf599dcb51aa057fe7477e058a8ff8814eadd` (includes favicon and `b1bc110` login display repair).

## Scope

- `app/lib/openclaw.ts`: decode `connection_ready` as a strict boolean and `product_action` as an optional string. Existing request URL/body/auth behavior is unchanged.
- `app/components/ChatComponent.tsx`: server-confirmed readiness reveals the existing handoff card even with zero facts/no intent; save/restore/reset that flag with the existing workspace. Explicit handoff can reoffer a dismissed card; fee information cannot reopen it. Decline hides it. No automatic navigation or payment on a chat response.
- `app/components/ProfessionalHandoffCard.tsx`: clarify USD $39.90 platform connection fee, 30 days, no automatic renewal, professional service fees separate. Existing price, callbacks and checkout path remain unchanged.
- `scripts/test-product-handoff.cjs` and `scripts/product-handoff-protected.json`: offline TSX/hook/JSX test harness and protected baseline hashes.

The fee is not a professional service invoice. Order Engine, payment handlers, prices, order state machine, settlement and Invoice code are untouched.

## Offline verification

From the repository root with the project's existing TypeScript dependency:

```sh
node scripts/test-product-handoff.cjs
```

13 checks passed, exit 0, Node v24.19.0. Actual TSX/API decoder code is transpiled/executed using test doubles. The SHA-256 of `hasClientSession`, `sendToLogin`, and `continueToProfessional` matches the baseline. Local validation used an already available TypeScript dependency, without installation.

This is NOT a full Next.js production build, browser/hydration check, real login, real model test, or payment acceptance. Aika must perform the normal clean candidate build and later authorized browser verification. No mock is evidence of real AI capability.

## Coordination and acceptance

Use together with branch `codex/goaa-us-product-policy-20260903` for authoritative backend fee answers and handoff detection. The frontend alone cannot fix model fee explanations. That backend branch is based on the CORS archive and contains OLD frontend code: never deploy its frontend over this branch.

Keep the current C1 release in place pending production deployment approval. Before any approved deployment, verify the actual C1 engine matches the backend baseline and stop on drift; do not overwrite local production changes.

After separate deployment approval: verify guest/real-login click and return, zero-fact tax handoff, fee questions (no navigation/payment), decline/reoffer, refresh, and one real model response using US/USD defaults. No live charges or new orders for this acceptance without explicit authorization.
