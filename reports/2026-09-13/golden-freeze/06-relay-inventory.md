# 06 — relay（中轉倉）盤點

- 日期：2026-09-13；唯讀（未 push）。

## 1. repo 與現況

| 項目 | 值 |
|---|---|
| repo | `https://github.com/taofengtx/goaa-relay`（public、預設 `main`） |
| 本輪 staging | `/tmp/goaa-relay-stage`（branch `main`、clean） |
| 本輪起始 HEAD | `064a5cdb47564bead5e1abcf04bf5e06303e5bbe`（＝ R7-G1 完成報告） |
| remote | `github-relay:taofengtx/goaa-relay.git`（key `~/.ssh/goaa_relay_ed25519`） |
| 另一 clone | `/tmp/goaa-relay`（Claude Code 用，**本輪未動**） |

## 2. 內容佈局（`reports/`）

- `reports/2026-09-11/`（C1/C2 前期各輪）
- `reports/2026-09-12/`：`d0-hardening/`、`d0-2-tcp5432/`、`d0-3-ufw8080/CANCELLED.md`、`d0-3b-tunnel-migration/RECON.md`、`d0-4-model-router/REPORT.md`、`r1-db/{RECON.md,PRECHECK-ROLES.md}`、`r2-db-create/REPORT.md`、`r3-db-migrate/REPORT.md`、`r4-backend/{RECON.md,REPORT-steps1-4.md,REPORT-step5.md}`、`r5-clerk-live/REPORT.md`、`r5b-frontend/{RECON.md,BUILD.md,DEPLOY.md,DEPLOY-2.md,DEPLOY-3.md}`、`r6-golive/REPORT.md`、`r7-secret-swap/REPORT.md`、`r7-g1-admin-bootstrap/REPORT.md`
- `reports/2026-09-13/golden-freeze/` ← **本輪新增**

## 3. 缺口（relay 沒有的）

| 缺什麼 | 影響 |
|---|---|
| 任何**程式碼**（relay 依令只放程式碼與報告；實際上目前只有報告） | 無法從 relay 重建系統；relay 不是備份 |
| C1/C2 的**部署樹**（前端 release 1969 檔、後端 37 檔） | 生產 artifact 仍只在 C1 |
| C2 的 `goaa_c2test`、C1 的 `goaa_platform` **備份** | 見 07 報告（`/root/backups/` 僅 C1 側、且為 DB dump） |
| 九月 8–13 的 **25 個 local-only commit** | 與 05 報告同一風險 |

## 4. 紀律（本輪遵守）

- 未 force-push、未 rewrite；commit 一律 `git commit -F <file>`（去 BOM）。
- 推送前秘密掃描：命中數必須為 **0**（TOTAL_HITS）。
- 報告內可路由 IPv4 末段以 `⟨N⟩` 切分；sha256 一律截 16 hex。
