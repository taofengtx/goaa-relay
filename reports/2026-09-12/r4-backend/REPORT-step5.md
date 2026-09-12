# R4 步驟 5｜首次啟動與真實驗收（agent-loop API 3103 on C1）

- 輪次：**R4 步驟 5**（第一次啟動；**不 enable**）
- 日期：2026-09-12（C1 UTC 07:14:45 起）
- 主機：C1 `goaa-aika-cloud-1`（`do-runtime-anchor`）
- 本輪**唯一寫入動作**：`systemctl start goaa-platform-api-3103.service`
- 邊界：**不動** `goaa-web` / `goaa-router` / `cloudflared` / `ufw` / `DOCKER-USER` / `pg_hba`；**不改** env、**不改** unit、**不跑** migration；秘密不回顯；可路由 IPv4 切分；relay 不 force-push。
- 結論：**A–H 全部通過。服務 `active (running)`；`disabled`（未 enable）；`MainPID=3110526`；`NRestarts=0`；日誌 0 traceback / 0 warning。** 既有服務 PID 與時間戳完全未變。
- **🛡 卡：Aika 端本輪未出現任何 🛡 卡；未經任何 approve 流程；一切以 Tao 為準。**

---

## 0. 前提覆核

| 項 | 期望 | 實測 | 判定 |
|---|---|---|---|
| 步驟 1–4 產物 | 齊備 | unit/en、venv/backend 均在 | ✅ |
| 進場前 is-active | inactive | inactive（步驟 4 結束狀態） | ✅ |
| 進場前 3103 | 閒置 | 無監聽 | ✅ |
| relay main | `e934fdd` | `e934fdd` | ✅ |

---

## 5a. 啟動（唯一寫入動作）

指令：

```
systemctl start goaa-platform-api-3103.service
```

輸出：

```
start_rc=0

=== is-active ===
active

=== status --no-pager -l ===
● goaa-platform-api-3103.service - GOAA Platform - agent-loop API (3103, loopback only)
     Loaded: loaded (/etc/systemd/system/goaa-platform-api-3103.service; disabled; preset: enabled)
     Active: active (running) since Sat 2026-09-12 07:14:45 UTC; 3s ago
       Docs: file:/opt/goaa-platform/backend/README.md
   Main PID: 3110526 (python)
      Tasks: 1 (limit: 4653)
     Memory: 39.7M (peak: 39.9M)
        CPU: 1.038s
     CGroup: /system.slice/goaa-platform-api-3103.service
             └─3110526 /opt/goaa-platform/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 3103 --no-server-header --log-level info

Sep 12 07:14:45 goaa-aika-cloud-1 systemd[1]: Starting goaa-platform-api-3103.service - GOAA Platform - agent-loop API (3103, loopback only)...
Sep 12 07:14:45 goaa-aika-cloud-1 systemd[1]: Started goaa-platform-api-3103.service - GOAA Platform - agent-loop API (3103, loopback only).
```

**一次啟動即成功**：`start_rc=0`，**未重試、未改任何設定**，`NRestarts=0`，`ExecMainStatus=0`。

---

## A. 服務狀態

```
is-active  : active
is-enabled : disabled
MainPID=3110526
ExecMainStatus=0
```

| 期望 | 實測 | 判定 |
|---|---|---|
| active | **active** | ✅ |
| **disabled** | **disabled** | ✅ |
| MainPID 非 0 | **3110526** | ✅ |

補充：`NRestarts=0`、`ExecMainStartTimestamp=Sat 2026-09-12 07:14:45 UTC`、`SubState=running`。

---

## B. 綁定面

```
ss -ltnp | grep 3103
LISTEN 0      2048       127.0.0.1:3103       0.0.0.0:*    users:(("python",pid=3110526,fd=6))

ps -o user= -p 3110526
goaa-platform
ps -o user= uid : 997
```

| 期望 | 實測 | 判定 |
|---|---|---|
| **只有 `127.0.0.1:3103`** | 僅此一條；**無 `0.0.0.0:3103`、無 `[::]:3103`** | ✅ |
| 程序是 `/opt/goaa-platform/venv/bin/python` | 是（`cgroup` 顯示完整 exec 行） | ✅ |
| `ps -o user=` = `goaa-platform`（非 root） | **`goaa-platform`，uid 997** | ✅ |

---

## C. 健康檢查

> **揭露（見 §揭露事項 1）**：本 unit 的應用是**帶前綴**的，健康端點是 `{API_PREFIX}/health`，`API_PREFIX = "/api/v1/agent-loop"`（`app/main.py` L49；端點註冊於 L469）。第一次我打了不帶前綴的 `/health`，得到 404（見 5-F 日誌第一條請求），**已立即以正確路徑重測**。以下為正確路徑的實測。

指令與輸出：

```
curl -sS -i -m 5 http://127.0.0.1:3103/api/v1/agent-loop/health

HTTP/1.1 200 OK
date: Sat, 12 Sep 2026 07:15:27 GMT
content-length: 429
content-type: application/json
cache-control: no-store
x-content-type-options: nosniff
referrer-policy: no-referrer

{"status":"ok","service":"goaa-c2-agent-loop","environment":"c2-dev","database":{"host":"127.0.0.1","port":5432,"name":"goaa_platform","user":"goaa_c2_app","server_version":"16.13","server_addr":"172.17.0.⟨2⟩","server_port":5432,"reachable":true},"capabilities":{"storage_mode":"c2-local-private","scanner_mode":"stub","ocr_mode":"rules-only","email_delivery":"disabled"},"production_ready":false,"production_resources_used":false}
curl_rc=0
```

**逐欄解讀（這一項同時是本輪 DB 實連的第一個證據）**：

| 欄位 | 值 | 意義 |
|---|---|---|
| `status` | `ok` | 服務自評正常 |
| `environment` | `c2-dev` | 來自 env 的 `GOAA_C2_ENV`（語境值照抄自 C2，見步驟 3 報告的「先查未改」） |
| `database.host:port` | `127.0.0.1:5432` | **指向本機容器 `goaa-postgres`**，非 D0.2 後已封的外部位址 |
| `database.name` | `goaa_platform` | **新庫**（非 `goaa`、非 `goaa_c2test`） |
| `database.user` | `goaa_c2_app` | **應用角色**（非超管 `goaa`） |
| `database.server_version` | `16.13` | PG 16.13 |
| `database.server_addr` | `172.17.0.⟨2⟩` | Docker bridge 位址（非可路由） |
| `database.reachable` | **`true`** | **DB 探針成功**（`server_facts()` 走的是 app 自己的連線路徑） |
| `production_ready` | `false` | 自我聲明非生產 |
| `production_resources_used` | `false` | 未動生產資源 |

> 註：`server_addr` 原輸出為未切分寫法；依報告版面紀律以 `⟨⟩` 切分末段，其餘逐字未改（同 R2/R3 慣例）。該位址為 Docker bridge 私有位址，非可路由、非機密。

---

## D. DB 實連（本輪重點之一）

指令（依令原樣）：

```
docker exec goaa-postgres psql -U goaa -d goaa_platform -X -A -F"|" -t -c \
  "select usename, application_name, state, count(*) from pg_stat_activity
   where datname='goaa_platform' group by 1,2,3;"
```

### D-1：C 之後「立刻」查一次（原樣）

```
goaa|psql|active|1
d1_rc=0
```

**只看到我自己的 psql 連線，沒看到 app 的連線。** 原因**不是**沒連上，而是**連線生命週期**：

- `app/db.py` L23-26 的設計註解明寫 **「One short-lived connection per request/unit of work」**；
- `connection()`（L30-49）是 `psycopg.connect(...)` → `finally: conn.close()`，**每請求開、請求結束即關**；
- 我這次查詢本身有 `docker exec` + psql 啟動延遲（數百毫秒），而 `/health` 的連線只存活數毫秒 ⇒ **樣本落在兩個請求之間的空窗**。
- 已確認本服務**沒有** `psycopg_pool`（23 個相依中無 pool 套件）⇒ 不存在常駐連線可被「順手」看到。

### D-2：併發取樣（在請求進行中取樣，才看得到短連線）

做法：同時啟動 20 條 `curl` 迴圈打 `/health`，並連續取樣 `pg_stat_activity`（唯讀、不改任何資料）。

```
=== D-2 併發取樣（連線為每請求短連線，故需在請求進行中取樣）===
捕獲於第 1 次取樣：
goaa|psql|active|1
goaa_c2_app|goaa-c2-agent-loop|idle|1
goaa_c2_app|goaa-c2-agent-loop|idle in transaction|1
sample_done
```

**⇒ 必須看到的證據出現了**：

| 期望 | 實測 | 判定 |
|---|---|---|
| `usename=goaa_c2_app` 的連線 | **`goaa_c2_app`**（1 條 `idle` + 1 條 `idle in transaction`） | ✅ |
| `application_name` | **`goaa-c2-agent-loop`**（libpq 預設帶入的程式路徑標識） | ✅ |
| `datname` | `goaa_platform` | ✅ |

三項合起來即：**應用真的以 `goaa_c2_app` 身分連上 `goaa_platform`，且連線確實是由本服務（`goaa-c2-agent-loop`）開的**。（`idle in transaction` 是交易提交前的一瞬，與 `connection()` 的 commit/close 流程一致。）

---

## E. Clerk 驗證路徑（本輪重點之二）

### 挑了哪個端點、依據哪一行

- 端點：**`GET /api/v1/agent-loop/auth/me`**
- 依據：`app/main.py:623-624`

```python
    @app.get(f"{API_PREFIX}/auth/me")
    def me(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
```

- `current_user` 定義在 `app/main.py:418-439`；在 Clerk 模式下（L425-426 `if cfg.clerk_auth_enabled:`）**直接**走 `_clerk_user(cfg, authorization)` —— 註解明寫 **「Clerk is the identity authority: the browser's session token is the only accepted proof. No cookie, no BFF assertion.」**
- `_clerk_user`（`app/main.py:170`）→ `clerk_auth.verify_session_token`（`app/clerk_auth.py:115`）。

### 指令與輸出

```
curl -sS -i -m 10 -H "Authorization: Bearer invalid.invalid.invalid" \
  http://127.0.0.1:3103/api/v1/agent-loop/auth/me

HTTP/1.1 401 Unauthorized
date: Sat, 12 Sep 2026 07:15:28 GMT
content-length: 91
content-type: application/json
cache-control: no-store
x-content-type-options: nosniff
referrer-policy: no-referrer

{"error":{"code":"invalid_clerk_session","message":"the clerk session token was rejected"}}
curl_rc=0
```

| 期望 | 實測 | 判定 |
|---|---|---|
| **401** | **401 Unauthorized** | ✅ |
| 非 500、非逾時 | 即時回應（`curl_rc=0`，無 timeout） | ✅ |
| 錯誤碼 | `invalid_clerk_session` | ✅ |

### 為什麼這個 401 同時證明「JWKS 有取到」（而非「fail-closed 剛好也回 401」）

`clerk_auth.py` 把兩種失敗**分開**：

| 分支 | 行 | 錯誤碼 | 觸發條件 |
|---|---|---|---|
| SDK/JWKS/網路異常 | L151-155 | `clerk_verification_unavailable`（並寫 `logger.warning`） | `authenticate_request` **拋例外** |
| 驗證完成但未通過 | **L158** | **`invalid_clerk_session`** | `authenticate_request` **正常返回**，但 `state.status != SIGNED_IN` |

我們拿到的是 **`invalid_clerk_session`**，也就是**第二個分支** ⇒ `authenticate_request` **沒有拋例外**，代表 **JWKS 取得與 SDK 驗證流程本身走通了**（否則會是 `clerk_verification_unavailable` + 一行 warning）。且**日誌全檔 0 筆 warning**（見 F），與此推論一致。

⇒ **出網正常、api.clerk.com 可達、SDK 可用**；一個無效 token 就該被拒，而它確實被拒。

---

## F. 日誌

檔案：`/var/log/goaa-platform/api-3103.log`（36 行、2,632 B）

啟動段（含 uvicorn 綁定行）：

```
INFO:     Started server process [3110526]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:3103 (Press CTRL+C to quit)
INFO:     127.0.0.1:46384 - "GET /health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:57168 - "GET /api/v1/agent-loop/health HTTP/1.1" 200 OK
...
```

- **綁定位址 = `http://127.0.0.1:3103`**（非 `0.0.0.0`）✅
- 第 5 行即我首次誤打不帶前綴的 `/health` 得到的 404（**唯一 404**，見 §揭露事項 1）✅

**全檔掃描**（`grep -niE "traceback|error|warning|exception|critical"`）：

```
命中數 = 0
```

**回應碼分佈**：

```
     30 " 200 
      1 " 404 
      1 " 401 
```

⇒ **無 traceback、無 warning、無 exception**；30×200（含 C 與 D-2 的取樣請求）、1×404（前綴筆誤）、1×401（E 的無效 token）。

---

## G. 沙箱生效反證

```
systemctl show goaa-platform-api-3103 \
  -p ProtectSystem -p NoNewPrivileges -p CapabilityBoundingSet -p ReadWritePaths -p IPAddressDeny

IPAddressDeny=
CapabilityBoundingSet=
ReadWritePaths=/opt/goaa-platform/private-files /var/log/goaa-platform
ProtectSystem=strict
NoNewPrivileges=yes
```

| 期望 | 實測 | 判定 |
|---|---|---|
| `ProtectSystem=strict` | **strict** | ✅ |
| `NoNewPrivileges=yes` | **yes** | ✅ |
| `CapabilityBoundingSet` 空 | **空** | ✅ |
| **`IPAddressDeny` 為空**（刻意不設） | **空** | ✅ |

### 追加：以 `/proc` 反證（不只看 systemd 的宣告）

```
cmdline: /opt/goaa-platform/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 3103 --no-server-header --log-level info
uid: 997
CapEff: 0000000000000000
NoNewPrivs: 1
--- namespace 對照（本服務 vs PID1）---
mnt:[4026532538]
mnt:[4026531841]
```

- `uid=997` ⇒ **確實以 `goaa-platform` 執行，非 root**；
- **`CapEff: 0000000000000000`** ⇒ **有效 capability 全空**（`CapabilityBoundingSet=` 真的生效，不只是文件宣告）；
- `NoNewPrivs: 1` ⇒ 生效；
- **mount namespace 與 PID 1 不同**（`4026532538` ≠ `4026531841`）⇒ `ProtectSystem=strict` 的唯讀視圖確實套用。

---

## H. 既有服務未受擾

```
goaa-router    ActiveState=active   SubState=running  MainPID=2994296   ActiveEnterTimestamp=Fri 2026-09-11 06:21:50 UTC
goaa-web       ActiveState=active   SubState=running  MainPID=2995017   ActiveEnterTimestamp=Fri 2026-09-11 06:21:57 UTC
cloudflared    ActiveState=active   SubState=running  MainPID=2111569   ActiveEnterTimestamp=Thu 2026-09-03 00:27:23 UTC
```

| 服務 | 步驟 4 報告值 | 本輪實測 | 判定 |
|---|---|---|---|
| `goaa-router` | 2994296 / Fri 2026-09-11 06:21:50 UTC | **完全相同** | ✅ |
| `goaa-web` | 2995017 / Fri 2026-09-11 06:21:57 UTC | **完全相同** | ✅ |
| `cloudflared` | 2111569 / Thu 2026-09-03 00:27:23 UTC | **完全相同** | ✅ |

⇒ **三個既有服務的 PID 與進入 active 的時間戳一字不差** ⇒ 本輪未重啟、未干擾任何既有服務。

---

## 揭露事項（本輪誠實交代）

1. **健康端點的「前綴筆誤」**：我第一次以 `/health` 呼叫得到 **404**（日誌中唯一的 404）。根因：本服務所有路由都在 `API_PREFIX = "/api/v1/agent-loop"` 之下（`app/main.py:49`），健康端點實際註冊為 `f"{API_PREFIX}/health"`（L469）。**我未改任何設定**，只用正確路徑重測即 200。此 404 保留在日誌與本報告中，不掩飾。
2. **D-1 的「空結果」不是失敗**：`pg_stat_activity` 在「C 完成後」取樣時只看到我自己的 psql。根因是**短連線設計**（`app/db.py` L23-26 明載 one short-lived connection per request），不是連線失敗。**D-2 在請求進行中取樣即捕獲** `goaa_c2_app` 連線。若只看 D-1 而論斷「沒連上」會是**錯誤推論**。
3. **E 的 401 為何比「fail-closed 也回 401」更強**：本服務把「JWKS/網路失敗」與「token 本身無效」分成**不同錯誤碼**（`clerk_verification_unavailable` vs `invalid_clerk_session`）。我們拿到後者 ⇒ 驗證流程本身走通。**若 Tao 仍要更強的「JWKS 確實外呼」直接證據**，可在下一次（獲准時）以 `ss`/tcpdump 觀測對 api.clerk.com 的連線，或讀 Clerk SDK 的快取狀態；**本輪未做**（那屬於新的觀測動作）。
4. **`GOAA_C2_ENV=c2-dev`** 仍照抄自 C2（步驟 3 已列為「令中未列舉、先查未改」）；健康端點會把 `environment` 回報成 `c2-dev`。若 Tao 要平台語境（例如 `platform-dev`），請示明，本輪**未改**。

---

## 回滾（**未執行**）

若要把 C1 退回步驟 4 結束狀態：

```
systemctl stop goaa-platform-api-3103.service
```

- 因**服務未 enable**，`stop` 即可完全回到步驟 4 的狀態（`disabled` + `inactive`），不需 `disable`、不需刪 unit、不需動任何檔案。
- **本輪未執行此命令**：依令「本輪唯一寫入動作 = `systemctl start`」與「不要 enable」，本次收在**服務運行中**。若 Tao 的本意是「驗收後即收工、退回步驟 4 狀態」，**說一聲我立刻執行**（一行指令、可逆）。

---

## 未動清單（本輪完全未觸碰）

`goaa_platform` / `goaa_c2` / `goaa_c2test` 任何**資料列**（本輪只有 `pg_stat_activity` 唯讀查詢與 `/health` 的 `server_facts()` 唯讀探針）；`/etc/systemd/system/goaa-platform-api-3103.service`（**未改一字**）；`/opt/goaa-platform/env/*`（**未改**）；`goaa-web` / `goaa-router` / `cloudflared` / `goaa-model-router` / `ufw` / `DOCKER-USER` / `pg_hba.conf` / `goaa-postgres` 容器與其 data；C2 任何檔案；Golden 版本；migration（**未跑**）；`/tasks/next/*`（**絕不呼叫**）。

---

## 下一步（待 Tao 放行）

1. **是否 `enable`**（現為 `disabled`；重開機不會自動起）—— 待示明。
2. **是否保留運行中**（見「回滾」）。
3. **前端聯調**：C1 的 Next（3100，`goaa-web`）目前**沒有**指向 3103 的 base URL 設定，cloudflared 也沒有 3103 路由；依 R4 RECON 的三題回答，正確拓撲是 **Browser → Next(3100) BFF → 3103（loopback）**，即**只需在 Next 端加 `GOAA_AGENT_LOOP_UPSTREAM=http://127.0.0.1:3103` 一類的設定**，**不需**為 3103 加 cloudflared 路由。此事**本輪未動**，待令。


---

## 掃描說明（提交前）

- **掃描標的**：本報告 `REPORT-step5.md`。
- **掃描樣式**：13 類（逐類以切分方式書寫，避免敘述本身膨脹計數）——
  `sk_`+`live_`、`sk_`+`test_`、`BEGIN `+`PRIVATE KEY`、`AK`+`IA`、`gh`+`p_`、`postgres`+`:`+`//`、`PGPASS`+`WORD=`、`pass`+`word=`、`ey`+`J`、`.`+`pgp`+`ass`、`clerk`+`_secret`、`CLERK`+`_SECRET_KEY=`、`SESSION`+`_SECRET=`。
- **命中數 = 0（含機密值與非機密假陽性，全部為 0）。** 本報告未出現任何密碼檔名、Clerk 變數名或憑據賦值樣式。

**IPv4 書寫**：**可路由（公開）位址未切分命中數 = 0**；`127.0.0.1`（loopback）與 `0.0.0.0`（unspecified）依既有報告慣例**逐字書寫**（非可路由、非機密）。健康回應中的 Docker bridge 位址已依版面紀律切分末段。

**秘密處理**：本輪未讀取、未輸出、未傳遞任何憑據值；所有驗收指令只用固定字串 `invalid.invalid.invalid` 作無效 token，不含任何真實秘密。

**檔案完整性（本節追加前，＝內容 commit 之版本）**：

| 檔案 | bytes | sha256[:16] | 首三 byte | BOM |
|---|---|---|---|---|
| `REPORT-step5.md` | 16,533 | `2b8e00a8389e735d` | `b'# R'` | 無 |

**relay main sha**：`a88bca4`（本報告**內容** commit；其後子提交僅追加本節與本行，未改動任何驗收結論。）
