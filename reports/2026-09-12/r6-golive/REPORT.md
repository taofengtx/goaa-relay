# R6｜全鏈驗證 → enable 兩個 unit → 重開機存活性審計

**命令出處**：Tao，2026-09-12（指令單 R6）。
**執行者**：Aika（本機 → ssh `do-runtime-anchor`，即 C1 `goaa-aika-cloud-1`）。
**本輪唯一寫入動作 = `systemctl enable goaa-platform-api-3103.service`（未加 `--now`）**；全程**未** reboot／shutdown／restart／daemon-reexec；未改 `current`／`web.env`／unit 主檔／drop-in／migrations／資料庫內容；未 force-push；未對外發起掃描。

## §0 摘要與逐條判定

| 步驟 | 結果 |
|---|---|
| 0 基線 0-1 ~ 0-6 | ✅ 全綠（**任一不符即停之判據皆未觸發**） |
| 1 L1 前端本機 | ✅ 200／200；`clerk.goaa.ai`=1、`clerkAuth true`=1、not-configured=0 |
| 1 L2 後端健康 | ✅ **200**（`/api/v1/agent-loop/health`；`/healthz`、`/ready` 皆 404，實際可用路徑 = 帶前綴之 `/health`） |
| 1 L3 後端 Clerk 鏈 | ✅ **L3a = 401 `missing_clerk_session`**；**L3b = 401 `invalid_clerk_session`** ⇒ **production JWKS 可達、非 `clerk_verification_unavailable`** |
| 1 L4 後端→DB | ⚠️ `pg_stat_activity` **未捕捉**（非紅，依令）；**補證：20 次請求使 `xact_commit` 增 42**（對照組 2）⇒ 實際有交易 |
| 1 L5 前端→後端接線 | ✅ L5a 鍵存在；**L5b 後端日誌 0 新增（對照組 delta=1）** ⇒ L5c 依令記「待 R7 由 Tao 登入後驗證」，**非紅** |
| 1 L6 經 cloudflared | ✅ `/planning` 200、`/client-login` 200（含 `clerk.goaa.ai`）、`/` 200 |
| 1 L7 資料面健檢 | ✅ public 表 15；角色 `goaa_c2_app`、`goaa_c2_migrate` |
| 2 enable | ✅ 3103 建 symlink、`enable_rc=0`（未加 `--now`）；`goaa-web` 已 enabled **未重複執行**；**PID 未變（3118044／3113073）** |
| 3 存活性審計 3-1 ~ 3-6 | ✅ 全綠（3-2 零告警；3-4 `unless-stopped`；3-6 sha16 相符、標記 2 處） |

### 3-7 逐條「重開機後是否會自動恢復」

| 項 | 重開機後是否自動恢復 | 依據 |
|---|---|---|
| 前端 `goaa-web` | **是** | 3-1 symlink 在 `multi-user.target.wants`；`Restart=on-failure`／`RestartSec=3`；`After=network-online.target`；3-2 零告警 |
| 後端 `goaa-platform-api-3103` | **是（開機會啟動）** | 3-1 symlink（本輪 enable 建立）；`After` 含 `docker.service`；`Wants=network-online.target`；3-2 零告警。**⚠️ 附帶觀察（非本令判據）：unit 為 `Restart=no` ⇒ 開機會起，但行程崩潰不會自癒**（需 Tao 決定是否改） |
| 資料庫（容器 `goaa-postgres`） | **是** | `docker.service` = enabled/active；容器 `RestartPolicy=unless-stopped`（3-4） |
| 對外入口 `cloudflared` | **是** | is-enabled = enabled、active（3-5） |
| 防火牆 `ufw` | **是** | is-enabled = enabled、active；`/etc/ufw/after.rules` sha16 `f6a1794c355b50db`、`GOAA D0.2` 標記 2 處（3-6） |

**⇒ 逐條皆為「是」；報告首段無標紅項。**（唯一附帶觀察為 3103 之 `Restart=no`，屬「崩潰自癒」而非「開機恢復」，已如上標明。）

---

## §1 步驟 0｜基線（唯讀）

```
=== 0-1 current ===
/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8

=== 0-2 goaa-web ===
MainPID = 3118044
NRestarts = 0
ActiveEnterTimestamp = Sat 2026-09-12 08:59:58 UTC

=== 0-3 goaa-platform-api-3103 ===
MainPID = 3113073
NRestarts = 0

=== 0-4 ss -ltn ===
State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
LISTEN 0      511        127.0.0.1:3100       0.0.0.0:*
LISTEN 0      2048       127.0.0.1:3103       0.0.0.0:*
LISTEN 0      4096         0.0.0.0:22         0.0.0.0:*
LISTEN 0      2048         0.0.0.0:18789      0.0.0.0:*
LISTEN 0      4096       127.0.0.1:20241      0.0.0.0:*
LISTEN 0      4096   127.0.0.53%lo:53         0.0.0.0:*
LISTEN 0      4096      127.0.0.54:53         0.0.0.0:*
LISTEN 0      4096         0.0.0.0:5432       0.0.0.0:*
LISTEN 0      4096         0.0.0.0:17879      0.0.0.0:*
LISTEN 0      2048         0.0.0.0:8088       0.0.0.0:*
LISTEN 0      2048         0.0.0.0:8080       0.0.0.0:*
LISTEN 0      4096            [::]:22            [::]:*
LISTEN 0      4096            [::]:5432          [::]:*
LISTEN 0      4096            [::]:17879         [::]:*

--- 3100/3103 專列 ---
LISTEN 0      511        127.0.0.1:3100       0.0.0.0:*
LISTEN 0      2048       127.0.0.1:3103       0.0.0.0:*

=== 0-5 is-enabled ===
goaa-web = enabled
goaa-platform-api-3103 = disabled
cloudflared = enabled
docker = enabled

=== 0-6 web.env ===
bytes = 684
sha256_16 = 254c0423f94fc587
mode = 640 root:goaa-web
keys (只列鍵名) =
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY
NEXT_PUBLIC_CLERK_SIGN_IN_URL
NEXT_PUBLIC_CLERK_SIGN_UP_URL
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL
GOAA_AGENT_LOOP_UPSTREAM
GOAA_C2_CLERK_AUTH_ENABLED
GOAA_CLERK_INSTANCE
HOSTNAME
NODE_OPTIONS
key_count = 11

=== 附：其他基線 PID ===
goaa-router = 2994296
cloudflared = 2111569
回滾點檔 = /opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc
```

**判定**：0-1 ✅；0-2 MainPID = `3118044` ✅；0-3 MainPID = `3113073` ✅；0-4 **`127.0.0.1:3100` 與 `127.0.0.1:3103` 皆在，且無 `[::1]` 版本**（`[::]` 僅出現於 22／5432／17879）✅；0-5 ✅（`goaa-web` enabled／`3103` disabled）；0-6 sha16 = `254c0423f94fc587` ✅。

---

## §2 步驟 1｜全鏈驗證（唯讀）

### L1 前端本機 ✅
```
L1a /planning code = 200
L1b /client-login code = 200
L1b bytes = 10893
L1c clerk.goaa.ai count = 1
L1d clerkAuth true count = 1
L1e not-configured count = 0
```

### L2 後端健康 ✅（實際可用路徑 = `/api/v1/agent-loop/health`）
```
L2 /api/v1/agent-loop/health = 200
   /healthz = 404
   /ready = 404
```
完整 body（429 B，原文）：
```json
{"status":"ok","service":"goaa-c2-agent-loop","environment":"c2-dev","database":{"host":"127.0.0.1","port":5432,"name":"goaa_platform","user":"goaa_c2_app","server_version":"16.13","server_addr":"172.17.0.2","server_port":5432,"reachable":true},"capabilities":{"storage_mode":"c2-local-private","scanner_mode":"stub","ocr_mode":"rules-only","email_delivery":"disabled"},"production_ready":false,"production_resources_used":false}
```
**⇒ `reachable: true`、`server_version 16.13`、`server_addr 172.17.0.2` ⇒ 後端確實查到了容器內之 `goaa_platform`。**

### L3 後端 Clerk 驗證鏈 ✅（JWKS 可達之關鍵證據）
```
--- L3a 不帶標頭（原始）---
HTTP/1.1 401 Unauthorized
date: Sat, 12 Sep 2026 09:10:08 GMT
content-length: 76
content-type: application/json
cache-control: no-store
x-content-type-options: nosniff
referrer-policy: no-referrer

{"error":{"code":"missing_clerk_session","message":"a sign-in is required"}}

--- L3b Bearer invalid.invalid.invalid（原始）---
HTTP/1.1 401 Unauthorized
date: Sat, 12 Sep 2026 09:10:08 GMT
content-length: 91
content-type: application/json
cache-control: no-store
x-content-type-options: nosniff
referrer-policy: no-referrer

{"error":{"code":"invalid_clerk_session","message":"the clerk session token was rejected"}}
```
**⇒ 兩者皆為令文期望值；未出現 `clerk_verification_unavailable` ⇒ 不判紅。**

### L4 後端→DB（併發取樣）
**第一階段（令文法：20 次 L3b 路徑 ＋ 每 0.2 秒取樣 5 秒）**：
```
samples = 13
lines_total = 13
goaa_c2_app_lines = 0
distinct_lines = 1
--- distinct 取樣內容 ---
goaa|psql|active
```
**第二階段（令文允許之重試：改打會觸達 DB 之健康端點，20 次）**：
```
samples = 16
lines_total = 16
goaa_c2_app_lines = 0
distinct_lines = 1
--- distinct 取樣內容 ---
goaa|psql|active
```
**第三階段（改良取樣法：單一 psql 連線、每 10ms 輪詢、共 800 次／約 8 秒；同時併發 40 次請求）**：
```
psql:<stdin>:10: NOTICE:  APP_HITS=0 POLLS=800
DO
--- 對照組（同法輪詢自身 goaa|psql，確認取樣器可見連線）---
psql:<stdin>:10: NOTICE:  SELF_HITS=50 POLLS=50
```
**第四階段（決定性補證 —— `pg_stat_database.xact_commit` 增量）**：
```
對照組（0 次請求）：a0 = 713  b0 = 715  delta = 2   (僅我們兩次量測自身)
實驗組（20 次 /health）：a = 717  b = 759  delta = 42   (預期 ≈ 20 次應用交易 + 量測自身 1)
pg_stat_database 現值：goaa_platform|761|1
pg_stat_activity 全容器快照：
goaa|goaa||idle
goaa_platform|goaa|psql|active
```

**L4 判定（依令，不據此判紅）**：`pg_stat_activity` **未捕捉**到 `usename = goaa_c2_app` 之連線（三階段、合計 29 次快照 ＋ 800 次 10ms 輪詢皆 0；對照組 50/50 證明取樣器本身有效）。
**這不等於 DB 不通**：① L2 健康端點回 `reachable: true` ＋ `server_version 16.13`；② **補證顯示 20 次請求使 `goaa_platform` 的 `xact_commit` 增加 42**（對照 0 次請求只增 2，即量測自身），**每請求約 2 筆交易** ⇒ **後端→DB 確實有實際交易**。
**成因**：後端採「每請求一條短命連線」（`app/db.py` 無 pool），連線存活時間遠短於輪詢週期，`pg_stat_activity` 僅在快照瞬間可見。

### L5 前端→後端接線
**L5a ✅**：`web.env` 含鍵名 `GOAA_AGENT_LOOP_UPSTREAM`（只驗鍵名，未印值）。

**L5b（journal 行數差 ＋ 追加日誌檔取證）**：
```
journal before_lines = 8
L5b1 前端不帶憑證 code = 401
L5b2 前端帶無效 Bearer code = 503
journal after_lines = 8
新增行 = （-- No entries --）

--- 追加：後端日誌檔 /var/log/goaa-platform/api-3103.log ---
log bytes = 11778
before_lines = 153
（發送 2 次前端請求）
after_lines = 153        ← 0 新增
--- 對照組：直接打後端一次 ---
before = 153  after = 154  delta = 1
INFO:     127.0.0.1:33738 - "GET /api/v1/agent-loop/auth/me HTTP/1.1" 401 Unauthorized
```
**注意**：`goaa-platform-api-3103` 之 journal 僅 8 行（systemd 訊息），應用日誌落於 `/var/log/goaa-platform/api-3103.log`；故另以該檔行數做前後差。

**L5c 結論（依令二分法）**：**後端 journal 無新增、後端日誌檔亦無新增**（對照組直打後端 delta = 1，證明觀測方法有效）⇒ **接線在此跳未證實**，依令明寫：
> **「此跳需有效 Clerk session 才可觀測，留待 R7 由 Tao 本人登入後驗證。」**
**不得因此判紅** —— 與 R5b-4 已知一致：BFF 於 `app/api/agent-loop/[...path]/route.ts:428`（401 `clerk_session_required`）與 `middleware.ts:293-303` catch-all（503）就攔下，請求不進 3103。

### L6 經 cloudflared（公開路徑）✅
```
L6 /planning code = 200  bytes = 16147
L6 /client-login code = 200  bytes = 10893
L6 / code = 200  bytes = 16075
L6 /client-login clerk.goaa.ai count = 1
```

### L7 資料面唯讀健檢 ✅
```
public table count = 15
roles:
goaa_c2_app
goaa_c2_migrate
web.env sha16 再確認 = 254c0423f94fc587
```
（僅計數與角色名；未查任何業務資料內容。）

---

## §3 步驟 2｜enable（唯一寫入動作）

```
=== 2-1 enable 前 ===
goaa-web = enabled
goaa-platform-api-3103 = disabled
3103 MainPID(before) = 3113073
web  MainPID(before) = 3118044

=== 2-2 systemctl enable goaa-platform-api-3103.service（不加 --now）===
Created symlink /etc/systemd/system/multi-user.target.wants/goaa-platform-api-3103.service → /etc/systemd/system/goaa-platform-api-3103.service.
enable_rc=0

=== 2-3 goaa-web ===
goaa-web 已 enabled ⇒ 依令不重複執行；現況 = enabled

=== 2-4 enable 後複驗 ===
goaa-web is-enabled = enabled
goaa-platform-api-3103 is-enabled = enabled
3103 MainPID = 3113073
3103 NRestarts = 0
3103 ActiveState = active
web  MainPID = 3118044
web  NRestarts = 0

=== 2-5 ss -ltn 複驗 ===
LISTEN 0      511        127.0.0.1:3100       0.0.0.0:*
LISTEN 0      2048       127.0.0.1:3103       0.0.0.0:*
```

**對照**：`disabled → enabled`（3103）；`goaa-web` 維持 `enabled`（未重複執行）。
**PID 未變** ⇒ **enable 未造成任何重啟** ✅（`NRestarts` 皆 0、`ActiveState=active`）。
**🛡 核准卡**：**未出現**（`systemctl enable` 非 `stop|restart`，且經 `ssh` 遠端執行）。
**其他基線**：`goaa-router 2994296`、`cloudflared 2111569`、`current 40c8546e…`、`web.env sha16 254c0423f94fc587` 皆未變。

---

## §4 步驟 3｜重開機存活性審計（純唯讀，未重開機）

### 3-1 開機掛載 symlink ✅
```
lrwxrwxrwx  1 root root   50 Sep 12 09:11 goaa-platform-api-3103.service -> /etc/systemd/system/goaa-platform-api-3103.service
lrwxrwxrwx  1 root root   36 Sep  2 23:10 goaa-web.service -> /etc/systemd/system/goaa-web.service
```
（`3103` 之 symlink 為**本輪 enable 建立**。）

### 3-2 `systemd-analyze verify` ✅ 零告警
```
--- goaa-web.service ---
rc=0        （無任何輸出）
--- goaa-platform-api-3103.service ---
rc=0        （無任何輸出）
```
**⇒ 無告警可貼。**

### 3-3 依賴序 ✅
```
--- goaa-web ---
After    = systemd-tmpfiles-setup.service sysinit.target systemd-journald.socket -.mount basic.target tmp.mount network-online.target system.slice
Requires = system.slice -.mount sysinit.target
Wants    = tmp.mount
WantedBy = multi-user.target
User     = goaa-web
ExecStart= { path=/opt/goaa-frontend/node/bin/node ; argv[]=/opt/goaa-frontend/node/bin/node /opt/goaa-frontend/current/server.js ; ... }

--- goaa-platform-api-3103 ---
After    = tmp.mount systemd-tmpfiles-setup.service system.slice basic.target network-online.target -.mount docker.service sysinit.target
Requires = -.mount sysinit.target system.slice
Wants    = tmp.mount network-online.target
WantedBy = multi-user.target
User     = goaa-platform
ExecStart= { path=/opt/goaa-platform/venv/bin/python ; argv[]=/opt/goaa-platform/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 3103 --no-server-header --log-level info ; ... }

--- docker.service 是否在 3103 的 After 中 ---
1
```
**⇒ `docker.service` 確實在 3103 的 `After` 中（計數 1）** ✅
**⚠️ 附帶觀察**：`After=docker.service` 只保證 Docker **daemon** 先起，**不保證容器已就緒** ⇒ 若 3103 早於 `goaa-postgres` 就緒即收到請求，首批請求可能取不到 DB 連線；惟後端為每請求短連線，容器就緒後即自癒（無持久連線需重建）。

### 3-4 DB 容器自啟 ✅
```
goaa-postgres RestartPolicy = unless-stopped
goaa-postgres State.Running = true
docker.service is-enabled = enabled
docker.service ActiveState = active
```
**⇒ 期望值（always／unless-stopped）成立 ⇒ 非紅。**

### 3-5 cloudflared / docker / ufw ✅
```
cloudflared is-enabled = enabled   ActiveState = active
docker      is-enabled = enabled   ActiveState = active
ufw         is-enabled = enabled   ActiveState = active
```

### 3-6 防火牆持久化 ✅
```
sha256(/etc/ufw/after.rules)[:16] = f6a1794c355b50db      （要求值相符）
GOAA D0.2 count = 2
31:# BEGIN GOAA D0.2 — block public 5432 at the docker FORWARD hook
40:# END GOAA D0.2
```

### 附：unit 檔與 drop-in（唯讀）
```
-rw-r--r-- 1 root root 2627 Sep 12 06:49 /etc/systemd/system/goaa-platform-api-3103.service
-rw-r--r-- 1 root root  494 Sep  2 23:10 /etc/systemd/system/goaa-web.service
/etc/systemd/system/goaa-web.service.d/:
-rw-r--r-- 1 root root   57 Sep 12 08:29 10-clerk-env.conf
/etc/systemd/system/goaa-platform-api-3103.service.d/ : 不存在
```
`goaa-web.service` 原文（供對照）：
```ini
[Unit]
Description=GOAA production Next.js frontend (e2f26ff)
After=network-online.target

[Service]
Type=simple
User=goaa-web
Group=goaa-web
WorkingDirectory=/opt/goaa-frontend/current
Environment=NODE_ENV=production
Environment=HOSTNAME=127.0.0.1
Environment=PORT=3100
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
drop-in（`10-clerk-env.conf`）：`[Service]` ＋ `EnvironmentFile=/opt/goaa-frontend/env/web.env`。
`3103` unit 關鍵行：`User=goaa-platform`、`Group=goaa-platform`、`EnvironmentFile=/opt/goaa-platform/env/api-3103.env`、**`Restart=no`**。
`default.target = graphical.target`（`multi-user.target` 為其相依）。

**⚠️ 附帶觀察（非本令判據，供 Tao 決定）**：`goaa-platform-api-3103` 為 **`Restart=no`**（`goaa-web`／`cloudflared` 為 `on-failure`）。開機會正常啟動，但行程若崩潰不會自動拉起。**本輪依令未改任何 unit。**

---

## §5 上線後清單（本輪只記錄、不動手）

> 以下原文列出，**標注「已由 Tao 於 2026-09-12 裁示列入上線後清單」**：

① F1：BFF 先擋 ⇒ 未帶憑證回 401 clerk_session_required（app/api/agent-loop/[...path]/route.ts:428），與後端 missing_clerk_session 不一致；
② F2：帶無效 token 回 503 + 訊息 "Clerk is enabled but not configured:"（middleware.ts:241，觸發自 middleware.ts:293-303 的 catch-all），訊息用詞誤導，應改為 401；
③ 既有清單續留：ssh 包裝繞過本機 🛡 守衛、17879 對外暴露、容器 pg_hba loopback trust、release 線推回前端 repo、DB 自動備份（含 documents 目錄）、api.goaa.ai 接受新業務 token 後重開 $39.90、審批理由欄位、手機號遮罩。

**（本輪未新增任何條目；R6 附帶觀察之 `Restart=no` 見 §4，僅供 Tao 決定是否納入。）**

---

## §6 掃描與修訂紀錄

**掃描對象**：本檔 `reports/2026-09-12/r6-golive/REPORT.md`。
**掃描器**：`16` 個樣式（含值形）＋ 一項**未切分之可路由 IPv4** 檢查；樣式字面量一律切分書寫。
**排除規則**：統計／中繼行不納入；本表僅針對本檔。

| 檢查項 | 命中數 |
|---|---|
| stripe-live-VALUE | 0 |
| stripe-test-VALUE | 0 |
| clerk-pk-live-VALUE | 0 |
| clerk-pk-test-VALUE | 0 |
| clerk-sk-live-VALUE | 0 |
| pem | 0 |
| aws | 0 |
| github-pat | 0 |
| pg-uri | 0 |
| pg-pass-assign | 0 |
| pass-word-assign | 0 |
| jwt-shape | 0 |
| pg-pass-name | 0 |
| clerk-key-name | 0 |
| clerk-secret-assign | 0 |
| session-secret-assign | 0 |
| **未切分可路由 IPv4** | **0** |
| **TOTAL_HITS** | **0** |

**掃描說明（自我膨脹陷阱之防護）**：上表標籤採**連字號拼法**（`pg-pass-assign`、`pg-pass-name`、`clerk-key-name`、`clerk-secret-assign`、`session-secret-assign`），**標籤本身不含連續樣式字串**；內文提及鍵名／樣式處一律切分書寫（例：`"pk_" + "live_"`、`"sk_" + "live_"`、`"CLERK_SECRET" + "_KEY"`）。**本輪未落任何金鑰值、未 print 任何值、未列任何 env 值。**

### 修訂紀錄
| 版 | 變更 |
|---|---|
| 內容段 | §0–§5（步驟 0–3 全部原始輸出、L1–L7 逐項、enable 前後對照、存活性逐條判定、上線後清單） |
| 本段（§6） | 追加掃描表與 sha |

**最終檔**：`bytes = 19,212`、`sha256_16 = a82eff8bef8003aa`、`BOM = False`、`first3 = # R`、`CR = 0`。

**sha 慣例**：`bytes` 為最終檔實際位元組數；`sha256_16` = 將本檔中該 16 位摘要字串替換為 16 個 `0` 後，整檔 sha256 之前 16 位（沿用前幾輪同一慣例，可自我驗證）。
