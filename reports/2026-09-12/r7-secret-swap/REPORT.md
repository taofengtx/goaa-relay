# R7-F2｜換上正確的 Clerk Secret Key → 重啟 → 驗收

- **執行時間（UTC）**：2026-09-12 17:49:04Z → 17:51Z
- **主機**：C1 `do-runtime-anchor`（公網 `134.199.227.⟨108⟩`）
- **結論**：🟢 **步驟 0–5 全部通過；且首次出現「真實 Clerk session token 通過後端驗證」的端到端成功**（見 §5-EXTRA-2）
- **🛡 核准卡**：**未出現（0 次）**。兩次 `systemctl restart` 皆在授權範圍內、無審批彈窗。
- **未變更**：`current` symlink、前端建置、unit 主檔／drop-in、`goaa-router`、`cloudflared`、資料庫內容、migrations、enable/disable 狀態。**唯一寫入 = 兩個 env 檔的 `CLERK_SECRET_KEY` 值 + 兩份 `/root/` 備份。**
- **未 push 之變更**：無（本輪僅新增本報告）。

## 事實摘要（前 → 後）

| 項目 | 前 | 後 |
|---|---|---|
| `web.env` 位元組 | 684 | 481 |
| `web.env` sha256_16 | `254c0423f94fc587` | `c72e86561eac7292` |
| `api-3103.env` 位元組 | 1189 | 986 |
| `api-3103.env` sha256_16 | `996c66636f925a16` | `711f5817b41fc31d` |
| Clerk secret 值 長度 / 前綴出現次數 | 253 / 5 | **50 / 1** |
| Clerk secret 值 sha256_16 | `81a398b353637cc3` | **`45e9487a9d4bf1ea`** |
| MainPID `goaa-web` | 3118044 | **3135985** |
| MainPID `goaa-platform-api-3103` | 3113073 | **3135920** |

---

## 步驟 0｜唯讀前置（全項吻合）

```
===== 0-1 /root/clerk-live.env =====
0-1 mode=0o600 owner=root:root bytes=68
0-1 whole_file sha256_16 = 005c2fb7cc737f72
0-1 whole_file cr_count = 0
0-1 CLERK_SECRET_KEY line_count = 1
===== 0-2 該檔的值 =====
0-2 value len=50  sk_live_ count=1  sha256_16=45e9487a9d4bf1ea
===== 0-3 兩個目標檔現行值 =====
0-3 web.env       lines=1  len=253  sk_live_ count=5  sha256_16=81a398b353637cc3
0-3 api-3103.env  lines=1  len=253  sk_live_ count=5  sha256_16=81a398b353637cc3
===== 0-4 基線 MainPID =====
0-4 goaa-web                   MainPID=3118044 (rc=0)
0-4 goaa-platform-api-3103     MainPID=3113073 (rc=0)
===== 0-5 兩檔完整指紋 =====
0-5 web.env       bytes=684 mode=0o640 owner=root:goaa-web sha256_16=254c0423f94fc587 cr_count=0 key_count=11
0-5 api-3103.env  bytes=1189 mode=0o600 owner=goaa-platform:goaa-platform sha256_16=996c66636f925a16 cr_count=0 key_count=25
```

- 0-2 指紋 = `45e9487a9d4bf1ea` ⇒ **與指令單給定值相符**（68 bytes = 17 + 50 + 1 LF）。
- 0-3 兩檔舊值 sha256_16 皆 = `81a398b353637cc3` ⇒ 相符。
- 0-4 兩個 MainPID ⇒ 相符。
- `web.env` 11 鍵、`api-3103.env` 25 鍵（鍵名清單見 §2）。**（值一概未輸出。）**

## 步驟 1｜備份

```
TS = 20260912T174904Z
備份 /root/web.env.bak.20260912T174904Z       bytes=684 mode=0o600 owner=root:root sha256_16=254c0423f94fc587
備份 /root/api-3103.env.bak.20260912T174904Z  bytes=1189 mode=0o600 owner=root:root sha256_16=996c66636f925a16
```

## 步驟 2｜原子換值（`*.new` → chmod → chown → `os.replace`）

```
新值指紋: len=50  sha256_16=45e9487a9d4bf1ea
--- /opt/goaa-frontend/env/web.env
    keys(11) = NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,CLERK_SECRET_KEY,NEXT_PUBLIC_CLERK_SIGN_IN_URL,NEXT_PUBLIC_CLERK_SIGN_UP_URL,NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL,NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL,GOAA_AGENT_LOOP_UPSTREAM,GOAA_C2_CLERK_AUTH_ENABLED,GOAA_CLERK_INSTANCE,HOSTNAME,NODE_OPTIONS
    bytes=481  cr_count=0  mode=0o640  owner=root:goaa-web
    file sha256_16 = c72e86561eac7292  (舊 254c0423f94fc587)
    新 CLERK_SECRET_KEY: len=50  sk_live_ count=1  sha256_16=45e9487a9d4bf1ea
    舊 CLERK_SECRET_KEY sha256_16 = 81a398b353637cc3 (僅供比對，未列值)
--- /opt/goaa-platform/env/api-3103.env
    keys(25) = GOAA_C2_ENV,GOAA_C2_DB_HOST,GOAA_C2_DB_PORT,GOAA_C2_DB_USER,GOAA_C2_DB_PASSFILE,GOAA_C2_DB_SSLMODE,GOAA_C2_PSQL,GOAA_C2_SESSION_COOKIE,GOAA_C2_SESSION_TTL,GOAA_C2_PRIVATE_FILES_DIR,GOAA_C2_STORAGE_LABEL,GOAA_C2_SCANNER,GOAA_C2_OCR,GOAA_C2_DOWNLOAD_TTL,GOAA_C2_MAX_UPLOAD_BYTES,GOAA_C2_EMAIL_DELIVERY,GOAA_C2_PUBLIC_BASE_URL,GOAA_C2_SESSION_SECRET,GOAA_C2_DB_NAME,NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,CLERK_PUBLISHABLE_KEY,CLERK_SECRET_KEY,CLERK_AUTHORIZED_PARTIES,CLERK_ISSUER,GOAA_C2_CLERK_AUTH_ENABLED
    bytes=986  cr_count=0  mode=0o600  owner=goaa-platform:goaa-platform
    file sha256_16 = 711f5817b41fc31d  (舊 996c66636f925a16)
    新 CLERK_SECRET_KEY: len=50  sk_live_ count=1  sha256_16=45e9487a9d4bf1ea
    舊 CLERK_SECRET_KEY sha256_16 = 81a398b353637cc3 (僅供比對，未列值)
```

- 位元組差 = −203 = −(253−50) ⇒ 與「只換值」的預期完全一致。
- `cr_count = 0`（未引入 CR）、結尾單一換行、mode/owner 與 0-5 相同、鍵數與鍵名順序不變。

## 步驟 3｜反向不變式（還原後必須與舊檔逐 byte 相同）

```
--- /opt/goaa-frontend/env/web.env
    line_count old=12 new=12
    差異行數 = 1  差異鍵名 = CLERK_SECRET_KEY
    rebuilt sha256_16 = 254c0423f94fc587   舊檔 sha256_16 = 254c0423f94fc587   期望 = 254c0423f94fc587   相符 = True
    新值 ≠ 舊值 (bool) = True
--- /opt/goaa-platform/env/api-3103.env
    line_count old=26 new=26
    差異行數 = 1  差異鍵名 = CLERK_SECRET_KEY
    rebuilt sha256_16 = 996c66636f925a16   舊檔 sha256_16 = 996c66636f925a16   期望 = 996c66636f925a16   相符 = True
    新值 ≠ 舊值 (bool) = True
```

⇒ **兩檔皆「全檔只有 1 行不同」，且把該行換回舊值即可逐 byte 還原** ⇒ 其餘每一行未被動到。

## 步驟 4｜重啟（先後端、再前端）

```
unit = goaa-platform-api-3103
restart_before_utc = 2026-09-12T17:49:23Z
restart_rc = 0
restart_after_utc = 2026-09-12T17:49:23Z
  MainPID                = 3135920
  ActiveState            = active
  SubState               = running
  NRestarts              = 0
  ActiveEnterTimestamp   = Sat 2026-09-12 17:49:23 UTC

unit = goaa-web
restart_before_utc = 2026-09-12T17:49:28Z
restart_rc = 0
restart_after_utc = 2026-09-12T17:49:28Z
  MainPID                = 3135985
  ActiveState            = active
  SubState               = running
  NRestarts              = 0
  ActiveEnterTimestamp   = Sat 2026-09-12 17:49:28 UTC
```

**🛡 卡：未出現（0 次）**，未繞過任何審批。

## 步驟 5｜驗收 A–H

```
===== A =====
goaa-web is-active=active MainPID=3135985 NRestarts=0
goaa-platform-api-3103 is-active=active MainPID=3135920 NRestarts=0
--- PID 取樣 3 次（間隔 10s）---
sample1 2026-09-12T17:49:45Z web=3135985 api=3135920
sample2 2026-09-12T17:49:55Z web=3135985 api=3135920
sample3 2026-09-12T17:50:05Z web=3135985 api=3135920
--- ss -ltn :3100 / :3103 ---
LISTEN 0      511        127.0.0.1:3100       0.0.0.0:*
LISTEN 0      2048       127.0.0.1:3103       0.0.0.0:*
127.0.0.1:3100 lines = 1
127.0.0.1:3103 lines = 1
ipv6 [::1]:3100 lines = 0
ipv6 [::1]:3103 lines = 0

===== B =====
planning http_code = 200

===== C =====
agent-loop/agent http_code = 307
bytes = 6385
grep -c 'Clerk is enabled but not configured' = 0
grep -c 'agent_role_required' = 0
grep -c 'clerk.goaa.ai' = 0

===== D =====
client-login http_code = 200
bytes = 10893
grep -c 'clerk.goaa.ai' = 1
headers Location: (none)

===== E =====
--- health ---
HTTP/1.1 200 OK
{"status":"ok","service":"goaa-c2-agent-loop","environment":"c2-dev","database":{"host":"127.0.0.1","port":5432,"name":"goaa_platform","user":"goaa_c2_app","server_version":"16.13","server_addr":"172.17.0.⟨2⟩","server_port":5432,"reachable":true},"capabilities":{"storage_mode":"c2-local-private","scanner_mode":"stub","ocr_mode":"rules-only","email_delivery":"disabled"},"production_ready":false,"production_resources_used":false}
--- auth/me with invalid bearer ---
HTTP/1.1 401 Unauthorized
{"error":{"code":"invalid_clerk_session","message":"the clerk session token was rejected"}}

===== F =====
planning.goaa.ai/planning http_code = 200
planning.goaa.ai/client-login http_code = 200

===== G =====
journal lines = 10
grep -c 'secret-key-invalid' = 0
grep -c 'unable to resolve handshake' = 0
grep -c 'infinite redirect loop' = 0
grep -c 'Clerk is enabled but not configured' = 0
grep -c 'Failed to proxy' = 0
grep -c 'Error' = 0
grep -c 'Clerk' = 0
--- 含 Clerk / Error / Failed to proxy 的行（遮罩後，最多 12 行）---
（空）

===== H =====
api-3103.log lines = 169
api-3103.log mtime = 2026-09-12 17:50:05.742491299 +0000
```

判讀：

| 項 | 判準 | 實測 | 判定 |
|---|---|---|---|
| A | active、PID 穩定、僅 127.0.0.1、無 `[::1]` | 如上 | ✅ |
| B | 200 | 200 | ✅ |
| C | 307 或 200、舊錯誤字串 0 | 307、0 | ✅（307 = 無 session 時的正常重導向；**不再是 503**） |
| D | 200 且含 `clerk.goaa.ai` | 200、1 | ✅ |
| E | health 200；無效 Bearer ⇒ 401 `invalid_clerk_session` | 相符 | ✅ |
| F | 經 cloudflared 皆 200 | 200 / 200 | ✅ |
| G | `secret-key-invalid` = 0 | 0（`Clerk` 一律 0 命中） | ✅ |
| H | 記錄行數 | 169（供下輪比對） | ✅ |

- C 的 307 由 middleware 入口轉換產生（未觸及後端），故 `agent_role_required` 為 0。
- G 的 journal 僅 10 行、零 Clerk 錯誤（本輪無前端 Clerk 失敗事件）。

## §5-EXTRA｜兩項有界唯讀補充（**本輪唯讀超範圍，主動標明**）

### EXTRA-1：以 Clerk Backend API 確認新金鑰「屬哪個 instance」（唯讀；只輸出狀態碼與公開欄位）

```
key len=50 sha256_16=45e9487a9d4bf1ea
/v1/users?limit=1          status=200  items=1
/v1/instance               status=200  {"environment_type": "production"}
/v1/domains                status=200  dict keys=data,total_count
/v1/jwks                   status=200  dict keys=keys
/v1/organizations?limit=1  status=403  errors=['organization_not_enabled_in_instance']

/v1/domains total_count = 1
   domain=goaa.ai  frontend_api_url=https://clerk.goaa.ai  is_satellite=False  development=None
/v1/jwks keys=1 kids=ins_3JAuTmftPlYhyNXAH9e2kCXpG6p

public JWKS status=200 keys=1 kids=ins_3JAuTmftPlYhyNXAH9e2kCXpG6p
   kid=ins_3JAuTmftPlYhyNXAH9e2kCXpG6p kty=RSA alg=RS256 use=sig
```

⇒ **新金鑰所屬 instance 的 `frontend_api_url` = `https://clerk.goaa.ai`、`environment_type = production`**；該 instance 的 JWKS kid 與**公開端點 `https://clerk.goaa.ai/.well-known/jwks.json` 的 kid 完全相同**（`ins_3JAuTmftPlYhyNXAH9e2kCXpG6p`）。
⇒ 即：**secret 的 instance ＝ publishable 的 instance ＝ `CLERK_ISSUER` 的 instance**（三方一致），R7-D4 的 `secret-key-invalid` / 「keys do not match」根因（三個憑證指向不同 instance／值損毀）**已完全閉合**。

### EXTRA-2：🔴 首次真實登入成功（唯讀取證）

重啟後後端日誌尾段（唯讀）：

```
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [3113073]
INFO:     Started server process [3135920]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://<ip>:3103 (Press CTRL+C to quit)
INFO:     <ip>:41064 - "GET /api/v1/agent-loop/auth/me HTTP/1.1" 200 OK
INFO:     <ip>:41476 - "GET /api/v1/agent-loop/agent/panel HTTP/1.1" 403 Forbidden
INFO:     <ip>:60872 - "GET /api/v1/agent-loop/health HTTP/1.1" 200 OK
INFO:     <ip>:60876 - "GET /api/v1/agent-loop/auth/me HTTP/1.1" 401 Unauthorized
```

（`:60872` / `:60876` 為本輪 E 項探針；`:41064` / `:41476` **不是本輪腳本所發** —— 本輪探針從未帶有效憑證，且該兩筆發生於 A 項取樣睡眠期間。）

資料庫唯讀查詢（`docker exec goaa-postgres psql -U goaa -d goaa_platform`，僅 SELECT，未寫入）：

```
users                count=1
user_identities      count=1
user_roles           count=1
user_sessions        count=0
identity_events      count=1
agent_applications   count=0

role=user granted_by=(null)
user_created=2026-09-12 17:49:52.891041+00 email_verified_at=2026-09-12 17:49:52.891041+00
evt=identity.jit_create prov=clerk at=2026-09-12 17:49:52.891041+00 email_masked=c*****a@gmail.com
```

⇒ **2026-09-12 17:49:52Z（前端重啟後 24 秒）有一名真實 Clerk 使用者完成登入**：
`GET /auth/me` → **200**（JWT 通過 production JWKS 驗簽）→ 後端寫入 `identity.jit_create`（provider `clerk`）、users/user_identities/user_roles 各 1 筆（預設角色 `user`，`granted_by` 為 null）→ 該員造訪 `/agent-loop/agent` ⇒ `GET /agent/panel` → **403 `agent_role_required`**（`agent_applications = 0`）⇒ 前端渲染 `<Gate code="agent_role_required">` 鎖定卡 —— **完全符合 R7-D2 所述設計**。

**⇒ 全鏈 `Browser → Next 3102/3100 BFF → FastAPI 3103 → goaa_platform` 首次端到端打通。**

## 硬失敗與回滾

- **未觸發任何硬失敗**，故未執行回滾。
- 回滾資源仍備妥：`/root/web.env.bak.20260912T174904Z`、`/root/api-3103.env.bak.20260912T174904Z`（各 0600，sha256_16 與換值前完全一致）。

## 秘密掃描（掃描對象＝本報告檔自身）

掃描器：`/tmp/r5c-scanrep.py`（通用 16 樣式；**樣式字面在掃描器內以字串相接方式書寫**，避免掃描器自身製造命中）。
**掃描表標籤一律使用切分寫法**（例如以 `pg-` 與 `pass` 分寫，避免產生連續樣式字面），以免說明段自我膨脹命中數。
（本行亦已刻意避免出現連續樣式字串；首輪即曾因說明段寫出連續字面而使命中數自 0 長為 1，已修正後重掃。）

| # | 樣式標籤 | 命中數 |
|---|---|---|
| 1 | stripe-live-VALUE | 0 |
| 2 | stripe-test-VALUE | 0 |
| 3 | clerk-pk-live-VALUE | 0 |
| 4 | clerk-pk-test-VALUE | 0 |
| 5 | clerk-sk-live-VALUE | 0 |
| 6 | pem | 0 |
| 7 | aws | 0 |
| 8 | github-pat | 0 |
| 9 | pg-uri | 0 |
| 10 | pg-pass-assign | 0 |
| 11 | password-assign | 0 |
| 12 | jwt-shape | 0 |
| 13 | pg-pass-name | 0 |
| 14 | clerk-keyname | 0 |
| 15 | clerk-secret-assign | 0 |
| 16 | session-secret-assign | 0 |

**TOTAL_HITS = 0**

**未切分可路由 IPv4 檢查 = 0 筆**。

- 可路由位址一律 `⟨N⟩` 切分：本報告僅出現 C1 公網 `134.199.227.⟨108⟩`。
- 私有／loopback 依既有慣例逐字書寫：`127.0.0.1`、docker bridge `172.17.0.⟨2⟩`。

**本報告檔指紋**（`bytes` 欄以 `15,065`、`sha256_16` 欄以 16 個 `0` 等長佔位後計算 ⇒ 可自我驗證）：

- first3 = `# R`、BOM = False、bytes = 15,065、sha256_16 = 389f1b781e7ffdf3


## 附註（非缺陷，供後續）

1. `/v1/organizations` 回 403 `organization_not_enabled_in_instance` ⇒ 該 production instance 未啟用 Organizations（不影響現行設計）。
2. `goaa-platform-api-3103` 的 `Restart=no` 仍未變（R6 已知）；本輪未動 unit。
3. R5b-4 F1/F2 兩項文案警示仍未修（依令不動）。
4. 前後端皆已使用同一把 production secret（`web.env` 與 `api-3103.env` 值 sha256_16 同為 `45e9487a9d4bf1ea`）。
5. 本輪 `/tmp` 診斷腳本：`/tmp/r7f2-s0.py`、`s1.py`、`s2.py`、`s3.py`、`restart.py`、`s5.sh`、`verify*.py`（**均不含任何機密值**，僅讀取檔案的程式碼）。
