# GOAA Shell Capability V0 — Design Specification

> **版本**: V0.3 (Design Spec — 刀 2A 設計修訂版)
> **階段**: 設計規範（**不寫代碼、不部署、不重啟、不改 systemd、不碰 `/etc/goaa`、不讀 secret**）
> **當前時間**: 2026-06-15 PT
> **託管**: `docs/architecture/GOAA_SHELL_CAPABILITY_V0_DESIGN.md`
> **審查修訂 v0.1**: 2026-06-14 — 修復 3 項 BLOCKING（缺 blocklist/缺狀態機/缺 approved requeue），白名單縮減至 10 命令，V0 刀 1 禁止所有 pipe/redirect/shell=True，輸出/審計 schema 擴充
> **審查修訂 v0.2**: 2026-06-14 — 拆分實施階段：刀 1 嚴格限定 Schema + Validator + Policy + 拒絕測試（無真實 subprocess 執行）；刀 2 才允許隔離的只讀 Executor
> **審查修訂 v0.3**: 2026-06-15 — Policy code alignment: 修正 §6.2 模板 ID/timeout/limit 與已發布 `shell_policy.py` 一致；新增 §0 策略真相層級；拆分刀 2A/2B；定稿 MINIMAL_ENV；修正路徑檢查（`Path.is_relative_to`）；新增 `verify_execution_plan`；定稿 ResourcePolicy
> **狀態標註**:
>   - `EXISTING` — 代碼已存在、生產已驗證
>   - `PARTIAL` — 代碼部分存在但缺口明確
>   - `DESIGN_ONLY` — 文檔級概念，無代碼實作
>   - `PROPOSED` — 本文件新創提案（V0 待實作）
>   - `OUT_OF_SCOPE` — V0 不涵蓋
>   - `LOCKED` — 已發布代碼為權威，設計文檔以之為基線

---

## 0. 策略真相層級（`PROPOSED`）

### 0.1 Policy Code Truth

刀 1 已發布代碼為當前 **Policy Truth**，刀 2 Executor 必須與其精確一致：

| 檔案 | 角色 | 狀態 |
|---|---|---|
| `services/rag/workers/shell_schema.py` | 資料結構（`ShellTaskRequest`, `ShellValidationResult`, `ValidationStatus`, `GitRevParseMode`, `ApprovedUnit`） | `EXISTING LOCKED` |
| `services/rag/workers/shell_policy.py` | 不可變策略定義（10 模板白名單、RESOURCE_MAP、BLOCK 清單、TEMPLATE_POLICY） | `EXISTING LOCKED` |
| `services/rag/workers/shell_validator.py` | 純驗證邏輯（template/resource/path/block token 校驗、metadata 保留鍵拒絕） | `EXISTING LOCKED` |

### 0.2 衝突處理規則

如本設計文檔與已發布 Policy 代碼衝突，**以已發布 Policy 代碼為當前基線**。本文檔修訂以消除所有衝突為目標：

| 衝突項目 | 設計文檔（舊） | Policy 代碼（當前真相） | 修訂動作 |
|---|---|---|---|
| df template_id | `df_h` | `df_summary` | 文檔統一為 `df_summary` |
| git_rev_parse 模板拆分 | `git_rev_parse_head` / `git_rev_parse_branch` 兩個 template_id | 單一 `git_rev_parse` + `GitRevParseMode` 枚舉（`HEAD_SHORT`/`BRANCH_NAME`） | 文檔統一為單一模板 + 枚舉模式 |
| timeout 值 (LOW 模板) | 3s | 5s（`TEMPLATE_POLICY["pwd"][0]` = 5） | 文檔全部修正為 5s |
| timeout 值 (git/systemctl) | 5s | 10s（`TEMPLATE_POLICY["git_rev_parse"][0]` = 10） | 文檔全部修正為 10s |
| stdout/stderr limit | 各模板獨立值（4KB/1KB 等） | 全部統一 `32768/16384`（`TEMPLATE_POLICY`） | 文檔統一為全域值 |
| risk_level | 全部 LOW | LOW（pwd 等 7 模板）/ medium（git_status_short, git_rev_parse, systemctl_is_active） | 文檔修正為對應值 |
| requires_approval | 全部「審批: 否」 | `True`（git_status_short, git_rev_parse, systemctl_is_active） | 文檔修正為對應值 |
| resource_required | git_status/repo_main | `needs_resource=True`（git_status_short, git_rev_parse, systemctl_is_active） | 文檔修正為對應值 |
| MINIMAL_ENV HOME | `/home/aika` | 刀 1 未實作 executor | 刀 2A 定稿為 `/nonexistent` |
| MINIMAL_ENV PATH | `/usr/bin:/bin:/usr/local/bin` | 刀 1 未實作 executor | 刀 2A 定稿為 `/usr/bin:/bin` |

### 0.3 刀 2A / 2B 拆分

| 刀 | 範圍 | 執行方式 | 模板覆蓋 |
|---|---|---|---|
| 刀 2A | 隔離只讀 Executor（初始發布） | `subprocess.run(argv, shell=False)` | 8 template_id / 9 argv 變體（暫緩 df_summary, git_status_short） |
| 刀 2B | 有界流 Executor（後續擴充） | `Popen` + 有界 pipe 讀取 + process-group killpg | 追加 df_summary, git_status_short→全部 10 template_id |

---

## 1. 目標與非目標

### 目標 (V0 範圍)

1. 定義一個**可安全執行 shell 命令**的 Worker 執行引擎，讓 AI（Aika）在 allowlist + risk engine + approval gate + redaction gate 內執行本地命令，**不再繞過安全閘直接 `subprocess`**。
2. **繼承 F-lite 安全架構**（allowlist / risk / approval / redaction / audit），可被 Router 感知、可被 5188 Console 審批。
3. 作為 `goaa_task_runner` 的**通用 shell handler**（`exec_shell`），與現有 embed/topk 專用 handler 並存於 `TASK_HANDLERS` dict。
4. 補齊 F-lite 缺口中的「shell executor + command allowlist + path allowlist + timeout + truncation + audit」。

### 非目標 (V0 不包含)

- **任意 shell 執行**：V0 不做 `subprocess(shell=True)`。所有命令通過 `subprocess.run(argv, shell=False)` 執行，argv 由 allowlist 模板產生。
- **管道、重定向、命令替換、環境變數展開**：V0 刀 1 全部禁止。不允許 `|`, `>`, `>>`, `<`, `$()`, `` ` ``, `&&`, `||`, `;`, 換行拼接多命令。
- **sudo / root / doas 操作**：V0 永遠禁止。
- **網路命令**：V0 刀 1 禁止 `curl`, `wget`, `ping`, `nc`, `ssh`, `scp`。
- **跨節點執行**：V0 只做本地 (aika-core-01) shell 執行。跨節點 (`execution_target=cloud`) 待後續。
- **系統包安裝**：V0 禁止 `apt`, `pip`, `npm`, `gem`。
- **生產部署 / git push / systemctl start/stop/restart**：V0 禁止所有非唯讀操作。
- **secret 讀取**：V0 禁止讀取 `/etc/goaa/*`, `~/.ssh/*`, `~/.config/goaa-email/*`, `/proc/*/environ`, 任何 `*.env` 或 `secrets*` 檔案。
- **rollback 機制**：V0 不實現 rollback（shell 為一次性執行，非檔案寫入操作）。
- **資源隔離 (cgroup/容器化)**：V0 僅 `ulimit` 軟限制，不做完整容器化。
- **Provider Review Hold**：V0 複用 Router 現有 `awaiting_approval` 通路，不引入獨立的 provider_review_node。
- **OpenClaw 整合**：V0 不實作 OpenClaw。§15 僅保留契約草案。
- **QwenPaw 取代**：V0 文件不得宣稱已取代 QwenPaw。QwenPaw 並排驗收見 §17。
- **刀 1 真實執行**：刀 1（§20）嚴格限定 Schema + Validator + Policy + 拒絕測試，不產生任何真實系統命令。刀 2 才允許 `subprocess.run()`，且需 Tao 單獨批准。

---

## 2. 三端真相對齊

### 2.1 Git Truth (dev repo `main` @ `a157a7b`)

| 資產 | 路徑 | 行數 | 狀態 |
|---|---|---|---|
| Local Task Runner | `services/rag/workers/task_runner.py` | 199 | `EXISTING` |
| Redaction pipeline | `services/rag/f_lite_redact.py` | 75 | `EXISTING` |
| Base redact (5 patterns) | `services/rag/extract_qwenpaw.py` `redact()` | — | `EXISTING` |
| Router api.py (dev copy) | `infra/router/api.py` | ~660 | `EXISTING` |
| F-lite design spec | `docs/architecture/GOAA_LOCAL_TASK_RUNNER_F_LITE.md` | 268 | `EXISTING` |
| Workflow Graph spec | `docs/architecture/GOAA_WORKFLOW_GRAPH_SPEC.md` | 320 | `EXISTING` (design only) |
| Runtime OS blueprint | `docs/architecture/RUNTIME_OS_STRATEGIC_BLUEPRINT_V1.md` | 323 | `EXISTING` |
| V0 設計規範 (v0.3) | `docs/architecture/GOAA_SHELL_CAPABILITY_V0_DESIGN.md` | 1291→1400+ | `PROPOSED` |
| Shell Schema | `services/rag/workers/shell_schema.py` | 72 | `EXISTING LOCKED` |
| Shell Policy | `services/rag/workers/shell_policy.py` | 147 | `EXISTING LOCKED` |
| Shell Validator | `services/rag/workers/shell_validator.py` | 327 | `EXISTING LOCKED` |
| Shell Policy Tests | `services/rag/workers/tests/test_shell_policy.py` | — | `EXISTING LOCKED` |
| Shell Validator Tests | `services/rag/workers/tests/test_shell_validator.py` | — | `EXISTING LOCKED` |

**Shell executor**: 在 dev repo 任何 `.py` 文件中，`grep -rn "subprocess\|os\.system\|Popen\|exec_shell\|execute_command" services/rag/workers/ local-console/` 返回 **零匹配**。

### 2.2 Runtime Truth (DO `/opt/goaa` @ `1d67bd6`)

| 項目 | 狀態 | 證據 |
|---|---|---|
| `goaa-router` | active ✅ | `systemctl is-active` |
| `api.py` 行數 | ~660 | `wc -l` |
| approve endpoint | `EXISTING` | `UPDATE tasks SET status='approved'` (L495) |
| reject endpoint | **`NOT_FOUND`** | 僅 L478 註解「本刀不做」 |
| shell executor | **`NOT_FOUND`** | `grep` 零匹配 |
| subprocess/Popen | **`NOT_FOUND`** | `grep` 零匹配 |
| awaiting_approval recovery | `EXISTING` (0930806) | `rebuild_loads_awaiting_approval_tasks()` 存在於 DO api.py |
| tool_invocations | **`DESIGN_ONLY`** | 僅 L546 註解 hook |
| dispatcher | running | `tasks_pool=0, pending=0, running=0` |

### 2.3 Documentation Truth

| 文檔 | 對 Shell Capability 的定義 | 狀態 |
|---|---|---|
| F-lite v0.3 (§0) | 「讓 AI 生成可審計的 execution plan，在 allowlist + risk + approval 內執行」 | `EXISTING` |
| F-lite v0.3 (§4) | MVP Allowlist 定義：5 種任務類型，禁止 arbitrary shell | `EXISTING` |
| F-lite v0.3 (§16) | 必新建列表：approve/reject 端點、approval 持久化、5188 審批 UI | `EXISTING` (缺口) |
| Runtime OS Blueprint (§三) | 5 階段任務生命週期（含「exec_shell(git log)」為願景範例，非生產代碼） | `DESIGN_ONLY` |
| Workflow Graph (§4.1) | `goaa_task_runner` adapter = F-lite executor，status pending | `DESIGN_ONLY` |

---

## 3. 現有能力與缺口摘要

### EXISTING（可直接複用）

| 能力 | 代碼位置 | V0 複用方式 |
|---|---|---|
| 任務調度入口 | `task_runner.py` `main()` → `run_task()` → `TASK_HANDLERS` dispatch | 擴充 `TASK_HANDLERS` 加入 `exec_shell` |
| 標準 task_result 格式 | `task_runner.py` `run_task()` 輸出 dict (status/duration/error) | 完全複用 |
| Secret redaction (5 base patterns) | `extract_qwenpaw.py` `redact()` | `import` 複用 |
| F-lite redaction (3 patterns: PG/SSH/sudo) | `services/rag/f_lite_redact.py` | `import` + `sanitize_with_count()` |
| Router risk engine | `api.py` `TASK_REVENUE` dict (risk 1-4) + `select_model()` + dispatcher | 由 Router 決定 risk level |
| awaiting_approval gate | `api.py` P0/P1+risk≥4 → `status="awaiting_approval"` | 高風險 shell 直接進此通路 |
| approve endpoint | `api.py` `POST /task/approve` | 擴充：approve 同時推進至 queued |
| awaiting_approval recovery (restart) | `api.py` `rebuild_loads_awaiting_approval_tasks()` (0930806) | 引用現有機制 |
| Audit INSERT on approve | `api.py` approve handler → `audit_log` INSERT | 複用 |
| Task 日誌與結果目錄 | `/opt/goaa/tasks/` / `/opt/goaa/task_results/` / `/opt/goaa/logs/` | 完全複用 |

### PARTIAL（部分存在，需補全）

| 能力 | 現有 | 缺口 |
|---|---|---|
| timeout | `task_runner.py` timeout=120 (HTTP 層) | 無 shell-level timeout（`subprocess.run(timeout=N)` 未實作） |
| output truncation | `text_redacted` 用於 RAG 輸出 | 無 stdout/stderr byte-level truncation |
| audit trail | approve endpoint 有 `audit_log` INSERT | 無 shell 執行前後通用 audit trail |

### DESIGN_ONLY（有文檔，無代碼）

| 能力 | 文檔出處 |
|---|---|
| Provider Review Hold | `Workflow Graph §5`, `F-lite §9` |
| Workflow Graph (12 Node Types) | `GOAA_WORKFLOW_GRAPH_SPEC.md` |
| Cloud/local/auto routing | `HANDOFF.md`, `Runtime OS §4.3` |
| tool_invocations dual-write | `api.py` L546 註解, `Roadmap v1.2 P1.2.1` |

### NOT_FOUND（V0 須新建）

| 能力 | V0 設計章節 |
|---|---|
| Shell execution engine (subprocess.run, shell=False) | §5, §16 (§20 刀 2A) |
| 10-command allowlist (8 template_id / 9 argv 變體 for 刀 2A) | §6 |
| Named resource path resolution | §7 |
| BLOCK path enforcement | §7 |
| Executor Policy 獨立覆核 (verify_execution_plan) | §20 刀 2A |
| Template-level parameter validation | §8 |
| reject endpoint (POST /task/reject) | §13 |
| approved→queued 自動推進 (dispatcher) | §13 |
| Shell 執行前後 audit_log 雙寫 | §14 |
| FastAPI → OpenClaw contract draft | §15 |

---

## 4. Router / Worker / Console / OpenClaw 責任邊界

```
OpenClaw (DO :18789)
  └─ Public API Gateway (對外開發者 / Framer 官網)
  └─ V0: OUT_OF_SCOPE。§15 僅保留未來契約草案
  └─ V0 不參與任何狀態流轉

Router (DO :8080, goaa-router)
  └─ 任務狀態唯一真相源（所有狀態變更由 Router 控制）
  └─ 風險分級 (TASK_REVENUE → risk 1-4)
  └─ 調度決策（risk≤3: direct queue / risk≥4: awaiting_approval）
  └─ 審批端點: POST /task/approve (EXISTING, 擴充), POST /task/reject (PROPOSED)
  └─ 審計寫入 (audit_log TABLE)
  └─ Dispatcher: 只提取 queued 任務, 並原子搶佔推進至 running
  └─ V0 新增: approve 後在同一事務推進至 queued; reject 端點

Worker (aika-core-01, task_runner.py + shell_executor.py NEW)
  └─ 只執行 queued 狀態任務（由 Dispatcher 分配）
  └─ 不設定 task 狀態（Router 為真相源）
  └─ 本地命令執行 (subprocess.run(argv, shell=False))
  └─ 10 命令 allowlist + named resource + template validation
  └─ timeout / truncation / ulimit
  └─ 輸出經 redaction pipeline 後回傳 (複用 EXISTING f_lite_redact)
  └─ 現有 embed/topk handler 維持不變

Console (aika-core-01 :5188)
  └─ 僅做 proxy / UI（審批狀態真相源在 Router）
  └─ 審批 UI: 待審批列表 + approve/reject 按鈕
  └─ 執行歷史查看
  └─ Console 不自存審批狀態
  └─ V0 缺口: 5188 審批 UI 未實作, 須新建
```

**V0 執行流程**:
```
User task → Router dispatch
  → [risk≤3 & allowlist] → Router sets queued → Worker poll → execute → return
  → [risk≥4] → Router sets awaiting_approval
       → Console 審批 → POST /task/approve
       → Router: approve + queued (同一事務)
       → Worker poll → execute → return
```

---

## 5. ShellTaskRequest / ShellTaskResult Schema

### 5.1 ShellTaskRequest（`PROPOSED`，由 Router dispatch 下發）

```json
{
  "task_id": "uuid",
  "task_type": "exec_shell",
  "template_id": "string",            // allowlist 模板 ID (e.g. "git_status_short", "df_summary")
  "resolved_argv": ["string", ...],    // 已解析的 argv (allowlist 模板產生, 非用戶輸入)
  "resource_name": "string|null",      // 命名資源 (e.g. "repo_main"), Worker 解析為真實路徑
  "env_overrides": {},                 // V0: 始終 {}，不允許環境變數覆蓋
  "timeout_s": 10,                     // V0 刀 1: max 10s (按模板固定)
  "risk_level": 1,                     // 由 Router 設定
  "priority": 1,
  "requested_by": "string",
  "approval_id": "uuid|null"
}
```

**安全邊界**:
- `template_id` 是 allowlist 鍵名, `resolved_argv` 由模板產生, 非用戶原始輸入
- `resource_name` 必須來自配置白名單, Worker 用 `realpath` 解析
- `env_overrides` V0 始終為空 dict (禁止 `PGPASSWORD=xxx cmd`)
- `timeout_s` V0 刀 1 最高 10s, 由模板固定, 不接受用戶指定
- Worker 只看到 argv, 不看到原始 `command` / `args`

### 5.2 ShellTaskResult（`PROPOSED`）

```json
{
  "task_id": "uuid",
  "tool_name": "exec_shell",
  "template_id": "string",
  "resolved_argv_hash": "string",
  "resource_name": "string",
  "cwd_hash": "string",
  "status": "succeeded | failed | timed_out | blocked | cancelled",
  "exit_code": 0,
  "stdout_redacted": "string",          // 經 f_lite_sanitize() 後, max 32KB
  "stderr_redacted": "string",          // 經 f_lite_sanitize() 後, max 16KB
  "stdout_bytes": 1234,
  "stderr_bytes": 0,
  "stdout_truncated": false,
  "stderr_truncated": false,
  "timed_out": false,
  "redaction_hits": 0,                  // sanitize_with_count() 返回
  "duration_ms": 1234,
  "started_at": "iso_timestamp",
  "finished_at": "iso_timestamp",
  "worker_id": "aika-core-01",
  "policy_version": "v0.1",
  "approval_id": "uuid|null",
  "error": "string|null"
}
```

**禁止記錄**:
- 完整環境變數
- Token / 密碼 / 私鑰 / secret 檔案內容
- 未脫敏原始 stdout/stderr
- 調度元資料 (`env_overrides`, `priority`, `requested_by` 除 hash 外)

---

## 6. 命令模板白名單（`EXISTING LOCKED` — V0 刀 1 最小集，與 `shell_policy.py` `TEMPLATE_POLICY` 一致）

### 6.1 設計原則

- 每條 allowlist 條目 = 固定 `argv` 模板, 非原始 shell 語句
- V0 刀 1 **不使用 `shell=True`**
- 執行方式: `subprocess.run(argv, shell=False, timeout=N, env=MINIMAL_ENV, ...)`
- V0 刀 1 **禁止**：管道 `|`、重定向 `>` `>>` `<`、命令替換 `$()` `` ` ``、邏輯運算符 `&&` `||` `;`、換行拼接多命令、環境變數展開、通配符越界、路徑穿越 `..`、符號鏈接逃逸
- 所有命令 timeout ≤ 10s（按模板固定）
- stdout 上限 32768 bytes, stderr 上限 16384 bytes（全域統一，按模板固定）

### 6.2 V0 白名單表（與 `shell_policy.py` `TEMPLATE_POLICY` 完全一致）

```
# ── Policy 元資料 ──
POLICY_VERSION: str = "shell-v0.1-knife1"
TIMEUNIT: seconds
STDOUT_LIMIT: 32768 bytes (全域)
STDERR_LIMIT: 16384 bytes (全域)
```

| # | template_id | argv | resource | timeout | risk | needs_approval | needs_resource | 刀 2A/B |
|---|---|---|---|---|---|---|---|---|
| 1 | `pwd` | `["pwd"]` | 不需要 | **5s** | low | false | false | **2A** |
| 2 | `whoami` | `["whoami"]` | 不需要 | **5s** | low | false | false | **2A** |
| 3 | `hostname` | `["hostname"]` | 不需要 | **5s** | low | false | false | **2A** |
| 4 | `date_iso` | `["date", "--iso-8601=seconds"]` | 不需要 | **5s** | low | false | false | **2A** |
| 5 | `uptime_pretty` | `["uptime", "-p"]` | 不需要 | **5s** | low | false | false | **2A** |
| 6 | `free_human` | `["free", "-h"]` | 不需要 | **5s** | low | false | false | **2A** |
| 7 | `git_rev_parse` | `["git", "-C", "<resource>", "rev-parse", "--short", "HEAD"]` / `["git", "-C", "<resource>", "rev-parse", "--abbrev-ref", "HEAD"]` | repo_main | **10s** | **medium** | **true** | **true** | **2A** |
| 8 | `systemctl_is_active` | `["systemctl", "is-active", "<unit>"]` | **runtime_local** (用途見 §7) | **10s** | **medium** | **true** | **true** | **2A** |
| 9 | `df_summary` | `["df", "-h", "--output=source,size,used,avail,pcent,target"]` | 不需要 | **5s** | low | false | false | **2B** |
| 10 | `git_status_short` | `["git", "-C", "<resource>", "status", "--short"]` | repo_main | **10s** | **medium** | **true** | **true** | **2B** |

**Key alignments**:
- **template_id**: `df_h` → `df_summary`（已修正）；`git_rev_parse_head`/`git_rev_parse_branch` → 單一 `git_rev_parse` + `GitRevParseMode` 枚舉（`HEAD_SHORT`/`BRANCH_NAME`）（已修正）
- **timeout**: 所有 LOW 模板統一 **5s**（非 3s）；所有 medium 模板統一 **10s**（非 5s）
- **stdout/stderr limit**: 全部統一 **32768/16384**（非各模板獨立值）
- **risk_level**: git/systemctl 為 **medium**（非 LOW）
- **needs_approval**: git/systemctl 為 **true**（非「審批: 否」）
- **needs_resource**: git_status_short, git_rev_parse, systemctl_is_active 需要命名資源

#### 6.2.1 `git_rev_parse` 枚舉模式

`git_rev_parse` 使用單一 template_id 配合 `GitRevParseMode` 枚舉：

```python
class GitRevParseMode(enum.Enum):
    HEAD_SHORT = "HEAD_SHORT"           # → argv: ["git", "-C", <resource>, "rev-parse", "--short", "HEAD"]
    BRANCH_NAME = "BRANCH_NAME"         # → argv: ["git", "-C", <resource>, "rev-parse", "--abbrev-ref", "HEAD"]
```

**9 個固定 argv 變體**：8 個 template_id 中，`git_rev_parse` 有 2 個固定變體（`HEAD_SHORT` / `BRANCH_NAME`），其餘各 1 個，總計 **9 個固定 argv 變體**。

#### 6.2.2 `systemctl_is_active` 枚舉單位

`systemctl_is_active` 使用單一 template_id 配合 `ApprovedUnit` 枚舉：

```python
class ApprovedUnit(enum.Enum):
    GOAA_LOCAL_CONSOLE = "goaa-local-console"
    GOAA_WORKER_AGENT = "goaa-worker-agent"
    GOAA_TELEMETRY_WRITER = "goaa-telemetry-writer"
    OLLAMA = "ollama"
    GOAA_ROUTER = "goaa-router"
```

`systemctl_is_active` 當前 Policy 標記為 `needs_resource=True`。其 resource 參數 `runtime_local` 用於 identifying 本機 runtime 環境上下文（非執行路徑）；實際 cwd 由 ResourcePolicy 決定（見 §7）。不得在 Knife 2A 中私自改變 Policy。**Knife 2A Executor 必須忠實執行當前 Policy 定義，包括 `systemctl_is_active` 需要 `resource_name` 的約束。**

#### 6.2.3 刀 2A / 2B 拆分明細

**刀 2A**（初始發布）：8 個 template_id / 9 個 argv 變體
```
pwd, whoami, hostname, date_iso, uptime_pretty, free_human, git_rev_parse (2), systemctl_is_active
```

**刀 2B**（後續擴充）：追加 2 個 template_id
```
df_summary, git_status_short
```
刀 2B 才允許 `Popen` + 有界 pipe 讀取 + process-group killpg（見 §20 刀 2B）。

### 6.3 硬阻斷清單（V0 永遠拒絕，不論是否在 allowlist 外）

```
# 任意 shell 執行器
bash -c, sh -c, dash -c, zsh -c, fish -c
eval, exec, source, .

# 權限提升
sudo, su, doas, pkexec, run0

# 環境變數洩漏
env, printenv, declare, export, set (without args), compgen

# 網路命令
curl, wget, ping, nc, netcat, ssh, scp, rsync, telnet
nmap, masscan, tcpdump, socat, mtr, traceroute, dig, nslookup
ftp, sftp, wget2, aria2c

# 代碼執行器 (interpreters with -c flag)
python -c, python3 -c, perl -e, ruby -e, node -e, php -r
lua -e, R -e, tclsh, wish, lua, groovy -e

# 解碼與加密
base64 -d, base32 -d, openssl enc (decrypt), gpg -d
xxd -r, hexdump -C (raw)

# 系統變更
sudo, su, doas (重複強調)
chown, chmod, chattr, mount, umount
rm (except controlled paths in later phases)
mv, cp, dd, mkfs, fdisk, parted, cryptsetup, lvm
iptables, ufw, nft
systemctl start|stop|restart|enable|disable|daemon-reload
journalctl (V0 禁止 — 日誌讀取非刀 1 範圍)

# 套件管理
apt, apt-get, dpkg, snap
pip, pip3, npm, yarn, gem, cargo
brew, port, pacman, dnf, yum, zypper

# Git 寫操作
git push, git commit, git checkout, git merge, git rebase
git reset, git branch -d, git tag, git revert

# Docker / 容器化
docker, podman, containerd, nerdctl, ctr

# 檔案銷毀
shred, wipe, secure-delete, sfill, smem
```

---

## 7. 路徑規則（`PROPOSED` — 刀 2A 定稿）

### 7.1 ResourcePolicy 設計

刀 2 不開放用戶指定路徑。所有路徑通過配置中的命名資源解析。每個資源有獨立的安全策略：

```python
@dataclass(frozen=True)
class ResourcePolicy:
    canonical_path: str
    allowed_owner_names: FrozenSet[str]
    allowed_prefix: Path
    must_be_directory: bool = True
    reject_world_writable: bool = True
    reject_blocked_paths: bool = True

RESOURCE_POLICIES: Dict[str, ResourcePolicy] = {
    "repo_main": ResourcePolicy(
        canonical_path="/home/aika/Projects/goaa-ai-main",
        allowed_owner_names=frozenset({"aika"}),
        allowed_prefix=Path("/home/aika/"),
        must_be_directory=True,
        reject_world_writable=True,
    ),
    "runtime_local": ResourcePolicy(
        canonical_path="/opt/goaa/repo",
        allowed_owner_names=frozenset({"root", "aika"}),
        allowed_prefix=Path("/opt/goaa/"),
        must_be_directory=True,
        reject_world_writable=True,
    ),
}
```

注意：「真實 owner」需在實現前做 L1 只讀現場核驗，未核驗前不得硬編碼 UID。

### 7.2 路徑檢查流程

```python
def resolve_and_verify_resource(resource_name: str) -> Path:
    policy = RESOURCE_POLICIES.get(resource_name)
    if not policy:
        raise PathRejected(f"unknown resource: {resource_name}")

    # 1. os.path.realpath 解析（防 symlink 繞過）
    p = Path(policy.canonical_path).resolve(strict=True)

    # 2. 前綴校驗（使用 Path.is_relative_to，Python 3.9+）
    try:
        is_safe = p.is_relative_to(policy.allowed_prefix)
    except AttributeError:
        # Python < 3.9 fallback: os.path.commonpath
        from os.path import commonpath
        is_safe = commonpath([str(p), str(policy.allowed_prefix)]) == str(policy.allowed_prefix)
    if not is_safe:
        raise PathRejected(f"prefix escape: {p} not under {policy.allowed_prefix}")

    # 3. 必須是目錄
    if policy.must_be_directory and not p.is_dir():
        raise PathRejected(f"not a directory: {p}")

    # 4. 所有者檢查（按用戶名，非當前進程 UID）
    import pwd
    try:
        st = p.stat()
        owner_name = pwd.getpwuid(st.st_uid).pw_name
    except (KeyError, OSError) as e:
        raise PathRejected(f"cannot determine owner: {e}")
    if owner_name not in policy.allowed_owner_names:
        raise PathRejected(f"wrong owner: {owner_name} (allowed: {policy.allowed_owner_names})")

    # 5. 拒絕 world-writable
    if policy.reject_world_writable and (p.stat().st_mode & 0o002):
        raise PathRejected(f"world-writable: {p}")

    # 6. BLOCK 路徑檢查（從 shell_policy 導入）
    for prefix in BLOCKED_PATH_PREFIXES:
        if str(p).startswith(prefix):
            raise PathRejected(f"blocked path prefix: {prefix}")

    return p
```

### 7.3 禁止模式

```
🔴 禁止用戶提供任意路徑
🔴 禁止 os.path.realpath 後未做前綴檢查
🔴 禁止 str.startswith 作為唯一前綴檢查（改用 Path.is_relative_to 或 os.path.commonpath）
🔴 禁止統一使用 os.getuid() == st_uid（改用 pwd.getpwuid + 名稱列表）
🔴 禁止接受 resource_name 以外的任何路徑參數
```

### 7.4 BLOCK 路徑

以下路徑**任何命令**不得以任何方式訪問：

```
/etc/goaa/
/etc/goaa/*.env
/home/*/.ssh/
/root/.ssh/
/proc/*/environ
/proc/*/cmdline
/dev/
/sys/
/run/secrets/
任何匹配 *.env 的檔案
任何匹配 *secret* 的檔案 (不區分大小寫)
任何匹配 id_rsa, id_ed25519, id_ecdsa, id_dsa 的檔案
~/.config/goaa-email/
/var/lib/postgresql/*/data/   (PG data 目錄)
/etc/sudoers*
/etc/sudoers.d/*
```

### 7.5 路徑校驗流程（舊版→已由 §7.2 取代）

```
已被 §7.2 resolve_and_verify_resource() 取代
改為 ResourcePolicy 模型
```

---

## 8. 參數校驗（`PROPOSED`）

### 8.1 校驗層級

```
Layer 1: template_id exists in allowlist
Layer 2: resolved_argv 長度與模板一致
Layer 3: 每個 argv 元素符合模板定義 (固定字串 / 枚舉 / 數字範圍)
Layer 4: argv 無 shell injection 特徵 ($(), `, ;, |, &, ||, &&)
Layer 5: 路徑參數過 resource resolution + BLOCK check
```

### 8.2 禁止模式（Layer 4 — 實用子層）

```
命令替換:      $(...), `...`
環境變數展開:   $VAR, ${VAR}
路徑遍歷:      ..
邏輯運算符:    &&, ||, ;
管道:          |
重定向:        >, >>, <, 2>, 2>&1
換行嵌入:      換行符號, \n
空值 argv:     ["", null, undefined]
超長參數:      單一參數 > 256 字元
負數或零:      head -n -1 (數值參數範圍檢查)
隱藏 flag:     --hidden, --password, --secret (模板無定義即拒絕)
```

---

## 9. 管道、重定向、命令替換策略（`OUT_OF_SCOPE` — V0 刀 1 全部禁止）

V0 刀 1 **不支援**以下任何操作：

```
|       管道 (pipe)
>       覆蓋重定向
>>      追加重定向
<       輸入重定向
2>      stderr 重定向
2>&1    stderr 合併至 stdout
$(...)  命令替換
`...`   反引號命令替換
&&      邏輯 AND 連結
||      邏輯 OR 連結
;       順序執行分隔
&       背景執行
```

Worker 收到含以上特徵的 `resolved_argv` → 直接返回 `status: "blocked"`, `error: "feature_not_supported_in_v0_dao1"`。

多命令: 使用 `argparse` 的 `remainder` 或 `nargs` 捕獲後檢查, 若含 shell 特徵則拒絕。

---

## 10. Timeout / Stdout/Stderr 截斷 / Exit Code（`PROPOSED` — 刀 2A 定稿）

### 10.1 Timeout（與 `TEMPLATE_POLICY` 一致）

| 層級 | 值 | 機制 | 對應模板 |
|---|---|---|---|
| LOW 模板 timeout | **5s** | `subprocess.run(argv, timeout=5, shell=False)` | pwd, whoami, hostname, date_iso, uptime_pretty, free_human, df_summary |
| medium 模板 timeout | **10s** | `subprocess.run(argv, timeout=10, shell=False)` | git_status_short, git_rev_parse, systemctl_is_active |
| V0 刀 1 全局上限 | 10s (任何命令不得超過) | 由 allowlist 模板硬編碼 | — |
| SIGTERM 寬限期 | 2s | `timeout` → `process.terminate()` → 2s → `process.kill()` | 刀 2B，刀 2A 僅用 `subprocess.run(timeout=)` |

### 10.2 Stdout/Stderr 截斷

```
stdout 閾值: 32768 bytes (全域統一, 見 §6.2)
stderr 閾值: 16384 bytes (全域統一, 見 §6.2)

if len(output) > threshold:
    output = output[:threshold]
             + "\n-- TRUNCATED at N bytes --\n"
    truncated_flag = true
```

### 10.3 `capture_output` 記憶體約束

```text
subprocess.run(capture_output=True)
在記憶體中完整緩衝 stdout 和 stderr
截斷發生在執行完成後
因此不能形成父進程記憶體硬上限

刀 2A 接受此 residual risk：
  8 個模板皆為固定 argv 的簡單系統命令，
  不會產生不受控大輸出（預計顯著低於 32KB）。

  pwd 輸出長度受路徑長度影響，可能達到數 KB，
  但仍受 stdout 32KB 展示上限約束。

刀 2B 才實現真正的有界 pipe 讀取（見 §20 刀 2B）。
```

### 10.4 Exit Code 處理

| Code | 回傳 |
|---|---|
| 0 | `status="succeeded"` |
| 1-127 | `status="failed"`, `error` 含 stderr (redacted) |
| 124 | `status="timed_out"` (GNU timeout convention) |
| 130 | `status="failed"`, `error="SIGINT"` |
| 137 | `status="failed"`, `error="SIGKILL"` (9) |
| ≥125 | `status="failed"`, `error="system_error"` |

---

## 11. 資源限制（`PROPOSED`）

### 11.1 ulimit 軟限制

| 資源 | V0 值 | 用途 |
|---|---|---|
| `RLIMIT_CPU` | 30s (比 timeout 多一層防護) | CPU 時間上限 |
| `RLIMIT_FSIZE` | 1MB | 單一檔案寫入上限 (阻擋 fork bomb 寫入) |
| `RLIMIT_NOFILE` | 64 | 開啟檔案上限 |
| `RLIMIT_NPROC` | 16 | 子行程上限 |
| `RLIMIT_AS` | 512MB | 地址空間上限 |

### 11.2 實現方式

```python
import resource, subprocess

def _set_limits():
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1 * 1024 * 1024, 1 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_NPROC, (16, 16))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))

proc = subprocess.run(
    argv,
    shell=False,
    timeout=10,
    preexec_fn=_set_limits,
    capture_output=True,
    text=True,
    env=MINIMAL_ENV,       # 見 §10.4
)
```

### 11.3 最小繼承環境（刀 2A 定稿 — 每執行固定環境，不繼承父進程 Shell）

```python
MINIMAL_ENV = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "HOME": "/nonexistent",
    "XDG_CONFIG_HOME": "/nonexistent",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
}
```

禁止繼承: `PGPASSWORD`, `DATABASE_URL`, `ZOHO_PASS`, `OPENAI_API_KEY`, `AWS_*`, `SSH_*`, 任何 `GIT_*` token 變數。

**Git 外部配置風險緩解**：

| 風險 | 緩解 | Residual |
|---|---|---|
| git 讀 `~/.gitconfig` | `HOME=/nonexistent` → 無此路徑 | LOW — 無 user config 洩漏 |
| git 讀 `/etc/gitconfig` | `GIT_CONFIG_NOSYSTEM=1` → 跳過 | NONE |
| git 讀 global config file | `GIT_CONFIG_GLOBAL=/dev/null` → 跳過 | NONE |
| git 啟動 SSH/GPG helper | `GIT_TERMINAL_PROMPT=0` → 禁止交互 | LOW — repo-local `core.sshCommand` 仍可能被讀取（但 exec 時 argv 已固定） |
| git 使用 fsmonitor daemon | `GIT_OPTIONAL_LOCKS=0` → 減少 lock | LOW — `.git/config` 中 fsmonitor 配置仍可能被讀取，但無外部網路調用 |
| git 查找 repo-local helper | `git -C <path> status --short` 僅讀取 HEAD/index/refs，不啟動 credential helper | NONE — 唯讀操作無需認證 |

**git 命令在無 HOME 下的行為**（推理，非執行）：

| 命令 | 需要 HOME？ | 原理 |
|---|---|---|
| `git rev-parse --short HEAD` | ❌ 不需要 | 僅讀 `.git/HEAD` + `.git/refs/`，無 config 依賴 |
| `git status --short` | ❌ 不需要 | 僅讀 HEAD/index/worktree，不讀 global config（`GIT_CONFIG_GLOBAL=/dev/null`） |

**systemctl is-active DBUS 依賴**：

```text
❌ 不需要 DBUS_SESSION_BUS_ADDRESS
✅ 透過 /run/dbus/system_bus_socket（file socket）通信
✅ 無需 XDG_RUNTIME_DIR
✅ 無需任何 user session bus 環境變數
```

### 11.4 `subprocess.run(capture_output=True)` Residual Risk

刀 2A 明確承認：

```text
subprocess.run(capture_output=True)
在父進程記憶體完整緩衝 stdout 和 stderr
截斷在執行完成後發生
不能形成記憶體硬上限

刀 2A residual risk 接受條件：
  8 模板皆為固定 argv 系統命令
  輸出天然有界或高度可預測，預計顯著低於 32KB
  pwd 輸出受路徑長度影響（可能數 KB），仍受 stdout 32KB 上限約束
  無模板會產生不受控 GB 級輸出

刀 2B 才實現真正的有界 Popen 讀取
```

---

## 12. Secret Redaction（`EXISTING` + `PROPOSED` 整合）

### 12.1 執行前校驗

Shell Executor 在執行命令前, 對 `resolved_argv` 進行 `f_lite_sanitize()` 檢查。若 argv 本身包含 secret pattern, 直接返回 `status="blocked"`, `error="command_contains_secret_pattern"`, 不入執行。

### 12.2 輸出後脫敏

```python
# import 策略: PYTHONPATH 注入（與刀 1 一致）
# 刀 1 測試命令: PYTHONPATH=services/rag/workers python3 -m unittest ...
# 刀 2A 測試命令擴充: PYTHONPATH=services/rag/workers:services/rag python3 -m unittest ...
# shell_executor.py 內:
from f_lite_redact import f_lite_sanitize, sanitize_with_count

stdout_safe, hits = sanitize_with_count(raw_stdout)
stderr_safe, _ = sanitize_with_count(raw_stderr)
```

**import 策略說明**：

| 啟動方式 | PYTHONPATH 設定 | 是否一致 |
|---|---|---|
| unittest 測試 | `PYTHONPATH=...services/rag/workers:services/rag` | ✅ |
| CLI (`python3 -m workers.shell_executor`) | 父 shell 設定 PYTHONPATH 或 worker 啟動腳本 | ✅ |
| systemd service（刀 3 後） | Worker 啟動腳本設定 PYTHONPATH | ✅ |

脫敏順序：
1. `base_redact()` — 5 base patterns (sk-/AIza/ghp_/Bearer/key=val)
2. `F_LITE_PATTERNS` — 3 F-lite patterns (PG/SSH/sudo)

### 12.3 已驗證（`EXISTING`）

- `services/rag/f_lite_redact.py` commit `38d33af` ✅
- `test_f_lite_redact.py` 10/10 pass ✅
- 整合於 approve endpoint note redaction ✅

---

## 13. 完整狀態機與 approve/reject 機制（`EXISTING` + `PROPOSED`）

### 13.1 完整狀態集（11 狀態）

```
created
validated
awaiting_approval
approved
queued
running
succeeded
failed
timed_out
rejected
cancelled
```

### 13.2 允許的狀態轉換

```
# 低風險路徑 (risk≤3, allowlist command):
created → validated → queued → running → succeeded
                                          → failed
                                          → timed_out

# 高風險路徑 (risk≥4, 或非 allowlist):
created → validated → awaiting_approval
                        ├── approved → queued → running → succeeded
                        │                                       → failed
                        │                                       → timed_out
                        └── rejected

# 取消 (任何尚未 running 的狀態):
created | validated | awaiting_approval | approved | queued → cancelled
```

### 13.3 Router 角色

- **Router 是任務狀態唯一真相源**。所有狀態變更（created / validated / awaiting_approval / approved / queued / running / succeeded / failed / timed_out / rejected / cancelled）必須由 Router 控制。
- Worker 不直接變更任務狀態。Worker 執行完成後通過 `POST /task/complete` 回報結果, 由 Router 判斷推進至 `succeeded` / `failed` / `timed_out`。

### 13.4 approve 後自動入隊（`PROPOSED` — 取代原 `pending_dispatcher_support`）

```
POST /task/approve 流程:

1. 校驗: 任務當前 status == "awaiting_approval"
2. 冪等檢查:
   - 同一 approval_id: 返回已有結果 (200 OK, "already_processed")
   - 不同 approval_id 但任務已是 approved/queued/running: 返回 409 Conflict
3. 寫入: approved_by, approved_at, approval_note
4. 同一資料庫事務中:
   a. UPDATE tasks SET status='approved', ...
   b. UPDATE tasks SET status='queued', queued_at=NOW()
5. commit → 任務狀態為 queued
6. Dispatcher 提取 queued 任務 → Worker poll → 原子搶佔 queued → running
```

### 13.5 重複 approve 行為

| 場景 | 結果 |
|---|---|
| 同一 `approval_id` 再次調用 | 返回已有結果 (200), 不重複入隊 |
| 不同 `approval_id`, 任務已是 approved/queued/running | 返回 409 Conflict, 不重複執行 |
| 任務已是 rejected/cancelled | 返回 400 Bad Request, 不允許重新審批 |

### 13.6 服務重啟後恢復

```
awaiting_approval: 繼續等待審批 (Router 0930806 現有機制 auto-rebuild)
approved:          恢復時推進至 queued (或由 recovery 任務補償推進)
queued:            繼續等待 Worker (Dispatcher 重啟後會重建佇列)
running:           按 lease/heartbeat 判斷恢復、失敗或重派 (V0 設計中, 非刀 1 範圍)
```

### 13.7 approve endpoint（`EXISTING` — 需擴充）

- `POST /task/approve` in `api.py` L477-508: `UPDATE tasks SET status='approved'`
- V0 擴充: 在同一事務中進一步推進至 `queued` (見 §13.4)
- `audit_log` INSERT 保留

### 13.8 reject endpoint（`PROPOSED`）

- `POST /task/reject` (新建)
- `UPDATE tasks SET status='rejected', rejected_by=%s, reject_reason=%s, rejected_at=NOW()`
- `audit_log` INSERT
- 前端 5188 Console 顯示 rejected 並可查看原因

---

## 14. Audit_log 與 Tool_invocations

### 14.1 Shell 執行審計（`PROPOSED`）

執行前 INSERT（Router 執行, 或 Worker 回報）：

```
audit_log INSERT:
  action_type = "shell_exec"
  task_id = <task_id>
  template_id = <template_id>
  resolved_argv_hash = sha256(json.dumps(resolved_argv))
  resource_name = <resource_name>
  risk_level = <risk_level>
  approval_id = <approval_id|null>
  status = "executing"
  created_at = NOW()
```

執行後 UPDATE：

```
audit_log UPDATE:
  status = "succeeded | failed | timed_out | blocked"
  exit_code = <exit_code>
  output_hash = sha256(stdout_redacted)
  redaction_hits = <hits>
  duration_ms = <ms>
  stdout_truncated = <bool>
  stderr_truncated = <bool>
  stdout_bytes = <N>
  stderr_bytes = <N>
```

### 14.2 tool_invocations（`DESIGN_ONLY` — V0 不重實作）

| 項目 | 發現 |
|---|---|
| PG schema | `v4_agents.tool_invocations` table 存在 |
| API endpoint | POST /tool_invocations 在生產 api.py 中**不存在**（僅 L546 有註解 `# P1.2.1 hook: tool_invocations dual-write`） |
| 歷史代碼 | commit 122abc0 曾實現 |
| V0 決策 | **不重新實作**。V0 審計走 `audit_log` 表。`tool_invocations` 雙寫待 Roadmap P1.2.1 明確需求後再補。 |

---

## 15. FastAPI → OpenClaw 契約草案（`PROPOSED`）

### 15.1 背景

目前 GOAA 無 OpenClaw 實作（僅在 `RUNTIME_OS_STRATEGIC_BLUEPRINT.md` 中定義為「Public API Gateway / API Layer, DO :18789」）。V0 Shell Capability 不直接依賴 OpenClaw，此處僅保留未來對接契約草案。

### 15.2 契約草案

```json
// OpenClaw POST /v1/agents/{agent_id}/execute
// → shell task dispatch to GOAA Router
{
  "agent_id": "string",
  "task_type": "shell_exec",
  "payload": {
    "template_id": "string",
    "resource_name": "string",
    "timeout_s": 10
  },
  "callback_url": "string|null",
  "idempotency_key": "string"
}
// Response (202 Accepted):
{
  "task_id": "uuid",
  "status": "pending | awaiting_approval | queued",
  "estimated_completion_s": 5
}
```

### 15.3 路由邏輯

```
OpenClaw receive → 驗證 agent_id / idempotency_key
  → POST /tasks/dispatch to GOAA Router (內部 HTTP)
  → Router: risk engine + allowlist check
  → [risk≤3] → queued → Worker execute
  → [risk≥4] → awaiting_approval → Console 審批 → approve → queued → execute
  → Worker 完成 → POST /task/complete → Router → callback_url (if set)
```

### 15.4 V0 範圍

- `PROPOSED` — 僅契約草案，無實作
- OpenClaw 本身 `OUT_OF_SCOPE`（V0 不做）
- OpenClaw 不參與 V0 狀態流轉

---

## 16. 與現有 task_runner 的銜接方式（`PROPOSED`）

### 16.1 並存架構

```
task_runner.py (現有, 199行)
  ├─ TASK_HANDLERS = {
  │     "exec_embed_corpus_full": _handle_exec_embed_corpus_full,   # EXISTING
  │     "exec_topk_query_verify": _handle_exec_topk_query_verify,   # EXISTING
  │     "exec_shell": _handle_exec_shell,                           # V0 NEW
  │ }
  ├─ run_task() dispatch loop (不變)
  ├─ 標準 task_result 輸出 (不變)
  └─ main() CLI entry (不變)
```

### 16.2 Handler 註冊

```python
def _handle_exec_shell(params: dict) -> dict:
    """
    params (from task JSON, 不含 secret):
      template_id: str         (allowlist 模板 ID)
      resolved_argv: list[str] (由 Router/Prior 驗證者產生)
      resource_name: str|null  (命名資源)
      timeout_s: int           (按模板固定, max 10)
      approval_id: str|null
    """
    from shell_executor import run_shell
    from shell_schema import ShellValidationResult, ValidationStatus

    # 重構 ShellValidationResult
    result = ShellValidationResult(
        status=ValidationStatus.VALID,
        template_id=params["template_id"],
        resolved_argv=params.get("resolved_argv", []),
        resource_name=params.get("resource_name"),
        timeout_seconds=params.get("timeout_s", 10),
        # ... 其他欄位從 Policy 提取
    )

    exec_result = run_shell(result)
    return {
        "status": exec_result.status.value,
        "exit_code": exec_result.exit_code,
        "stdout_redacted": exec_result.stdout_redacted,
        # ...
    }
```

### 16.3 新檔案

V0 新建以下檔案（刀 1→2A→2B→3 逐步引入）：

```
# 刀 1（已發布 LOCKED）
services/rag/workers/shell_schema.py        # ShellTaskRequest / ShellTaskResult schema
services/rag/workers/shell_policy.py        # allowlist templates + resource map + BLOCK list
services/rag/workers/shell_validator.py     # template/resource/path/block 校驗
tests/test_shell_policy.py                  # policy 完整性測試
tests/test_shell_validator.py               # validator 拒絕測試

# 刀 2A（設計中）
services/rag/workers/shell_executor.py      # subprocess.run(argv, shell=False) + truncation + redaction
                                            # 8 template_id / 9 argv 變體
                                            # 包含 verify_execution_plan()
                                            # 不包含 df_summary, git_status_short
tests/test_shell_executor.py                # mock + 真實執行測試（8 模板）

# 刀 2B（後續擴充）
# 擴充 shell_executor.py
# 追加 Popen + 有界 pipe + process-group killpg
# 追加 df_summary, git_status_short
```

---

## 17. QwenPaw 並排驗收方案（`PROPOSED`）

### 17.1 背景

QwenPaw (`:8088`) 在 Roadmap v1.3 §7 中定位為「過渡備用」，但目前仍為 Aika 的主要執行媒介。Shell Capability V0 完成後，Aika 部分本地操作應逐步轉移至 Shell Executor，QwenPaw 保留為備用通道。

### 17.2 驗收方案（三階段）

**第一階段：固定任務對比測試**（10 個固定任務，~30min 主動測試）

由 QwenPaw 與 GOAA Shell V0 分別執行以下任務，比較輸出：

```
測試 1:  pwd
測試 2:  whoami
測試 3:  hostname
測試 4:  date --iso-8601=seconds
測試 5:  uptime -p
測試 6:  df -h --output=source,size,used,avail,pcent,target  (刀 2B)
測試 7:  free -h
測試 8:  git -C <repo> status --short  (刀 2B)
測試 9:  git -C <repo> rev-parse --short HEAD
測試 10: systemctl is-active goaa-local-console
```

（測試 6 和 8 屬於刀 2B 範圍，刀 2A 驗收時僅驗證 8 個模板）

比較指標：

```
成功率
執行耗時
exit code
stdout / stderr 內容一致性
脫敏效果（若有敏感內容）
審計完整性（audit_log 記錄）
策略拒絕準確性（故意觸發非 allowlist 命令）
```

**第二階段：短時穩定性測試**（1-2 小時 soak test）

```
執行以上 10 個任務循環 50 次
檢查:
  - 無 memory leak
  - 無 unexpected process accumulation
  - audit_log 表增長健康
  - 無假陽性 (allowlist 拒絕不該拒絕的命令)
  - 無假陰性 (blocklist 放行不該放行的命令)
```

**第三階段：延長穩定性測試**（通過第二階段後才考慮）

```
24-48h 連續運行
僅在必要時進行
若前兩階段皆通過即可考慮 rollout
```

### 17.3 階段性切換原則

```
Phase 0 (當前): QwenPaw 100% 接管所有執行
Phase 1 (V0 完成 + 第一階段通過): QwenPaw + Shell V0 並排
  - QwenPaw 保留: 瀏覽器自動化、檔案讀寫(非shell)、多模態處理
  - Shell V0 接管: 10 個 allowlist 命令執行
Phase 2 (第二階段通過): Shell V0 成為主要執行層
  - QwenPaw 僅在 Shell V0 不可用時 fallback
Phase 3 (第三階段 + Router 能力完整): QwenPaw 可選退役
  - 取決於 Router + Shell Executor 能力完整度, 不預設取代
```

### 17.4 本文件立場

**本文件不宣稱已取代 QwenPaw**。V0 完成後 QwenPaw 仍為主要執行層，直到上述三階段驗收全部通過。

---

## 18. V0 測試清單（`PROPOSED` — 刀 2A/2B 分拆）

### 18.1 單元測試（shell_executor.py — 刀 2A）

#### verify_execution_plan 測試

```
[ ] test_verify_template_id_known: "pwd" ∈ ALLOWED_TEMPLATE_IDS → verified
[ ] test_verify_template_id_unknown: "evil_cmd" ∉ ALLOWED_TEMPLATE_IDS → rejected
[ ] test_verify_policy_version_match: "shell-v0.1-knife1" == POLICY_VERSION → verified
[ ] test_verify_policy_version_mismatch: "shell-v0.2-xxx" != POLICY_VERSION → rejected
[ ] test_verify_resource_known: "repo_main" ∈ RESOURCE_MAP → verified
[ ] test_verify_resource_unknown: "/etc/passwd" ∉ RESOURCE_MAP → rejected
[ ] test_verify_argv_pwd: result.resolved_argv == ["pwd"] → verified
[ ] test_verify_argv_forged: result.template_id="pwd", result.resolved_argv=["rm","-rf","/tmp/x"] → **REJECTED (ARGV_MISMATCH)**
[ ] test_verify_git_rev_parse_head: resolved_argv == expected HEAD_SHORT argv → verified
[ ] test_verify_git_rev_parse_branch: resolved_argv == expected BRANCH_NAME argv → verified
[ ] test_verify_git_rev_parse_forged_hash: resolved_argv=["git","-C","...","rev-parse","--short","AAAA"] → **REJECTED**
[ ] test_verify_systemctl_approved_unit: resolved_argv[-1] ∈ ApprovedUnit → verified
[ ] test_verify_systemctl_forged_unit: resolved_argv[-1]="goaa-router-start" ∉ ApprovedUnit → **REJECTED**
[ ] test_verify_timeout_exact: result.timeout_seconds == TEMPLATE_POLICY[tid][0] → verified
[ ] test_verify_timeout_forged: timeout=999 != 5 → **REJECTED**
[ ] test_verify_stdout_limit: result.stdout_limit_bytes == 32768 → verified
[ ] test_verify_stdout_limit_forged: limit=999999 → **REJECTED**
[ ] test_verify_stderr_limit: result.stderr_limit_bytes == 16384 → verified
[ ] test_verify_risk_level: result.risk_level matches TEMPLATE_POLICY[tid][3] → verified
[ ] test_verify_requires_approval: matches TEMPLATE_POLICY[tid][5] → verified
```

#### Executor mock 測試

```
[ ] test_executor_input_valid: VALID ShellValidationResult → 正確調用 subprocess.run
[ ] test_executor_rejects_invalid_status: REJECTED 狀態 → POLICY_MISMATCH
[ ] test_executor_rejects_empty_argv: resolved_argv=[] → POLICY_MISMATCH
[ ] test_executor_shell_false: mock 驗證 shell=False 被傳遞
[ ] test_executor_minimal_env: mock 驗證 env=MINIMAL_ENV
[ ] test_executor_cwd_default: 無 resource → cwd="/"
[ ] test_executor_cwd_resource: repo_main → cwd=經 ResourcePolicy 驗證後的路徑
[ ] test_executor_timeout_from_policy: mock 驗證 timeout 來自 result
[ ] test_executor_stdout_truncation: >32768B mock stdout → stdout_truncated=True
[ ] test_executor_redaction_called: 驗證 f_lite_sanitize 被調用
[ ] test_executor_nonzero_exit: exit code 1 → EXECUTION_FAILED
[ ] test_executor_timeout: mock TimeoutExpired → EXECUTION_TIMED_OUT
[ ] test_executor_unicode_decode: 非 UTF-8 bytes → errors="replace"
[ ] test_executor_internal_error: 意外異常 → EXECUTION_INTERNAL_ERROR
[ ] test_executor_path_rejected: symlink escape → EXECUTION_PATH_REJECTED
```

### 18.2 刀 2B 追加測試（Popen + 有界讀取）

```
[ ] test_template_df_summary: argv == ["df", "-h", "--output=..."]
[ ] test_template_git_status: argv starts with ["git", "-C", ..., "status", "--short"]
[ ] test_popen_bounded_read: 讀滿 stdout_limit 後關閉 pipe
[ ] test_popen_timeout_killpg: timeout → os.killpg cleanup
[ ] test_popen_shell_false: Popen 不使用 shell=True
[ ] test_popen_process_group: start_new_session=True 驗證
```

### 18.3 真實執行測試候選（刀 2A — 只提出，不執行）

```
刀 2A: pwd, whoami, hostname, date_iso, uptime_pretty, free_human,
        git_rev_parse (HEAD_SHORT + BRANCH_NAME), systemctl_is_active
刀 2B: df_summary, git_status_short (需 Popen)
```

### 18.4 整合測試

```
[ ] Router dispatch (risk≤3) → task_runner → shell_executor → POST /task/complete → succeeded
[ ] Router dispatch (risk≥4) → awaiting_approval → POST /task/approve → queued → execute → succeeded
[ ] Router dispatch (risk≥4) → awaiting_approval → POST /task/reject → rejected → cancelled
[ ] POST /task/approve 冪等: 重複調用返回 200 / 409
[ ] POST /task/reject 後再 approve → 400
[ ] 服務重啟後 awaiting_approval 任務恢復
[ ] Console 5188 審批 UI 端點存活
[ ] f_lite_sanitize() 掛在 shell_executor 輸出前正確運作
```

### 18.5 安全測試

```
[ ] BLOCK 路徑無法被任何 allowlist 命令讀取
[ ] shell injection pattern 無法繞過 allowlist
[ ] 最小環境變數不洩漏 secret
[ ] 超長參數無法造成 DoS
[ ] argv 層的 10 命令模板無法被擴充
[ ] 不存在的 template_id → blocked
[ ] 未知 resource_name → blocked
[ ] subprocess.run(shell=False) 使用 argv, 不會被 shell 解析
```

---

## 19. 回滾與禁用開關（`PROPOSED`）

### 19.1 Shell Executor 全局開關

```
File: /opt/goaa/conf/shell_executor.enabled
Content: "enabled" | "disabled" | "readonly"
```

| 狀態 | 行為 |
|---|---|
| `enabled` | 正常運作 |
| `disabled` | 所有 shell 任務返回 `status: "blocked"`, `error: "shell_executor_disabled"` |
| `readonly` | 僅執行 allowlist 唯讀命令（V0 刀 1 全部命令皆唯讀, readonly 等價於 enabled） |

### 19.2 臨時禁用（Runtime）

```
GET /health → {
    "shell_executor": "enabled | disabled | readonly",
    "shell_executor_updated_at": "iso_timestamp"
}
```

### 19.3 回滾策略

| 層級 | 操作 | 時間 |
|---|---|---|
| 立即 | 將 `/opt/goaa/conf/shell_executor.enabled` 設為 `disabled` | < 1s |
| 重啟 | `systemctl restart goaa-router`（讓 Router 不再 dispatch shell 任務） | < 5s |
| 降級 | 恢復 QwenPaw 為主執行通道（見 §17 Phase 0） | < 30s |
| 完全回滾 | `git revert` shell_executor 相關 commit | < 5min |

---

## 20. 分階段實現計畫（`PROPOSED` — 刀 1 `LOCKED`，刀 2A 設計中）

### 刀 1：Schema + Validator + Policy + 拒絕測試（Day 1）

**狀態**: ✅ **已發布 LOCKED** (commit `a157a7b`)

刀 1 嚴格限定：不產生任何真實系統命令。不得包含真實 subprocess.run()、真實 stdout/stderr 捕獲、Task Runner 註冊、Router 接入、Console UI、DO 部署、OpenClaw 接入、服務重啟。

**已發布檔案** `LOCKED`：
```
services/rag/workers/shell_schema.py       # ShellTaskRequest / ShellTaskResult schema
services/rag/workers/shell_policy.py       # allowlist templates + resource map + BLOCK list
services/rag/workers/shell_validator.py    # template_id + argv + resource + path + block token 校驗
tests/test_shell_policy.py                # allowlist 完整性 + 阻斷清單測試
tests/test_shell_validator.py             # 每條模板 argv / 資源 / 阻斷模式測試
```

**刀 1 驗證指標**：
```text
124 測試全部通過
AST 審查確認無 subprocess/os/asyncio/pty/pexpect/shlex/socket 匯入
所有 BLOCKING 問題已修復（metadata 參與 argv、runtime 類型檢查、SHA 基線）
```

### 刀 2A：隔離只讀 Executor（初始發布，需 Tao 單獨批准）

**刀 2A 範圍**：
- 8 個 template_id / 9 個 argv 變體
- `subprocess.run(argv, shell=False)`
- `verify_execution_plan()` 獨立 Policy 覆核
- 固定 cwd 策略
- MINIMAL_ENV
- stdout/stderr truncation + F-lite redaction
- 不接 Router、不接 Task Runner、不接 DO

**cwd 策略**：

```python
DEFAULT_CWD = "/"

def resolve_cwd(result: ShellValidationResult, policy: ResourcePolicy) -> str:
    """
    不需要 resource 的模板: cwd = /
    需要 resource 的模板: cwd = 經 ResourcePolicy 驗證後的 canonical path
    Executor 不得繼承父進程 cwd
    """
    if result.resource_name and result.resource_name in RESOURCE_POLICIES:
        policy = RESOURCE_POLICIES[result.resource_name]
        p = resolve_and_verify_resource(result.resource_name)
        return str(p)
    return DEFAULT_CWD
```

**verify_execution_plan 設計**：

```python
@dataclass(frozen=True)
class PlanVerificationResult:
    verified: bool
    reason_code: str = ""
    details: str = ""

def verify_execution_plan(
    result: ShellValidationResult,
) -> PlanVerificationResult:
    """
    獨立從當前 Policy 重新計算預期 argv 並與 result 逐維度比對。
    這是 subprocess.run 前的最後一道閘。
    """
```

必須覆核以下 9 項維度，全部精確匹配才回 `verified=True`：

| # | 維度 | 檢查方式 | 偽造範例 → 結果 |
|---|---|---|---|
| 1 | template_id | `result.template_id in ALLOWED_TEMPLATE_IDS` | `"evil_cmd"` → REJECTED |
| 2 | policy_version | `result.policy_version == POLICY_VERSION` | `"v0.2"` → REJECTED |
| 3 | resource_name | `result.resource_name in ALLOWED_RESOURCE_NAMES`（若模板需要） | `"/etc/passwd"` → REJECTED |
| 4 | **resolved_argv** | 從 Policy 重新生成預期 argv 後 `==` 逐元素比對 | `{pwd→["rm","-rf","/tmp/x"]}` → **REJECTED (ARGV_MISMATCH)** |
| 5 | timeout | `result.timeout_seconds == TEMPLATE_POLICY[tid][0]` | `999` → REJECTED |
| 6 | stdout_limit | `result.stdout_limit_bytes == TEMPLATE_POLICY[tid][1]` | `999999` → REJECTED |
| 7 | stderr_limit | `result.stderr_limit_bytes == TEMPLATE_POLICY[tid][2]` | `999999` → REJECTED |
| 8 | risk_level | `result.risk_level == TEMPLATE_POLICY[tid][3]` | `"none"` → REJECTED |
| 9 | requires_approval | `result.requires_approval == TEMPLATE_POLICY[tid][5]` | `False` but policy says `True` → REJECTED |

**argv 重新生成邏輯**（關鍵防禦）：

```python
def _recompute_expected_argv(result: ShellValidationResult) -> List[str]:
    """從 Policy + result 欄位重新計算預期 argv。"""
    tid = result.template_id
    resource = result.resource_name

    if tid in ("pwd", "whoami", "hostname"):
        return _template_argv(tid)  # 直接查 Policy

    elif tid == "date_iso":
        return ["date", "--iso-8601=seconds"]
    elif tid == "uptime_pretty":
        return ["uptime", "-p"]
    elif tid == "free_human":
        return ["free", "-h"]
    elif tid == "df_summary":
        return ["df", "-h", "--output=source,size,used,avail,pcent,target"]

    elif tid == "git_status_short":
        if resource not in RESOURCE_MAP:
            raise PlanRejected("unknown resource")
        return ["git", "-C", RESOURCE_MAP[resource], "status", "--short"]

    elif tid == "git_rev_parse":
        if resource not in RESOURCE_MAP:
            raise PlanRejected("unknown resource")
        rp = RESOURCE_MAP[resource]
        argv_head = ["git", "-C", rp, "rev-parse", "--short", "HEAD"]
        argv_branch = ["git", "-C", rp, "rev-parse", "--abbrev-ref", "HEAD"]
        if result.resolved_argv not in (argv_head, argv_branch):
            raise PlanRejected("git_rev_parse argv mismatch")
        return result.resolved_argv  # 任一匹配即通過

    elif tid == "systemctl_is_active":
        unit = result.resolved_argv[-1] if result.resolved_argv else ""
        if unit not in APPROVED_UNITS_STR:
            raise PlanRejected("unapproved systemd unit")
        return ["systemctl", "is-active", unit]

    raise PlanRejected(f"unknown template: {tid}")
```

**阻抗演示 — 偽造 `ShellValidationResult` 必定被拒絕**：

```python
# 偽造對象：
forged = ShellValidationResult(
    status=ValidationStatus.VALID,
    template_id="pwd",
    resolved_argv=["rm", "-rf", "/tmp/x"],  # ← 偽造
    timeout_seconds=5,
    stdout_limit_bytes=32768,
    stderr_limit_bytes=16384,
    risk_level="low",
    requires_approval=False,
    policy_version="shell-v0.1-knife1",
)

result = verify_execution_plan(forged)
# → PlanVerificationResult(
#       verified=False,
#       reason_code="ARGV_MISMATCH",
#       details="expected ['pwd'], got ['rm', '-rf', '/tmp/x']"
#   )
# → 不通過，subprocess.run 不會被調用
```

**刀 2A 新檔案**：
```
services/rag/workers/shell_executor.py      # subprocess.run + verify_execution_plan + 截斷 + 脫敏
tests/test_shell_executor.py                # mock 測試 + 真實執行測試（8 模板）
```

**刀 2A 完成條件**：
```text
verify_execution_plan 測試全部通過（含偽造對象拒絕）
8 模板 mock 測試全部通過
8 模板真實執行測試全部通過
無 df_summary, git_status_short
不接 Router, 不接 Task Runner
```

### 刀 2B：有界流 Executor（後續擴充，需 Tao 另案批准）

**刀 2B 範圍**：
- 追加 df_summary, git_status_short（全部 10 模板）
- 改用 `Popen` + 有界 pipe 讀取（實現真正記憶體硬上限）
- process-group cleanup (`os.killpg`)
- `start_new_session=True`

**刀 2B 執行模型**：

```python
import subprocess, signal, os

proc = subprocess.Popen(
    argv,
    shell=False,
    cwd=resolved_cwd,
    env=MINIMAL_ENV,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    start_new_session=True,    # 獨立 process group
)

try:
    stdout, stderr = proc.communicate(timeout=timeout_seconds)
except subprocess.TimeoutExpired:
    pgid = os.getpgid(proc.pid)
    os.killpg(pgid, signal.SIGTERM)
    try:
        proc.communicate(timeout=2)  # 2s grace
    except subprocess.TimeoutExpired:
        os.killpg(pgid, signal.SIGKILL)
        proc.communicate()
```

**刀 2B 完成條件**：
```text
Popen 有界讀取測試通過
process-group killpg 測試通過
df_summary, git_status_short 真實執行測試通過
全部 10 模板完整覆蓋
```

### 刀 3：Task Runner 接入（Day 3-4）

```
[ ] 擴充 task_runner.py TASK_HANDLERS: 註冊 exec_shell
[ ] 調整 _handle_exec_shell() 調用 shell_executor.run_shell()
[ ] 實現 shell 執行審計 INSERT/UPDATE (§14.1)
[ ] 單元測試: import 正確, 參數傳遞正確
[ ] 整合測試: task_runner → shell_executor (mock 模式先, 真實後)
```

### 刀 4：Router 狀態機與 approve/reject/requeue（Day 4-5）

```
[ ] 實現 reject endpoint (POST /task/reject, 含冪等檢查)
[ ] 擴充 approve endpoint: approve + queued 同一事務推進
[ ] 補 dispatcher 提取 queued 任務邏輯 (只提取 queued, 不再看 approved)
[ ] 實現 Worker POST /task/complete → Router 推進 succeeded/failed/timed_out
[ ] 冪等測試: 同一 approval_id 返回 200; 不同 approval_id 返回 409
[ ] 整合測試: 完整 dispatch→approve→queue→execute→complete 鏈路
```

### 刀 5：Console 審批 UI（Day 5-6）

```
[ ] 5188 Console 審批 UI (pending/approved/rejected 列表 + approve/reject 按鈕)
[ ] Console proxy 到 DO Router 審批端點 (同 D.1 模式)
[ ] 全局開關 (shell_executor.enabled)
[ ] 審計 dashboard (Console 執行歷史)
[ ] 文檔更新
```

### 刀 6：QwenPaw 並排驗收（Day 6-7）

```
[ ] QwenPaw ↔ Shell V0 第一階段對比測試 (10 固定任務, ~30min)
[ ] QwenPaw + Shell V0 第二階段 soak test (1-2h)
[ ] 第三階段延長測試 (24-48h, 通過前兩階段後才考慮)
[ ] 安全測試完整批次
[ ] 壓力測試 (併發命令、大輸出、長 timeout 邊界)
[ ] 性能基準測試
```

### 刀 7：OpenClaw 契約驗證（待啟動，無固定時程）

```
[ ] OpenClaw → GOAA Router dispatch → Shell V0 端到端測試
[ ] callback_url 驗證
[ ] idempotency_key 驗證
[ ] 非同步任務回調路徑測試
[ ] OpenClaw 本身 V0 不入範圍, 見 §15
```

---

## 附錄 A：與現有文檔對照表

| 本文件 § | 對應 F-lite § | 對應 Workflow Graph § | 對應 Runtime OS § |
|---|---|---|---|
| 1 (目標/非目標) | §0 | §0 | §一 |
| 2 (三端對齊) | §14 | — | — |
| 3 (能力缺口) | §15, §16 | §4.1 | — |
| 4 (責任邊界) | — | §4 | §二, §四 |
| 5 (Schema) | — | §2, §3 | §三 |
| 6 (命令白名單) | §4, §5 | — | — |
| 7 (路徑規則) | §4 | — | — |
| 8 (參數校驗) | §4 | — | — |
| 9 (管道/重定向 — OUT_OF_SCOPE) | — | — | — |
| 10 (timeout/截斷) | §5 | §2 (timeout_sec) | §五 (Worker timeout) |
| 11 (資源限制) | §5 | — | — |
| 12 (secret redaction) | §8 | §6 | — |
| 13 (狀態機) | §9, §11 | §5, §8 | §五 |
| 14 (audit/tool_invocations) | §12 | §6 | §三 |
| 15 (FastAPI→OpenClaw) | — | §4.1 | §二 |
| 16 (task_runner 銜接) | §14 (#1) | §4.1 | — |
| 17 (QwenPaw 並排) | §0 | — | §七 |
| 18 (測試清單) | — | — | — |
| 19 (回滾/關閉) | — | — | §五 |
| 20 (分階段實現) | — | — | §六 |

---

## 附錄 B：現有資產 SHA256 參考

```
services/rag/workers/task_runner.py: 199 lines, 2 handlers (embed/topk), 0 shell
services/rag/f_lite_redact.py: 75 lines, 5 base + 3 F-lite patterns
infra/router/api.py: ~660 lines, TASK_REVENUE with risk 1-4
DO /opt/goaa/router/api.py: SHA256=c9260d65 (production == infra, synced)
```

---

**END OF DESIGN DOCUMENT**

> *本文件為設計規範（Design Spec），非 production ready，未實現。*
> *版本 V0.3 — 刀 2A 設計修訂版：Policy code alignment（修正 §6.2 模板 ID/timeout/limit/risk/approval 與已發布 `shell_policy.py` 完全一致）；新增 §0 策略真相層級；正式拆分刀 2A/2B；定稿 MINIMAL_ENV（HOME=/nonexistent + git 隔離變數）；修正路徑檢查為 `Path.is_relative_to` + ResourcePolicy；新增 `verify_execution_plan`（9 維度獨立覆核，含偽造 argv 阻斷演示）；定稿 cwd 策略（不需要 resource→`/`，需要→經 ResourcePolicy 驗證後 canonical path）；明確 `capture_output` residual risk；明確 import 策略（PYTHONPATH 注入，與刀 1 一致）。*
> *狀態標註嚴格區分 EXISTING / PARTIAL / DESIGN_ONLY / PROPOSED / OUT_OF_SCOPE。*
> *所有 PROPOSED 標註項為新創提案，待 Tao 確認後始可切入實作階段。*
