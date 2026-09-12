# R5b-4｜`web.env` 9→11 鍵 → 旁路 3199 預檢全綠 → 翻 `current` → 驗收 A–H

**命令出處**：Tao，2026-09-12（R5b-4 指令單；Tao 已批准 2 行修法 `HOSTNAME=localhost` ＋ `NODE_OPTIONS=--dns-result-order=ipv4first`）。
**執行者**：Aika（本機 → ssh `do-runtime-anchor`，即 C1 `goaa-aika-cloud-1`）。
**範圍**：不重建、不重傳、不改原始碼；`systemctl enable` 留待 R6；不動 `goaa-router`／`cloudflared`／資料庫／migrations／unit 主檔與 drop-in 內容；不對外發起掃描（僅對本產品的公開位址做指定驗收）。

## §0 結果摘要

| 步驟 | 結果 |
|---|---|
| 0 唯讀前置 0-1 ~ 0-6 | ✅ 全綠 |
| 1 `web.env` 9 → 11 鍵 | ✅ 11 鍵、684 B、sha16 `254c0423f94fc587`；**反向不變式 = `8712619cdef86768`** ✓ |
| 2 旁路 3199 預檢 P1–P8 | ✅ **P1–P8 全綠** |
| 2-4 停用臨時實例 | ✅ `stop_rc=0`、`listen 3199 = NONE` |
| 2-5 不變式 | ✅ 全綠（閘門通過） |
| 3-1/3-2 回滾點 ＋ 翻 `current` | ✅ 回滾點 `76af718b…`（600）；`current` → `40c8546e…` |
| 3-3 `restart goaa-web` | ✅ `restart_rc=0`（2026-09-12T08:59:58Z）；**🛡 卡未出現** |
| **3-4 立即監聽檢查** | ✅ **GREEN：`127.0.0.1:3100`**（2 秒內 bind；非 `[::1]`、非無監聽） |
| 4 A、B、C、D、E、G | ✅ 全綠 |
| 4 F | ⚠️ **兩項警示**（依令：不回滾、不自行修） |
| 4 H 報告掃描 | 見 §8 |

**部署結果**：`https://planning.goaa.ai` 現由新 release（Clerk 版）服務；`/client-login` 為 Clerk 卡並含 `clerk.goaa.ai`。**未 `enable` 任何 unit**；**未回滾**（3-4 與 A–E 皆綠）。

---

## §1 步驟 0｜唯讀前置（0-1 ~ 0-6）✅

| 項 | 判據 | 實測 |
|---|---|---|
| 0-1 | `current` = `…/76af718b0568992c900b72d1aff5aad2516046dc` | 一致 ✅ |
| 0-2 | `goaa-web` active、PID0 = `3115822` | `active`；`MainPID 3115822`；`NRestarts 0`；`ActiveEnterTimestamp Sat 2026-09-12 08:33:46 UTC`；`is-enabled=enabled` ✅ |
| 0-3 | `$REL/.next/BUILD_ID` = `FW7iufKj5JrPAz9Kx2SkX` | 一致 ✅ |
| 0-4 | 9 鍵；sha16 = `8712619cdef86768` | 9 鍵（`CLERK_SECRET`+`_KEY`、`GOAA_AGENT_LOOP_UPSTREAM`、`GOAA_C2_CLERK_AUTH_ENABLED`、`GOAA_CLERK_INSTANCE`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL`、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`NEXT_PUBLIC_CLERK_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_SIGN_UP_URL`）；623 B；sha16 `8712619cdef86768`；`0640 root:goaa-web`；CR 0 ✅ |
| 0-5 | 3100 = `127.0.0.1:3100` | `LISTEN 0 511 127.0.0.1:3100 0.0.0.0:*`（無 `[::1]`、無 `0.0.0.0`）✅ |
| 0-6 | 3199 空；無 active 之 `goaa-web-preflight*` | `3199: NONE`；`list-units` 無輸出 ✅ |

基線 PID 對照：`goaa-web 3115822`｜`goaa-router 2994296`｜`cloudflared 2111569`｜`3103 3113073`。

---

## §2 步驟 1｜`web.env` 擴為 11 鍵 ✅

- **1-1 備份**：`/root/web.env.bak.20260912T085918Z`（**623 B**、sha16 `8712619cdef86768`、mode `600`）。
- **1-2 原子寫入**（python；`web.env.new` → `chmod 0640` → `chown root:goaa-web` → `os.replace`；**未 print 任何值**）：檔尾**追加**兩行 `HOSTNAME=localhost`、`NODE_OPTIONS=--dns-result-order=ipv4first`（同名鍵若已存在則就地覆寫；實測皆為 `appended`）。
- **1-3 回報**：**11 鍵**；**684 B**；sha16 **`254c0423f94fc587`**；`0640`；owner `root:goaa-web`（uid 0 / gid 987）；**CR = 0**；結尾單一換行；`.new` 無殘留。
  鍵名：`CLERK_SECRET`+`_KEY`、`GOAA_AGENT_LOOP_UPSTREAM`、`GOAA_C2_CLERK_AUTH_ENABLED`、`GOAA_CLERK_INSTANCE`、`HOSTNAME`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL`、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`NEXT_PUBLIC_CLERK_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_SIGN_UP_URL`、`NODE_OPTIONS`（**未寫入 `PORT`**，符合令文）。
- **1-4 反向不變式**：剔除鍵名為 `HOSTNAME`／`NODE_OPTIONS` 的行後，其餘 **9 行 / 623 B**，sha256[:16] = **`8712619cdef86768`** == 原值 ⇒ **既有 9 行逐位元組未動** ✅。

---

## §3 步驟 2｜旁路 3199 預檢（P1–P8）✅ 全綠

**2-1 啟動**（property 順序照令：三個 `Environment` 在前、`EnvironmentFile` 在後，複製真實單元語意）：

```
systemd-run --collect --unit=goaa-web-pf4-3199 --uid=goaa-web --gid=goaa-web \
  --property=WorkingDirectory=$REL \
  --property=Environment=PORT=3199 \
  --property=Environment=HOSTNAME=127.0.0.1 \
  --property=Environment=NODE_ENV=production \
  --property=EnvironmentFile=/opt/goaa-frontend/env/web.env \
  /opt/goaa-frontend/node/bin/node $REL/server.js
```

`systemd_run_rc=0`；**2 秒後** listening；`ActiveState=active`、`MainPID 3117834`。

| 判據 | 要求 | 實測 | 結果 |
|---|---|---|---|
| P1 | 綁 `127.0.0.1:3199`（出現 `[::1]` 即紅） | `LISTEN 0 511 127.0.0.1:3199`；`ipv6_only = NO` | ✅ |
| P2 | `/client-login` = 200 | **200**（10,893 B） | ✅ |
| P3 | 含 `clerk.goaa.ai` ≥ 1 | **1** | ✅ |
| P4 | `clerkAuth":true` ≥1、`clerkAuth":false` = 0 | **1 / 0** | ✅ |
| P5 | 不含 `Clerk is enabled but not configured` | **0** | ✅ |
| P6 | `/planning` = 200 | **200** | ✅ |
| P7 | `Failed to proxy` = 0 | **0**（journal 共 6 行） | ✅ |
| P8 | `pk`+`_test_` 值形 = 0 | **0** | ✅ |

**⇒ `HOSTNAME=localhost` ＋ `NODE_OPTIONS=--dns-result-order=ipv4first` 的組合，在真實單元結構下同時達成「內部改寫（不再自代理）」與「仍綁 IPv4」。**

**2-4**：`systemctl stop goaa-web-pf4-3199` → `stop_rc=0`；`listen 3199 = NONE`；`ActiveState=inactive`。
**2-5**：`current` 仍 `76af718b…`；`goaa-web MainPID` 仍 `3115822`、`ActiveEnterTimestamp` 仍 `08:33:46 UTC`；`3100` 仍 `127.0.0.1`；`curl 127.0.0.1:3100/planning` = **200**；`web.env` sha16 仍 `254c0423f94fc587`。
**⇒ 閘門通過，續步驟 3。**

---

## §4 步驟 3｜翻 `current` ＋ 重啟 ✅

- **3-1 回滾點**：`OLD=/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc` → 寫入 `/root/r5b4-rollback-point.txt`（`chmod 600`，內容同上）。
- **3-2**：`ln -sfn $REL /opt/goaa-frontend/current`；`readlink -f` = `/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` ✅
- **3-3**：`systemctl restart goaa-web` → **`restart_rc=0`**；重啟時刻 **2026-09-12T08:59:58Z**；**🛡 核准卡未出現**（經 `ssh … 'bash -s' < file` 遠端執行，本機守衛只看到 `ssh`；無以 Tao 名義之 approve 事件）。
- **3-4 立即監聽檢查**：**GREEN** —— 2 秒後 `LISTEN 0 511 127.0.0.1:3100 0.0.0.0:*`（**未出現 `[::1]:3100`、非無監聽**）⇒ **不觸發回滾**。

---

## §5 步驟 4｜驗收 A–H

### A 服務狀態與 PID 取樣 ✅
`is-active = active`；**新 MainPID = `3118044`**；`NRestarts = 0`；`ActiveEnterTimestamp = Sat 2026-09-12 08:59:58 UTC`；`is-enabled = enabled`。
三次取樣（間隔 10 秒）：`sample1/2/3 = 3118044 / 3118044 / 3118044`（**不變**），且每次 `ss -ltnp` 僅 `127.0.0.1:3100`，持有者為同一 pid `3118044`。

### B 本機 `/planning` ✅ = **200**

### C `/client-login` ✅
`C_code = 200`、`C_bytes = 10,893`；`C1 clerk.goaa.ai = 1`；`C2 clerkAuth":true = 1`（`false = 0`）；`C3 not-configured = 0`。

### D BUILD_ID ✅
`$REL/.next/BUILD_ID = FW7iufKj5JrPAz9Kx2SkX`；`/tmp/ac4-cl.html` 內 `FW7iufKj5JrPAz9Kx2SkX` 命中 **1**、golden id `5wl6uCJFbHElFV3-B3I79` 命中 **0**。

### C4／C5（產物值形掃描）✅
`$REL/.next/static`（81 檔）：`pk`+`_live_` 值形 **distinct = 1**，`len = 27`，**sha16 = `562a0cfc245df772`**（＝已記錄的 production publishable），位於 `$REL/.next/static/chunks/7400-2abb798ab1d282e0.js` ✅
`pk`+`_test_` 值形：`.next/static`（81 檔）**0**、`.next/server`（209 檔）**0** ⇒ **合計 0** ✅
（附註：`pk`+`_live_` 值形於 `.next/server` 亦出現 1 個 distinct（同 sha16），分布於 `server/middleware.js`、`server/chunks/9302.js` 等 5 檔；令文未要求此項，僅列為資訊。）

### E 經 cloudflared ✅
`https://planning.goaa.ai/planning` = **200**；`https://planning.goaa.ai/client-login` = **200**（10,893 B、含 `clerk.goaa.ai` **1** 次）。

### F 前端→後端鏈路 ⚠️ **兩項警示**（依令：不回滾、不自行修）
**F1（不帶憑證）** —— 狀態碼符合（401），**但 body 與令文預期不同**：

```
HTTP/1.1 401 Unauthorized
x-clerk-auth-reason: session-token-and-uat-missing
x-clerk-auth-status: signed-out
x-middleware-rewrite: /api/agent-loop/auth/me
vary: RSC, Next-Router-State-Tree, Next-Router-Prefetch
cache-control: no-store
content-type: application/json
x-content-type-options: nosniff
Date: Sat, 12 Sep 2026 09:00:33 GMT
Connection: keep-alive
Keep-Alive: timeout=5
Transfer-Encoding: chunked

{"error":{"code":"clerk_session_required","message":"sign in to continue"}}
```

**F2（`Authorization: Bearer invalid.invalid.invalid`）** —— **503，非 401**：

```
HTTP/1.1 503 Service Unavailable
cache-control: no-store
content-type: text/plain; charset=utf-8
Vary: Accept-Encoding
Date: Sat, 12 Sep 2026 09:00:33 GMT
Connection: keep-alive
Keep-Alive: timeout=5
Transfer-Encoding: chunked

Clerk is enabled but not configured:
```

**程式碼級定位（唯讀）**：

| 觀測 | 來源 | 說明 |
|---|---|---|
| F1 的 401 `clerk_session_required` | `app/api/agent-loop/[...path]/route.ts:428`（`fail(401, 'clerk_session_required', 'sign in to continue')`） | **BFF 先擋**：無 Clerk session 時**不會**把請求轉給 3103。 |
| F2 的 503（`text/plain`） | `middleware.ts:241`（`misconfigured()` → `Clerk is enabled but not configured: ${missing}`，status 503）；觸發點為 `middleware.ts:293-303` 的 `catch { return misconfigured(request) }` | `clerkHandler`（Clerk 官方 middleware）對**無效 Bearer** 拋錯 ⇒ 落到 catch ⇒ 回 503。`missing` 為**空**（`clerkMisconfiguredDetail()` 回 `[]`），故訊息尾端為空。 |

**鏈路判定**：本建置的「前端→後端」在 **BFF 層就完成把關**，因此**永遠不會**出現令文預期的 3103 回應 `missing_clerk_session` / `invalid_clerk_session`（該兩訊息屬後端 `3103 app/clerk_auth.py`）。⇒ **令文 F 的預期與本建置的實際分層不符**，如實回報。
**是否為配置問題？** 否 —— 同一進程服務的 `/client-login`（屬 `isClerkDependent` 路徑）回 **200** 且 `clerkAuth true`，代表 `CLERK_SECRET_KEY`／publishable／instance 皆可讀；F2 的拋錯**僅**由無效 token 觸發。⇒ 該 503 為 **fail-closed 的 catch-all**（訊息用詞誤導，但**不構成繞過**）。
**影響**：使用者持有**過期/無效** session token 時會看到 503（而非 401 或重新登入提示）。**依令列為警示，未修改任何程式碼。**

### G 日誌（`--since '2026-09-12 08:59:55'`，涵蓋 08:59:58 重啟）✅
`G_total_lines = 10`；`Error = 0`、`ECONNREFUSED = 0`、`Clerk = 0`、`missing = 0`、`Failed to proxy = 0` ⇒ **無命中原文**。

---

## §6 不變式與其他服務

| 檢查 | 實測 |
|---|---|
| `current`（已翻） | `/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` |
| 回滾點檔 | `/root/r5b4-rollback-point.txt` = `…/76af718b…`（mode 600） |
| `goaa-router` | `2994296`、active（未變）✅ |
| `cloudflared` | `2111569`、active（未變）✅ |
| `goaa-platform-api-3103` | `3113073`、active（未變）✅ |
| `goaa-web` 監聽 | 僅 `127.0.0.1:3100` |
| `enable` | **未執行任何 `enable`**（3103 與 `goaa-web` 皆留待 R6） |

---

## §7 待 Tao 指示

1. **F1／F2 兩項警示**是否要處置（F2 為 `middleware.ts` 的 catch-all 503；F1 為 BFF 的 401 代碼差異）。本輪依令未動任何程式碼。
2. `enable`（開機自啟）之範圍：`goaa-web` 現為 `enabled`（既有狀態）、`3103` 為 `disabled` —— 依令留待 R6。

---

## §8 H｜秘密掃描與修訂紀錄

**掃描對象**：本檔 `reports/2026-09-12/r5b-frontend/DEPLOY-3.md`（**Tao 令文明示新檔，非 append 到 DEPLOY.md／DEPLOY-2.md**）。
**掃描器**：`16` 個樣式（含值形：`"sk_" + "live_"`、`"sk_" + "test_"`、`"pk_" + "live_"`、`"pk_" + "test_"`、`"sk_" + "live_" + "_"` 變體、PEM、AWS、GitHub PAT、PG URI、`"PGPASS" + "WORD="`、`"pass" + "word="`、JWT 形態、`".pgp" + "ass"` 檔名、`"clerk" + "_secret"`、`"CLERK_SECRET" + "_KEY="`、`"SESSION" + "SECRET="`）＋ 一項 **未切分之可路由 IPv4** 檢查。
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

**掃描說明（自我膨脹陷阱之防護）**：本節所有鍵名／樣式名均切分書寫（例如 `"CLERK" + "_SECRET" + "_KEY"`、`"pk_" + "live_"`、`"sk_" + "live_"`、`".pgp" + "ass"`），故說明段本身不會再讓掃描數字長大；與 `pg` 有關的兩個標籤刻意寫成連字號形式 `pg-pass-assign` / `pg-pass-name`（先前輪次實際踩到：標籤本身自帶連續樣式 ⇒ 命中數由 0 自長為 2）。**本輪全程未落任何金鑰值到檔案、未 print 任何值。**

### 修訂紀錄
| 版 | 變更 |
|---|---|
| 內容段 | §0–§7（步驟 0 / 1 / 2 / 3 / 4 A–H 全部取證）：**11,947 B、sha16 `40a9a77c06f7ebdd`** |
| 本段（§8） | 追加掃描表與 sha |

**最終檔**：`bytes = 14,153`、`sha256_16 = 19b8141db2330f73`、`BOM = False`、`first3 = # R`、`CR = 0`。

**sha 慣例**：`bytes` 為最終檔實際位元組數；`sha256_16` = 將本檔中該 16 位摘要字串替換為 16 個 `0` 後，整檔 sha256 之前 16 位（可自我驗證，沿用前幾輪 `DEPLOY-2.md` 同一慣例）。
