# 07 — C1 生產 release / 服務 / 資料庫盤點

- 日期：2026-09-13；**全程唯讀**（未改檔、未重啟、未 enable/disable、未寫 DB）。
- 宿主：`do-runtime-anchor`（`goaa-aika-cloud-1`、Ubuntu 24.04.4、公網 `134.199.227.⟨108⟩`、2 vCPU）。

## 1. 前端 release

| 項目 | 值 |
|---|---|
| `current` → | `/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` |
| `BUILD_ID` | `FW7iufKj5JrPAz9Kx2SkX` |
| release 樹 | **1,969 檔 / 28,138,994 bytes** |
| `releases/` 數量 | **22** |
| 回滾點（`/root/r5b4-rollback-point.txt`） | `/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc`（＝GitHub 上的 golden `76af718` ✓） |
| service | `goaa-web.service` → `127.0.0.1:3100`；MainPID `3135985`；`enabled` |

env：`/opt/goaa-frontend/env/web.env` = **481 bytes / sha16 `c72e86561eac7292` / 11 鍵 / 0640 root:goaa-web`**（只列鍵數，未印值）。

## 2. 後端 3103

| 項目 | 值 |
|---|---|
| 部署樹 | `/opt/goaa-platform/backend/`（**37 檔**，R4 已驗證逐檔 == 本機 git `dc64591b…`） |
| venv | `/opt/goaa-platform/venv/`（Python 3.12.3） |
| service | `goaa-platform-api-3103.service`；MainPID `3135920`；`enabled`；**`Restart=no`** ⚠️ |
| 監聽 | 僅 `127.0.0.1:3103` |
| 啟動 | `uvicorn app.main:app --host 127.0.0.1 --port 3103 --no-server-header` |
| env | `/opt/goaa-platform/env/api-3103.env` = **986 bytes / sha16 `711f5817b41fc31d` / 25 鍵 / 0600** |
| 日誌 | `/var/log/goaa-platform/api-3103.log`（169 行；`200`×97、`401`×48、`404`×3、`403`×1） |

備份（皆 root 唯讀）：`/root/web.env.bak.20260912T085918Z`(623 B)、`…T084443Z`(560 B)、`…T174904Z`(684 B / sha16 `254c0423f94fc587`)；`/root/api-3103.env.bak.20260912T075855Z`（舊 Dev 值）、`…T174904Z`(1189 B / sha16 `996c66636f925a16`)。

## 3. 其他 C1 服務（同機共存）

| unit | 埠 | 狀態 |
|---|---|---|
| `goaa-web` | `127.0.0.1:3100` | enabled + active（PID 3135985） |
| `goaa-router` | `0.0.0.0:8080` | active（PID 2994296）；來源 `/opt/goaa/router` |
| `cloudflared` | — | active（PID 2111569，全程未變） |
| `goaa-platform-api-3103` | `127.0.0.1:3103` | enabled + active（PID 3135920） |
| `goaa-worker-agent` | — | active |
| `openclaw` | `0.0.0.0:18789` | active |
| `goaa-model-router` | — | **disabled + inactive**（D0.4） |
| `ufw` | — | active / enabled |

監聽：`127.0.0.1:3100`、`127.0.0.1:3103`、`0.0.0.0:18789`、`0.0.0.0:8080`、`0.0.0.0:5432`（docker-proxy，D0.2 後外部不可達）。

## 4. 資料庫

### 4.1 新庫 `goaa_platform`（Clerk 棧用）

- **15 表 / 3 函式 / 3 觸發器 / 1 sequence / 41 index**；owner 全 `goaa_c2_migrate`；`schema_migrations` **6 筆**（0001–0006）。
- 資料：`users`=2、`user_identities`=2、`identity_events`=**6**、`user_roles`=3 列、`agent_applications`=1（**已 `approved`**）、`agent_licenses`=1、`agent_license_documents`=1、`user_sessions`=0、`agent_review_events`=12。
- `user_roles` 三列：`c*****a@gmail.com`=user、`t*****x@gmail.com`=user ＋ **admin**（R7-G1 寫入、`granted_by=null`）＋ `agent`（系統自動、`granted_by`=本人 uuid）。

### 4.2 舊庫 `goaa`（黃金 commerce/dispatch）

**45 張表**。與 commerce 有關：`goaa_order_payments`(**41**)、`goaa_order_settlements`(**14**)、`goaa_order_invoices`(**7**)、`goaa_order_estimates`(**19**)、`goaa_order_service_orders`(**36**)、`goaa_order_opportunities`(10)、`goaa_order_tokens`(259)、`goaa_order_agent_subscriptions`(**0**)、`goaa_order_users`(72)、`goaa_order_deliveries/packages/files`、`goaa_order_messages`、`goaa_order_events`(538)。
Agent/RAG：`goaa_agent_knowledge_docs`(**2**)、`goaa_agent_knowledge_chunks`(105)、`goaa_agent_skills`(**2**)、`goaa_agent_profiles/leads/preferences/tokens`、`agents`(**0**)。
Runtime：`nodes`(1)、`tasks`(21)、`tool_invocations`(21)、`tools`、`models`、`credits`(4)、`credit_transactions`(**0**)、`audit_log`(5)、`goaa_planning_sessions`(117)。

> 註：`goaa_platform` 與 `goaa` 是**兩個獨立庫**；新 Clerk 棧只碰前者。

## 5. 未動聲明

本輪對 C1 未執行任何寫入指令；唯一讀取動作為 `psql -c "select …"` 與 `systemctl`/`ss`/`sha256sum` 類查詢。
