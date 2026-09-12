# R5b 前置 — C1 前端切換（`planning.goaa.ai`）唯讀勘查

- 令：2026-09-12 01:03（Round R5b 前置）
- 執行：Aika（`default`）
- 目標：把 **Clerk 版前端**在 **C1** 上線（`planning.goaa.ai`）；後端 3103 已就緒（loopback）。
- **本輪唯讀**：不 build、不改 symlink、不改 unit、不改 env、不重啟任何服務。
- 紀律：env 只列變數名；可路由 IPv4 切分；sha256 前 16；relay 不 force-push。
- 執行時刻：`2026-09-12T08:0x–08:2xZ`（UTC）

---

## 0. 邊界宣告

| 項目 | 本輪 |
|---|---|
| 寫入 C1 | **0**（只讀 `ls`／`cat`／`systemctl cat`／`ss`／`grep`／`find`／`readlink`／`/proc`） |
| 寫入 C2 | **0**（同上） |
| 建置 | **未執行** |
| `current` symlink | **未動**（仍 `76af718b…`） |
| unit／env 檔 | **未動** |
| 服務重啟 | **0 次** |
| 🛡 卡 | **未出現**（本輪無任何特權／破壞性操作）；未經 Tao approve（無需） |

---

## 1. A. C1 現況（目標端）

### A1 目錄佈局 —— **`releases/<戳記> + current` symlink（可回滾）**

```
$ ls -la /opt/goaa-frontend/
drwxr-xr-x  4 root     root     4096 Sep  7 10:17 .
drwxr-xr-x  7 root     root     4096 Sep 12 06:46 ..
lrwxrwxrwx  1 root     root       68 Sep  7 10:17 current -> /opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc
-rw-r--r--  1 root     root  8506685 Sep  6 20:52 goaa-web-auth-20260906-013c6b23….tar.gz
-rw-r--r--  1 root     root  8507908 Sep  6 23:07 goaa-web-legal-20260906-9927c44d….tar.gz
-rw-r--r--  1 root     root  8508151 Sep  6 21:16 goaa-web-passreveal-20260906-253a78c6….tar.gz
drwxr-xr-x  6 1001     1001     4096 May 13 14:50 node
drwxr-xr-x 23 root     root     4096 Sep  7 10:23 releases

$ readlink -f /opt/goaa-frontend/current
/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc

$ ls -la /opt/goaa-frontend/current/ | head -30
drwxr-xr-x  5 goaa-web goaa-web 4096 Sep  7 10:15 .
drwxr-xr-x 23 root     root     4096 Sep  7 10:23 ..
drwxr-xr-x  4 goaa-web goaa-web 4096 Sep  7 10:15 .next
drwxr-xr-x 17 goaa-web goaa-web 4096 Sep  7 10:15 node_modules
-rw-r--r--  1 goaa-web goaa-web  629 Sep  7 10:15 package.json
drwxr-xr-x  3 goaa-web goaa-web 4096 Sep  3 00:44 public
-rw-r--r--  1 goaa-web goaa-web 4725 Sep  7 10:15 server.js

$ du -sh /opt/goaa-frontend/*
8.2M  …/goaa-web-auth-20260906-013c6b23….tar.gz
8.2M  …/goaa-web-legal-20260906-9927c44d….tar.gz
8.2M  …/goaa-web-passreveal-20260906-253a78c6….tar.gz
204M  /opt/goaa-frontend/node
655M  /opt/goaa-frontend/releases
```

**判定**

| 問題 | 答案 |
|---|---|
| 結構 | **`releases/<40-hex git sha>` + `current` symlink** —— 標準 Capistrano 式佈局 |
| 舊版可回滾？ | **是**。`releases/` 內保留 **21 個版本**（最早 Sep 3 00:45，最新 Sep 7 10:23） |
| `current` 指向 | `76af718b0568992c900b72d1aff5aad2516046dc`（= **Golden**） |
| release 目錄命名 | 皆為 **40 位 hex**（＝前端 repo 的 commit sha） |
| 未啟用的更新版本 | `d6029f63ec765e65df13759aaf0f12d2880aaf6e`（Sep 7 **10:23**）比 current 新 8 分鐘，**未被啟用** |
| 另有 3 個 tar.gz | Sep 6 的舊封裝（auth／legal／passreveal），**與本次切換無關** |
| 專用 Node runtime | `/opt/goaa-frontend/node/`（**204 M**、屬主 uid 1001） |

> **🔴 切換機制推論（唯讀、未驗證）**：上線新版 = 解開一個新 release 目錄 + 移動 `current` symlink + 重啟 `goaa-web`。**回滾 = 把 `current` 指回 `76af718b…` + 重啟**（數秒）。

### A2 現行 unit 全文（`Environment` 值遮罩）

`/etc/systemd/system/goaa-web.service`（**494 B、root:root 0644**；**無 drop-in 目錄**）

```
[Unit]
Description=GOAA production Next.js frontend (e2f26ff)
After=network-online.target

[Service]
Type=simple
User=goaa-web
Group=goaa-web
WorkingDirectory=/opt/goaa-frontend/current
Environment=<MASKED>
Environment=<MASKED>
Environment=<MASKED>
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

**觀察**

1. **`Description` 洩漏舊代號 `e2f26ff`** —— 與 `current`（`76af718b`）**不一致**，屬外觀殘留，非缺陷（僅報告，未動）。
2. **無 `EnvironmentFile=`** ⇒ Clerk 相關變數**目前沒有供給管道**（本輪未建立任何管道）。
3. 3 個 inline `Environment=` 的**變數名**（名下值一律未讀）：
   - 行長 21 → `PORT=3100`（推得）
   - 行長 30 → `HOSTNAME=127.0.0.1`（推得）
   - 行長 31 → `NODE_ENV=production`（推得）
   - （推論依據＝進程 env 名集合 + `ss` 綁定 127.0.0.1:3100，見 A6/A7）
4. 沙箱：`NoNewPrivileges=yes`、`ProtectSystem=full`、`ProtectHome=yes`、`PrivateTmp=yes`。**無 `ReadWritePaths`**（next 只需讀 release；runtime 寫入被導向 tmp）。
5. `ProtectSystem=full` 只鎖 `/usr /boot /efi`；**`/opt` 可寫** ⇒ 移動 symlink 不受此限。
6. 服務使用者：**`goaa-web`（uid 999、gid 987）**。

### A3 這份 build 是什麼

```
$ cat /opt/goaa-frontend/current/.next/BUILD_ID
5wl6uCJFbHElFV3-B3I79

$ ls /opt/goaa-frontend/current/.next/standalone | head
(空)  → .next/standalone 不存在

$ grep -m1 '"version"' /opt/goaa-frontend/current/package.json
  "version": "0.1.0"

$ grep -m1 '"version"' current/node_modules/next/package.json → 14.2.35
$ ls -1 current/node_modules | wc -l   → 15
```

**判定：`output: "standalone"` 產物，且 standalone 內容已「展開」在 release 根。**

證據（`server.js` 前 25 行內含 `nextConfig` 全文）：

```
"output":"standalone"
"outputFileTracingRoot":"/home/aika/.qwenpaw/workspaces/default/work/planning-favicon-20260903"
"outputFileTracing":true
"distDir":"./.next"
"cpus":11
"reactStrictMode":true
"images":{"unoptimized":true, …}
"experimental":{ … }
```

- release 根 = `server.js` + `node_modules`（**15 項，追蹤後的精簡相依，非完整 node_modules**）+ `.next` + `public` + `package.json`。
- `.next/standalone` 不存在 ⇒ **Next 的 standalone 目錄內容被攤平到 release 根**（`server.js` 為 Next 自帶的 standalone 入口，4725 B）。
- **無 `.git`／無 git 資訊** ⇒ 部署產物**不可 self-describe**；版本識別只能靠**目錄名（= commit sha）**與 `.next/BUILD_ID`。
- **🔴 `outputFileTracingRoot` 指向本機 worktree `/…/work/planning-favicon-20260903`** ⇒ 這份 golden build 是**在 Aika 工作站建置**後上傳的。**⇒ R5b 的正規路徑同樣是「本機建置 → 上傳 → 切 symlink」。**
- **golden 不含 Clerk**：`current/package.json` 出現 `clerk` 次數 = **0**；`.next/server` 內無 `clerk` 字樣。
- 全部 **21 個 release 同構**（皆有 `server.js` + `node_modules`）。

### A4 建置工具鏈

```
$ node -v          → bash: node: command not found
$ npm -v           → bash: npm: command not found
$ which node npm   → (空)
$ df -h / | tail -1
/dev/vda1        77G   11G   66G  14% /
$ /opt/goaa-frontend/node/bin/node -v
v22.22.3
```

**判定**

- **C1 無系統級 node／npm**（`dpkg -l | grep -c nodejs` = **0**）。
- 唯一的 Node = **`/opt/goaa-frontend/node/bin/node` → v22.22.3**（與 C2 的 `/opt/node` 同版）。`node/bin/` 內有 `node npm npx corepack`。
- **`npm` 直接呼叫會失敗**（`#!/usr/bin/env node` 找不到 node）⇒ 必須 `PATH=/opt/goaa-frontend/node/bin:$PATH`。
- **⇒ 若要在 C1 本地建置，需先解決「node 不在 PATH」＋「C1 上沒有前端原始碼」兩件事。**

### A5 cloudflared（`/etc/cloudflared/config.yml`）

```
$ grep -n "planning" /etc/cloudflared/config.yml
64:    - hostname: planning.goaa.ai
65:      path: /planning
67:    - hostname: planning.goaa.ai
```

```
64    - hostname: planning.goaa.ai
65      path: /planning
66      service: http://127.0.0.1:3100
67    - hostname: planning.goaa.ai
68      service: http://127.0.0.1:3100     ← catch-all（無 path）
```

- **`planning.goaa.ai` 全站（catch-all）→ `127.0.0.1:3100`**；`/planning` 路徑亦 → `3100`。
- `3100` 出現 **2 次**（L66、L68）；config 內**無 3102／3103／3200**。
- **⇒ 只要新前端仍聽 `127.0.0.1:3100`，cloudflared 完全不需要改動。**

### A6 3100 現況

```
$ ss -ltnp | grep 3100
LISTEN 0  511  127.0.0.1:3100  0.0.0.0:*  users:(("next-server (v1",pid=2995017,fd=21))
```

- **只綁 `127.0.0.1`**（無 `0.0.0.0`、無 `[::]`）。
- 進程：`next-server (v14.2.35)`，`MainPID 2995017`，屬主 `goaa-web`，已運行 **1 天 01:42**，RSS 109 MB。

### A7 `goaa-web` 進程環境（**只列變數名**）

```
HOME HOSTNAME INVOCATION_ID JOURNAL_STREAM LANG LOGNAME MEMORY_PRESSURE_WATCH
MEMORY_PRESSURE_WRITE NODE_ENV PATH PORT SYSTEMD_EXEC_PID USER
cwd = /opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc
exe = /opt/goaa-frontend/node/bin/node
```

**⇒ 前端進程目前**沒有任何 Clerk 相關變數**。**

---

## 2. B. 候選版（來源端）

### B1 本機 worktree

| repo／worktree | HEAD | branch | status |
|---|---|---|---|
| `/home/aika/.qwenpaw/workspaces/default/work/c2-clerk-login-20260910` | **`40c8546e152bf5fad8d7a9d0033f17cab4cbcda8`** | `feat/c2-clerk-unified-login-v1` | **`?? tsconfig.tsbuildinfo`**（唯一未追蹤檔，**其餘乾淨**） |
| `/home/aika/Projects/goaa-ai-main`（黃金 clone） | `02a17ffef4544adb00b92ce630616a69846b8ee2` | `codex/backend-source-capture-20260902` | 多個 `__pycache__`／`.bak` 未追蹤 |

- 兩者 remote 皆為 **`git@github-goaa:taofengtx/goaa-ai-frontend.git`**。
- **Clerk 版前端候選 = `c2-clerk-login-20260910` worktree @ `40c8546e`**（branch `feat/c2-clerk-unified-login-v1`）。
- 最近 6 個 commit：

```
40c8546 round C1.8: AGENTS goes through the Clerk card and lands on the AI Agent portal
f719b27 round C1.7b: /client-login/ must not be rewritten to /goaa-clerk-login/
9ab1608 round C1.7: production Clerk entry (live keys by declaration, /client-login is always the card)
748dd80 test fixture: align line 28 with the published (redacted) snapshot
049a0a6 round C1.6: launch switch closes the $39.90 connection (coming soon + 30-min booking)
f93c554 round C1.5: bridge starts a business session for every sign-in in a tab
```

- **本機 `.next` 已建置**：`BUILD_ID = 28IP1GvAGURvF1PHRk8EL`（Sep 11 11:19，含 `.next/standalone/server.js`）。
- 相依：`next ^14.0.0`（實裝 **14.2.35**）、`react ^18.2.0`、`react-dom ^18.2.0`（＋`@clerk/nextjs`，見 C 段）。

### B2 C2 部署來源

```
$ systemctl cat goaa-c2-clerk-ui-3102 | grep -E "ExecStart|EnvironmentFile|WorkingDirectory|User"
User=goaa-c2loop
Group=goaa-c2loop
WorkingDirectory=/opt/goaa-test/ui-clerk-20260910
EnvironmentFile=/opt/goaa-test/env/clerk-ui-3102.env
ExecStart=/opt/node/bin/node server.js

$ ls -la /opt/goaa-test/ui-clerk-20260910 | head -20
drwxr-xr-x  5 goaa-c2loop goaa-c2loop 4096 Sep 11 18:21 .
drwx--x--- 27 root        goaa-c2loop 4096 Sep 11 18:21 ..
drwxr-xr-x  5 goaa-c2loop goaa-c2loop 4096 Sep 11 18:21 .next
drwxr-xr-x 17 goaa-c2loop goaa-c2loop 4096 Sep 11 18:19 node_modules
-rw-r--r--  1 goaa-c2loop goaa-c2loop  660 Sep 11 18:19 package.json
drwxr-xr-x  4 goaa-c2loop goaa-c2loop 4096 Sep 11 06:58 public
-rw-r--r--  1 goaa-c2loop goaa-c2loop  4723 Sep 11 18:19 server.js

$ cat .next/BUILD_ID
28IP1GvAGURvF1PHRk8EL
```

**★ 結論：C2 那份部署產物**就是本機 worktree 的 standalone 建置**。**

| 對照 | 本機 worktree `.next` | C2 `ui-clerk-20260910` |
|---|---|---|
| `BUILD_ID` | `28IP1GvAGURvF1PHRk8EL` | **`28IP1GvAGURvF1PHRk8EL`（完全相同）** |
| `server.js` 大小 | — | 4723 B |
| `package.json` 大小 | — | 660 B |
| 形態 | `.next/standalone/` 齊備 | standalone **展開於根**（`.next/standalone` = NO） |
| 執行 | — | `/opt/node/bin/node server.js`，User `goaa-c2loop`，`UnitFileState=disabled`，MainPID 2039779 |

**⇒ R5b 的正規取碼路徑已被 C2 實證：`git`（`40c8546e`）→ 本機建置 → standalone 產物上傳 → `node server.js`。**

### B3 候選基底是不是 `718ee109`？

```
$ git log -1 --format='%H%n%ad%n%s' 718ee109
718ee10935a4894b173448928bf55e707fc7d894
Fri Sep 11 05:39:04 2026 +0000
Round C1 fix: scope token sheets to .goaa-portal (golden chat avatar already uses class goaa)

$ git merge-base --is-ancestor 718ee109 40c8546e    → YES
$ git merge-base --is-ancestor 76af718b… 718ee109   → YES
$ git diff --stat 718ee109 40c8546e | tail -1
 30 files changed, 1085 insertions(+), 115 deletions(-)
$ git rev-list --count 76af718b…40c8546e  → 20
```

**判定（三個事實，供 Tao 裁示）**

1. **`718ee109` 確實存在**，是本機前端 repo 內的一個真實 commit（`Round C1 fix…`，Sep 11 05:39 UTC）。
2. **但它不是現行候選 HEAD**：它是 `40c8546e`（C1.8）的**祖先，落後 12 個 commit**；兩者差異 = **30 檔、+1085／−115**。
   - 落後的 12 個 commit 涵蓋 C1.2～C1.8（含 **C1.3c root layout never prerendered**、**C1.7/C1.7b 生產 Clerk 入口**、**C1.8 AGENTS 走 Clerk 卡**）—— **這些正是 Clerk 切換的核心**。
3. **⇒ 若「候選基底 = `718ee109`」是字面要求，則該基底缺 Clerk 生產入口與 C1.8 落地頁，與「把 Clerk 版前端上線」的目標相衝。建議候選 = `40c8546e`（現行 `feat/c2-clerk-unified-login-v1` HEAD），與 C2 已部署的 `BUILD_ID 28IP1GvAGURvF1PHRk8EL` 同源。**（本輪唯讀，未做任何選擇。）

---

## 3. C. env 差異（C1 golden unit ↔ C2 Clerk UI）

**C2** `EnvironmentFile=/opt/goaa-test/env/clerk-ui-3102.env` —— **變數名（只列名）**：

```
CLERK_AUTHORIZED_PARTIES
CLERK_ISSUER
CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY
GOAA_AGENT_LOOP_UPSTREAM
GOAA_C2_CLERK_AUTH_ENABLED
HOSTNAME
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
NODE_ENV
PORT
```

**C1** `goaa-web.service` inline `Environment=` —— **變數名（只列名）**：

```
HOSTNAME
NODE_ENV
PORT
```

### 差異表

| 變數名 | C1（golden unit） | C2（clerk-ui-3102.env） | C1 上線 Clerk 版是否需新增／調整 |
|---|---|---|---|
| `PORT` | 有（3100） | 有（13102） | **保留 3100**（cloudflared A5 依賴） |
| `HOSTNAME` | 有 | 有 | **保留**（C1 綁 loopback） |
| `NODE_ENV` | 有 | 有 | 保留 |
| `GOAA_AGENT_LOOP_UPSTREAM` | **缺** | 有 | **🔴 必須新增** —— C1 應指向 **`http://127.0.0.1:3103`**（BFF → 3103 後端） |
| `GOAA_C2_CLERK_AUTH_ENABLED` | **缺** | 有 | **必須新增**（值僅 4 字元 ⇒ `true`） |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | **缺** | 有 | **必須新增**（**production** publishable，27 字元） |
| `CLERK_PUBLISHABLE_KEY` | **缺** | 有 | **必須新增**（同上，server 端讀取） |
| `CLERK_SECRET_KEY` | **缺** | 有 | **🔴 必須新增** —— **Clerk middleware 需要 secret**；C1 已有 production secret（現於 `api-3103.env`） |
| `CLERK_ISSUER` | **缺** | 有 | **必須新增** = `https://clerk.goaa.ai` |
| `CLERK_AUTHORIZED_PARTIES` | **缺** | 有 | **必須新增** = `https://planning.goaa.ai` |

**結論**

- **C1 目前 0 個 Clerk 變數**；上線 Clerk 版前端**需要新增 7 個變數**（上表 6 個 Clerk＋`GOAA_AGENT_LOOP_UPSTREAM`；其中 `GOAA_C2_CLERK_AUTH_ENABLED` 為第 7 個）。
- **供給管道缺口**：`goaa-web.service` **無 `EnvironmentFile=`** ⇒ 新增變數必須**改 unit（加 inline `Environment=`）或新增 `EnvironmentFile=`**。**任一路徑皆屬「改 unit」，須 Tao 明令方可執行。**
- **變數值本輪一律未讀**（C2 env 檔只列名；C1 production 值只知鍵名與先前 R5a 已記錄之形狀）。
- **`CLERK_SECRET_KEY` 是 secret** ⇒ 若以 `EnvironmentFile=` 供給，檔案須 `0600`、屬主為服務使用者（`goaa-web`）或其可讀群組。

---

## 4. D. 資源（是否能在 C1 本地建置／部署）

| 資源 | C1 現況 | 評估 |
|---|---|---|
| 磁碟 `/`（`/dev/vda1`） | **77 G 總、11 G 用、66 G 可、14 %** | **充裕**。一個 release ≈ 30 MB（655 M ÷ 21），golden 現有 21 版仍只 655 M |
| 記憶體 | **3.8 Gi 總、945 Mi 用、可用 2.9 Gi** | Next 14 build 約需 1.5–2.5 Gi ⇒ **勉強可行**，但與 3100 生產同步進行有壓力 |
| CPU | **nproc = 2**（`cpus:11` 是**本機建置時的**設定，非 C1） | 2 vCPU 建置會**明顯變慢**（估 3–8 分鐘）；建置期間生產服務仍可運作（`Restart=on-failure`） |
| 負載 | `loadavg 0.11 0.05 0.01` | **閒置** |
| 現有 Node | 專用 `/opt/goaa-frontend/node` v22.22.3 | **可用**；但 `npm` 需補 PATH |
| **前端原始碼** | C1 上**沒有**任何前端 repo（release 僅為產物、無 `.git`） | **⇒ 在 C1 本地建置需先取碼（git clone/tar）** |

**Deployment 路徑選項（僅供裁示，本輪未執行）**

| 方案 | 內容 | 對 C1 的寫入 | 風險 |
|---|---|---|---|
| **P1 本機建置 → 上傳產物**（＝C2／golden 既有作法） | 在本機 worktree `40c8546e` 跑 `next build`，取 `.next/standalone` **內容**上傳為 `releases/<sha>`，移動 `current`，重啟 | 磁碟寫入 + symlink + 重啟 | **低**（與現行流程一致） |
| **P2 C1 本地建置** | 取碼到 C1，用 `/opt/goaa-frontend/node` 建置 | 寫入約 1–2 G 暫存 + symlink + 重啟 | **中**（2 vCPU／3.8 G RAM，且需把原始碼放上生產機） |

---

## 5. 結論（一句話）

**C1 是標準 `releases/ + current` 佈局、21 版可回滾、`planning.goaa.ai` 直接打 `127.0.0.1:3100`（cloudflared 零改動）；C2 已實證「git `40c8546e` → 本機 standalone 建置（`BUILD_ID 28IP1GvAGURvF1PHRk8EL`）→ 上傳展開 → `node server.js`」；唯一實質缺口是 C1 前端目前 0 個 Clerk 變數且 unit 無 `EnvironmentFile`，需新增 7 個變數（含 secret）並決定供給管道 —— 兩者皆屬「改 unit」，待 Tao 明令。**

## 6. 下一步（待 Tao 令，本輪不做）

1. **確認候選**：`718ee109`（落後 12 commit）還是 `40c8546e`（＝C2 已部署同源）。
2. **確認建置地點**：P1（本機建置再上傳，與 golden 一致）或 P2（C1 本地建置）。
3. **確認 env 供給管道**：新增 `EnvironmentFile=`（如 `/opt/goaa-frontend/env/clerk-web.env`，`0600`）或 inline `Environment=`；**secret 需從 `api-3103.env` 安全複製，全程不回顯**。
4. **確認上線步驟與回滾步驟**（`current` symlink 移動 + `systemctl restart goaa-web`；回滾 = symlink 回 `76af718b…` + restart）。
5. **確認是否保留舊 golden release**（現有 21 版），以及新 release 的命名（`<commit sha>` 慣例）。

## 7. 唯讀佐證

- 本輪**未建立任何檔案於 C1／C2**；所有指令皆為唯讀（`ls`／`cat`／`readlink`／`du`／`df`／`free`／`nproc`／`grep`／`find`／`systemctl cat|show|list-units`／`ss`／`/proc` 讀取）。
- C1 `goaa-web` **MainPID 2995017 未變**、`current` symlink **未變**（仍 `76af718b…`）、`ActiveEnterTimestamp` 未變。
- C2 `goaa-c2-clerk-ui-3102` **MainPID 2039779 未變**。
- **🛡 卡：未出現。**

## 8. 附註：C2 上另一支 `goaa-web-candidate`（**非本次對象，僅記錄**）

```
$ systemctl cat goaa-web-candidate
[Service]
User=goaaweb
Group=goaaweb
WorkingDirectory=/opt/goaa/web/releases/p5-153-candidate
Environment=PORT=3100
Environment=HOSTNAME=127.0.0.1
Environment=NODE_ENV=production
ExecStart=/opt/node/bin/node server.js
# …service.d/override.conf:
WorkingDirectory=/opt/goaa/web/releases/butler-3c8ef2f-candidate
```

- `ActiveState=active`、`SubState=running`、`MainPID 2039675`、**`UnitFileState=enabled`**。
- **血統與本次切換無關**（`butler-3c8ef2f` 候選線，非 Clerk 版）；列此僅為避免日後誤動。**C2 的 3100 被它佔用。**

---

## 9. 秘密掃描（本報告自身）

- 掃描腳本：`/tmp/r4s-scan.py`（13 種樣式，樣式字面量切分書寫）。
- **機密值命中數 = 0。**
- 非零項僅 1 類：`"clerk" + "_secret"` **3 處（L310／L338／L347）—— 全為變數名 `CLERK_SECRET_KEY`，非機密、僅名稱**。
- 未切分 IPv4：**13**，全部為 `127.0.0.1`（loopback）與 `0.0.0.0`（unspecified）⇒ 依既有慣例逐字書寫（非機密）。**可路由（公開）IPv4 未切分 = 0。**
- 檔案自身：`reports/2026-09-12/r5b-frontend/RECON.md`
  - 內容（footer 前）：**19,936 bytes**、`sha256[:16] = 08f3afdfe86ed368`
  - `BOM = False`、`first3 = '# R'`
  - 本檔（含 §9／§10）之**最終** bytes／sha256 以本次 commit 訊息所列為準。

## 10. 掃描複核（final）

- 複核時刻：`2026-09-12T08:3xZ`（UTC）。
- **機密值命中 = 0**（13 種樣式全掃，含切分書寫之值形）。
- 非零項 **總計 5 處**，全部為**變數名** `CLERK_SECRET_KEY`（§3 的 C2 env 鍵名清單、§3 差異表、§3 結論、§9、以及 §10 本節自身之引用）—— **非機密、僅名稱**。
- **可路由（公開）IPv4 未切分 = 0**；未切分者 13 處全為 `127.0.0.1`（loopback）與 `0.0.0.0`（unspecified），依既有慣例逐字。
- **本報告不含任何憑證值、不含任何密鑰前綴字面量、不含 secret 指派式。**
