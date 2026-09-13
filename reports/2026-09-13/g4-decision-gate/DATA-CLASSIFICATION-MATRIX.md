# DATA-CLASSIFICATION-MATRIX — GOAA（G-4 §3）

**日期**：2026-09-13 ｜ **範圍**：schema / config / code-level 分類（**未讀取任何正文或客戶內容**）
**權威環境**：C1（Live）｜`goaa`（commerce，18 MB）｜`goaa_platform`（identity，8,783 kB）｜C2（Test）｜D0（Aika-Box，local）
**列讀方式**：`information_schema.columns` + `count(*)` + 檔案 metadata + 代碼靜態判讀。**無 SELECT 正文**。

**證據等級**：`E1` = 資料庫 schema/計數實測；`E2` = 檔案系統 metadata 實測；`E3` = 代碼靜態判讀；`E4` = 約定/文件宣告（未實測）。

**紅字鐵律**：本檔只寫 schema、欄位、計數、型別。**任何欄位值、token、密鑰、客戶文本一律不出現。**

**計數校正**：本輪改用 `count(*)` 實測，與 G-3 報告中部分 `pg_stat_user_tables.n_live_tup`（估計值、部分已過期）不同 ⇒ **以本檔為準**（例：`sessions` 106（非 6）、`messages` 547（非 34）、`tasks` 21、`tool_invocations` 21、`audit_log` 5、`nodes` 1、`business_tokens` 4）。

---

## A. 矩陣

| # | Data Class | System / Table / Path | PII? | Sensitivity | Customer / Provider / Admin access | Stored in RAG? | May go to external Skill? | May go to external AI Agent? | Retention defined? | Deletion implemented? | Audit logged? | Backup included? | E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Clerk identity** | `goaa_platform`: `users`(2) `user_roles`(4) `user_identities`(2) `identity_events`(8) `user_sessions`(0)；外部：Clerk Prod instance（`clerk.goaa.ai`） | YES | High | C: self / P: self / A: yes | NO | **NO** | **NO** | NO | ✗ 無 user-delete 路徑；`identity_events` 依 0003 設計為 append-only（特性非缺陷） | ✓ `identity_events`(8) | **✗ 無任何 dump** | E1 |
| 2 | **email / phone** | `goaa_platform.users.email`（**全 NULL**）`user_identities.email_snapshot`(2)；`goaa_order_users.email`(72) `phone`；`credits.email`(4)；`goaa_email_send_log.to_email`(2) | YES | High | C: self / P: self / A: yes | NO | **NO** | **NO** | NO | ✗ | △ 僅寄送日誌 | △ 僅 09-06 commerce dump | E1 |
| 3 | **license metadata** | `goaa_platform`: `agent_applications`(1) `agent_licenses`(1)；`goaa`: `goaa_agent_profiles.license_type/license_states`(2) | YES（姓名／證號） | High | C: 部分 / P: self / A: yes | NO | △ **metadata-only**（NIPR/ARELLO 查驗結果可） | △ metadata-only | NO | ✓ 有硬刪 stale license 路徑（`delete from agent_licenses`） | ✓ `agent_review_events`(12) | **✗** | E1,E3 |
| 4 | **license document** | `goaa_platform.agent_license_documents`(1) `storage_key`；檔案 `/opt/goaa-platform/private-files/<sha256>.pdf`（1 檔、109,349 B、0600） | YES（身分證件） | **Critical** | C: ✗ / P: self（下載 TTL 120 s） / A: yes | NO | **NO** | **NO** | ✗ 無 TTL（`DOWNLOAD_TTL` 只是連結時效） | ✓ 軟刪列 + `storage.delete_bytes` 實刪檔案（E3） | △ `identity_events` | **✗ 無備份、無異地** | E1,E2,E3 |
| 5 | **Customer Chat** | `goaa`: `sessions`(106) `messages`(547)（`content` text）；`qwenpaw_memory_chunks`(1,165，`text_redacted`) | YES | High | C: self / P: 僅該案 / A: yes | **YES**（經 `f_lite_sanitize` 脫敏後入庫） | **NO** | **NO**（須先 consent + egress 契約） | NO | △ 僅 archive 旗標，**無 purge** | ✗ router 端讀取無審計 | △ 部分 | E1,E3 |
| 6 | **Matter** | `goaa`: `goaa_order_service_orders.handoff_context`(jsonb,36) `goaa_order_opportunities`(10) `goaa_agent_leads`(13) | YES | High | C: self / P: 配對後 / A: yes | NO | △ 需 consent | △ 需 consent | NO | ✗ | ✓ `goaa_order_events`(538) | △ commerce dump | E1 |
| 7 | **Professional Handoff** | `goaa`: `goaa_order_deliveries`(3) `goaa_order_delivery_packages`(17) `goaa_order_delivery_package_files`(29) `goaa_order_messages`(8) | YES | High | C: self / P: self / A: yes | NO | △ 需 consent | △ 需 consent | NO | ✗ | ✓ events | △ | E1 |
| 8 | **Order** | `goaa`: `goaa_order_service_orders`(36) `goaa_order_events`(538) `goaa_order_tokens`(259) `goaa_order_users`(72) | YES | Medium-High | C: self / P: 配對後 / A: yes | NO | △ metadata-only | △ metadata-only | NO | ✗ | ✓ events | △ | E1 |
| 9 | **Quote / Estimate** | `goaa`: `goaa_order_estimates`(19) `goaa_order_supplement_requests`(17) `..._items`(38) | YES（輕） | Medium | C: self / P: self / A: yes | NO | △ metadata-only | △ metadata-only | NO | ✗ | ✓ events | △ | E1 |
| 10 | **Invoice** | `goaa`: `goaa_order_invoices`(7) `pdf_key`；`invoice_pdf.py` | YES | Medium | C: self / P: self / A: yes | NO | **NO** | **NO** | NO | ✗ | △ | △ | E1,E3 |
| 11 | **Payment metadata** | `goaa`: `goaa_order_payments`(41，`payment_type`/`status`/`amount`/`idempotency_key`) | NO | High（金融） | C: self / P: 部分 / A: yes | NO | △ metadata-only | △ metadata-only | NO | ✗ | ✓ events | △ | E1 |
| 12 | **Stripe identifiers** | `goaa`: `goaa_order_agents.stripe_connect_account_id`(28) `..._service_orders.connect_checkout_session_id/service_checkout_session_id`(36) `goaa_order_settlements.transfer_id`(14) | NO | High | C: ✗ / P: self（僅 acct 狀態） / A: yes | NO | **僅 Stripe**（不得轉第三方 Skill/Agent） | **僅 Stripe** | N/A | ✗（`accounts.del` 未實作） | ✓ events + settlements | △ | E1 |
| 13 | **AI Memory** | `goaa`: `qwenpaw_memory_chunks`(1,165，5928 kB，`text_redacted` + `embedding vector` + `metadata`) `agent_memory`(0) `conversation_memory`(0)；D0 `~/.qwenpaw/workspaces/default/{memory,MEMORY.md}` | YES（業餘者情境） | Medium-High | C: ✗ / P: ✗ / A: via D0 | **YES** | **NO** | △ 僅在「本機 Ollama」內；**雲端模型需 consent** | NO | ✗ 無刪除 API（僅檔層可手動） | ✗ | **✗** | E1,E2 |
| 14 | **RAG chunks** | `goaa`: `goaa_agent_knowledge_chunks`(105，`content`+`embedding`，256 kB) `goaa_agent_knowledge_docs`(2) `agent_documents`(0) | YES（可能含客戶文件） | **High** | C: ✗ / P: self（上傳／刪除） / A: yes | **YES（本身即 RAG）** | **NO** | **NO** | NO | ✓ 硬刪兩表（`agent_db.py` DELETE chunks + docs；**無 tombstone**） | ✗（無審計） | **✗** | E1,E3 |
| 15 | **Skill invocation** | `goaa`: `goaa_agent_skills`(2，enabled 旗標) `tools`(8) `tool_invocations`(21，`args`/`result` jsonb)；registry `local-console/registry/skills.json`(4)；前端 skill store(s1–s4) | YES（args/result 可含） | High | C: ✗ / P: self（切 enabled） / A: yes | NO | **YES（正是外呼點）** | YES | NO | ✗ | △ `tool_invocations` 本身即日誌 | **✗** | E1,E3 |
| 16 | **AI Agent invocation** | `goaa`: `v4_agents`(3) `models`(0) `goaa_agent_tokens`(6) | NO | Medium | C: ✗ / P: self / A: yes | NO | NO | N/A | NO | ✗（僅 `revoked_at` 欄，未用） | ✗ | **✗** | E1 |
| 17 | **Worker task payload** | router 記憶體 `task_pool`；`goaa.tasks`(21)；`/opt/goaa/logs/tasks/*.jsonl`；**外送**：`api.deepseek.com` | YES（可含情境） | High | C: ✗ / P: ✗ / A: 不透明 | NO | NO | **⚠ YES — 今日即已外送 DeepSeek** | NO | ✗ | ✗ | **✗** | E1,E3 |
| 18 | **Worker result** | `/task/complete` → `logs` 欄（worker 輸出全文）→ JSONL + `messages` | YES（可含） | Medium-High | C: ✗ / P: ✗ / A: 不透明 | NO | NO | ⚠ 同上（`exec_chat` 結果） | NO | ✗ | ✗ | **✗** | E3 |
| 19 | **Audit log** | `goaa.audit_log`(5，含 `ip_address`/`operator`/`details`) `tool_invocations`(21)；`goaa_platform.identity_events`(8) `agent_review_events`(12)；`goaa_order_events`(538) | YES（IP/行為者） | Medium | C: ✗ / P: ✗ / A: yes | NO | **NO** | **NO** | NO | ✗（僅 `identity_events`/`agent_review_events` 由 0003 觸發器 append-only） | N/A（本身就是） | △ | E1,E3 |
| 20 | **Router / runtime logs** | `/opt/goaa/logs/**/*.jsonl`（tasks/workers/revenue…）；`/var/log/goaa-platform/api-3103.log`（36,678 B）`worker-agent.log`；journald（4.0 GB 持久） | YES（可含） | Medium | C: ✗ / P: ✗ / A: yes | NO | NO | ⚠（`call_deepseek` 內容） | **✗ 無 logrotate、無 TTL** | ✗ | ✗ | **✗** | E1,E2,E3 |
| 21 | **Credential / bearer token** | `goaa.goaa_order_tokens`(**259 明文、0 撤銷**) `goaa_agent_tokens`(6 明文) `goaa_platform.business_tokens`(4 明文)；對照：`user_sessions.token_hash`、`email_verifications.token_hash`、`goaa_verify_codes.code_hash`（皆雜湊 ✓） | NO | **Critical** | —（不得有一般存取） | NO | **NO** | **NO** | N/A | △ 有 `revoked_at` 欄但 **259/259 未撤銷** | ✗ | ⚠ **commerce dump 內含明文 token** | E1,E3 |
| 22 | **Customer uploaded files** | `goaa_order_files`(15) `..._package_files`(29)：`original_filename`/`mime_type`/`storage_key`/`bucket` | YES | High | C: self / P: 該案 / A: yes | NO | **NO** | **NO** | NO | ✗ | △ | △ | E1 |
| 23 | **Public marketing content** | `www.goaa.ai`（Framer，687,067 B）、`planning.goaa.ai` 靜態資產 | NO | Low | 公開 | NO | NO | NO | N/A | N/A | ✗ | N/A | E2 |

---

## B. 必須回答：外部化（externalization）三問

### B1. 預設**禁止**離開 GOAA（`DENY by default`）
> 任何「外部 Skill / 外部 AI Agent / 第三方 SaaS」呼叫，以下資料**一律不得**作為 payload：

1. **Clerk 身份與會話**：#1（`user_identities`、`identity_events`、任何 Clerk subject/token）
2. **憑證類**：#21（order/agent/business token、session cookie）——**連 metadata 也從嚴**（長度與指紋可，值是機密）
3. **證件原文**：#4（`private-files/*.pdf`）——任何形式（base64、截圖、OCR 文本）皆禁
4. **金流識別碼**：#12（Connect account id、checkout session id、transfer id）——僅 Stripe 本身可收
5. **審計軌跡**：#19（`identity_events`／`audit_log`／`order_events`）——不得外送，只可內讀
6. **客戶原文**：#5 客戶側 chat 全文、#6 Matter `handoff_context`、#22 上傳檔——未經同意不得外送
7. **RAG 原 chunks**：#14（`content`）；**只可**外送其 embedding 向量或不可逆摘要，且需 Tao 決策

### B2. **需要用戶明示 consent**（per-case，可撤回、需留痕）
- #5 **客戶 chat → 外部 AI Agent**（例：Pipedream 技能鏈）：需「本次」同意 + 顯示將送往的 provider + 可撤回
- #6 **Matter / handoff context → 外部 Skill**：同上（高敏感）
- #7 **交付物與案件訊息 → 外部 Skill**：同上
- #13 **AI Memory → 雲端模型**：今日記憶存於本機 Ollama 語境；一旦改用雲端模型即需 consent
- #3 **license metadata → NIPR/ARELLO**：可，但僅「可驗證欄位」（姓名、證號、州），不得附帶案件內容

### B3. **可以 metadata-only**（無 PII、無正文、無識別碼）
- #8/#9/#11：`order_id`、`payment_type`、`status`、`amount_cents`、`currency`、時間戳
- #15：`skill_id`、`enabled`、`billing_mode`、`permission_level`、呼叫次數、耗時、成功/失敗計數
- #17/#18：worker 指標（CPU/RAM/磁碟）、`task_type`、`duration_ms`、`status`（**不含 prompt 與 result 正文**）
- #3：`license_type`、`license_states`、**查驗布林結果**（不含證號原文與文件）
- #14：`chunk_index`、`document_id`、**向量**、`text_hash`
- #20：request path、HTTP code、latency（不含 query 值）

> **降級不變式**：`consent` 不成立時，一律**退回 B3 的 metadata-only**，而非「拒絕服務」。理由是 G-3 §2 的 C2 gate 必須能在無客戶資料下驗收。

---

## C. 現行控制缺口（依嚴重度）

| 級別 | 缺口 | 證據 | 對應 G-3 里程碑 |
|---|---|---|---|
| **P0** | `goaa_platform`（#1/#2/#3/#4）**完全無備份**；identity 資料不可存活 | E1：無 dump、無 cron、`pg_restore` 不在 PATH | M0 |
| **P0** | #21 明文 bearer token 且 259/259 未撤銷，且**已進入 09-06 commerce dump** | E1 | M0/M2 |
| **P1** | 無任何 **retention** 定義（全 23 類皆 NO） | E1 | M1.5/M2 |
| **P1** | 無 **PII 脫敏**層：`f_lite_sanitize` 只遮 secret（PG/SSH/sudo/API key），**不遮 email/電話/地址** | E3 | M2 |
| **P1** | #17/#18 worker payload/result 經**未認證公網**路由器流動（見 G-4 §2） | E1/E3 | M0 |
| **P2** | #14 RAG 硬刪無 tombstone、無審計 | E3 | M2 |
| **P2** | #19 `audit_log` 僅 5 列（實質未用）；router 讀取無審計 | E1 | M1.5 |
| **P2** | #13 AI Memory 無刪除 API | E1 | M2 |
| — | ✓ **已達標**：#4 檔案實刪、#14 硬刪、`identity_events`/`agent_review_events` append-only、C2 `private-files` 檔名為 sha256（非原名） | E1/E3 | — |

---

*本檔為 G-4 §3 指定產物。主報告見同目錄 `G4-FINAL-DECISION-GATE.md`。*
