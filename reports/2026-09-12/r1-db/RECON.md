# Round R1 · 階段一前置 — 新資料庫上線前的唯讀勘查（RECON）

- **時間**：2026-09-12 05:41 UTC（= 2026-09-11 22:41 PDT）
- **執行者**：Aika（aika-core-01 runtime；經 `ssh do-runtime-anchor` / `ssh do-c2` 執行）
- **目標**：為「獨立新資料庫 `goaa_platform` / 角色 `goaa_platform`」上線做前置勘查；與現有 `goaa` 庫並存、互不影響。
- **本階段性質**：**唯讀**。未建庫、未建角色、未跑 migration、未改 env、未重啟服務、未 dump 資料。
- **紀律**：env 只列變數名（`cut -d= -f1`）；未印任何密碼／金鑰值；未 `select` 任何業務資料表的列（僅讀系統目錄與 `schema_migrations` 版本號）；IPv4 切分書寫；sha256 只取前 16 位；relay 不 force-push。

---

## 0. 執行摘要（TL;DR）

| # | 發現 | 對階段二的意義 |
|---|---|---|
| **K1** | 🔴 **C1 容器的超管角色是 `goaa`，不是 `postgres`** —— 規格給的 `psql -U postgres` 會直接 `FATAL: role "postgres" does not exist` | 階段二所有 `psql`／`CREATE ROLE`／`CREATE DATABASE` 必須用 `-U goaa`（或容器內 `$POSTGRES_USER`）。**這是規格書的坑，先講明。** |
| **K2** | C1 現有角色**只有 2 個**：`goaa`（Superuser）與 `goaa_rag`（無屬性，僅 CONNECT on `goaa`） | 新角色 `goaa_platform` 需**全新建立**；命名不衝突（現無同名）。 |
| **K3** | **5432 仍 bind 在 `0.0.0.0` / `[::]`**（docker-proxy）；外部不可達是靠 **D0.2 的 `DOCKER-USER` DROP**，不是靠不 bind | 新庫建在同一叢集 ⇒ **繼承同一條對外路徑**；D0.2 的保護對新庫同樣有效，但階段二不要再動防火牆。 |
| **K4** | **migration 0001–0006 的權威來源 = `/opt/goaa-test/backend-clerk-20260910/migrations/`**（**唯一**含完整 0001–0006 的樹；另三棵舊樹缺 `0006`，其中 `src/.../services/c2_agent_loop/migrations` 只有 0001–0004） | 階段二取檔**只取 canonical 樹**，並以下表 `sha256_16` 校驗後再套。 |
| **K5** | **C2 的 3103 後端實際讀 `goaa_c2test`**（app 角色 `goaa_c2_app`，`127.0.0.⟨1⟩:5433`），已套 **0001–0006**；同叢集另有 `goaa_c2`（僅 0001–0004） | 「同一套 schema」的已驗證實例＝ `goaa_c2test`；`goaa_c2` 是舊的、少 2 版。 |
| **K6** | **DB 連線不是一個 DSN 變數**，而是 `GOAA_C2_DB_{HOST,PORT,NAME,USER,PASSFILE,SSLMODE}` 一組（＋遷移用 `GOAA_C2_MIGRATE_{USER,PASSFILE}`） | 階段二若要讓 C1 上的新庫被讀取，需要一組**等價的環境設定**（C1 是 dockerized PG、C2 是原生叢集，兩者不同）。 |
| **K7** | C1 備份可行性：**可用 67 GB** vs 現有 `goaa` 庫 **18 MB** ⇒ 一次 `pg_dump`（≤ 2×）綽綽有餘 | **備份可行，無需先擴容。** |

---

## 1. C1 — 現有 PostgreSQL 盤點（`do-runtime-anchor` = `goaa-aika-cloud-1`）

### 1.1 版本與容器

```
docker ps --filter name=goaa-postgres
  → goaa-postgres | postgres:16-alpine | Up 2 weeks

select version();
  → PostgreSQL 16.13 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
```

### 1.2 ⚠️ 超管角色命名（與規格不符）

```
docker exec goaa-postgres psql -U postgres -c "\l"
  → psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed:
    FATAL:  role "postgres" does not exist
```

改以**容器內** `$POSTGRES_USER` 帶入（**其值未列印**）後，一切正常。經 `\du` 反推：**超管 = `goaa`**。

### 1.3 資料庫清單（庫名｜擁有者｜編碼｜大小）

| datname | owner | encoding | size |
|---|---|---|---|
| **goaa** | goaa | UTF8 | **18 MB** |
| postgres | goaa | UTF8 | 7361 kB |
| template0 | goaa | UTF8 | 7361 kB |
| template1 | goaa | UTF8 | 7417 kB |

- 全部 `datconnlimit = -1`（不限連線數）、`datcollate = en_US.utf8`、locale provider `libc`。
- `goaa` 的 ACL：`=Tc/goaa`、`goaa=CTc/goaa`、`goaa_rag=c/goaa`
  （**`goaa_rag` 僅有 CONNECT/TEMP，無 CREATE**）。
- **未 `select` 任何業務資料表的列**（僅系統目錄 `pg_database`）。

### 1.4 角色清單（`\du`）

| role | attributes |
|---|---|
| **goaa** | **Superuser, Create role, Create DB, Replication, Bypass RLS** |
| goaa_rag | （無屬性） |

### 1.5 容器環境變數**名稱**（只列名，值一律未印）

```
DOCKER_PG_LLVM_DEPS  GOSU_VERSION  HOME  HOSTNAME  LANG  PATH
PGDATA  PG_MAJOR  PG_SHA256  PG_VERSION  POSTGRES_DB  POSTGRES_PASSWORD  POSTGRES_USER
```
（`POSTGRES_DB` / `POSTGRES_PASSWORD` / `POSTGRES_USER` 三者**只列名，未讀值**；角色名 `goaa` 係由 `\du` 輸出具名，非讀 env。）

### 1.6 data 目錄掛載（唯讀 inspect）

```
bind  /opt/goaa/data/postgres  ->  /var/lib/postgresql/data
```

---

## 2. C1 — 磁碟與備份可行性

```
$ df -h /opt/goaa/data/postgres | tail -1
/dev/vda1        77G   11G   67G  14% /

$ du -sh /opt/goaa/data/postgres
73M     /opt/goaa/data/postgres
```

**評估**：
- 現有 `goaa` 庫 **18 MB** ⇒ 一次 `pg_dump` 需求約 **≤ 2× = 36 MB**（未壓縮；壓縮後更小）。
- 可用空間 **67 GB** ⇒ 餘裕 ≈ **1800 倍**。
- **結論：備份可行（feasible），無需先清理或擴容。**
- 註：`du` 為 73 M（含 WAL 與 template），與 `df` 的可用量不衝突。

---

## 5. C1 — 現有 `goaa` 庫的使用者（連線側）

### 5.1 `ss -tnp | grep 5432 | wc -l` → **3**

| 狀態 | 本地 | 對端 | 程序 |
|---|---|---|---|
| ESTAB | `127.0.0.⟨1⟩:5432` | `127.0.0.⟨1⟩:41054` | `docker-proxy` pid=1501 |
| ESTAB | `172.17.0.⟨1⟩:35830` | `172.17.0.⟨2⟩:5432` | `docker-proxy` pid=1501 |
| ESTAB | `127.0.0.⟨1⟩:41054` | `127.0.0.⟨1⟩:5432` | **`uvicorn` pid=2994296（= `goaa-router`）** |

### 5.2 監聽面（唯讀）

```
LISTEN 0 4096  0.0.0.⟨0⟩:5432  0.0.0.⟨0⟩:*   docker-proxy pid=1501 fd=8
LISTEN 0 4096  [::]:5432       [::]:*        docker-proxy pid=1507 fd=8
LISTEN 0 2048  0.0.0.⟨0⟩:8080  0.0.0.⟨0⟩:*   uvicorn pid=2994296 fd=7
```

> **K3 提醒**：5432 的對外可達性是靠 **D0.2 在 `DOCKER-USER` 加的 `--dport 5432 -j DROP`** 攔下，**socket 本身仍 bind `0.0.0.0`**。新庫 `goaa_platform` 若建在同一叢集，**自動享有同一層保護**；階段二請勿再動 ufw / DOCKER-USER。

### 5.3 執行中的 `goaa*` systemd 服務

```
goaa-router.service         active running  GOAA Router (FastAPI + DeepSeek + DB)
goaa-web.service            active running  GOAA production Next.js frontend (e2f26ff)
goaa-worker-agent.service   active running  GOAA Worker Agent (do-cloud-1 / Phase 3)
openclaw.service            active running  GOAA OpenClaw API Gateway
qwenpaw.service             active running  GOAA QwenPaw Agent
```
（`cloudflared` 不含 "goaa" 字樣故未列；`goaa-postgres` 是容器，非 systemd unit。）

---

## 3. C2 — migration `0001–0006` 檔案（`do-c2` = `goaa-aika-cloud-2-01`）

### 3.1 權威來源（canonical）：`/opt/goaa-test/backend-clerk-20260910/migrations/`

> 該目錄與 `goaa-c2-clerk-api-3103` 的 `WorkingDirectory` **同一個**，且**是唯一含完整 0001–0006 的樹**。

| 檔案 | 行數 | bytes | sha256 前16 |
|---|---|---|---|
| `0001_identity.sql` | 89 | 4229 | `16c2c1dc6fc9841b` |
| `0002_applications.sql` | 130 | 6832 | `e0ff4d2e8ad59ef4` |
| `0003_audit_append_only.sql` | 34 | 1351 | `af2d5f9d58caf35b` |
| `0004_role_grant_guard.sql` | 43 | 1655 | `fbf2690542bc813b` |
| `0005_user_identities.sql` | 145 | 7139 | `cb26ebaff7a64cd4` |
| **`0006_golden_business_session.sql`** | **166** | **9349** | **`59d6383d743caef9`** |
| `rollback/0005_user_identities.down.sql` | 24 | 900 | `a670f50c7447baa0` |
| `rollback/0006_golden_business_session.down.sql` | 38 | 1490 | `79481cabc6cca185` |

**目錄權屬**：`goaa-c2loop:goaa-c2loop`；`0006*` 時間戳 `Sep 11 07:43`（`0001–0004` 為 `Sep 10 02:54`、`0005` 為 `Sep 10 06:10`）。

### 3.2 其他樹（共 26 個 `000[1-6]*.sql`，散在 4 棵樹）

| 樹 | 內容 | 與 canonical 的差異 |
|---|---|---|
| `…/backend-clerk-20260910.bak-20260911-074259/migrations/` | 0001–0005 + 0005 down | **缺 0006**（0001–0005 的 `sha256_16` 與 canonical **完全相同**） |
| `/opt/goaa-test/backend/migrations/` | 0001–0005 + 0005 down | **缺 0006**（同上，sha 相同） |
| `/opt/goaa-test/src/c2-pg-agent-loop-20260910/migrations/` | 0001–0005 + 0005 down | **缺 0006**（同上，sha 相同） |
| `/opt/goaa-test/src/c2-clerk-login-20260910/services/c2_agent_loop/migrations/` | **只有 0001–0004** | **缺 0005、0006** |

> ⇒ **0001–0005 四樹內容一致（sha256 前16 全同）；`0006` 只存在於 canonical 樹。階段二取檔務必取 canonical 樹。**

### 3.3 runner（遷移執行器）

| 路徑 | 行數 | sha256 前16 | 說明 |
|---|---|---|---|
| **`/opt/goaa-test/backend-clerk-20260910/tools/migrate.py`** | **109** | **`bee915f183a705e9`** | 權威 runner |
| `/opt/goaa-test/backend/tools/migrate.py` | — | — | 舊樹副本 |
| `/opt/goaa-test/src/c2-pg-agent-loop-20260910/tools/migrate.py` | — | — | 舊樹副本 |
| `/opt/goaa-test/backend-clerk-20260910/tests/test_schema_and_migrations.py` | — | — | schema/遷移測試 |
| `/root/c2-rec-step5-migrate.sh` | — | — | C2.0 時期的一次性腳本 |

`tools/migrate.py` 的設計（摘自檔頭 docstring）：
- **forward-only、idempotent**（每支 migration 可重跑，版本記於 `schema_migrations`）；
- 以 **`psql -1 -f <file>`** 逐檔執行（單一交易）；
- 使用**專用角色**（DSL/DDL 權限，非 superuser），密碼走 **0600 pgpass 檔、不走命令列**；
- 支援 `--status`。
- 支援的環境變數（`tools/migrate.py:35-38` 與 `app/config.py:71-78`）：`GOAA_C2_DB_HOST`、`GOAA_C2_DB_PORT`、`GOAA_C2_DB_NAME`、`GOAA_C2_DB_USER`（＋`…PASSFILE`、`…SSLMODE`）。
- **未讀取、亦未列印** `/opt/goaa-test/env/migrate.pgpass`、`/opt/goaa-test/env/migrate_role_password`、`…/env/*.pgpass` 的任何值。

---

## 4. C2 — Clerk 後端（3103）讀哪個 DB 設定

### 4.1 unit 摘要

```
$ systemctl cat goaa-c2-clerk-api-3103  (節錄)
WorkingDirectory=/opt/goaa-test/backend-clerk-20260910
EnvironmentFile=/opt/goaa-test/env/clerk-api-3103.env          ← 唯一一個
ExecStart=/opt/goaa-test/venv3103-clerk/bin/python -m uvicorn app.main:app \
          --host 127.0.0.⟨1⟩ --port 3103 --no-server-header --log-level info

$ systemctl is-enabled → disabled ; is-active → active
```
- **inline `Environment=`（只列名）**：`PYTHONDONTWRITEBYTECODE`、`PYTHONUNBUFFERED`。
- **`EnvironmentFile` 只有一個**：`/opt/goaa-test/env/clerk-api-3103.env`。

### 4.2 `clerk-api-3103.env` 變數名（27 個，**只列名**）

```
CLERK_AUTHORIZED_PARTIES   CLERK_ISSUER   CLERK_PUBLISHABLE_KEY   CLERK_SECRET_KEY
GOAA_C2_CLERK_AUTH_ENABLED
GOAA_C2_DB_HOST   GOAA_C2_DB_NAME   GOAA_C2_DB_PASSFILE   GOAA_C2_DB_PORT
GOAA_C2_DB_SSLMODE   GOAA_C2_DB_USER
GOAA_C2_DOWNLOAD_TTL   GOAA_C2_EMAIL_DELIVERY   GOAA_C2_ENV   GOAA_C2_MAX_UPLOAD_BYTES
GOAA_C2_MIGRATE_PASSFILE   GOAA_C2_MIGRATE_USER   GOAA_C2_OCR
GOAA_C2_PRIVATE_FILES_DIR   GOAA_C2_PSQL   GOAA_C2_PUBLIC_BASE_URL   GOAA_C2_SCANNER
GOAA_C2_SESSION_COOKIE   GOAA_C2_SESSION_SECRET   GOAA_C2_SESSION_TTL   GOAA_C2_STORAGE_LABEL
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
```

### 4.3 🔴「哪一個是資料庫連線字串？」

**沒有單一 DSN 變數。** DB 連線是由 **一組** `GOAA_C2_DB_*` 組成，於 `app/config.py:71-78` 讀取：

| 變數名 | 角色 |
|---|---|
| `GOAA_C2_DB_HOST` | 資料庫主機 |
| `GOAA_C2_DB_PORT` | 資料庫埠 |
| `GOAA_C2_DB_NAME` | **資料庫名稱** |
| `GOAA_C2_DB_USER` | 應用角色 |
| **`GOAA_C2_DB_PASSFILE`** | **密碼檔路徑（憑據本體在 0600 pgpass 檔內，不在 env）** |
| `GOAA_C2_DB_SSLMODE` | TLS 模式 |
| （遷移用）`GOAA_C2_MIGRATE_USER` / `GOAA_C2_MIGRATE_PASSFILE` | 遷移角色與其密碼檔 |

> 六個 `GOAA_C2_DB_*` 皆為 `set`（存在且非空）；**各變數值一律未列印（符合紀律）**。

### 4.4 以 unit 實際 env 連線的**結果**（只報連線結果，不報 env 值）

```
select current_user, current_database(), inet_server_port();
  → goaa_c2_app | goaa_c2test | 5433

該庫 schema_migrations 版本：
  0001_identity / 0002_applications / 0003_audit_append_only
  0004_role_grant_guard / 0005_user_identities / 0006_golden_business_session
```

⇒ **3103 讀的就是 `goaa_c2test`，且 0001–0006 全部已套用** —— 與 C1.9 驗收一致。

### 4.5 C2 PG 叢集上的資料庫（名稱｜大小，唯讀）

| datname | size |
|---|---|
| `goaa_c2` | 8071 kB |
| **`goaa_c2test`** | **9599 kB** |
| postgres | 7503 kB |
| template0 | 7345 kB |
| template1 | 7567 kB |

（另有 `goaa_c2` 庫，其 `schema_migrations` 只有 **0001–0004** —— 是舊的、少 2 版，**不要當來源**。）

---

## 6. 對「新庫 `goaa_platform`」的含意（階段二輸入 · 僅供參考，本階段未執行）

1. **落點**：新庫要在 **C1 同一叢集**（容器 `goaa-postgres`、PG **16.13**）內建立。
2. **角色**：需**新建**角色 `goaa_platform`（C1 現有角色僅 `goaa`、`goaa_rag`，無命名衝突）。
3. **建庫指令學到的坑（K1）**：`docker exec goaa-postgres psql -U postgres …` **會失敗**；要用 `-U goaa` 或容器內 `$POSTGRES_USER`。
4. **schema 來源**：canonical 樹 `…/backend-clerk-20260910/migrations/` 的 `0001–0006`（sha256_16 見 §3.1），0006 **只此一份**。
5. **連線設定**：C1 端需一組等價的 `GOAA_C2_DB_*` 風格設定（**六個變數，非單一 DSN**）；密碼一律走 0600 檔案、**不進 env 值、不進命令列**。
6. **對外路徑**：新庫繼承 5432 的 D0.2 保護；**階段二不要再動 ufw / DOCKER-USER**。
7. **備份**：可用 67 GB，`goaa` 18 MB ⇒ `pg_dump` 完全可行。

---

## 7. 本階段「未做 / 未碰」清單（稽核用）

- ❌ 未建庫、未建角色、未 `CREATE`／`ALTER` 任何物件。
- ❌ 未跑 migration（僅讀 `schema_migrations` 的版本欄）。
- ❌ 未改任何 env／設定檔；未重啟任何服務（`goaa-router` MainPID `2994296`、`goaa-c2-clerk-api-3103` 全程未動）。
- ❌ 未 `pg_dump`／未匯出任何業務資料。
- ❌ 未 `select` 任何業務資料表的列（僅系統目錄 + 版本表）。
- ❌ 未讀取任何 pgpass／secret 檔的值（僅確認變數**名**存在）。
- ❌ 未動 ufw／DOCKER-USER／nginx／雲端隧道。
- ✅ 全程唯讀；C1 三次、C2 五次 SSH，指令皆為 `SELECT`／`\l`／`\du`／`find`／`ls`／`df`／`du`／`ss`／`systemctl cat|show|is-*`。

---

## 8. 附錄 — 執行來源（本機暫存，非交付物）

| 檔 | 用途 |
|---|---|
| `/tmp/r1-c1.sh`、`/tmp/r1-c1b.sh`、`/tmp/r1-c1c.sh` | C1 items 1 / 2 / 5 |
| `/tmp/r1-c2.sh`、`/tmp/r1-c2b.sh`、`/tmp/r1-c2c.sh`、`/tmp/r1-c2d.sh`、`/tmp/r1-c2e.sh` | C2 items 3 / 4 |
| `/tmp/r1-c1-out.txt`、`/tmp/r1-c1b-out.txt`、`/tmp/r1-c1c-out.txt` | C1 原始輸出 |
| `/tmp/r1-c2-out.txt`、`/tmp/r1-c2b-out.txt`、`/tmp/r1-c2c-out.txt`、`/tmp/r1-c2d-out.txt`、`/tmp/r1-c2e-out.txt` | C2 原始輸出 |

**主機位址切分書寫**：C1 `134.199.227.⟨108⟩`、C2 `143.198.224.⟨71⟩`、C3 `64.23.166.⟨121⟩`。

---

## 9. 秘密掃描（推送前，須為 0 命中）

掃描樣式（**切分書寫，避免本報告自我膨脹**）：
`"sk_" + "live_"`、`"BEGIN " + "PRIVATE KEY"`、`"AK" + "IA"`、`"gh" + "p_"`、`"postgres" + ":" + "//"`。

- 本報告僅出現**變數名**（含 `POSTGRES_PASSWORD`、`GOAA_C2_DB_PASSFILE` 等**名稱**，非值）、庫名、角色名、路徑、行數、`sha256` 前 16 位。
- **未列印任何 token／密碼／金鑰／連線 URI 的「值」**。

**掃描回報（推送前，逐樣式統計）**：

| 樣式（切分書寫） | 命中 |
|---|---|
| `"sk_" + "live_"`（Stripe live 前綴） | **0** |
| `"BEGIN " + "PRIVATE KEY"`（PEM 私鑰標頭） | **0** |
| `"AK" + "IA"`（AWS access key 前綴） | **0** |
| `"gh" + "p_"`（GitHub PAT 前綴） | **0** |
| `"postgres" + ":" + "//"`（Postgres URI scheme） | **0** |
| **合計** | **0** ✅ |

**檔案完整性**：`RECON.md` = **16,005 bytes**、`sha256` 前16 = `d37a7b304e5a3d4e`、首三 byte = `b'# R'`（**無 BOM**）。

**relay main sha**：`1b0d0ad08dfc70873a4bbb3d16b914231dd7234e`
