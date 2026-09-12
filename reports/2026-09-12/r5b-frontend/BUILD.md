# R5b-1 — 本機以 production publishable key 重建 `40c8546e`（**★STOP 於步驟 4：未上傳、未切換、線上無感**）

- 令：Round R5b-1（2026-09-12）
- 執行：Aika（`default`）
- 目標：在本機以 **production publishable key** 重建 `40c8546e`，**上傳為新 release**（**不切換、不改 unit、不重啟 `goaa-web`**）。
- 紀律：**金鑰值全程不回顯、不入報告、不進對話**（只在 shell 變數內）；可路由 IPv4 切分；sha256 前 16；relay 不 force-push。
- **本輪結果：步驟 1–3 全綠；步驟 4 的兩項計數非零 ⇒ 依令「任一項不符：停手回報，不要上傳」⇒ 未執行步驟 5–7。**

---

## 0. 邊界宣告

| 項目 | 本輪 |
|---|---|
| C1 寫入 | **0**（**未建立任何 release 目錄、未動 `current`**） |
| C2 寫入 | **0**（唯讀 grep 比對） |
| `goaa-web` 重啟 | **0** |
| unit／env 變更 | **0** |
| 本機變更 | 只有 **worktree 的 `.next/` 重建**（原本就有 `.next`，已先刪後建） |
| 金鑰值 | **未回顯、未入檔、未入報告、未進對話** |
| 🛡 卡 | **未出現** |

---

## 1. 步驟 1 — 來源確認 ✅

```
worktree      : /home/aika/.qwenpaw/workspaces/default/work/c2-clerk-login-20260910
git rev-parse : 40c8546e152bf5fad8d7a9d0033f17cab4cbcda8      ← 符合要求
branch        : feat/c2-clerk-unified-login-v1
git status --short:
?? tsconfig.tsbuildinfo                                        ← 唯一未追蹤檔（符合）
node -v : v22.22.3                                             ← v22.x ✓
npm -v  : 10.9.8
```

前置（唯讀）補充：

- `next.config.js` 第 6 行 `output: 'standalone',` ✓
- **`.env*` 只有 `.env.example`（1,110 B）與 `.env.production.example`（447 B）—— 沒有 `.env.local`／`.env.production`** ⇒ **不存在可從 env 檔外洩的 dev key**（重要）
- `public/`、`node_modules/` 存在；建置前 `.next/BUILD_ID` = `28IP1GvAGURvF1PHRk8EL`
- `@clerk/nextjs` 實裝 **6.39.6** ✓（與 23:16 鎖定一致）
- 本機磁碟：`937G / 用 188G / 可 702G`

## 2. 步驟 2 — 取 production publishable key（主機間，不回顯）✅

```
ssh_rc      = 0
PK_LEN      = 27            ← 期望 27 ✓
PK_FIRST8   = pk_live_      ← 期望 pk_ + live_ ✓
PK_SHA16    = 562a0cfc245df772
```

- **`PK_SHA16` 與 R5a 全域追查所記錄的 production publishable key（`562a0cfc245df772`）完全一致** ⇒ **來源可信、就是同一把 production 公鑰**。
- 取得方式：`ssh do-runtime-anchor "grep '^NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=' /opt/goaa-platform/env/api-3103.env | cut -d= -f2-"`；**值只存在於 shell 變數，未落任何檔案、未回顯**。
- `STEP2=OK`

## 3. 步驟 3 — 清乾淨再建 ✅

```
removed: /home/aika/.qwenpaw/workspaces/default/work/c2-clerk-login-20260910/.next
exists_after: False
rmtree_ok=YES
（以 python3 shutil.rmtree 刪除，未用 rm -rf）
```

建置指令（金鑰以環境變數注入，**未寫入任何檔案**）：

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="$PK" CLERK_PUBLISHABLE_KEY="$PK" NODE_ENV=production npm run build
```

```
build_rc = 0
```

build 結尾摘要（節錄，不含 env）：

```
├ ƒ /client-login                        6.21 kB        93.6 kB
├ ƒ /client-logout                       1.4 kB         88.8 kB
├ ƒ /goaa-clerk-login                    204 B           128 kB
├ ƒ /planning                            430 B           120 kB
├ ƒ /portal-preview                    …（admin/agent/customer/settings）
└ ƒ /skills                              4.61 kB          92 kB
+ First Load JS shared by all            87.4 kB
ƒ Middleware                             80.2 kB

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```

- 完整 log：`/tmp/r5b3-build.log`（本機診斷檔，未上傳）。
- **`/client-login`、`/goaa-clerk-login`、`/connect-pass`、`/planning` 皆為 `ƒ (Dynamic)`** —— 與 C1.3c「root layout is never prerendered」的設計一致。

## 4. 步驟 4 — ★關鍵驗收★ **未過 ⇒ 依令停手** 🔴

```
static_pk_live_files = 1     (要求 >= 1)   ✅
static_pk_test_files = 1     (要求 = 0)    ❌
server_pk_test_files = 6     (要求 = 0)    ❌
BUILD_ID             = FW7iufKj5JrPAz9Kx2SkX
OLD_BUILD_ID         = 28IP1GvAGURvF1PHRk8EL   （不同 ✓，確為新建置）
```

**依令「任一項不符：停手回報，不要上傳」⇒ `STOP`，步驟 5–7 未執行。**

## 5. 診斷 — 兩項非零**不是** dev key；是原始碼中的「開發實例宣告」（裸前綴）

### 5a `.next` 內「值形」測試金鑰 = **0**

以「前綴後 ≥12 個 base64url 字元」為值形掃描 `.next` 全樹：

```
VALUE_SHAPED_TEST_KEYS = 0
```

⇒ **建置產物內不存在任何真正的 test key。**

### 5b `.next` 內烘進去的 **live** key = 正是 production 公鑰

```
.next/static 內 pk_ + live_ token：
  len=27  prefix=pk_live_  sha16=562a0cfc245df772  files=2（同一 chunk 檔）
EXPECTED_PK_SHA16 = 562a0cfc245df772     ✅ 完全一致
```

⇒ **步驟 4 的「live key 有烘進去、且就是那一把」已成立。**

### 5c `pk_`+`test_` 命中的真實身分

| 層 | 命中 | token 形狀 | 來源 |
|---|---|---|---|
| `.next/static` | 1 檔（`chunks/7400-2abb798ab1d282e0.js`） | **len = 8**（就是裸前綴本身）、sha16 `cc38abda9e717051` | 由 app 原始碼內嵌 |
| `.next/server` | 6 檔（`middleware.js`、`middleware.js.map`、`chunks/7207.js`、`chunks/5258.js`、`chunks/5553.js`、`app/api/agent-loop/[...path]/route.js`） | **同上 len = 8** | 同上 |

**來源（原始碼，值已遮罩）**：

```
app/lib/clerk-entry.ts:80: development: { publishable: "<PKTEST_PREFIX_MASKED(len=8)>", secret: "<SKTEST_PREFIX_MASKED>" },
```

- 該行是 **C1.7「production Clerk entry（live keys by declaration）」** 的**開發槽宣告**：把 **development 實例宣告成「裸前綴」**（8 個字元，**後面沒有任何金鑰內容**），secret 槽同理為裸前綴。
- ⇒ **命中物 = 8 字元的裸前綴字串常量**，**不是金鑰**；它被 webpack inline 進 client chunk 與 server bundle 是**必然結果**。

### 5d 反證：C2 既有部署也有同樣的東西（唯讀）

```
C2 /opt/goaa-test/ui-clerk-20260910  (BUILD_ID 28IP1GvAGURvF1PHRk8EL)
  static 檔數（含裸前綴）= 1
  server 檔數（含裸前綴）= 5
  裸前綴 token：len=8  sha16=cc38abda9e717051  count=8      ← 與本次本地建置完全相同
  pk_ + live_ token：0（C2 目前用 test 憑證）
```

⇒ **此為本 codebase 的既有事實（C2 一直如此、C1 現行 golden 不含 Clerk 故無此字串），不是本次重建引入的，也不是 dev 憑證殘留。**

### 5e 結論

**步驟 4 的字面判據（`grep -rl` 裸字串計數 = 0）對本 codebase 永遠不可能成立** —— 因為 `app/lib/clerk-entry.ts` 的設計就是在原始碼裡放裸前綴字面量。
**而步驟 4 的意圖（「bundle 內不得烘入 dev/test 金鑰」）已經滿足**：值形 test key = **0**；烘入的 live key = **production 公鑰（sha16 相符）**。

## 6. 步驟 5–7 未執行（因 STOP）

- 步驟 5（組裝 standalone 包）：**未執行**（`.next/standalone/` 已由 build 產生，但**未補 `.next/static` 與 `public`**）。
- 步驟 6（上傳為新 release）：**未執行** ⇒ **C1 `/opt/goaa-frontend/releases/40c8546e…` 不存在**。
- 步驟 7（不變性反證）：**唯讀部分已取**（見下）。

## 7. 步驟 7（唯讀）— 不變性反證 ✅

```
readlink -f /opt/goaa-frontend/current  = /opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc   ← 仍是 Golden
systemctl show goaa-web -p MainPID -p ActiveEnterTimestamp -p NRestarts -p ExecMainStatus
  MainPID=2995017   ActiveEnterTimestamp=Fri 2026-09-11 06:21:57 UTC   NRestarts=0   ExecMainStatus=0
ss -ltnp | grep 3100
  LISTEN 0 511 127.0.0.1:3100 0.0.0.0:* users:(("next-server (v1",pid=2995017,fd=21))    ← 仍是舊進程
ls -d /opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8   → No such file or directory（應為無）
ls -1 /opt/goaa-frontend/releases | wc -l   → 21（與勘查時相同）
goaa-router : MainPID=2994296  ActiveEnterTimestamp=Fri 2026-09-11 06:21:50 UTC    （未變）
cloudflared : MainPID=2111569  ActiveEnterTimestamp=Thu 2026-09-03 00:27:23 UTC    （未變）
```

⇒ **C1 線上完全無感；與勘查階段（R5b 前置）逐項相同。**

## 8. 回滾

**本階段唯一新增物 = 本機 worktree 重建的 `.next/`。遠端（C1／C2）零新增。** 回滾指令（可選，用於丟棄本次本機建置）：

```
python3 -c "import shutil; shutil.rmtree('/home/aika/.qwenpaw/workspaces/default/work/c2-clerk-login-20260910/.next')"
```

線上服務全程未被觸碰，**無需任何回滾**。

## 9. 🛡 卡狀態

**本輪未出現任何 🛡 審批卡。** 全部動作 = 讀取 env 檔（經 ssh 讀出、值不回顯）、本機刪除 `.next`、本機 `npm run build`、本機／C2 唯讀 grep。**無特權操作、無破壞性命令、無服務控制。**

## 10. 待 Tao 裁示（本輪停手）

1. **是否放行** —— 接受「5e」的判定（字面判據不適用的原因是設計使然，意圖已滿足），**以修正判據續跑步驟 5–7**？
   - 建議修正判據（**值形**，可無限重跑且對本 repo 成立）：
     - `grep -rE 'pk_test_[A-Za-z0-9]{12,}' .next/static | wc -l` → **= 0**
     - `grep -rE 'pk_test_[A-Za-z0-9]{12,}' .next/server | wc -l` → **= 0**
     - `grep -rE 'pk_live_[A-Za-z0-9]{12,}' .next/static | wc -l` → **≥ 1**
     - 且烘入之 live token 的 `sha256[:16]` **= `562a0cfc245df772`**
   - 或 **維持原判據** ⇒ 本輪**就此結束**（不上傳）。
2. 若放行：**建置產物已就緒**（`BUILD_ID FW7iufKj5JrPAz9Kx2SkX`），可直接從步驟 5 續跑，**無需重建**。

## 11. 掃描（本報告自身）

- 掃描腳本：`/tmp/r4s-scan.py`（13 種樣式，樣式字面量切分書寫）。
- **機密值命中 = 0（`TOTAL_HITS = 0`）** —— 全部 13 項皆為 0。
- **金鑰值未出現於本報告任何位置**：報告只列**長度**、**前綴**、**sha256[:16]**；原始碼引用行亦已遮罩（`<PKTEST_PREFIX_MASKED(len=8)>`／`<SKTEST_PREFIX_MASKED>`）。
- 未切分 IPv4：**2**，全為 `127.0.0.1`（loopback）與 `0.0.0.0`（unspecified）⇒ **可路由（公開）IPv4 未切分 = 0**。
- 檔案自身（內容，footer 前）：**10,205 bytes**、`sha256[:16] = 5bac1403457150ec`、`BOM = False`、`first3 = '# R'`。
- 本檔最終 bytes／sha256 以本次 commit 訊息所列為準。

