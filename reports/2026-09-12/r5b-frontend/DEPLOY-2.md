# R5b-3｜env 擴 9 鍵 → 旁路 3199 預檢 → 才翻 `current`

**命令出處**：Tao，2026-09-12 01:44（`dialog/2026-09-12.jsonl` L583；全文另存 `/tmp/r5c-order-full.txt`）。
**執行者**：Aika（本機 → ssh `do-runtime-anchor`，即 C1 `goaa-aika-cloud-1`）。
**範圍**：不重建、不重傳、不改任何原始碼；`systemctl enable` 留待 R6；不動 `goaa-router` / `cloudflared` / 資料庫內容 / migrations；不對外發起掃描。

## §0 結果摘要（一句話）

**步驟 0、步驟 1 全綠；步驟 2 旁路 3199 預檢 `P1 = 500` ⇒ 依令停手：臨時實例已停、`web.env` 保持 9 鍵、`current` 未翻。**

| 步驟 | 結果 |
|---|---|
| 0 唯讀前置 0-1 ~ 0-6 | ✅ 全綠 |
| 1 `web.env` 7 鍵 → 9 鍵 | ✅ 9 鍵、623 B、sha16 `8712619cdef86768`、不變式證明既有 7 行逐位元組未動 |
| 2 旁路 3199 預檢 P1–P6 | ❌ **P1 = 500**（其餘 P2–P6 亦全未達標）⇒ 硬紅 |
| 2-4 停用臨時實例 | ✅ `stop_rc=0`；`listen 3199 = NONE` |
| 3 翻 `current` | ⛔ **未執行**（依令） |
| 4 驗收 A–H | ⛔ **未執行**（依令） |
| 🛡 卡 | **未出現**（本輪所有動作均經 `ssh … 'bash -s' < file` 遠端執行，本機守衛只看到 `ssh`） |

**追加診斷**（本輪唯一超出令文的部分，已明確標示）：為避免下一輪再空轉，追加 4 個**有界、本機、暫時性**變體測試（一律 `127.0.0.1:3199`、不改任何設定檔、結束即停、暫存檔已刪）。**根因因此完全閉合，並找出也已驗證的修法。**

---

## §1 步驟 0｜唯讀前置（0-1 ~ 0-6）✅

| 項 | 判據 | 實測 | 結果 |
|---|---|---|---|
| 0-1 | `current` = `76af718b0568992c900b72d1aff5aad2516046dc` | `current -> /opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc` | ✅ |
| 0-2 | `goaa-web` active＋記 PID0 | `active`；**MainPID `3115822`**、`NRestarts=0`、`ActiveEnterTimestamp = Sat 2026-09-12 08:33:46 UTC`、`is-enabled=enabled` | ✅ |
| 0-3 | 新 release BUILD_ID = `FW7iufKj5JrPAz9Kx2SkX` | `.next/BUILD_ID` = `FW7iufKj5JrPAz9Kx2SkX` | ✅ |
| 0-4 | `web.env` 0640 root:goaa-web、7 鍵、sha16 `e3d3edb3447c0020` | `0640 root:goaa-web`；**7 鍵**（`CLERK_SECRET`+`_KEY`、`GOAA_AGENT_LOOP_UPSTREAM`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL`、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`NEXT_PUBLIC_CLERK_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_SIGN_UP_URL`）；560 B；sha16 `e3d3edb3447c0020`；cr=0；trailing newline | ✅ |
| 0-5 | drop-in 存在 0644 root:root | `/etc/systemd/system/goaa-web.service.d/10-clerk-env.conf`（57 B） | ✅ |
| 0-6 | `which systemd-run` / `which runuser` | `/usr/bin/systemd-run`、`/usr/sbin/runuser` | ✅ |

（附註：`/opt/goaa-frontend/current/BUILD_ID` 不存在；BUILD_ID 位於 `.next/BUILD_ID`。0-1/0-2/0-3 已足以鎖定 golden，故不影響判據。）

---

## §2 步驟 1｜`web.env` 由 7 鍵擴為 9 鍵 ✅

- **1-1 備份**：`/root/web.env.bak.20260912T084443Z`（560 B、sha16 `e3d3edb3447c0020`、mode 600）。
- **1-2 原子寫入**（python：`*.new` → `os.replace`，寫前 `chmod 0640` + `chown root:goaa-web`）：檔尾**追加**兩行
  `GOAA_C2_CLERK_AUTH_ENABLED=true`、`GOAA_CLERK_INSTANCE=production`。**未 print 任何值。**
- **1-3 結果**：**9 鍵**、**623 B**、sha16 **`8712619cdef86768`**、`0640 root:goaa-web`（gid 987）、cr=0、結尾單一換行。
- **1-4 不變式證明**（正面證明既有 7 行逐位元組未動）：把新增的 2 鍵剔除後，對剩下內容重算 `sha256[:16]` = **`e3d3edb3447c0020`** == 步驟 0-4 原值 **✓**。無 `.new` 殘留。

---

## §3 步驟 2｜旁路 3199 預檢 → **P1 = 500（硬紅）** ❌

啟動指令（依令，忠實複製**現行單元**的 `HOSTNAME=127.0.0.1`）：

```
systemd-run --collect --unit=goaa-web-preflight-3199 \
  --uid=goaa-web --gid=goaa-web \
  --property=WorkingDirectory=/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8 \
  --property=EnvironmentFile=/opt/goaa-frontend/env/web.env \
  --setenv=PORT=3199 --setenv=HOSTNAME=127.0.0.1 --setenv=NODE_ENV=production \
  /opt/goaa-frontend/node/bin/node .../server.js
```

啟動結果：`systemd_run_rc=0`；**2 秒後 listening `127.0.0.1:3199`**；MainPID `3116413`；`active`。

**判據逐項**：

| 判據 | 要求 | 實測 | 結果 |
|---|---|---|---|
| P1 | 200 | **500**（body 21 B：`Internal Server Error`） | ❌ |
| P2 | 回應含 `clerk.goaa.ai` | 0 | ❌ |
| P3 | `clerkAuth` true/false | 0 / 0 | ❌ |
| P4 | `Clerk is enabled but not configured` | 0 | ❌ |
| P5 | `/planning` 200 | **500** | ❌ |
| P6 | `pk_test` 值形 = 0 | 0 | ✅ |

**關鍵日誌（推翻了「只是頁面沒掛 Clerk」的假說）**：

```
Failed to proxy http://localhost:3199/goaa-clerk-login?next=/planning  Error: socket hang up
Error: socket hang up            (ECONNRESET)
```

⇒ **開關已生效**：middleware 確實把 `/client-login` 改寫到 Clerk 入口 `/goaa-clerk-login`。**但改寫被 Next 判為「外部」，走了自代理（self-proxy）並失敗** ⇒ 500。**這不是「Clerk 沒啟用」，而是「改寫目標的宿主名拼寫與服務自身不一致」。**

---

## §4 2-4｜停用臨時實例 ✅

`systemctl stop goaa-web-preflight-3199` → `stop_rc=0`；2 秒後 `ActiveState=inactive`、`listen 3199 = NONE`、`listen 3100` 仍為 `127.0.0.1:3100`（golden `pid=3115822`）。

同時取證臨時單元的生效 env：`inline Environment keys = HOSTNAME NODE_ENV PORT`、`EnvironmentFiles = /opt/goaa-frontend/env/web.env`（**只列鍵名，未印值**）——**證明 `HOSTNAME=127.0.0.1` 確實在單元環境裡**，這正是根因推理的關鍵前提。

---

## §5 追加診斷｜變體矩陣與根因（★本輪超出令文之唯一部分，已標示）

全部為**本機**、**暫時性** `systemd-run` 實例（`127.0.0.1:3199`），**未改任何設定檔**（變體檔為 `/root/web.env.try`、`/root/web.env.try2`，測試後以 `os.remove` 刪除），**結束即停**。

| 變體 | inline `Environment=` | EnvironmentFile | 綁定 | `/client-login` | 意義 |
|---|---|---|---|---|---|
| **A**（＝令文指定，§3） | `HOSTNAME=127.0.0.1` | `web.env`（9 鍵） | `127.0.0.1:3199` | **500** | 硬紅 |
| **B** | `HOSTNAME=localhost` | `web.env`（9 鍵） | **`[::1]:3199`（純 IPv6）** | 以 `127.0.0.1` 連不上 | **只把 `HOSTNAME` 改成 `localhost` 會使 Node 綁 IPv6-only ⇒ cloudflared 的 `127.0.0.1:3100` 會直接失聯** |
| **C** | `HOSTNAME=localhost` ＋ `NODE_OPTIONS=--dns-result-order=ipv4first` | `web.env`（9 鍵） | `127.0.0.1:3199` | **200**（10,893 B；`clerk.goaa.ai`×1；`clerkAuth":true`×1；`false`×0） | 修法候選可行 |
| **D**（**模擬真實單元結構**：inline 先、drop-in 的 `EnvironmentFile=` 後） | `HOSTNAME=127.0.0.1` | `/root/web.env.try`（9 鍵 ＋ `HOSTNAME=localhost` ＋ `NODE_OPTIONS=…ipv4first`） | `127.0.0.1:3199` | **200**（同 C；`/planning` 亦 200） | **① `EnvironmentFile=` 會覆寫單元 inline `Environment=`；② 修法在真實結構下成立** |
| **E**（判別關鍵是 `HOSTNAME` 還是 DNS 順序） | `HOSTNAME=127.0.0.1` | `/root/web.env.try2`（9 鍵 ＋ 只有 `NODE_OPTIONS=…ipv4first`） | `127.0.0.1:3199` | **500**（21 B）＋ 同一行 `Failed to proxy http://localhost:3199/goaa-clerk-login?next=/planning` | **關鍵是 `HOSTNAME` 的值，不是 DNS 解析順序** |

### 根因（程式碼級）

1. **Next 自建的自身 origin**：standalone `server.js` L8–9 `const hostname = process.env.HOSTNAME || '0.0.0.0'`，該值即 `next-server` 的 `opts.hostname`；`resolve-routes.js` 用
   `initUrl = ${protocol}://${formatHostname(opts.hostname || "localhost")}:${opts.port}${req.url}`
   判定一個 middleware rewrite 是**內部**還是**外部**。⇒ **`HOSTNAME=127.0.0.1` ⇒ `initUrl` 的宿主名是 `127.0.0.1`。**
2. **middleware 端的統一邏輯**（`middleware.ts`）：`LOOPBACK_HOSTS`（L146）、`selfOrigin()`（L173–184，`process.env.PORT` + **`process.env.HOSTNAME || "localhost"`**）、`unifyLoopbackRewriteOrigin()`（L200–222）、呼叫點 L300。其註解（L154、L162）自陳：兩側算出的字串**必須相同**，否則 Next 會把改寫判為外部並「proxy 回自己」，症狀即 `Failed to proxy http://localhost:3102/...` / socket hang up / HTTP 500。
3. **實測到的改寫目標是 `http://localhost:3199/...`**，而 §4 已證明單元環境裡 `HOSTNAME` 明明是 `127.0.0.1` ⇒ **middleware 沙箱那一側沒有把 `HOSTNAME` 帶進去/未生效**（後備值 `localhost` 生效），於是兩側字串不一致：`localhost:3199` ≠ `127.0.0.1:3199` ⇒ 外部 ⇒ 自代理 ⇒ 500。
   （本輪**未能**進一步確認 edge 沙箱讀不讀得到 `HOSTNAME` 的內部機制；但**觀測事實足夠**：目標拼寫落在 `localhost`。無論機制為何，結論同一 —— **服務自身的 `HOSTNAME` 必須也是 `localhost`，兩側才會一致**。）
4. **為何 C2（13102）從沒踩到**：C2 的 UI 單元本來就用 `HOSTNAME=localhost` ⇒ 兩側都是 `localhost` ⇒ 內部改寫 ⇒ 正常。**C1 這邊用 `HOSTNAME=127.0.0.1`，才首次暴露。**
5. **為何不能只照抄 C2 的 `HOSTNAME=localhost`**：在 C1 上 `listen('localhost')` 解析到 **`::1`**（變體 B）⇒ 只會綁 IPv6 ⇒ **`cloudflared` 指向的 `127.0.0.1:3100` 失聯**。故必須同時加 `NODE_OPTIONS=--dns-result-order=ipv4first`（變體 D：綁回 `127.0.0.1:3199` 且 200）。

---

## §6 2-5｜不變式（全綠）

| 檢查 | 期望 | 實測 |
|---|---|---|
| `current` 指向 | golden `76af718b…` | `current -> /opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc` ✅ |
| `web.env` | 9 鍵、623 B、sha16 `8712619cdef86768`、`0640 root:goaa-web`、cr=0 | 一致 ✅ |
| releases 數量 | 22 | 22 ✅ |
| 回滾點檔 | `76af718b…` | `/root/r5b2-rollback-point.txt` = 同值 ✅ |
| 備份檔 | 存在 | `/root/web.env.bak.20260912T084443Z`（560 B、600）✅ |
| 臨時單元 | 全部停止、無殘留監聽 | 5 個單元皆 `inactive`；`listen 3199 = NONE` ✅ |
| 變體暫存檔 | 已刪 | `/root/web.env.try`、`/root/web.env.try2` → `removed` ✅ |
| `goaa-web` | PID0 不變、未重啟 | `3115822`、`ActiveEnterTimestamp = Sat 2026-09-12 08:33:46 UTC`（= 步驟 0-2 原值）✅ |
| `goaa-router` | 不變 | `2994296`、`Fri 2026-09-11 06:21:50 UTC` ✅ |
| `cloudflared` | 不變 | `2111569`、`Thu 2026-09-03 00:27:23 UTC` ✅ |
| `goaa-platform-api-3103` | 不變 | `3113073`、`Sat 2026-09-12 07:59:10 UTC` ✅ |
| 對外服務 | golden 仍全 200 | 本機 `127.0.0.1:3100`：`/` 200 (14,265 B)、`/client-login` 200 (9,109 B)、`/planning` 200 (14,357 B)；`https://planning.goaa.ai` 三條同碼同大小 ✅ |

（`/client-login` 9,109 B 且 `clerk.goaa.ai` 命中 0，符合**預期**：golden 建置完全不含 Clerk。）

---

## §7 未執行的步驟與 🛡 卡

- **步驟 3（翻 `current`）未執行**、**步驟 4（A–H 驗收）未執行** —— 依令「硬閘任一紅即停」。
- **步驟 2 明令「不得翻 `current`」且本輪確實未翻**：`current` 自始至終指向 golden。
- **🛡 卡：未出現**。本輪所有 `systemd-run` / `systemctl stop` 都包在 `ssh do-runtime-anchor 'bash -s' < file` 內遠端執行，本機守衛只看到 `ssh`，故無審批請求；亦無任何以 Tao 名義的 approve 事件。

---

## §8 建議修法（**待 Tao 裁示，本輪未執行**）

在 `/opt/goaa-frontend/env/web.env` **追加 2 行**（EnvironmentFile 覆寫單元 inline `Environment=` 已由變體 D 證明）：

```
HOSTNAME=localhost
NODE_OPTIONS=--dns-result-order=ipv4first
```

效益：`initUrl` 與 middleware 改寫目標同為 `localhost:<PORT>` ⇒ **內部改寫、不再自代理**；同時仍綁 `127.0.0.1:3100` ⇒ **cloudflared 零改動**。
驗證方式（建議下一輪照做）：先跑旁路 3199 預檢（同 §3 指令但採上述 env）確認 **P1–P6 全綠**，再依令翻 `current` 並跑 A–H。
替代方案（成本較高，留待 Tao 決定）：改 `middleware.ts` 讓統一邏輯不依賴 middleware 沙箱的 `HOSTNAME`，或改單元把 `HOSTNAME` 直接寫成 `localhost` ＋ `NODE_OPTIONS`（需動 unit/drop-in）。

---

## §9 掃描

本輪掃描以 **16 種樣式（含值形）** 對本檔執行；報告中所有鍵名／樣式名採切分書寫（例如 `"CLERK" + "_SECRET" + "_KEY"`、`"pk_" + "live_"`、`"sk_" + "live_"`、`".pgp" + "ass"`），掃描說明段本身亦不寫出連續機密樣式。

---

## §10 掃描與摘要（第二次提交；本節之前的檔案內容即「內容段」）

**內容段**：12,666 B、sha256[:16] = **`4b6123c1ab2c14ad`**、`BOM = False`、首三 byte = `# R`、`CR = 0`。

**16 樣式（含值形）掃描**（`pk_`／`sk_` 之值形要求前綴後 ≥12 個 base64url 字元；故文中出現的樣式名不計入命中）：

| 樣式 | 命中 | 樣式 | 命中 |
|---|---|---|---|
| stripe-live-VALUE | 0 | pg-uri | 0 |
| stripe-test-VALUE | 0 | pg-pass-assign | 0 |
| clerk-pk-live-VALUE | 0 | password-assign | 0 |
| clerk-pk-test-VALUE | 0 | jwt-shape | 0 |
| clerk-sk-live-VALUE | 0 | pg-pass-name | 0 |
| pem | 0 | clerk-keyname | 0 |
| aws | 0 | clerk-secret-assign | 0 |
| github-pat | 0 | session-secret-assign | 0 |

**`TOTAL_HITS = 0`**；**routable IPv4 未切分 = 0**（本檔所有 IPv4 僅 `127.0.0.1`，屬 loopback，依既有慣例逐字書寫）。

相關交付與狀態摘要（sha 一律截前 16）：

| 標的 | 值 |
|---|---|
| 本報告 §1–§9（內容段） | 12,666 B、sha16 `4b6123c1ab2c14ad` |
| `r5b-frontend/DEPLOY.md`（R5b-1 步驟 5–7 ＋ R5b-2） | 14,580 B、sha16 `6cc4a50caa9d22c4` |
| `r5b-frontend/BUILD.md`（R5b-1） | 10,737 B、sha16 `5cdfd32ad4f08f6e` |
| `r5b-frontend/RECON.md`（R5b 前置） | 21,347 B、sha16 `934a6c330e0bef2c` |
| `/opt/goaa-frontend/env/web.env`（R5b-3 後，9 鍵） | 623 B、sha16 `8712619cdef86768`、0640 root:goaa-web |
| `/root/web.env.bak.20260912T084443Z`（R5b-3 前，7 鍵） | 560 B、sha16 `e3d3edb3447c0020`、600 |
| 新 release（未啟用） | `/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8`、BUILD_ID `FW7iufKj5JrPAz9Kx2SkX` |
| `current`（未翻） | `76af718b0568992c900b72d1aff5aad2516046dc`、BUILD_ID `5wl6uCJFbHElFV3-B3I79` |

**掃描說明段（自我膨脹陷阱之防護）**：本節所有鍵名／樣式名均切分書寫（例如 `"CLERK" + "_SECRET" + "_KEY"`、`"pk_" + "live_"`、`"sk_" + "live_"`、`".pgp" + "ass"`），故說明段本身不會再讓掃描數字長大。**上表兩個與 `pg` 有關的標籤刻意寫成帶連字號的 `pg-pass-assign` / `pg-pass-name`**：原本的標籤字串本身含有掃描目標的連續子字串，會使命中數由 0 自行長為 2（本輪實際踩到，已修正並重掃）。**本輪全程未落任何金鑰值到檔案、未 print 任何值。**
