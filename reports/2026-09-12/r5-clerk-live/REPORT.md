# R5a｜後端 3103 換上 production Clerk 憑證並重驗 —— **STOP（步驟 1 阻斷）**

- 輪次：**R5a**（Clerk 憑證切換至 production）
- 日期：2026-09-12（C1/C2 UTC 07:2x）
- 結論：**在步驟 1 就觸發「找不到 live 憑證即停手」的條件 ⇒ 未執行步驟 3、步驟 4。**
  - **C1 零變更**：`api-3103.env` 未被修改、未建立備份、未傳輸任何憑證、**服務未重啟**（`MainPID 3110526` 不變、`NRestarts=0`）。
  - **C2 零變更**：全程唯讀。
  - **🛡 卡：本輪未出現任何 🛡 卡**（因為沒有執行到 `restart`）。
- 邊界遵守：未動前端、未動 `cloudflared` / `ufw` / `DOCKER-USER` / `pg_hba`、未碰 `goaa` 庫、未改 unit。**未使用任何非指定目錄搜尋**（未去別處翻憑證）。

---

## 1. 步驟 1｜定位 D2（C2）上的 production 憑證檔

### 1.1 依令執行（原樣指令）

```
for f in /opt/goaa-test/env/*; do
  [ -f "$f" ] || continue
  pk=$(grep -c 'pk_live' "$f" 2>/dev/null || echo 0)
  sk=$(grep -c 'sk_live' "$f" 2>/dev/null || echo 0)
  pkt=$(grep -c 'pk_test' "$f" 2>/dev/null || echo 0)
  printf '%s pk_live=%s sk_live=%s pk_test=%s\n' "$f" "$pk" "$sk" "$pkt"
done
```

> **量測瑕疵（已修正，誠實交代）**：`grep -c` 在「零命中」時會**同時**輸出 `0` 並回傳離開碼 1，因此 `|| echo 0` 會讓同一個 `0` 被印兩次（輸出折行成 `0` 與 `0` 兩行）。此為**輸出格式問題、不影響結論**（全部都是 0）。下表為修正版（移除 `|| echo 0`，並額外納入隱藏檔、三個備份檔與更廣的 `pk_`/`sk_` 計數）。

### 1.2 命中次數表（**只要數字**）

| 檔案 | pk_live | sk_live | pk_test | sk_test | pk_（廣） | sk_（廣） |
|---|---|---|---|---|---|---|
| `/opt/goaa-test/env/app.pgpass` | 0 | 0 | 0 | 0 | 0 | 0 |
| `/opt/goaa-test/env/app_role_password` | 0 | 0 | 0 | 0 | 0 | 0 |
| `/opt/goaa-test/env/clerk-api-3103.env` | **0** | **0** | 2 | 1 | 2 | 1 |
| `/opt/goaa-test/env/clerk-api-3103.env.bak-20260911-100202` | **0** | **0** | 2 | 1 | 2 | 1 |
| `/opt/goaa-test/env/clerk-ui-3102.env` | **0** | **0** | 2 | 1 | 2 | 1 |
| `/opt/goaa-test/env/clerk-ui-3102.env.bak-20260911-103145` | **0** | **0** | 2 | 1 | 2 | 1 |
| `/opt/goaa-test/env/clerk-ui-3102.env.bak-c16-open` | **0** | **0** | 2 | 1 | 2 | 1 |
| `/opt/goaa-test/env/clerk.env` | **0** | **0** | 2 | 1 | 2 | 1 |
| `/opt/goaa-test/env/clerk.env.bak-20260911-103150` | **0** | **0** | 2 | 1 | 2 | 1 |
| `/opt/goaa-test/env/goaa-c2-backend.env` | 0 | 0 | 0 | 0 | 0 | 0 |
| `/opt/goaa-test/env/migrate.pgpass` | 0 | 0 | 0 | 0 | 0 | 0 |
| `/opt/goaa-test/env/migrate_role_password` | 0 | 0 | 0 | 0 | 0 | 0 |
| `/opt/goaa-test/env/session_secret` | 0 | 0 | 0 | 0 | 0 | 0 |
| `/opt/goaa-test/env/.c2test-3103.env`（隱藏檔） | 0 | 0 | 0 | 0 | 0 | 0 |
| `/opt/goaa-test/env/.pgpass`（隱藏檔） | 0 | 0 | 0 | 0 | 0 | 0 |

**live 憑證檔搜尋（`grep -l`，含隱藏檔）：**

```
含 pk_live 的檔：（無）
含 sk_live 的檔：（無）
```

### 1.3 主要 Clerk 檔的鍵名（`cut -d= -f1 | sort`；只列名）

| 檔案 | 鍵名 |
|---|---|
| `clerk.env` | `CLERK_AUTHORIZED_PARTIES`、`CLERK_ISSUER`、`CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` |
| `clerk-api-3103.env` | 上述 5 鍵 + `GOAA_C2_CLERK_AUTH_ENABLED` + 既有 21 個 `GOAA_C2_*`（共 27） |
| `clerk-ui-3102.env` | `CLERK_AUTHORIZED_PARTIES`、`CLERK_ISSUER`、`CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`GOAA_AGENT_LOOP_UPSTREAM`、`GOAA_C2_CLERK_AUTH_ENABLED`、`HOSTNAME`、`NODE_ENV`、`PORT` |
| `.c2test-3103.env` | **只有 DB 系鍵**（無任何 Clerk 鍵） |

### 1.4 5 個 Clerk 鍵的「形狀」（值的前 8 字元；僅前綴、非全值）

| 鍵 | 形狀 | 長度 |
|---|---|---|
| `CLERK_PUBLISHABLE_KEY` | `pk_`+`test_` | 62 |
| `CLERK_SECRET_KEY` | `sk_`+`test_` | 50 |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `pk_`+`test_` | 62 |

⇒ **C2 上的 Clerk 憑證「全部是 test 前綴」，沒有任何 production（live）憑證。**

### 1.5 判定：**觸發停手條件**

依令：「若找不到 `pk_live`/`sk_live`，**立刻停手回報，不要猜、不要去別的目錄翻**。」
⇒ **停手。未執行步驟 3、步驟 4。**

---

## 2. 步驟 2｜C2 自己會不會被影響

### 2.1 C2 兩支服務實際載入的 EnvironmentFile

```
--- goaa-c2-clerk-api-3103 ---
EnvironmentFiles=/opt/goaa-test/env/clerk-api-3103.env (ignore_errors=no)
--- goaa-c2-clerk-ui-3102 ---
EnvironmentFiles=/opt/goaa-test/env/clerk-ui-3102.env (ignore_errors=no)
```

### 2.2 判定

| 問題 | 回答 |
|---|---|
| 含 `pk_live`/`sk_live` 的檔 | **一個都沒有**（`grep -l` 兩者皆空） |
| 該檔是否被 C2 兩支服務載入？ | **不存在「該檔」** ⇒ 前提不成立 |
| C2 下次重啟會不會切到 production？ | **不會。** 兩支服務載入的 `clerk-api-3103.env` / `clerk-ui-3102.env` 內容**都只有 test 前綴憑證**（`pk_test` 命中 2、`sk_test` 命中 1）⇒ 重啟後仍為 **test/dev 身分** |
| 本輪對 C2 的變更 | **零**（全程唯讀） |

### 2.3 順帶查到、但與本題無關的兩點（只報告，未動）

1. env 目錄另有兩個**隱藏檔**：`.c2test-3103.env`（758 B，僅 DB 系鍵、無 Clerk 鍵）與 `.pgpass`；以及 3 個備份檔（`clerk-api-3103.env.bak-20260911-100202`、`clerk-ui-3102.env.bak-20260911-103145`、`clerk-ui-3102.env.bak-c16-open`、`clerk.env.bak-20260911-103150`）—— **全部都是 test 憑證**，無一例外。
2. env 目錄權限 `drwx--x--- root:goaa-c2loop`，憑證檔為 `-r--r----- root:goaa-c2loop`；**未變更**。

---

## 3. 步驟 3｜**未執行**（原因）

**未備份、未傳輸、未改寫。** 因為**來源（C2 上的 production 憑證檔）不存在**：
要以「主機間直傳」方式取得 live 憑證，前提是**它們得先存在於某台主機上**；C2 的憑證目錄（含備份與隱藏檔）**全域 0 個 live 前綴**。

### 3.1 C1 現況（唯讀佐證，證明「未變更」且「同值」）

| 鍵 | C1 有 | C2 有 | 值是否相同 | 長度 |
|---|---|---|---|---|
| `CLERK_PUBLISHABLE_KEY` | yes | yes | **YES（同值）** | 62 |
| `CLERK_SECRET_KEY` | yes | yes | **YES（同值）** | 50 |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | yes | yes | **YES（同值）** | 62 |
| `CLERK_ISSUER` | yes | yes | **YES（同值）** | 47 |
| `CLERK_AUTHORIZED_PARTIES` | yes | yes | **YES（同值）** | 45 |
| `GOAA_C2_CLERK_AUTH_ENABLED` | yes | yes | **YES（同值）** | 4 |

> 比較方式：對兩邊的值各取 sha256 後**只比對是否相等**，**不輸出任何值或雜湊值**。

| 項 | 實測 |
|---|---|
| C1 鍵數 | **25**（不變） |
| C1 env 檔 | `mode=0600`、`uid=997`（`goaa-platform`）、`gid=986`、`1103 bytes`（不變） |
| C1 檔內 live 樣式殘留 | **0** |
| C1 服務 | `active (running)`、`MainPID 3110526`、`NRestarts=0`、`disabled`、僅 `127.0.0.1:3103`（**與步驟 5 結束時完全相同**） |
| C1 `/root/` 是否有 live 暫存檔 | **無**（無任何 `clerk`/`live`/`env.bak` 相關檔） |

⇒ **C1 的 3103 目前與 C2 使用同一組 test 憑證**；R5a 想達成的「換上 production」**完全未發生**。

---

## 4. 步驟 4｜**未執行**

未 `restart`、未驗 A–F。**因此本輪無 🛡 卡**（審批只在 `systemctl restart` 時才會出現）。服務維持步驟 5 的狀態：`active` + `disabled` + `MainPID 3110526`。

---

## 5. 回滾

**不需要。** 本輪對 C1/C2 **未做任何變更**（未備份、未改檔、未重啟）。
附錄（供 Tao 參考，**未執行**）——若未來真的完成換值而要回滾：

```
cp -a /root/api-3103.env.bak.<戳記> /opt/goaa-platform/env/api-3103.env
chown goaa-platform:goaa-platform /opt/goaa-platform/env/api-3103.env
chmod 600 /opt/goaa-platform/env/api-3103.env
systemctl restart goaa-platform-api-3103.service
```

---

## 6. 🛡 卡狀態

**Aika 端本輪未出現任何 🛡 卡；未經任何 approve 流程。**（未執行 `restart`，故未觸發審批。）一切以 Tao 為準。

---

## 7. 需要 Tao 裁定的事

1. **production 憑證的來源**：目前 C1/C2 **都沒有** live 憑證（全域 0 命中，含備份與隱藏檔）。
   R5a 的「主機間直傳」需要一個**既有檔案**；請示明**該檔在哪台主機的哪個路徑**（或由 Tao 先放上 C1/C2 的某路徑）。
   **我未去任何非指定目錄搜尋**（依令）。
2. **是否仍要用 planning.goaa.ai 的 production instance**：切到 live 憑證時，`CLERK_ISSUER` 會變成 production issuer；步驟 4-D 的「**JWKS 取得到**」驗收**依賴 Clerk 該 production instance 已完成網域驗證與 DNS 設定**。若網域尚未驗證，換值的結果會是 `clerk_verification_unavailable`（而非 `invalid_clerk_session`）—— 這正是 Tao 在 4-D 要我分辨的那個訊號。**建議在提供憑證時一併確認 production instance 是否已上線。**
3. **與 2026-09-11 事件的關聯（僅供對照）**：當時 Tao 在對話中貼過一把 live 密鑰，該值被視為**已洩漏並要求輪換**，且事後全域 live-前綴（`sk_`+`live_`）殘留已歸零。⇒ 本輪在 C2 全域找不到任何 live 憑證，**與該處置一致**；亦即**目前沒有任何現成的 live 憑證可搬**。
4. **C1 現階段身分**：3103 目前與 C2 **共用同一組 test 憑證**（值相同）。在尚未取得 live 憑證前，**C1 的 3103 不應被視為 production 身分**。
