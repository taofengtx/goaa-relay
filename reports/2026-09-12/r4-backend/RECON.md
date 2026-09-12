# Round R4 前置 — Clerk 後端（3103）上 C1 的唯讀勘查

- **輪次**：R4 前置（唯讀）
- **發令**：Tao（2026-09-12）
- **範圍**：把 C2 的 FastAPI（`goaa-c2-clerk-api-3103`）在 C1 重建一份、接新庫 `goaa_platform` 的**前置調查**
- **本輪產出**：本報告（唯讀勘查），**不含任何變更**
- **狀態**：✅ 完成。**未建目錄、未建 venv、未裝套件、未寫 env、未建 unit、未開埠、未重啟任何服務。**

> **唯讀自證**：本輪在 C1 只執行了 `python3 -V`／`dpkg -l`／`python3 -m venv --help`（僅顯示說明，不建立）／`curl -o /dev/null`（不寫檔）／`ss -ltnp`／`systemctl list-unit-files`／`systemctl cat`／`ls`／`df`／`grep`。在 C2 只執行了 `du`／`ls`／`find`／`grep`／`sed`／`systemctl cat`／`python3 -V`／`pip freeze`（**唯一寫入 = `/root/r4-requirements.lock`，為令明列之產物**）。
> **未觸發任何 🛡 審批卡。**

---

## A. C2（來源）勘查

### A1 程式樹 `/opt/goaa-test/backend-clerk-20260910`

| 項目 | 結果 |
|---|---|
| `du -sh .` | **448K** |
| owner | `goaa-c2loop:goaa-c2loop` |
| `git rev-parse HEAD` | **`not a git repo`**（**部署樹內沒有 `.git`**）|
| `.py` 檔數（排除 venv*） | **24** |
| `app/` 行數合計 | **3,179** 行 |

目錄樹（maxdepth 2，排除 `.git`）：
```
.
./app                （__pycache__ 略）
./deploy
./migrations
./migrations/rollback
./tests
./tests/support
./tools
```
頂層檔案：`.gitignore`(50 B)、`README.md`(11,265 B)、`requirements.txt`(648 B)、`requirements-dev.txt`(118 B)。

`app/` 11 個模組：`__init__.py`、`ai_review.py`、`audit.py`、`clerk_auth.py`、`clerk_identity.py`、`config.py`、`db.py`、`golden_session.py`、`main.py`、`security.py`、`storage.py`。

### ★ A1b 部署樹是否可從版本控制重建 —— **逐檔比對：完全一致 ✅**

C2 部署樹**不是 git repo**，所以我把整棵樹逐檔 sha256 取回，與本機 git worktree
`work/c2-pg-agent-loop-20260909` @ **`dc64591ba7485aa973f373d5340842297f28b630`**（`services/c2_agent_loop/`）比對：

| 項目 | 結果 |
|---|---|
| C2 檔案數（排除 `__pycache__`/`*.pyc`） | **37** |
| 本機 worktree 檔案數 | **37** |
| 只在 C2 | **0** |
| 只在本機 | **0** |
| 同名但內容不同 | **0** |
| **相符且逐位元相同** | **37 / 37** |
| **判定** | **`IDENTICAL`** |

- manifest 檔：C2 產出 → 取回本機 `/tmp/r4-c2-manifest.txt`，3,521 B、sha256 前16 **`fef041df84e8d543`**。
- **樹摘要（排序後 file:sha256 正規化）**：sha256 前16 **`81b17744f8134956`**。

⇒ **結論：C1 的部署來源應為 git commit `dc64591b`，不必從 C2 拷檔。** 這是 R4「可重現」的關鍵前提，且已驗證成立。

### A2 unit 全文（`goaa-c2-clerk-api-3103.service`；`Environment=` 值已遮罩）

`/etc/systemd/system/goaa-c2-clerk-api-3103.service`
```ini
[Unit]
Description=goaa C2 Clerk isolation test - agent-loop API (3103, loopback only)
Requires=postgresql@16-goaa_c2test.service
After=network-online.target postgresql@16-goaa_c2test.service

[Service]
Type=exec
User=goaa-c2loop
Group=goaa-c2loop
WorkingDirectory=/opt/goaa-test/backend-clerk-20260910
EnvironmentFile=/opt/goaa-test/env/clerk-api-3103.env
Environment=<redacted>
Environment=<redacted>
ExecStart=/opt/goaa-test/venv3103-clerk/bin/python -m uvicorn app.main:app \
          --host 127.0.0.1 --port 3103 --no-server-header --log-level info
Restart=no
TimeoutStopSec=20
KillSignal=SIGTERM
NoNewPrivileges=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectClock=yes
ProtectHostname=yes
ProtectProc=invisible
ProcSubset=pid
RestrictNamespaces=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
RestrictAddressFamilies=AF_UNIX AF_INET
LockPersonality=yes
SystemCallArchitectures=native
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM
CapabilityBoundingSet=
AmbientCapabilities=
UMask=0077
IPAddressDeny=any
IPAddressAllow=localhost
ReadWritePaths=/opt/goaa-test/private-files /opt/goaa-test/log
ReadOnlyPaths=/opt/goaa-test/backend-clerk-20260910 /opt/goaa-test/venv3103-clerk \
              /opt/goaa-test/env /opt/goaa-test/wheels
StandardOutput=append:/var/log/goaa-c2-clerk-20260910/api-3103.log
StandardError=append:/var/log/goaa-c2-clerk-20260910/api-3103.log

[Install]
WantedBy=multi-user.target
```

drop-in **`10-clerk-egress.conf`**（既有、非本輪）：
```
[Service]
IPAddressAllow=104.18.37.⟨202⟩/32
IPAddressAllow=172.64.150.⟨54⟩/32
```
（註解：`api.clerk.com (104.18.37.⟨202⟩, 172.64.150.⟨54⟩)  [JWKS /v1/jwks + users.get]`，測試期專用、additive only。）

drop-in **`20-c2test-private-files.conf`**：
```
[Service]
ReadWritePaths=/opt/goaa-test/private-files-c2test
```

**🔴 三個必須在 C1 改掉的硬編碼**：
1. `Requires=` / `After=` `postgresql@16-goaa_c2test.service` —— **C1 的 PG 是 Docker 容器**（`goaa-postgres`），沒有這個單元 ⇒ 必須刪除或換成 `docker.service`。
2. `User` / `Group=goaa-c2loop` —— C1 沒有這個使用者 ⇒ 需新建（或明確改用既有身分）。
3. `ReadOnlyPaths` / `StandardOutput` 指向 `/opt/goaa-test/…` —— C1 **沒有 `/opt/goaa-test`**（見 B4）。

### A3 env 變數名（**27 個**；只列名、不列值）

| 分組 | 變數名 | 數 |
|---|---|---|
| **DB 類** | `GOAA_C2_DB_HOST`、`GOAA_C2_DB_PORT`、`GOAA_C2_DB_NAME`、`GOAA_C2_DB_USER`、`GOAA_C2_DB_PASSFILE`、`GOAA_C2_DB_SSLMODE`、`GOAA_C2_MIGRATE_USER`、`GOAA_C2_MIGRATE_PASSFILE` | **8** |
| **Clerk 類** | `CLERK_ISSUER`、`CLERK_SECRET_KEY`、`CLERK_PUBLISHABLE_KEY`、`CLERK_AUTHORIZED_PARTIES`、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`GOAA_C2_CLERK_AUTH_ENABLED` | **6** |
| **其他** | `GOAA_C2_ENV`、`GOAA_C2_PSQL`、`GOAA_C2_PRIVATE_FILES_DIR`、`GOAA_C2_STORAGE_LABEL`、`GOAA_C2_SCANNER`、`GOAA_C2_OCR`、`GOAA_C2_EMAIL_DELIVERY`、`GOAA_C2_DOWNLOAD_TTL`、`GOAA_C2_MAX_UPLOAD_BYTES`、`GOAA_C2_SESSION_SECRET`、`GOAA_C2_SESSION_COOKIE`、`GOAA_C2_SESSION_TTL`、`GOAA_C2_PUBLIC_BASE_URL` | **13** |

8 + 6 + 13 = **27** ✅

**定義檔權限**：`/opt/goaa-test/env/` 為 `drwx--x--- root:goaa-c2loop`；`clerk-api-3103.env` = `-r--r----- root:goaa-c2loop`（**0440，service 可讀、其他不可**）。

**`config.py` 另有預設值但 env 未設的鍵**（R4 無須提供，會走預設）：
`GOAA_C2_BUILD_REVISION`、`GOAA_C2_DB_CONNECT_TIMEOUT`、`GOAA_C2_DB_STATEMENT_TIMEOUT_MS`、`GOAA_C2_ALLOWED_MIME`。

**🔴 env 檔同目錄另有 4 個「獨立秘密檔」**（R4 必須各自處理，**皆不可從 lock 重建**）：

| 檔案 | 權限 | 用途 |
|---|---|---|
| `app.pgpass` | `0600 goaa-c2loop` | app 角色連線（PGPASSFILE） |
| `migrate.pgpass` | `0600 root` | migrate 角色連線 |
| `session_secret` | `0600 root`（65 B） | **`GOAA_C2_SESSION_SECRET` 的來源** |
| `clerk.env` | `0440 root:goaa-c2loop`（382 B） | Clerk 金鑰群 |

（另 `app_role_password` / `migrate_role_password` 各 64 B、`.c2test-3103.env`、`.pgpass` —— 皆 `root` 專屬；**本輪未讀取其內容**。）

### A4 相依鎖定 ✅

```
/opt/goaa-test/venv3103-clerk/bin/python -V  →  Python 3.12.3
pip freeze > /root/r4-requirements.lock      →  lock_rc=0
wc -l  →  23 行
sha256sum | cut -c1-16  →  deea988f19166741
```
`pyvenv.cfg`：`home=/usr/bin`、`include-system-site-packages=false`、`version=3.12.3`、`executable=/usr/bin/python3.12`。
`venv3103-clerk` 大小 **74M**。

lock（23 套件，逐字）：
```
annotated-types==0.8.0      anyio==4.15.1            bcrypt==4.2.1
certifi==2026.7.22          cffi==2.1.1              clerk-backend-api==7.0.0
click==8.5.0                cryptography==50.0.1     fastapi==0.115.6
h11==0.16.0                 httpcore==1.0.9          httpx==0.28.1
idna==3.19                  psycopg==3.2.3           psycopg-binary==3.2.3
pycparser==3.0              pydantic==2.13.5         pydantic_core==2.46.5
PyJWT==2.13.0               starlette==0.41.3        typing-inspection==0.4.4
typing_extensions==4.16.0   uvicorn==0.32.1
```

**🔴 離線安裝來源存在**：`/opt/goaa-test/wheels/` = **22 個 pinned wheel、8.4M**（含 `psycopg_binary-3.2.3-cp312-cp312-manylinux_2_17_x86_64…whl`）。README 的 "Install from scratch" 段即以 **offline wheel install** 建立 venv。
（註：22 wheel 對 23 套件 —— `PyJWT` 不在 wheel 目錄，推測隨 `clerk-backend-api` 的相依鏈解析安裝；C1 有 PyPI 連通，此點無影響。）

### A5 應用行為（決定 C1 要不要資料目錄／外網）

**需要「可寫目錄」**：
```
app/config.py:101  GOAA_C2_PRIVATE_FILES_DIR  預設 /opt/goaa-test/private-files
app/storage.py:43  root = Path(private_files_dir)
app/storage.py:46  root.mkdir(parents=True, exist_ok=True)   ← 啟動後第一次寫入才會建
app/storage.py:59  os.open(tmp, O_WRONLY|O_CREAT|O_EXCL, 0o600)
```
⇒ **C1 需要一個 0700 的私有檔案目錄**（C2 為 `/opt/goaa-test/private-files` + drop-in `private-files-c2test`）。

**需要「對外網路」**（只到 Clerk）：
```
app/clerk_auth.py:41   from clerk_backend_api import Clerk
app/clerk_auth.py:100  Clerk(bearer_auth=secret_key)      ← SDK 會打 api.clerk.com
app/clerk_auth.py 模組 docstring：fail closed；任何 SDK/網路/JWKS 失敗即拒，iss/sub 缺失即拒
```

> **🔴🔴 這是 C1 重建最容易踩的坑**：C2 的 unit 有 `IPAddressDeny=any` + `IPAddressAllow=localhost`，**Clerk 出網是靠 drop-in `10-clerk-egress.conf` 白名單兩個 Cloudflare anycast IP 才通的**。C1 若照抄主 unit 而**不**加等價 drop-in，**Clerk token 驗證會全部失敗（fail-closed ⇒ 全站拒登）**。
>
> **兩個選項（需 Tao 裁示）**：
> - **(A) 照抄白名單**：加 drop-in 允許 `api.clerk.com` + Clerk dev frontend API（`lenient-phoenix-9847.clerk.accounts.dev`）的 Cloudflare IP。**缺點**：anycast IP 會漂移，屬脆性設定（C2 的 UI drop-in 就多白名單了 2 個帳號網域 IP，可見其脆弱）。
> - **(B)（建議）3103 的 unit 不設 `IPAddressDeny=any`**：C1 host 已 `default deny incoming / allow outgoing`，出網本身不開任何入向埠；服務仍 `127.0.0.1` 綁定、`ProtectSystem=strict`、`NoNewPrivileges`、空 `CapabilityBoundingSet`。**優點**：不依賴會漂移的 IP 白名單、不會因為 Cloudflare 換 IP 而靜默全站拒登。**缺點**：少了「只准連 Clerk」的縱深防禦。
>
> **本輪未做任何選擇，等你決定。**

### A6 健康與路由

```
app/main.py:49    API_PREFIX = "/api/v1/agent-loop"
app/main.py:412   docs_url    = f"{API_PREFIX}/docs"
app/main.py:413   openapi_url = f"{API_PREFIX}/openapi.json"
app/main.py:469   @app.get(f"{API_PREFIX}/health")
```
其餘路由（節錄）：
```
main.py:454  POST /api/v1/agent-loop/auth/register
main.py:455  POST /api/v1/agent-loop/auth/login
main.py:456  POST /api/v1/agent-loop/auth/logout
main.py:457  POST /api/v1/agent-loop/auth/verify-email
```
`main.py` 內 `@app.<verb>` 路由總數：**28** 條（與 C2 現況「路由 28 條」一致）。

### A7 啟動時會不會自跑 migration —— **不會 ✅**

`grep -rn "migrate|schema_migrations|create_all" app/` 的命中**全部是說明文字/註解**，**沒有任何執行路徑**：
```
app/audit.py:6        （docstring）
app/main.py:175       （註解）
app/main.py:1350      （docstring：Revoke…）
```
- **`app/` 完全不碰 `schema_migrations`**（見 §A8-2 佐證）。
⇒ **R4 只需把 migration 跑完（R2 已完成）；應用啟動不負責建表。**

### ★ A8 權限相容性稽核（本輪最重要）★

#### A8-1 針對「C1 較窄」的五項逐項搜尋

| # | 目標表 | C1 授予 | 搜尋「C1 缺的動詞」 | 結果 |
|---|---|---|---|---|
| 1 | `business_subjects` | SELECT / INSERT | `UPDATE` / `DELETE FROM` | **無命中** ✅ |
| 2 | `business_subject_links` | SELECT / INSERT | `UPDATE` / `DELETE FROM` | **無命中** ✅ |
| 3 | `business_tokens` | SELECT / INSERT / **UPDATE** | `DELETE FROM` | **無命中** ✅ |
| 4 | `user_identities` | SELECT / INSERT / **UPDATE** | `DELETE FROM` | **無命中** ✅ |
| 5 | `schema_migrations` | SELECT | `INSERT` / `UPDATE` / `DELETE` | **無命中** ✅ |
| 6 | 綜合樣式（Tao 指定） | — | — | **3 命中**，全部是 `update business_tokens …`（**該表在 C1 授予 UPDATE 範圍內**）|

#### A8-2 全樹 SQL 動詞＋目標表清單（`app/` 內）

| 語句 | 檔案:行 | 目標表 | **C1 是否有該權限** |
|---|---|---|---|
| `insert into` | `app/audit.py:36` | `agent_review_events` | **有**（insert）✅ |
| `insert into` | `app/clerk_identity.py:154` | `identity_events` | **有**（insert）✅ |
| `insert into` | `app/clerk_identity.py:263` | `users` | **有**（arwd）✅ |
| `insert into` | `app/clerk_identity.py:276` | `user_roles` | **有**（arwd）✅ |
| `insert into` | `app/clerk_identity.py:281` | `user_identities` | **有**（arw）✅ |
| `insert into` | `app/golden_session.py:139` | `identity_events` | **有** ✅ |
| `insert into` | `app/golden_session.py:202` | `business_subjects` | **有**（insert；`returning id` 需 SELECT，亦有）✅ |
| `insert into` | `app/golden_session.py:209` | `business_subject_links` | **有** ✅ |
| `update` | `app/golden_session.py:253` | `business_tokens` | **有**（update）✅ |
| `insert into` | `app/golden_session.py:259` | `business_tokens` | **有** ✅ |
| `update` | `app/golden_session.py:306` | `business_tokens` | **有** ✅ |
| `update` | `app/golden_session.py:353` | `business_tokens` | **有** ✅ |
| `insert into` | `app/main.py:346` | `idempotency_keys` | **有**（arwd）✅ |
| `insert into` | `app/main.py:385` | `agent_license_documents` | **有**（arwd）✅ |
| `insert into` | `app/main.py:520` | `users` | **有** ✅ |
| `insert into` | `app/main.py:529` | `user_roles` | **有** ✅ |
| `insert into` | `app/main.py:561` | `user_sessions` | **有**（arwd）✅ |
| `update` | `app/main.py:604` | `user_sessions` | **有** ✅ |
| `update` | `app/main.py:610` | `user_sessions` | **有** ✅ |
| `update` | `app/main.py:643` | `email_verifications` | **有**（arwd）✅ |
| `update` | `app/main.py:653` | `users` | **有** ✅ |
| `insert into` | `app/main.py:693` | `agent_applications` | **有**（arwd）✅ |
| `update` | `app/main.py:709` | `agent_applications` | **有** ✅ |
| `update` | `app/main.py:746` | `agent_licenses` | **有**（arwd）✅ |
| `insert into` | `app/main.py:759` | `agent_licenses` | **有** ✅ |
| **`delete from`** | `app/main.py:771` | `agent_licenses` | **有**（arwd）✅ |
| `update` | `app/main.py:804` | `agent_applications` | **有** ✅ |
| `update` | `app/main.py:941` | `agent_license_documents` | **有** ✅ |
| `update` | `app/main.py:1043` | `agent_applications` | **有** ✅ |
| `insert into` | `app/main.py:1058` | `user_roles` | **有** ✅ |
| **`delete from`** | `app/main.py:1065` | `user_roles` | **有**（arwd）✅ |
| `update` | `app/main.py:1145` | `agent_applications` | **有** ✅ |
| `insert into` | `app/main.py:1216` | `user_roles` | **有** ✅ |
| `update`（**文件字串**）| `app/golden_session.py:13` | `goaa_order_tokens` | **不執行**（見 A8-3）✅ |

**「無」的項數：0。⇒ 沒有任何一項需要在 R4 部署前補 GRANT。**（本輪亦未執行任何 GRANT。）

#### A8-3 兩個容易漏掉但已排除的陷阱

1. **`on conflict … do update`（UPSERT）** —— 若存在，`business_subjects`／`business_subject_links`／`identity_events`／`agent_review_events` 這些 C1 只有 `ar` 的表**會需要 UPDATE 權限而爆掉**。
   全樹 `on conflict` 共 **5 處**，**全部是 `do nothing`，沒有一次 `do update`** ✅：
   ```
   app/main.py:348            on conflict (key) do nothing
   app/main.py:529            on conflict do nothing
   app/main.py:1059           on conflict (user_id, role) do nothing
   app/main.py:1217           on conflict (user_id, role) do nothing
   app/clerk_identity.py:276  on conflict do nothing
   ```
   ⇒ **無隱含 UPDATE 需求。**
2. **`goaa_order_tokens`** —— 這個表**不在 `goaa_platform` 裡**。查證：它只出現在 `app/golden_session.py:11,13`，**是模組 docstring 對「golden runtime 機制」的引述**（`runtime/order_db.py` 的 SQL），**不是本服務執行的語句** ⇒ **無影響** ✅。

#### A8-4 危險動詞

`TRUNCATE` / `ALTER TABLE` / `DROP TABLE|INDEX` / `CREATE TABLE|INDEX|SCHEMA` / `GRANT` / `REVOKE` 在 `app/` 內**全部 0 命中**（所有命中皆為 docstring／註解文字）✅ —— 與 `audit.py` 開頭自述「本模組只提供 insert，沒有 update/delete 路徑」一致。

> **R3 的 ACL 發現在此得到結論**：C1 比 C2 嚴的 6 處權限，**後端一個都沒用到**。C2 多出來的 `w`/`d` 是 `tests/conftest.py` 的 `ALTER DEFAULT PRIVILEGES` 遺留，**不是應用需求**。

---

## B. C1（目標）勘查

### B1 Python / venv / pip

```
Python 3.12.3
VENV_OK                        （python3 -m venv 可用）
pip 24.0  (/usr/lib/python3/dist-packages/pip, python 3.12)
python3-venv     3.12.3-0ubuntu2.1     ii
python3-pip      24.0+dfsg-1ubuntu1.3  ii
python3-pip-whl  24.0+dfsg-1ubuntu1.3  ii
ensurepip_ok 24.0
/usr/bin/python3 → python3.12
```
⇒ **與 C2 同版（3.12.3）、venv/pip/ensurepip 齊備，無需 apt 安裝。**

### B2 對外網路（只測連通）

```
pypi_http            = 200     ✅
files_pythonhosted   = 200     ✅
api_clerk_http       = 401     ✅（可達；401 = 未帶金鑰的正常回應，該端點需認證）
```
⇒ **C1 可從 PyPI 直接建 venv**（不必搬 wheels）；**可達 Clerk API**。

### B3 埠／服務

```
LISTEN 127.0.0.1:3100   next-server   pid=2995017     ← Golden 前端 goaa-web
LISTEN 0.0.0.0:8080     uvicorn       pid=2994296     ← goaa-router
```
**3103 目前無人佔用 ✅**（C2 的 3103 綁 `127.0.0.1`，C1 亦應只綁 loopback）。

`systemctl list-unit-files | grep goaa`：
```
goaa-model-router.service   disabled   （D0.4 已停用）
goaa-router.service         enabled
goaa-web.service            enabled
goaa-worker-agent.service   enabled
```

### B4 磁碟／目錄

```
/dev/vda1   77G   11G   67G   14%  /            ← 空間充裕（venv + 資料目錄 << 1G）
/opt:  containerd, digitalocean, goaa, goaa-frontend, goaa-frontend-e2f26ff.tar.gz
```
**🔴 C1 沒有 `/opt/goaa-test`** —— R4 需要一個新的根目錄（建議 `/opt/goaa-platform/`，與 Golden 的 `/opt/goaa`、C2 的 `/opt/goaa-test` 區隔）。**本輪未建。**

`/opt/goaa-frontend/current → releases/76af718b0568992c900b72d1aff5aad2516046dc`（Golden，未動）。

### B5 前端怎麼呼叫後端（C1）

```
WorkingDirectory=/opt/goaa-frontend/current
Environment=NODE_ENV=production
Environment=HOSTNAME=127.0.0.1
Environment=PORT=3100
```
⇒ **C1 的 `goaa-web` 沒有 `EnvironmentFile`、沒有任何「後端 base URL」變數**（Golden 前端的後端位址燒在 build 裡，且它走的是 `8080` 的 router）。
⇒ **R4 若要上 UI，必須為 C1 前端 env 新增 drop-in，鍵名照抄 C2（見 §C）。**

### B6 cloudflared ingress

`/etc/cloudflared/config.yml` 內 `service:` 指向的目標只有兩個本機埠：**`127.0.0.1:3100`**（多條 hostname，含 `planning.goaa.ai`）與 **`127.0.0.1:8080`**（`api.goaa.ai`，20 條 path）／**`127.0.0.1:18789`**（openclaw catch-all）。
**沒有任何條目指向 3103。**

> **B6 判定（Tao 的問題）**：**`planning.goaa.ai` 不需要為 3103 加路由 —— 而且不應該加。**
> 依 00:44 固定的架構「`Browser → Next 3102 BFF → FastAPI 3103 → goaa_c2test`」，**瀏覽器永遠不直連後端**；3103 由 BFF 經 **loopback** 存取即可。
> 若把 3103 掛上 `planning.goaa.ai`，等於把後端暴露到公網，**直接違反既定架構**（也與 D0 系列「收掉公網面」的方向相反）。
> ⇒ **3103 只需 `127.0.0.1:3103`。若日後要讓瀏覽器看到 UI，該加路由的是 UI 的埠（3102），不是 3103。**

---

## C. 交叉：前端 env 的「後端 base URL」鍵

`/etc/systemd/system/goaa-c2-clerk-ui-3102.service`：
```
WorkingDirectory=/opt/goaa-test/ui-clerk-20260910
EnvironmentFile=/opt/goaa-test/env/clerk-ui-3102.env
ExecStart=/opt/node/bin/node server.js
IPAddressDeny=any / IPAddressAllow=localhost
```
`clerk-ui-3102.env` 變數名（10 個）：
```
CLERK_AUTHORIZED_PARTIES
CLERK_ISSUER
CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY
GOAA_AGENT_LOOP_UPSTREAM      ← ★ 這就是「後端 base URL」
GOAA_C2_CLERK_AUTH_ENABLED
HOSTNAME
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
NODE_ENV
PORT
```

> **✅ C1x 答案**：**`GOAA_AGENT_LOOP_UPSTREAM`**。這是 C1 前端 env drop-in 要照抄的鍵；值應為 `http://127.0.0.1:3103`（loopback，與 §B6 的架構一致）。

**另記（C2 UI drop-in 的出網白名單比 API 多兩個 IP）**：
```
IPAddressAllow=104.18.37.⟨202⟩/32   （api.clerk.com）
IPAddressAllow=172.64.150.⟨54⟩/32   （api.clerk.com）
IPAddressAllow=104.18.34.⟨146⟩/32   （lenient-phoenix-9847.clerk.accounts.dev）
IPAddressAllow=172.64.153.⟨110⟩/32  （lenient-phoenix-9847.clerk.accounts.dev）
```
⇒ 前端（Next）自己也要出網到 Clerk —— 佐證 §A5 的「IP 白名單脆性」判斷。

---

## D. C2 執行期佈局（供 R4 對照）

| 路徑 | 權限 | 用途 |
|---|---|---|
| `/opt/goaa-test/` | `drwx--x--- root:goaa-c2loop` | 根 |
| `…/backend-clerk-20260910/` | `goaa-c2loop` | 程式（448K） |
| `…/venv3103-clerk/` | `goaa-c2loop` | venv（74M） |
| `…/wheels/` | `root` | 22 wheel / 8.4M |
| `…/env/` | `drwx--x--- root:goaa-c2loop` | env + pgpass |
| `…/private-files/` | `drwx------ goaa-c2loop` | 上傳文件 |
| `…/private-files-c2test/` | `drwx------ goaa-c2loop` | 現行 `GOAA_C2_PRIVATE_FILES_DIR` |
| `…/log/`、`…/run/` | `drwx------ root` | 保留 |
| `/var/log/goaa-c2-clerk-20260910/` | `drwxr-x--- goaa-c2loop` | uvicorn 日誌 |

服務狀態：`goaa-c2-clerk-api-3103` = **`disabled` 但 `active`**（未 enable、手動起）；`goaa-c2-clerk-ui-3102` = **`disabled` / `active`**。（供 R4 決定是否 enable。）
3103 監聽確認：`LISTEN 127.0.0.1:3103` ✅；3102 監聽 `127.0.0.1:13102`；PG `127.0.0.1:5433`。
模組可載入性：`import fastapi, psycopg, uvicorn, jwt, clerk_backend_api → imports_ok` ✅。

---

## E. 三題回答

### ① C1 重建需要哪些前置（套件／目錄／權限）？

**套件**：**零**。C1 已是 Ubuntu 24.04.4 + Python **3.12.3** + `python3-venv`/`python3-pip`/`ensurepip` 齊備，與 C2 同版；PyPI 可達（200）⇒ venv 直接建、`pip install -r <lock>` 即可，**不需要搬 `/opt/goaa-test/wheels`**（除非要證明離線可重建）。

**目錄**（C1 目前完全沒有，需新建）：
1. 程式根（建議 `/opt/goaa-platform/`，與 `/opt/goaa`、`/opt/goaa-test` 區隔）。
2. 原始碼（**來自 git `dc64591b`，勿從 C2 拷貝** —— §A1b 已證明兩者一致）。
3. venv（`…/venv3103/`）。
4. `env/`（**0440**，內含 27 變數的 env 檔 + 2 個 `0600` pgpass）。
5. 私有檔案目錄（**0700**，`GOAA_C2_PRIVATE_FILES_DIR` 指向它；`storage.py` 會 `mkdir`，但父目錄需可寫）。
6. 日誌目錄（建議 `/var/log/goaa-platform/`，`0750`）。

**權限／身分**：需一個 **專用服務帳號**（C2 為 `goaa-c2loop`）—— C1 現無此帳號；若不想新建帳號，需明確改用既有身分（**不建議**用 `root` 或 `aika`，帳號本身是最後一道界線）。env 檔與 pgpass 的 owner/權限要對齊 C2（env `0440` 服務可讀、pgpass `0600`）。

**系統整合**：unit 檔（須改 3 處硬編碼，見 §A2）；`Requires=postgresql@16-goaa_c2test.service` **必須刪除**（C1 PG 是 Docker 容器 `goaa-postgres`）；**Clerk 出網需明確決定**（§A5 的 A/B 兩案）。

**DB 側**：`goaa_platform` 已就緒（R2/R3 完成，15 表、owner `goaa_c2_migrate`）；C1 已有 `/root/.goaa_platform_app.pw`、`/root/.goaa_platform_migrate.pw`，需轉為服務可讀的 `0600` pgpass。**無需任何 GRANT**（§A8）。

### ② 有沒有「只存在於 C2、無法從 lock 重建」的東西？

**程式碼：沒有。** §A1b 逐檔 sha256 比對 37/37 完全相同 ⇒ **部署樹 = git `dc64591b` 的 `services/c2_agent_loop/`**，可從版本控制完整重建（且 `app/` 內 0 條 `CREATE`/`ALTER`/`GRANT`，無隱藏 DDL）。

**相依：沒有。** lock 23 行 + `psycopg-binary` 等 cp312 manylinux wheel，C1 可直接從 PyPI 取得（200）；C2 的 `/opt/goaa-test/wheels` 只是當時的離線加速手段。

**無法從 lock 重建的（4 類，皆屬秘密／環境，必須另行處置）**：
1. **`CLERK_SECRET_KEY`** —— Clerk Dev instance 的秘密金鑰。**唯一不可推導項**。需 Tao 決定：沿用 C2 那把（同一 Dev instance）／另發新 instance。**本輪未讀取、未回顯。**
2. **`GOAA_C2_SESSION_SECRET`**（C2 存於 `/opt/goaa-test/env/session_secret`，65 B）—— **C1 必須新生成，不可沿用 C2**（沿用會讓兩環境共用簽章密鑰）。**本輪未讀取。**
3. **兩把 DB 密碼** —— C1 已有明文檔（`/root/.goaa_platform_*.pw`，`0600`），需產生對應 pgpass。**本輪未讀取。**
4. **`CLERK_PUBLISHABLE_KEY` / `CLERK_ISSUER` / `CLERK_AUTHORIZED_PARTIES`** —— 與①同一 Clerk instance 的公開值（非秘密，但需與①一致）。

**另外「非程式、需自行準備」的**：`/opt/node`（若 R4 要上 UI，C1 的 node 路徑與 C2 不同 —— C1 用 nvm 的 v22.22.3，C2 用 `/opt/node/bin/node`）—— 但**本輪範圍僅後端 3103**，UI 留待後續輪次。

### ③ 你預估幾步、哪步風險最高？

**預估 6 步**（每步一驗、逐步回報，任一步驗收不過就停）：
1. **取碼**：從 git `dc64591b` 匯出 `services/c2_agent_loop/` 到 C1 新根目錄；**逐檔 sha256 對照本報告 §A1b 的 manifest（37/37）** 才往下。
2. **建 venv**：`python3 -m venv` + `pip install -r <lock>`；驗 `import` 五件套，且 `pip freeze` == lock。
3. **建目錄／身分／秘密**：服務帳號、`env/`（0440）、2 個 pgpass（0600）、**新生成** `SESSION_SECRET`、私有檔案目錄（0700）、日誌目錄。
4. **建 unit**（改掉 3 處硬編碼；決定 Clerk 出網方案 A/B）；**不 enable、不 start** —— 先 `systemd-analyze verify`。
5. **起服務並驗收**：`127.0.0.1:3103` 起來後跑 `/api/v1/agent-loop/health`；對 `goaa_platform` 做 **A8 全表 CRUD 冒煙**（以 `goaa_c2_app`，走非 loopback + PGPASSFILE），逐項比對「R3 §D 的 C1 權限集」；再驗 append-only 兩表仍擋 `UPDATE`/`DELETE`。
6. **收尾**：秘密掃描、報告、relay push、記憶。

**風險最高的 = 步驟 5（首次真實連線驗收）**，次高為步驟 4。理由：
- **最高：步驟 5** —— 這是**第一次讓後端同時面對「Clerk 真實驗證 ＋ 真 PG 連線 ＋ C1 較窄的權限集」**。R3 已證明 C1 的 ACL 與 C2 不同（雖然 A8 靜態顯示 0 缺口），但**靜態 grep 無法保證** `ON CONFLICT` 之外的執行期行為：`cur.execute` 參數型別、交易邊界、`RETURNING` 與權限的交互、psycopg 3 的 prepared/unprepared 差異等。**必須實測。**
- **次高：步驟 4** —— 兩個決定點：**(i) Clerk 出網**（§A5：A 案脆性、B 案較穩；選錯 ⇒ 全站 fail-closed 拒登，**症狀是「所有人都登不進去」**，容易誤判成別的問題）；**(ii) unit 硬編碼**（`Requires=postgresql@16-goaa_c2test` 若漏刪，**服務根本起不來**）。
- **步驟 3 的隱性風險**：`SESSION_SECRET` 若**沿用 C2** 則兩環境密鑰共用；pgpass 權限若設錯（非 `0600`）psycopg 會拒用。

---

## F. 紀律自證

- **唯讀**：本輪未建目錄/venv、未裝套件、未寫 env、未建 unit、未開埠、**未重啟任何服務**、未動 ufw／DOCKER-USER／`pg_hba`、未碰 `goaa` 庫、未碰 Golden、未碰 3100／8080／3102。
- **唯一寫入**：C2 `/root/r4-requirements.lock`（令明列之產物）。
- **env**：只列變數名（`cut -d= -f1`）；`systemctl cat` 的 `Environment=` 值以 `sed` 遮為 `<redacted>`。
- **秘密**：未讀取、未輸出、未傳輸任何 `CLERK_SECRET_KEY`／`SESSION_SECRET`／DB 密碼；C2 的 `app_role_password`／`migrate_role_password`／`.pgpass` 亦未讀取。
- **IPv4**：本報告一律 `⟨N⟩` 切分末段。
- **sha256**：只取前 16 位。
- **relay**：一般 commit ＋ fast-forward push，**未 force-push**。
- **🛡 卡**：**本輪無任何審批卡出現，亦無任何操作被攔截。**

---

## G. 產物

- 本報告：`reports/2026-09-12/r4-backend/RECON.md`
- 佐證素材（本機 `/tmp`，勿刪）：`r4-c2.sh`／`r4-c2-out.txt`、`r4-c2-a8.sh`／`r4-c2-a8-out.txt`、`r4-c2-g.sh`／`r4-c2-g-out.txt`、`r4-c2-h.sh`／`r4-c2-h-out.txt`、`r4-c2-i.sh`／`r4-c2-i-out.txt`、`r4-c2-j.sh`／`r4-c2-j-out.txt`、`r4-c1.sh`／`r4-c1-out.txt`、`r4-c2-manifest.sh`／`r4-c2-manifest.txt`（3,521 B、sha256 前16 `fef041df84e8d543`）、`r4-cmp.py`。
- **C2 部署樹摘要**：37 檔、樹摘要 sha256 前16 **`81b17744f8134956`**，== git `dc64591ba7485aa973f373d5340842297f28b630` 的 `services/c2_agent_loop/`。
- **C2 相依鎖**：`/root/r4-requirements.lock`（23 行、sha256 前16 `deea988f19166741`）。

---

## 秘密掃描（推送前，須為 0 命中）

樣式（切分書寫）：`"sk_" + "live_"`、`"sk_" + "test_"`、`"BEGIN " + "PRIVATE KEY"`、`"AK" + "IA"`、`"gh" + "p_"`、`"postgres" + ":" + "//"`、`"PGPASSWORD" + "="`、`"pass" + "word="`、`"ey" + "J"`、`".pgp" + "ass"`、`"clerk" + "_secret"`。

| 樣式（切分書寫） | 命中 |
|---|---|
| `"sk_" + "live_"`（Stripe live） | **0** |
| `"sk_" + "test_"`（Stripe test） | **0** |
| `"BEGIN " + "PRIVATE KEY"`（PEM 私鑰） | **0** |
| `"AK" + "IA"`（AWS key） | **0** |
| `"gh" + "p_"`（GitHub PAT） | **0** |
| `"postgres" + ":" + "//"`（PG URI） | **0** |
| `"PGPASSWORD" + "="` | **0** |
| `"pass" + "word="` | **0** |
| `"ey" + "J"`（JWT 形態） | **0** |
| `".pgp" + "ass"`（pgpass 檔名） | **4**（見下） |
| `"clerk" + "_secret"`（鍵名，非值） | **4**（見下） |
| **合計（機密值）** | **0** ✅ |


**非零命中（皆非機密值，明示不掩飾）**：
- `"clerk" + "_secret"` **4 處** —— 全部是**變數名稱**（`CLERK_` 加 `SECRET_KEY`）的出現（env 變數名清單／分組表／§A3 秘密檔表／§E ② 的敘述）。**沒有任何一處是鍵值本身**；本報告自始至終未讀取、未輸出該值。
- `".pgp" + "ass"` **4 處** —— 全部是**檔名**（`app.` 加 `pgpass`、`migrate.` 加 `pgpass`，以及兩處 `.` 加 `pgpass` 的敘述引用）。**不含任何密碼內容**。

**IPv4 書寫說明**：本報告中**可路由（公開）位址**一律以 `⟨N⟩` 切分末段（4 個 Cloudflare 位址已切分）；
**`127.0.0.1`（loopback）與 `0.0.0.0`（unspecified）依既有報告慣例逐字書寫** —— 兩者皆為非可路由、非機密位址。
⇒ **可路由 IPv4 未切分命中數 = 0。**

**檔案完整性**：`RECON.md` = **`BYTES` bytes**、sha256 前16 = `SHA16`、首三 byte = `b'# R'`（**無 BOM**）。

**relay main sha**：`CONTENT_COMMIT_SHA`
（本報告**內容** commit；其後子提交僅寫入本行與掃描回報，未改動任何結論。）
