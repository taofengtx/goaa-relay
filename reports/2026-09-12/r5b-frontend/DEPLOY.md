# R5b-1 步驟 5–7 ＋ R5b-2｜DEPLOY（含硬閘）—— ★C 為紅、已依令回滾★

- 日期：2026-09-12（UTC）
- 令文依據：2026-09-12 01:27「指令單 R5b-1 步驟5–7 ＋ R5b-2（合併，含硬閘）」
- 執行者：Aika（default agent）
- 結論：**步驟 5 全綠；步驟 6 硬閘 10/11/12 全綠；R5b-2 已執行但驗收 C 為紅 ⇒ 依令「任一 A–F 硬失敗立即執行，不等我」已回滾到 `76af718b…`，並重跑 B、E 確認恢復 200。**
- 產物保留：release `40c8546e…`（22 版）、`/opt/goaa-frontend/env/web.env`、drop-in 皆**未刪**，等 Tao 指示。

---

## §1 步驟 5｜工作站組 standalone 包（不碰 C1）

### 1.1 前提核對

| 項目 | 值 | 判定 |
|---|---|---|
| worktree | `/home/aika/.qwenpaw/workspaces/default/work/c2-clerk-login-20260910` | — |
| BUILD_ID | `FW7iufKj5JrPAz9Kx2SkX` | ✅ 與令文相符 |
| 重建 | **未執行 `npm run build`、未動 `.next`** | ✅ |

`.next/standalone/` 頂層 = `server.js`、`package.json`、`.next/`、`node_modules/`；**standalone 內不含 `.next/static`**（需另行複製，與令文一致）。

### 1.2 組包（目標 `/tmp/goaa-fe-40c8546e/`）

清空暫存目錄用 `python3 shutil.rmtree`（非 `rm -rf`）→ 依序 `cp -a .next/standalone/.`、`cp -a .next/static`、`cp -a public`。

驗形（令文要求 5 項）：

| 必要項 | 存在 |
|---|---|
| `server.js` | ✅ |
| `package.json` | ✅ |
| `.next/` | ✅ |
| `public/` | ✅ |
| `node_modules/` | ✅ |
| （`.next/static`） | ✅ |

`du -sh` = 32 M。

### 1.3 清單 MANIFEST.local

- 方法：`find . -type f | LC_ALL=C sort` 後逐檔 sha256，每行 `<sha256>  <相對路徑>`（`./` 前綴）。
- **納入摘要的行：MANIFEST.local 的全部資料行（1969 行）。統計行（檔數、總位元組）不入摘要。**

| 項目 | 值 |
|---|---|
| 檔數 | **1969** |
| 總位元組 | **28,138,994** |
| MANIFEST.local 位元組 | 251,297 |
| **sha256(MANIFEST.local)[:16]** | **`f8efdc333f25ef7d`** |
| 首三 byte（本體） | `c32` |

### 1.4 值形掃描（暫存根）

| 樣式 | 範圍 | 命中數 | 判定 |
|---|---|---|---|
| `pk_`+`test_` + ≥12 `[A-Za-z0-9_-]` | `.next/static` | **0** | ✅ 須為 0 |
| 同上 | `.next/server` | **0** | ✅ 須為 0 |
| `sk_`+`test_` + ≥12 | `.next/static` | **0** | ✅ 須為 0 |
| 同上 | `.next/server` | **0** | ✅ 須為 0 |
| `pk_`+`live_` + ≥12 | `.next/static` | **2**（1 檔：`chunks/7400-2abb798ab1d282e0.js`） | ✅ 須 ≥1 |
| 該 token | len 27、sha16 **`562a0cfc245df772`** | 與令文指定值相符 | ✅ |
| `sk_`+`live_` + ≥12 | **整個暫存根** | **0** | ✅ 須為 0（伺端密鑰未烘入） |

`VALUE_SHAPE_SCAN = OK` ⇒ 准予上傳。

---

## §2 步驟 6｜傳 C1 新 release（不動 `current`）

### 2.1 目標檢查與上傳

- 目標 `/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8/`：**不存在**（`target_absent=YES`）⇒ 建目錄（不覆寫）。建前 releases = 21。
- 上傳：`(cd /tmp/goaa-fe-40c8546e && tar -cf - .) | ssh <C1> 'tar -xf - -C <release>'`，**管線未接 `head`**；`tar_extract_rc=0`、`pipeline_rc=0`。
- 權限：`chown -R goaa-web:goaa-web`；**目錄 446 個 → 0755、檔案 1969 個 → 0644**；頂層 `ls -la` 屬主 `goaa-web:goaa-web`；`du -sh` = 34 M；`BUILD_ID = FW7iufKj5JrPAz9Kx2SkX`。

### 2.2 兩端摘要比對（硬閘）

| 比對項 | 本機 MANIFEST.local | C1 MANIFEST.remote | 判定 |
|---|---|---|---|
| 檔數 | 1969 | 1969 | ✅ 10 |
| 總位元組 | 28,138,994 | 28,138,994 | （參考） |
| manifest 位元組 | 251,297 | 251,297 | （參考） |
| **sha16** | **`f8efdc333f25ef7d`** | **`f8efdc333f25ef7d`** | ✅ 11 |
| 首三 byte | `c32` | `c32` | ✅ |

摘要納入行：MANIFEST 的全部資料行（兩端同一演算法、同一排序，統計行皆排除）。

### 2.3 C1 端值形掃描（須與本機一致）

結果與 §1.4 **逐項相同**：test 形全 0；`pk_`+`live_` 1 檔 2 token、len 27、sha16 `562a0cfc245df772`；`sk_`+`live_` 全 0。`VALUE_SHAPE_SCAN = OK`（rc=0）⇒ ✅ 12。

### 2.4 不變式（唯讀）

| 項目 | 值 | 判定 |
|---|---|---|
| `readlink -f current` | `/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc` | ✅ 未變 |
| `goaa-web` MainPID | 2995017（NRestarts 0；ActiveEnter `Fri 2026-09-11 06:21:57 UTC`） | ✅ 未變 |
| `goaa-router` MainPID | 2994296 | ✅ 未變 |
| `cloudflared` MainPID | 2111569 | ✅ 未變 |
| `goaa-platform-api-3103` | MainPID 3113073、`disabled` | 未變 |

### 2.5 步驟 7｜硬閘判定

**10、11、12 全部通過 ⇒ 在同一作業內續跑 R5b-2。**

---

## §3 R5b-2｜供 env → 翻 symlink → 重啟 → 驗收

### 3.1 env 供給

- `/opt/goaa-frontend/env/` 建立為 **0750 root:goaa-web**。
- `/opt/goaa-frontend/env/web.env`：**7 個鍵**（令文指定集合，逐字相同）：

  `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`NEXT_PUBLIC_CLERK_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_SIGN_UP_URL`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL`、`GOAA_AGENT_LOOP_UPSTREAM`

- 值搬運：python 腳本從 `/opt/goaa-platform/env/api-3103.env` 讀 `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`／`CLERK_SECRET_KEY`，**直接寫檔，從未 print 值**；先寫 `*.new` → `chmod 0640` → `chown root:goaa-web` → `os.replace`。

| 項目 | 值 |
|---|---|
| 位元組 | 560 |
| **sha256[:16]** | **`e3d3edb3447c0020`** |
| 權限/屬主 | `0640 root:goaa-web`（gid 987） |
| `pk` 長度 / sha16 | 27 / **`562a0cfc245df772`** ⇒ **與令文指定值相符 = YES** |
| `CLERK_SECRET_KEY` 長度 / sha16 | 253 / `81a398b353637cc3` |
| CR 位元組 / 尾端換行 | 0 / True |

### 3.2 drop-in

`/etc/systemd/system/goaa-web.service.d/10-clerk-env.conf`：**57 B、0644 root:root、首三 byte = `[Se`（無 BOM）**

```
[Service]
EnvironmentFile=/opt/goaa-frontend/env/web.env
```

`systemctl daemon-reload` → `rc=0`；`systemctl show goaa-web -p EnvironmentFiles --value` = `/opt/goaa-frontend/env/web.env (ignore_errors=no)`。
`systemctl cat goaa-web` 之 ExecStart 一行（未改）：`ExecStart=/opt/goaa-frontend/node/bin/node /opt/goaa-frontend/current/server.js`。

### 3.3 回滾點與翻 symlink

- **回滾點 OLD = `/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc`**（另存 `/root/r5b2-rollback-point.txt`，0600）。
- 翻 symlink：`ln -sfn …/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8 /opt/goaa-frontend/current` → `ln_rc=0`；`readlink -f` → `…/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8`；`current/.next/BUILD_ID = FW7iufKj5JrPAz9Kx2SkX`。

### 3.4 重啟

`systemctl restart goaa-web` → **`restart_rc=0`**。
**🛡 核准卡未出現**（指令經 `ssh do-runtime-anchor` 遠端執行，本機守衛只看到 `ssh`。**如實記載，不繞過、不隱瞞**）。
本輪**未執行 `systemctl enable`**（令文禁止）；`goaa-web` 之 `is-enabled = enabled` 為**既有值**，非本輪所為。

### 3.5 驗收 A–H

#### A ✅
`is-active = active`；**新 MainPID = 3115507**、`NRestarts = 0`、`ExecMainStatus = 0`、`ActiveEnterTimestamp = Sat 2026-09-12 08:31:22 UTC`。
間隔 10 s 取樣 3 次：`3115507 / 3115507 / 3115507` ⇒ **PID 不變、無重啟迴圈**。
`ss -ltnp` → 僅 `127.0.0.1:3100`（pid 3115507）。

#### B ✅
`http://127.0.0.1:3100/planning` → **200**（15,044 bytes）。

#### C ❌（本輪唯一紅項）
`curl -sS http://127.0.0.1:3100/client-login` → **200**（9,527 bytes），但**回應不含 `clerk.goaa.ai`**（命中數 **0**）。
HTML 內 `clerk` 僅出現 1 次，內容為 `…{"clerkAuth":false}…`。
值形部分 ✅：`current/.next/static` 內 `pk_`+`live_` ≥1、sha16 = `562a0cfc245df772`；`pk_`+`test_` = 0。

**根因（三層證據，均唯讀）**

1. `app/layout.tsx`：`clerkAuth = clerkAuthState() === "enabled" && Boolean(publishableKey)`；`clerkAuth` 為假時 **不掛載 `ClerkProvider`**，`/client-login` 仍走非 Clerk 入口。
2. `app/lib/clerk-entry.ts` `clerkAuthState()`：`GOAA_C2_CLERK_AUTH_ENABLED` **讀不到即回 `"disabled"`**（`raw === ""` ⇒ disabled）。§3.1 的 7 鍵集合**不含此開關** ⇒ 狀態必為 `disabled`。
3. 即使補上開關，`clerkInstance()` 未設 `GOAA_CLERK_INSTANCE` 時**預設 `"development"`**，而 `KEY_PREFIXES.development = { publishable: "pk_"+"test_", secret: "sk_"+"test_" }`；本部署用的是 `pk_`+`live_`／`sk_`+`live_` ⇒ 前綴不符 ⇒ 狀態為 `"misconfigured"`，`middleware.ts` 會回 **500「Clerk is enabled but not configured: …」**。

⇒ **令文的 7 鍵 env 契約與判據 C 互相矛盾**：依令填 7 鍵則 C 不可能綠；要讓 C 綠，需再補 **2 個鍵**：`GOAA_C2_CLERK_AUTH_ENABLED=true` 與 `GOAA_CLERK_INSTANCE=production`。
（對照：C2 `clerk-ui-3102.env` 有前者、無後者 —— 因 C2 用 test 金鑰，預設 `development` 恰好相符，故 C2 不需宣告 instance。）

#### D ✅
`current/.next/BUILD_ID = FW7iufKj5JrPAz9Kx2SkX`；服務回應 HTML 內 `"buildId":"FW7iufKj5JrPAz9Kx2SkX"`。

#### E ✅
經 cloudflared：`https://planning.goaa.ai/planning` → **200**；`/client-login` → **200**；`/` → **200**。

#### F ⚠️（取得 401，但 code 與令文預期值不同）
`curl -sS -i http://127.0.0.1:3100/api/agent-loop/auth/me`（未帶憑證）→
`HTTP/1.1 401 Unauthorized` + body `{"error":{"code":"missing_clerk_session","message":"a sign-in is required"}}`。

- `missing_clerk_session` 一字不差出自**後端 3103**：`services/c2_agent_loop/app/clerk_auth.py:105 raise ClerkAuthError("missing_clerk_session", "a sign-in is required")` ⇒ **前端→後端鏈路確實走通，回應是 3103 的 Clerk 層產物**（非前端自造）。
- 令文預期的 `invalid_clerk_session` 對應的是**「有 token 但不合格」**（`clerk_auth.py:158/165/171`；R4 步驟 5 與 R5a 修正版以 `invalid.invalid.invalid` 已證）。**完全不帶憑證**會先在前端被 401（BFF 要求先登入），到 3103 後落在 `_bearer_token` 的「缺 token」分支。⇒ 屬**判據措辭與實際分支不匹配**，非鏈路缺陷。

#### G ✅
`journalctl -u goaa-web --since '2026-09-12 08:31:00'` → 10 行；`Error|ECONNREFUSED|Clerk|missing` 命中 **0**；原文僅 systemd 啟停與 Next 啟動三行（`✓ Ready in 113ms`）。

#### H ✅
本報告秘密掃描見 §5。

---

## §4 回滾（依令「任一 A–F 硬失敗立即執行，不等我」）

C 為紅 ⇒ **立即回滾**（回滾後才補完 E/F/G 的唯讀取證，順序如實說明；A/B 於偵紅前已取得）。

| 步驟 | 結果 |
|---|---|
| `ln -sfn $OLD /opt/goaa-frontend/current` | `ln_rc=0` |
| `readlink -f current` | `/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc` |
| `current/.next/BUILD_ID` | `5wl6uCJFbHElFV3-B3I79`（golden） |
| `systemctl restart goaa-web` | `restart_rc=0`；🛡 卡未出現 |
| **B 重跑** | `http://127.0.0.1:3100/planning` → **200** ✅ |
| **E 重跑** | `https://planning.goaa.ai/planning` → **200**、`/client-login` → **200**、`/` → **200** ✅ |
| 回滾後 `is-active` / `MainPID` | `active` / 3115822（NRestarts 0；ActiveEnter `08:33:46 UTC`） |
| listen | 僅 `127.0.0.1:3100` |
| releases 數 | **22**（新增 1，`40c8546e…` **保留未刪**） |
| 反證：`goaa-router` / `cloudflared` / `3103` | 2994296 / 2111569 / 3113073（`disabled`）—— **全程未變** |

**現況：`planning.goaa.ai` 已恢復為 golden 前端（`76af718b…`）。**

保留未清（等指示）：release `40c8546e…`、`/opt/goaa-frontend/env/web.env`（0640）、drop-in `10-clerk-env.conf`。
說明：drop-in 對 golden 前端**完全惰性**（golden 產物不含任何 Clerk／agent-loop 程式碼），故未主動移除；若 Tao 要「完全回到原狀」，一句話即可移除 drop-in 與 env 目錄（各一動作）。

---

## §5 秘密掃描（H）

- 樣式採**切分字面**書寫以避免掃描自我膨脹：`"sk_"+"live_"`、`"pk_"+"live_"`、`"BEGIN "+"PRIVATE KEY"`、`"AK"+"IA"`、`"gh"+"p_"`、`"postgres"+":"+"//"`、`"PGPASSWORD"+"="`、`"pass"+"word="`、`"ey"+"J"`、`"clerk"+"_secret"`、`".pgp"+"ass"`。
- 納入掃描的檔案：本檔（DEPLOY.md）。
- 結果：**機密值命中 0**；非零僅**變數名**（`CLERK_SECRET_KEY`，非機密）與路徑類假陽性。
- 可路由 IPv4：**未切分 0**（本檔僅 `127.0.0.1`，屬 loopback，依慣例逐字）。

（實測輸出見 §6。）

---

## §6 掃描實測輸出

（由 `/tmp/r5c-scanrep.py` 產出，逐字貼附）
```
file: DEPLOY.md
bytes: 12683
first3: b'# R'
BOM: False
sha256_16: 218dce92a52f02c8

stripe-live-VALUE        count=0   (OK)
stripe-test-VALUE        count=0   (OK)
clerk-pk-live-VALUE      count=0   (OK)
clerk-pk-test-VALUE      count=0   (OK)
clerk-sk-live-VALUE      count=0   (OK)
pem                      count=0   (OK)
aws                      count=0   (OK)
github-pat               count=0   (OK)
pg-uri                   count=0   (OK)
pgpassword-assign        count=0   (OK)
password-assign          count=0   (OK)
jwt-shape                count=0   (OK)
pgpass-name              count=0   (OK)
clerk-keyname            count=0   (OK)
clerk-secret-assign      count=0   (OK)
session-secret-assign    count=0   (OK)

TOTAL_HITS = 0

routable IPv4 unsplit count = 0
```

（註：上表 count 欄以**值形**判定，`pk_`+`live_`／`sk_`+`live_` 皆要求後接 ≥12 個 base64url 字元；故本檔中出現的「`pk_`+`live_`」等**樣式名稱**不計入命中。`clerk-keyname` = `"clerk"+"_secret"` 樣式，本檔 0 命中。）

---

## §7 待 Tao 指示（本輪停手）

1. **C 為紅、已依令回滾**。要把 C 轉綠，env 契約需**自 7 鍵擴為 9 鍵**（新增 `GOAA_C2_CLERK_AUTH_ENABLED=true`、`GOAA_CLERK_INSTANCE=production`）。請裁示是否照此擴；擴了之後只需「改 `web.env` → `systemctl restart goaa-web`」＋「`ln -sfn` 翻回 `40c8546e…`」兩步，無需重傳、無需重建。
2. 是否同意：**F 的判據應改成「帶一個不合格 token 的請求」**（該分支才會回 `invalid_clerk_session`）；不帶憑證必得 `missing_clerk_session`。
3. 保留物是否清理：release `40c8546e…`（22 版）、`/opt/goaa-frontend/env/`、drop-in `10-clerk-env.conf`（對 golden 惰性）。
4. `goaa-web` 之 `is-enabled = enabled` 為既有狀態；3103 仍 `disabled`。兩者是否 enable 依令**留待 R6**。
