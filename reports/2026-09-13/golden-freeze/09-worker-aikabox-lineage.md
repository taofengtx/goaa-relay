# 09 — Worker / Aika-Box 血緣

- 日期：2026-09-13；唯讀。

## 1. Aika-Box 本機主控台（唯一「box」實體）

| 項目 | 值 |
|---|---|
| 源碼 | `/home/aika/Projects/goaa-ai-main/local-console/`（**在 GitHub 上**） |
| 樹摘要 | `faa9f6ba4603ef9b`（`origin/main`、`02a17ff`、`40c8546`、`dc64591`、`76af718` **五個 ref 完全一致**，19 檔） |
| 主要檔 | `main.py`（138,956 B）、`task_gateway.py`（30,971 B）、`task_envelope.py`、`intent_detector.py`、`auth.py`、`registry/agents.json`、`local_user.db`（12,288 B） |
| 進程 | `uvicorn main:app`（PID `6113`，`/opt/goaa/venv`），已跑 **33 天 23 小時** |
| 監聽 | `127.0.0.1:5188` ＋ **tailnet `100.114.37.90:5188`** |
| 工作樹狀態 | tracked 檔乾淨；僅 `__pycache__` 未追蹤 |

⚠️ 因進程是在 8/10 前後啟動、`main.py` 最後修改 8/2 ⇒ **實際在跑的是比 HEAD 更舊的載入版本**；重啟會載入新版，屬變更，本輪未做。

## 2. Worker 控制面（C1 `api.goaa.ai`）

`goaa-router` 來源 = `/opt/goaa/router`（git `1d67bd6`；`api.py` 1,093 行 + `db.py` 449 行）。
端點（部分）：`/worker/heartbeat`、`/tasks/next/{worker_id}`、`/task/complete`、`/tasks/dispatch`、`/tasks/queue`、`/task/approve`、`/workers/status`、`/workers/register`、`/workers/metrics`、`/revenue/status`、`/profit/status`、`/cost/status`、`/models/status`、`/sessions/*`、`/chat`、`/route`。
⇒ 它是**派遣/節點控制面**，不是 commerce API（見 08 報告）。

## 3. Worker 程式

- `/opt/goaa/workers/agent.py`（**5,918 B / sha16 `8b1ce13e532fd8e4`**）
- **L9：`ROUTER_URL = os.getenv("ROUTER_API", …)`** ⇒ 讀的是 `ROUTER_API`，不是 `ROUTER_URL`（D0.3B 關鍵陷阱）。
- 端點：`/worker/heartbeat`(L23)、`/tasks/next/<id>`(L32)、`/task/complete`(L101)。
- `/opt/goaa/workers/corpus_all.jsonl`（577,030 B）＝ worker 端語料。

## 4. Worker 機隊（6 台；各 ~5 秒輪詢）

| worker | 網段 | unit | WORKER_ID | ROUTER 變數 | 可達 |
|---|---|---|---|---|---|
| do-cloud-1 | `127.0.0.⟨1⟩` | `goaa-worker-agent` | do-cloud-1 | `ROUTER_API=127.0.0.⟨1⟩:8080` | 本機 |
| do-cloud-2（C2） | `143.198.224.⟨71⟩` | `goaa-worker-agent.service` | do-cloud-2 | `ROUTER_API=http://134.199.227.⟨108⟩:8080` | ✅ ssh |
| do-cloud-3（C3） | `64.23.166.⟨121⟩` | 同上 | do-cloud-3 | 同上 | ✅ ssh |
| aika-core-01 | `165.162.8.⟨177⟩` | `goaa-worker-agent.service` | aika-core-01 | **只有 `ROUTER_URL=`（無效！）** | 本機 |
| aika-1 | `98.191.202.⟨15⟩` | 未盤點 | aika-1 | 未盤點 | ❌ 憑據不可達 |
| aika-2 | `165.162.8.⟨177⟩` | `goaa-worker-agent`（User=`tao`） | aika-2 | `ROUTER_API=http://134.199.227.⟨108⟩:8080` | ✅ ssh `tao@` |

## 5. 能力指紋（`git grep -l` 檔數；`origin/main` vs 六月血緣）

| 樣式 | `origin/main`（2026-08-25） | `52694be`（六月 runtime 三支） |
|---|---|---|
| worker / 主控台 | 42 | 25 |
| dispatch | 74 | 62 |
| capability_grant | **15** | **0** |
| authorization_kernel | 45 | 27 |
| skill registry | 34 | 32 |
| baton | **21** | **0** |
| model_router | 20 | 18 |
| rag | 53 | 40 |

⇒ **`origin/main` 才是 worker 血緣最完整的一份**（capability_grant / baton 皆已併入）；六月的 `52694be` 系列（controlled-shell / orchestrator / evidence-store）落後 origin/main 80 個 commit、從未合併。

## 6. 文檔血緣（皆在 GitHub）

`docs/runtime/GOAA_PACKAGE{2,3}_BATON12_*_ARCHIVE_20260623.md`、`docs/runtime/...dispatch...`、`docs/nodes/node-capability-system.md`、`docs/roadmap/V4_1_Worker_PLAN.md`、`docs/roadmap/V5_0_WORKER_RUNTIME_MASTER_PLAN.md`、`docs/bootstrap/worker-os-bootstrap.md`、`docs/architecture/GOAA_SHELL_CAPABILITY_V0_DESIGN.md`、`docs/ip/PATENT_CONTINUATION_EVIDENCE_LEDGER.md`。
另有 `services/rag/workers/authorization_kernel/{__init__,action_request,authorization_evidence,authorization_snapshot}.py` ✓。

## 7. 判讀

- **Worker 面是「已在 GitHub、且可用」的一份**（與 Clerk/agent-loop 面完全相反）。
- Aika-Box 主控台源碼也在 GitHub；但**跑的是舊載入版本**，且主控台與 C1 `goaa-router` 是兩套不同的東西（5188 本機 vs 8080 雲端）。
- 唯一明確失效：**aika-core-01 的 `ROUTER_URL`（應為 `ROUTER_API`）** ⇒ 該節點目前不會被派遣（D0.3B 階段二待令處理）。
