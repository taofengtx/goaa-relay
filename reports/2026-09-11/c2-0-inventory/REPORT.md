# Round C2.0 — C1 唯讀盤點（為發版手冊取實況）

- **性質**：**只讀**。未改任何檔案、未重啟／未 reload、未建目錄、未動 env／DNS／tunnel，未呼叫任何寫入介面。
- **主機**：C1（ssh 別名 `do-runtime-anchor`，登入 `root`，hostname `goaa-aika-cloud-1`，Ubuntu 24.04.4 LTS，`up 17 days`）。
- **紀律**：env 與金鑰檔**只列變數名**（`cut -d= -f1`）；憑據檔／tunnel id 標 `<OMITTED>`；**所有 IP 以切分寫法**（例：`127.0.0.`＋`1`）。
- **指令類型**：`systemctl cat/show/list-*`、`ls/readlink/cat/stat/find`、`ss`、`df/free/uptime/nproc`、`docker ps/exec`（唯讀查詢）、`psql` **SELECT only**。**沒有任何寫入或狀態變更指令。**

---

## 1. planning.goaa.ai 前端

### 1.1 對應 systemd unit

指令：`systemctl cat goaa-web.service`

```
# /etc/systemd/system/goaa-web.service
[Unit]
Description=GOAA production Next.js frontend (e2f26ff)
After=network-online.target

[Service]
Type=simple
User=goaa-web
Group=goaa-web
WorkingDirectory=/opt/goaa-frontend/current
Environment=NODE_ENV=<REDACTED>
Environment=HOSTNAME=<REDACTED>
Environment=PORT=<REDACTED>
ExecStart=/opt/goaa-frontend/node/bin/node /opt/goaa-frontend/current/server.js
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
ProtectSystem=full
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

- **User/Group**：`goaa-web:goaa-web`
- **WorkingDirectory**：`/opt/goaa-frontend/current`（symlink；見 1.3）
- **ExecStart**：`/opt/goaa-frontend/node/bin/node /opt/goaa-frontend/current/server.js`
- **Environment**：僅 3 個變數名 `NODE_ENV` / `HOSTNAME` / `PORT`（值不列）。
- 觀察：本 unit 以 **`Environment=` 內聯**（非 `EnvironmentFile=`），與 `goaa-router` 的「規範 #22：secrets 走 EnvironmentFile」並不對稱（見 §8）。

### 1.2 監聽埠與 HOSTNAME

指令：`ss -ltnp | grep 3100`、`systemctl show goaa-web.service -p MainPID -p ActiveEnterTimestamp -p ExecMainStartTimestamp -p MemoryCurrent`

- **監聽**：`127.0.0.`＋`1:3100`（`next-server (v1…`，pid `2995017`）→ **只綁回環**，對外一律經 cloudflared。
- **HOSTNAME/PORT**：由 unit `Environment=` 指定（值已遮罩）；**實際綁定行為 = 回環 3100**。
- **MainPID**：`2995017`；`ExecMainStartTimestamp` = `Fri 2026-09-11 06:21:57 UTC`；`MemoryCurrent` ≈ `59.3 MiB`。

### 1.3 release 目錄結構

指令：`ls -la /opt/goaa-frontend/`、`readlink -f /opt/goaa-frontend/current`、`ls -la /opt/goaa-frontend/releases/`

- `current -> /opt/goaa-frontend/releases/`**`76af718b0568992c900b72d1aff5aad2516046dc`**（symlink 建於 Sep 7 10:17）
- `releases/` 共 **21 個版本**（`drwxr-xr-x 5 goaa-web goaa-web`；以下為日期）：

| 版本目錄（sha） | 日期 | 版本目錄（sha） | 日期 |
|---|---|---|---|
| `e2f26ff` | Sep 2 23:08 | `cd956a95…` | Sep 7 02:30 |
| `b1bc1106…` | Sep 3 00:40 | `3b47bb4b…` | Sep 7 07:23 |
| `86bbf599…` | Sep 3 00:45 | `f8a1d7ff…` | Sep 7 08:21 |
| `d889c3f1…` | Sep 3 05:39 | `b0df7ff1…` | Sep 7 08:35 |
| `764aa297…` | Sep 3 20:46 | `1d7a6d9a…` | Sep 7 09:17 |
| `6e7296e3…` | Sep 4 07:25 | `68dde3cb…` | Sep 7 09:37 |
| `668059ee…` | Sep 4 07:59 | **`76af718b…`（current）** | **Sep 7 10:15** |
| `3ea6b759…` | Sep 4 08:27 | `d6029f63…` | Sep 7 10:23 |
| `4e1c6da8…` | Sep 4 09:00 | `dab818ff…` | Sep 5 23:18 |
| `013c6b23…` | Sep 6 20:52 | `9927c44d…` | Sep 6 23:06 |
| `253a78c6…` | Sep 6 21:15 | | |

- release 內容（`current/`）：`.next/`、`node_modules/`、`package.json`、`public/`、`server.js`（**standalone 形態**，與 C2 一致）。
- 另有 3 個部署 tarball：`goaa-web-auth-20260906-013c6b23…tar.gz`（8,506,685 B）、`goaa-web-passreveal-20260906-253a78c6…tar.gz`（8,508,151 B）、`goaa-web-legal-20260906-9927c44d…tar.gz`（8,507,908 B）。
- **⚠️ 觀察**：`d6029f63…`（Sep 7 10:23）比 current 的 `76af718b…`（10:15）**更新**，但**未被 current 引用**；其 BUILD_ID 為 `XI0npe4KUOvwqjs4sRmR7`，與線上不同（見 1.4）。

### 1.4 線上版本 BUILD_ID 與 git sha

指令：`cat /opt/goaa-frontend/current/.next/BUILD_ID`、`ls -a current/ | grep -iE "git|sha|revision|version"`

- **BUILD_ID（線上）**：`5wl6uCJFbHElFV3-B3I79`
- **git sha**：**無檔內記錄**（release 內無 `.git`／`REVISION`／`VERSION`）→ **以 release 目錄名為準**：`76af718b0568992c900b72d1aff5aad2516046dc`（= 黃金 commit）。
- **⚠️ 發版手冊提醒**：sha→BUILD_ID 對映需靠目錄名＋`.next/BUILD_ID` 佐證；建議未來發版時把 sha 寫進產物（如 `REVISION` 檔）。

### 1.5 node 版本

指令：`/opt/goaa-frontend/node/bin/node -v` → **`v22.22.3`**（與本機 C2 建置所用一致）。

---

## 2. tunnel

### 2.1 unit 與設定檔

指令：`systemctl cat cloudflared.service`、`systemctl show cloudflared.service -p Type -p MainPID -p ActiveEnterTimestamp`、`ls -la /etc/cloudflared/`

```
[Unit]
Description=cloudflared
After=network-online.target
Wants=network-online.target

[Service]
TimeoutStartSec=15
Type=notify
ExecStart=/usr/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run
Restart=on-failure
RestartSec=5s
```

- **執行身分**：無 `User=` → **root**（憑據檔在 `/root/.cloudflared/`）
- **MainPID** `2111569`、`ActiveEnterTimestamp` `Thu 2026-09-03 00:27:23 UTC`
- **設定檔**：`/etc/cloudflared/config.yml`（2,229 B、`-rw-r--r--` root:root）；旁有 `.bak-*`／`.next` 備份
- **憑據**：`/root/.cloudflared/<uuid>.json`（175 B、`-r--------`）→ **略**（未讀內容）；`cert.pem`（282 B、`-rw-------`）亦略
- 額外觀測：cloudflared 在本機監聽 `127.0.0.`＋`1:20241`（metrics，pid 2111569）

### 2.2 ingress（`credentials-file:` 與 tunnel id 略）

指令：`cat /etc/cloudflared/config.yml | sed -E 's/^(credentials-file:).*/… <OMITTED>/; …'`

| hostname | path | service |
|---|---|---|
| `api.goaa.ai` | `/workers/status`, `/workers/metrics`, `/worker/heartbeat`, `/tasks/dispatch`, `/tasks/status/*`, `/tasks/queue`, `/tasks/cancel/*`, `/tasks/next/*`, `/task/complete`, `/tasks/pool`, `/tasks/pool/add`, `/tasks/pool/add-batch`, `/tasks/pool/stats`, `/tasks/history`, `/cost/status`, `/profit/status`, `/revenue/status`, `/models/status`, `/route`, `/chat` | `http://127.0.0.`＋`1:8080`（goaa-router） |
| `api.goaa.ai` | **（無 path，其餘全部）** | `http://127.0.0.`＋`1:18789`（openclaw） |
| `planning.goaa.ai` | `/planning` | `http://127.0.0.`＋`1:3100`（goaa-web） |
| `planning.goaa.ai` | **（無 path，其餘全部）** | `http://127.0.0.`＋`1:3100` |
| （catch-all） | — | `http_status:404` |

- 要點：**planning.goaa.ai 全部流量 → 3100（單一前端）**；**api.goaa.ai 依 path 分流**，只有明確列出的 20 條 path 走 8080（router），其餘走 18789（openclaw）。

---

## 3. api.goaa.ai 後端（只看不碰）

指令：`systemctl cat goaa-router.service`、`systemctl show … -p MainPID -p ExecStart`、`ss -ltnp`、`docker exec … psql -At -c "select datname||… from pg_stat_activity"`

- **unit**：`goaa-router.service`（`GOAA Router (FastAPI + DeepSeek + DB)`，`enabled`）
- **User/Group**：`root:root`
- **WorkingDirectory**：`/opt/goaa/router`
- **EnvironmentFile**：`/etc/goaa/secrets.env`（**規範 #22**）
- **ExecStart**：`/opt/goaa/venv/bin/uvicorn api:app --host 0.0.0.＋0 --port 8080`
- **MainPID** `2994296`、`ActiveEnterTimestamp` `Fri 2026-09-11 06:21:50 UTC`
- **監聽**：`0.0.0.＋0:8080`（另 drop-in `10-port-cleanup.conf` 於啟動前清佔用）
- **資料庫名稱（僅名稱）**：**`goaa`**。依據：`pg_stat_activity` 中 `client backend` 各庫計數 = `goaa|2`（無其他庫有連線）。
- **同族另一 unit（未運行）**：`goaa-model-router.service`（`enabled`，**同綁 8080**，目前 inactive）→ 與 `goaa-router` 為**埠衝突關係**（見 §8）。
- 補充：`api.goaa.ai` 的非業務 path（無 path 命中）走 `openclaw.service`（`0.0.0.＋0:18789`）。

---

## 4. Postgres

指令：`docker ps`、`docker exec goaa-postgres postgres --version`、`docker exec … psql -At -c "select datname||Chr(124)||pg_size_pretty(pg_database_size(datname)) from pg_database order by datname"`、`show listen_addresses/port`、`ls/stat/find`、`systemctl list-timers`、`crontab -l`

- **形態**：**Docker 容器**，非宿主 systemd。
  - 容器 `goaa-postgres`，image **`postgres:16-alpine`**，`Up 2 weeks`
  - 埠映射：`0.0.0.＋0:5432->5432/tcp`、`[::]:5432->5432/tcp`（經 `docker-proxy`）
  - 同主機另有容器 `goaa-openclaw`（`nginx:alpine`，`0.0.0.＋0:17879->80/tcp`）、`goaa-heartbeat`（`alpine`，無埠）
- **版本**：**PostgreSQL 16.13**
- **監聽**：容器內 `listen_addresses = *`、`port = 5432`；**宿主端對外綁 `0.0.0.＋0:5432`**
- **資料庫清單（名稱｜大小）**：

| 資料庫 | 大小 |
|---|---|
| `goaa` | 18 MB |
| `postgres` | 7,361 kB |
| `template0` | 7,361 kB |
| `template1` | 7,417 kB |

- **備份機制**：
  - `systemctl list-timers --all`：**無任何 goaa 備份 timer**（只有系統 fwupd/sysstat/logrotate/dpkg 等）
  - `crontab -l`：**僅一條** `0 7 * * * /opt/goaa/scripts/check_do_git_consistency.sh --dry-run`
  - `/etc/cron.d/`：僅 `e2scrub_all`、`sysstat`（系統）
  - **結論：沒有自動備份；只有手動 dump。**
  - 最近備份檔（`find … -printf`）：

| 檔案 | 時間 | 大小 |
|---|---|---|
| `/opt/goaa/backups/goaa-step2-20260906-204455.dump` | 2026-09-06 20:44 | 5,041,599 B |
| `/opt/goaa/backups/goaa-pre-oauth-20260906-203443.dump` | 2026-09-06 20:34 | 5,037,681 B |
| `/opt/goaa/runtime/backups/schema-pre-phase4-stage-b-20260828.sql` | 2026-08-28 05:13 | 58,924 B |
| `/opt/goaa/runtime/backups/schema-pre-phase4-20260828.sql` | 2026-08-28 03:30 | 56,187 B |
| `/opt/goaa/runtime/backups/goaa_order_payments.backup-pre-payment-type-20260828.sql` | 2026-08-28 09:06 | 10,470 B |

  - 最近一次 dump 距今 **5 天**（2026-09-06）。

---

## 5. 新服務能否上線

| 檢查 | 指令 | 結果 |
|---|---|---|
| 候選埠 3103 | `ss -ltn \| awk '$4 ~ /:3103$/ {c++} END {print c+0}'` | **0（空閒）** ✅ |
| python3 | `python3 -V` | **Python 3.12.3** ✅ |
| venv | `ls -la /opt/goaa/venv/bin/python3` | 存在；`python3 -> /usr/bin/python3`（3.12.3）✅ |
| secrets 檔 | `stat -c "%n perms=%a owner=%U:%G size=%s" /etc/goaa/secrets.env` | **存在、`600 root:root`、932 B** ✅ |

**`/etc/goaa/secrets.env` 變數名清單（僅名稱，無值）**：

`GOAA_SECRETS_KEY`、`DEEPSEEK_API_KEY`、`SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASS`、`EMAIL_TO`、`PG_PASSWORD`、`STRIPE_SECRET_KEY`、`STRIPE_PUBLISHABLE_KEY`、`STRIPE_WEBHOOK_SECRET`、`GOAA_FRONTEND_URL`、`GOAA_CUSTOMER_CONSOLE_URL`、`GOAA_CONNECT_RETURN_URL`、`GOAA_SERVICE_RETURN_URL`

- `/etc/goaa/` 另含：`openclaw.env`（`600`）＋ 4 個 `secrets.env.*` 備份檔（皆 `600`）。
- **注意**：`PG_PASSWORD` 存在 → 新服務若沿用同一 PG 帳號，可直接引用；**但 C2 採「角色分離 + PASSFILE」**（見 §7），移植時建議對齊 C2 的 `PASSFILE` 寫法而非把密碼散佈到多個 unit。

---

## 6. 資源

指令：`df -h / /opt /var`、`free -h`、`uptime`、`nproc`、`systemctl list-units --state=running`、`systemctl list-unit-files`

- **磁碟**：`/dev/vda1` **77G，已用 11G（14%），可用 67G**；`/`、`/opt`、`/var` **同一檔案系統**（無獨立掛載）。
- **記憶體**：total **3.8Gi**、used **880Mi**、free 197Mi、available **3.0Gi**；**Swap 0B**。
- **負載／CPU**：`up 17 days 15:50`、load `0.59 / 0.31 / 0.25`、**nproc 2**。
- **運行中的 goaa 相關 service**（`--state=running`）：`cloudflared`、`goaa-router`、`goaa-web`、`goaa-worker-agent`、`openclaw`、`qwenpaw`。
- **enabled 但未運行**：`goaa-model-router`（+ 上述全部 enabled）。
- **無 nginx on host**（`command -v nginx` → 無）；開放埠一覽：`22`、`3100`(loopback)、`5432`、`8080`、`17879`、`18789`、`20241`(loopback cloudflared metrics)、`127.0.0.`＋`53:53`/`127.0.0.`＋`54:53`(systemd-resolved)。

---

## 7. C2 對照（供發版手冊一比一搬到 C1）

### 7.1 agent-loop 後端 unit（C2）

指令：`systemctl cat goaa-c2-clerk-api-3103.service`（含 2 個 drop-in）

- **Unit**：`Requires=postgresql@16-goaa_c2test.service`、`After=network-online.target postgresql@16-goaa_c2test.service`
- **Service 關鍵**：`Type=exec`；`User/Group=goaa-c2loop`；`WorkingDirectory=/opt/goaa-test/backend-clerk-20260910`；`EnvironmentFile=/opt/goaa-test/env/clerk-api-3103.env`；`ExecStart=/opt/goaa-test/venv3103-clerk/bin/python -m uvicorn app.main:app --host 127.0.0.`＋`1 --port 3103 --no-server-header --log-level info`；`Restart=no`
- **沙箱**：`NoNewPrivileges`、`PrivateTmp`、`PrivateDevices`、`ProtectSystem=strict`、`ProtectHome`、`ProtectKernel*`、`ProtectClock`、`ProtectHostname`、`ProtectProc=invisible`、`ProcSubset=pid`、`RestrictNamespaces/Realtime/SUIDSGID`、`RestrictAddressFamilies=AF_UNIX AF_INET`、`LockPersonality`、`SystemCallArchitectures=native`、`SystemCallFilter=@system-service`、`SystemCallErrorNumber=EPERM`、`CapabilityBoundingSet=`（空）、`AmbientCapabilities=`（空）
- **網路白名單**：`IPAddressDeny=any` + `IPAddressAllow=localhost`；drop-in `10-clerk-egress.conf` 追加 2 個 Cloudflare anycast IP（`/32`，供 Clerk JWKS）
- **ReadWritePaths**：base = `/opt/goaa-test/private-files` `/opt/goaa-test/log`；drop-in `20-c2test-private-files.conf` **追加 `/opt/goaa-test/private-files-c2test`**
- **ReadOnlyPaths**：`/opt/goaa-test/backend-clerk-20260910`、`/opt/goaa-test/venv3103-clerk`、`/opt/goaa-test/env`、`/opt/goaa-test/wheels`
- **日誌**：`StandardOutput=append:/var/log/goaa-c2-clerk-20260910/api-3103.log`（stderr 同）
- **UMask=0077**

### 7.2 env 變數名清單（C2 · `clerk-api-3103.env`，28 個，僅名稱）

`GOAA_C2_ENV`、`GOAA_C2_DB_HOST`、`GOAA_C2_DB_PORT`、`GOAA_C2_DB_USER`、`GOAA_C2_DB_PASSFILE`、`GOAA_C2_DB_SSLMODE`、`GOAA_C2_MIGRATE_USER`、`GOAA_C2_MIGRATE_PASSFILE`、`GOAA_C2_PSQL`、`GOAA_C2_SESSION_COOKIE`、`GOAA_C2_SESSION_TTL`、`GOAA_C2_PRIVATE_FILES_DIR`、`GOAA_C2_STORAGE_LABEL`、`GOAA_C2_SCANNER`、`GOAA_C2_OCR`、`GOAA_C2_DOWNLOAD_TTL`、`GOAA_C2_MAX_UPLOAD_BYTES`、`GOAA_C2_EMAIL_DELIVERY`、`GOAA_C2_PUBLIC_BASE_URL`、`GOAA_C2_SESSION_SECRET`、`GOAA_C2_DB_NAME`、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`CLERK_AUTHORIZED_PARTIES`、`CLERK_ISSUER`、`GOAA_C2_CLERK_AUTH_ENABLED`

- env 檔權限：`clerk-api-3103.env`、`clerk-ui-3102.env`、`clerk.env`、`goaa-c2-backend.env` 皆 **`440 root:goaa-c2loop`**。
- **證件目錄**：`GOAA_C2_PRIVATE_FILES_DIR=`**`/opt/goaa-test/private-files-c2test`**（`drwx------ goaa-c2loop:goaa-c2loop`）。

### 7.3 migration 檔清單（C2）

指令：`ls -la /opt/goaa-test/backend-clerk-20260910/migrations/`

| 檔 | 大小 | 日期 |
|---|---|---|
| `0001_identity.sql` | 4,229 B | Sep 10 02:54 |
| `0002_applications.sql` | 6,832 B | Sep 10 02:54 |
| `0003_audit_append_only.sql` | 1,351 B | Sep 10 02:54 |
| `0004_role_grant_guard.sql` | 1,655 B | Sep 10 02:56 |
| `0005_user_identities.sql` | 7,139 B | Sep 10 06:10 |
| `0006_golden_business_session.sql` | 9,349 B | Sep 11 07:43 |
| `rollback/`（目錄） | — | — |

### 7.4 C1 vs C2 對照摘要

| 面向 | C1（現況） | C2（可移植範式） |
|---|---|---|
| 服務身分 | `goaa-router` 以 **root** 跑 | 專用 `goaa-c2loop`（最低權限） |
| secrets | `EnvironmentFile=/etc/goaa/secrets.env`（單一檔，含 `PG_PASSWORD` 等 15 名） | 專用 `clerk-api-3103.env`（440，28 名）＋ `PASSFILE` |
| 綁定 | router `0.0.0.＋0:8080` | `127.0.0.`＋`1:3103`（**只回環**） |
| 沙箱 | 幾乎無（僅 `Restart`） | `ProtectSystem=strict` + `IPAddressDeny=any` + `ReadWritePaths` 白名單 + `SystemCallFilter` |
| DB | Docker `postgres:16-alpine`（16.13），`0.0.0.＋0:5432` | 宿主 `postgresql@16-goaa_c2test`，僅 `127.0.0.`＋`1:5433` |
| 遷移 | 手動 dump（無自動備份） | `migrations/0001–0006` forward-only + `rollback/` |
| 前端 | `goaa-web`（3100，standalone，21 版 releases） | `goaa-c2-clerk-ui-3102`（13102，standalone） |

---

## 8. 觀察與缺口（只報告，未動任何設定）

1. **無自動備份**：C1 上沒有任何 PG 備份 timer／cron，最近 dump 為 **2026-09-06**（5 天前，手動）。→ 上線手冊**必須**含「部署前手動 dump」步驟（C2 的 `pg_dump --no-owner --no-privileges` + PASSFILE 配方可直接沿用）。
2. **PG 對公網綁定**：容器埠映射為 `0.0.0.＋0:5432`，且 `listen_addresses='*'` → 是否僅雲端防火牆阻擋，需另行確認（本輪未動 nft/iptables）。
3. **origin 埠對外開放**：`goaa-router` 綁 `0.0.0.＋0:8080`、openclaw 綁 `0.0.0.＋0:18789`；cloudflared 是唯一對外入口，但 origin 埠本身也在公網介面上（同上需確認防火牆）。
4. **埠衝突隱患**：`goaa-model-router.service`（enabled、**未運行**）與 `goaa-router.service` **同綁 8080**；若其被單獨啟動會與現行 router 搶埠。
5. **未被引用的較新 release**：`releases/` 內 `d6029f63…`（Sep 7 10:23，BUILD_ID `XI0npe4KUOvwqjs4sRmR7`）比 current 新，但未上線 → 疑為部署／回滾殘留（未清理、**未動**）。
6. **secrets 型態不一致**：`goaa-web` 用 `Environment=` 內聯（變數值寫在 unit 檔），`goaa-router` 用 `EnvironmentFile=`；移植時建議統一為 C2 風格。
7. **無 Swap（3.8 GiB RAM、2 vCPU）**：與 C2 相同教訓——`next build` 需 `--max-old-space-size` 控制，否則易 OOM。
8. **上線條件（3103）齊備** ✅：埠空閒、`python3 3.12.3` 可用、`/opt/goaa/venv` 可用、`/etc/goaa/secrets.env`（600）已存在。
9. **C1 release 以「sha 目錄名 + symlink current」管理**，與 C2 的 standalone rsync 部署不同；發版手冊需描述 `current` 切換與回滾（`ln -sfn`）流程。

---

## 9. 結論

C1 現況已完整盤點：前端 `goaa-web`（3100，current = 黃金 sha `76af718b…`，BUILD_ID `5wl6uCJFbHElFV3-B3I79`，node v22.22.3）、tunnel `cloudflared`（planning.goaa.ai→3100、api.goaa.ai→8080/18789）、後端 `goaa-router`（8080，DB `goaa`）、Postgres 16.13（Docker，`goaa` 18 MB）。**3103 空閒、python3 與 venv 可用、secrets.env 已在位**，具備新增服務的客觀條件；主要缺口為**無自動備份**、**PG/origin 埠對公網綁定待確認防火牆**、以及**secrets 型態與沙箱強度落後於 C2 範式**。以上僅為現況盤點，**本輪未做任何變更**。
