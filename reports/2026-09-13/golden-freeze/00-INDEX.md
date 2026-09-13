# 00 — INDEX：Golden Freeze + GitHub Archaeology（2026-09-13）

- 令：Tao 2026-09-13 00:58 【GOAA.AI MASTER ORDER｜Golden Freeze + GitHub Archaeology】
- 目標：**停止擴張 UI**；先把「1 首頁 + 4 端」確認為產品黃金面，再完整盤點
  GitHub / worktree / C1 release / relay / Stripe / Skills / AI Agent / Worker 的程式來源，
  為下一階段真實業務接線建立**唯一基線**。
- 紀律：**全程唯讀**（未 merge / rebase / delete / force-push、未改 C1、未部署、未付款、未寫 DB）。
- 本輪完成到報告即 **STOP**。

## 六大頭條

1. **C1 現行生產的前端與後端 commit 都不在 GitHub 任何 ref 上**（`40c8546e…` / `dc64591b…`）
   ⇒ GitHub 不是唯一真實來源；生產 = GitHub 祖先 `76af718` ＋ 25 個 local-only commit。
2. **黃金面已在生產成立**：1 首頁 + 3 端（customer / agent / admin）＋ 統一登入 `/client-login`；
   三端菜單與令文逐項相符（agent 5 項、admin 6 項）。令文第 4 面（Worker/Developer）原文被截斷。
3. **$39.90 專業連線在發版時是關閉的**：`GOAA_PAID_CONNECTION` 未設＝關；改用「coming soon ＋ 30 分鐘預約」。
   生產前端**刪除了** `app/api/stripe/{checkout,webhook,pass-status}` 三支路由。
4. **commerce 的資料層存在且曾用**（`goaa_order_payments` 41 列、`settlements` 14 列、`invoices` 7 列），
   但**寫入端未定位**（`api.goaa.ai` 的 `goaa-router` 內 0 命中 Stripe）。
5. **Worker / Aika-Box 血緣反而是最乾淨的一份**：主控台源碼在 GitHub（樹摘要 `faa9f6ba4603ef9b`，5 個 ref 一致），
   `origin/main` 已含 capability_grant / baton / authorization_kernel。
6. **首頁 live 已是新定位**（"Your Personal AI Agents" ×2、"Get Things Done" ×2、"Make Money" ×2、舊內容指紋 0），
   但 `<title>`/`og:title`/`twitter:title` **仍是舊定位** `GOAA.AI Life&Asset Intelligence`（3 處）。

## 逐檔指紋（`bytes` ＝ UTF-8 位元組數；`sha16` ＝ sha256 前 16 hex）

| 檔案 | bytes | sha16 |
|---|---|---|
| `01-golden-surface.md` | 4,850 | `0d5ab1da9c3a5d38` |
| `02-homepage-live-audit.md` | 2,865 | `d54d87ca6fd5a26a` |
| `03-unified-login-and-gates.md` | 2,288 | `5be53c681fdffe28` |
| `04-github-archaeology.md` | 5,221 | `67aac092fe5ccfc2` |
| `05-drift-production-vs-github.md` | 2,778 | `ec318c6c4a738e95` |
| `06-relay-inventory.md` | 1,992 | `91cbddfa64830f7e` |
| `07-c1-release-inventory.md` | 4,303 | `7d6452d039258510` |
| `08-stripe-lineage.md` | 4,802 | `86b714d93350528e` |
| `09-worker-aikabox-lineage.md` | 4,439 | `18668d902e4edee3` |
| `10-skills-and-ai-agent-lineage.md` | 2,724 | `f624b380c9459ce5` |
| `11-baseline-recommendation.md` | 2,708 | `b238d42d54611f30` |
| `12-open-questions.md` | 2,549 | `2e90587c991455dc` |

> 本檔（`00-INDEX.md`）自身的 bytes / sha16 見本輪 commit 訊息與 relay 回報（避免自我指涉）。

## 素材位置（皆為本機暫存，未 push 進 relay）

- GitHub：`/tmp/gh-a1.sh|a2.sh|a3.sh|a5.sh|a6.sh` 與 `*.out`；`/tmp/gh/refs_local.txt`、`refs_remote.txt`、
  `matrix.txt`／`matrix.json`（116 行逐 ref 矩陣）、`caps.txt`／`caps.json`（17 ref × 26 能力指紋）。
- live：`/tmp/gh/goaa_ai.{html,hdr}`、`/tmp/gh/www_goaa_ai.{html,hdr}`、`/tmp/gh/ends/*.{html,hdr}`（9 個端點）。
- C1 唯讀：`/tmp/gh-c1.sh`／`/tmp/gh-c1b.sh` 與 `c1.out`／`c1b.out`；`/tmp/gh-db1.sh`／`/tmp/gh-db2.sh`（DB 唯讀查詢）。

## 下一步（建議，未執行）

- 見 `11-baseline-recommendation.md` §3：**唯一動作** = 把兩條 local-only 生產分支推上 GitHub（推送前秘密掃描 0 命中）。
- 見 `12-open-questions.md`：令文 §4 補送、commerce 寫入端定位、$39.90 重開前提。

## STOP

本輪**到此為止**：不出現任何變更、不重啟服務、不寫 DB、不動金鑰。
