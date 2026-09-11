# Customer navigation and order-status recovery — source-only candidate

Base: `d889c3f15adac46d6ab8a3d87350e346e236ff33`.

Status: independent frontend review branch. No merge, deployment, service restart,
database access/migration, payment creation, webhook replay, or configuration change
was performed by this work. C1 transaction diagnosis remains with Aika.

## Scope (8 files: 3 modified, 5 added)

- M `app/customer-order-live/layout.tsx`: add customer navigation before existing overlays.
- M `app/customer-order-live/page.tsx`: explicit unavailable/loading/retry UI; withhold
  zero-price placeholders and transaction controls until an order has loaded; display
  awaiting estimate rather than a zero quote; checkout-return copy does not assert paid.
- M `app/connect-pass/page.tsx`: existing-order loading gate, visible failure, read-only
  recovery, tab-local attempt guard, pending-operation warning, persistent navigation.
- A `app/components/CustomerRecoveryNav.tsx`: sticky same-origin `/planning` link,
  no state clearing, no POST, no cancellation, no browser-history back to Stripe/Vercel.
- A `app/lib/customer-read-recovery.ts`: 20-second UI deadline for reads only.
- A `scripts/test-order-recovery.cjs`: offline component tests.
- A `scripts/order-recovery-protected.json`: parent-derived business-function SHA256s.
- A `ORDER_RECOVERY_REVIEW.md`: this review/handoff record.

## Behavior and deliberate tradeoffs

1. Existing order information must finish loading before the activation button works.
   Failed/timed-out/malformed/forbidden reads do not fall through to a new order.
2. `Re-check status` is a GET-only recovery action. It does not create an order,
   create Checkout, request a match, persist handoff context, or navigate automatically.
   A positive server `connectPaid` field is required for the paid-status recovery copy.
   A negative field is not called payment failure, and query strings are not payment proof.
3. Original normal paid-order matching/navigation remains in place. Recovery also offers
   the original order URL without initiating matching or payment. The former manual
   `Re-check Payment` UI is now read-only; it does not silently repeat business actions.
4. Fresh healthy purchase still invokes the original handlers. A synchronous click latch
   prevents double clicks. A versioned sessionStorage marker remembers an attempted
   operation for the same planning session/matter in this tab, including reloads.
   Previous checkout journey states and cancelled returns enter status recovery first.
5. Unknown outcomes are deliberately conservative: another purchase is not enabled just
   because 20 seconds elapsed or a read reports not yet paid. If no order ID was received,
   preserve the session and have support reconcile the original request. There is no
   force-unlock/delete-marker UI. Retrying a definitively failed transaction is NOT newly
   implemented. This limitation must be accepted before deployment; do not clear the
   marker as an acceptance shortcut.
6. The read deadline stops waiting in the new UI; it does not abort the underlying read.
   The slow-mutation timer only displays a warning; it neither cancels nor resubmits a POST.
   Do not assume leaving the page cancels server work. The marker is NOT server idempotency,
   a payment record, cross-device protection, or a complete cross-tab/account guard.

## Frozen / untouched

`ensureOrder`, `buyPass`, and `verifyConnectPaymentAndMatch` bodies are byte-identical to
the parent, as are the customer order handlers `run`, `accept`, `send`, `answer`, `upload`,
`confirm`, `downloadZip`, and `viewInvoice`. Tests enforce their parent-derived hashes.
This proves handler-body preservation, not that all UI behavior is unchanged: the new
gates, recovery buttons, and return message are intentional changes described above.

No edits to shared `order-api.ts`, `order-runtime.ts`, `OrderRuntimeBridge.tsx`, auth,
backend, payment/provider mode, fee/price, order-state transitions, settlement, Invoice,
Framer, deployment or environment configuration. No dependencies/lockfiles changed.
The source files copied locally for inspection are not part of the commit allowlist.

## Validation actually performed

Command from repository root:

```sh
node scripts/test-order-recovery.cjs
```

Local result: **25 passed, exit 0; Node v24.19.0**. Actual React hooks and TSX are
executed with `react-test-renderer`; API, browser storage, navigation, runtime and clock
are isolated doubles. No real API, login token, payment, DB, browser or app was used.
TypeScript transpilation diagnostics are checked; this is NOT a full typecheck/Next build.

Test tooling: existing isolated TypeScript/React/react-test-renderer dependencies were
reused using NODE_PATH; no dependencies were installed in this turn. react-test-renderer
is not a declared project dependency. Aika must report if it is unavailable and must
not silently install it into production or describe the test as run. If necessary,
prepare a separately approved disposable test-tool environment, matching React 18.

Coverage includes existing-order wait/failure/timeout/late reply, malformed order IDs,
guest redirect, fresh/existing purchases, double clicks, pending creation, reload latch,
cancelled return, previous checkout state, paid read recovery, identity change mid-read,
GET-only retry, unknown/no-order placeholder handling, awaiting quote, return-query copy,
sticky return link and protected handler hashes.

## Remaining production diagnosis and acceptance (not done here)

- Aika must still reconcile the user's order/session, webhook and pass state using
  configured read-only access. Loading states/screenshots alone do not prove payment.
- Aika must identify the actual Stripe success/cancel URL source and the old Vercel
  redirect chain. This frontend candidate does not change those settings.
- The existing shared runtime waits for order + delivery + supplement before showing
  its snapshot, polls without in-flight deduplication, and may retain stale data. That
  behavior is not fixed here; it needs runtime/network evidence and a separately scoped
  fix if it causes the production stall. The new UI exposes the failure and offers exit.
- Full Next build, real browser/sticky-layout/mobile check, authenticated return and
  real server behavior still require validation. Offline tests are not payment acceptance.

## Aika next step — verification only, not a deployment approval

1. Fetch this branch into a clean non-running workspace; verify parent and 8-file scope.
   Compare actual C1 frontend source/release to the parent. Stop on drift; do not overwrite
   newer work or change active symlinks. The backend branch is not a frontend baseline.
2. Read this document; rerun tests with actual versions/exit codes when tooling exists;
   build with the existing fail-closed production process in the isolated workspace.
3. Review the deliberate recovery lock behavior, preserve known order IDs/workspace,
   and verify return links in loading and loaded views on desktop/mobile.
4. Return test/build evidence plus the pending read-only C1/Stripe diagnosis. Do not
   create payments, replay webhooks, change callback configuration or deploy under this
   instruction. If approved later, only a new frontend release/goaa-web would be involved;
   preserve the current release as the exact rollback target.
