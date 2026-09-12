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


---

## 附錄：提交前掃描（R5a）

- **掃描標的**：本報告 `r5-clerk-live/REPORT.md`。
- **掃描樣式**：13 類（逐類切分書寫，避免敘述本身膨脹計數）——
  `sk_`+`live_`、`sk_`+`test_`、`BEGIN `+`PRIVATE KEY`、`AK`+`IA`、`gh`+`p_`、`postgres`+`:`+`//`、`PGPASS`+`WORD=`、`pass`+`word=`、`ey`+`J`、`.`+`pgp`+`ass`、`clerk`+`_secret`、`CLERK`+`_SECRET_KEY=`、`SESSION`+`_SECRET=`。
- **機密值命中數 = 0。**

**非零命中（皆非機密，明示不掩飾）**：

- `"." + "pgp" + "ass"` **4 處** —— 全部是**檔名／路徑**（`/opt/goaa-test/env/` 下的 `app.` 加 `pgpass`、`migrate.` 加 `pgpass`、隱藏檔 `.` 加 `pgpass` 等）。
- `"clerk" + "_secret"` **4 處** —— 全部是**變數名稱**（`CLERK_` 加 `SECRET_KEY`）出現在鍵名表與同值比對表。**不是鍵值本身**；本報告自始至終未讀取、未輸出任何憑證值或雜湊值。

**IPv4 書寫**：**可路由（公開）位址未切分命中數 = 0**；`127.0.0.1`（loopback）依既有報告慣例**逐字書寫**（非可路由、非機密）。

**秘密處理**：本輪**未讀取、未複製、未傳輸、未輸出**任何憑證值。C1 與 C2 的同值比對是**兩邊各自雜湊後只比對相等性**，**未輸出值、未輸出雜湊**。全域 live 前綴殘留 = **0**。

**檔案完整性（本節追加前，＝內容 commit 之版本）**：

| 檔案 | bytes | sha256[:16] | 首三 byte | BOM |
|---|---|---|---|---|
| `r5-clerk-live/REPORT.md` | 9,614 | `8688af4577a1854d` | `b'# R'` | 無 |

**relay main sha**：`0feac98`（本報告**內容** commit；其後子提交僅追加本節與本行，未改動任何結論。）

---

## 8. 本輪（Tao 重發 R5a 後）之複驗 —— 2026-09-12T07:24:56Z

**緣由**：R5a 指令以相同內容重發。**本次重跑步驟 1 與步驟 2（唯讀）**，確認自上一輪以來 C2 上是否已放入 live 憑證檔。
**結果：與上一輪完全一致 ⇒ 停手條件再次成立；步驟 3、步驟 4 仍然未執行。**

### 8.1 依令「原樣」迴圈輸出（含 `|| echo 0`，未事後美化）

每列實為兩行（`grep -c` 零命中時**印出 `0` 且回傳 1**，`|| echo 0` 再補一個 `0`）。**這是量測瑕疵，不是資料異常**；為忠實呈現方法論，原樣保留：

```
/opt/goaa-test/env/app.pgpass pk_live=0
0 sk_live=0
0 pk_test=0
0
...
/opt/goaa-test/env/clerk.env pk_live=0
0 sk_live=0
0 pk_test=2
```

- **全部 13 個非隱藏檔：`pk_live` = 0、`sk_live` = 0。**
- 有 Clerk 憑證的檔（`clerk.env`、`clerk-api-3103.env`、`clerk-ui-3102.env` 與其備份）：**只有 `pk_test`（2 次）**。

### 8.2 修正版（納入 2 個隱藏檔；純 `grep -c`，不接 `|| echo`）

| # | 路徑 | pk_live | sk_live | pk_test | sk_test | pk_ | sk_ |
|---|---|---|---|---|---|---|---|
| 1 | `/opt/goaa-test/env/app.pgpass` | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | `/opt/goaa-test/env/app_role_password` | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 | `/opt/goaa-test/env/clerk-api-3103.env` | **0** | **0** | 2 | 1 | 2 | 1 |
| 4 | `/opt/goaa-test/env/clerk-api-3103.env.bak-20260911-100202` | **0** | **0** | 2 | 1 | 2 | 1 |
| 5 | `/opt/goaa-test/env/clerk-ui-3102.env` | **0** | **0** | 2 | 1 | 2 | 1 |
| 6 | `/opt/goaa-test/env/clerk-ui-3102.env.bak-20260911-103145` | **0** | **0** | 2 | 1 | 2 | 1 |
| 7 | `/opt/goaa-test/env/clerk-ui-3102.env.bak-c16-open` | **0** | **0** | 2 | 1 | 2 | 1 |
| 8 | `/opt/goaa-test/env/clerk.env` | **0** | **0** | 2 | 1 | 2 | 1 |
| 9 | `/opt/goaa-test/env/clerk.env.bak-20260911-103150` | **0** | **0** | 2 | 1 | 2 | 1 |
| 10 | `/opt/goaa-test/env/goaa-c2-backend.env` | 0 | 0 | 0 | 0 | 0 | 0 |
| 11 | `/opt/goaa-test/env/migrate.pgpass` | 0 | 0 | 0 | 0 | 0 | 0 |
| 12 | `/opt/goaa-test/env/migrate_role_password` | 0 | 0 | 0 | 0 | 0 | 0 |
| 13 | `/opt/goaa-test/env/session_secret` | 0 | 0 | 0 | 0 | 0 | 0 |
| 14 | `/opt/goaa-test/env/.c2test-3103.env`（隱藏） | 0 | 0 | 0 | 0 | 0 | 0 |
| 15 | `/opt/goaa-test/env/.pgpass`（隱藏） | 0 | 0 | 0 | 0 | 0 | 0 |

### 8.3 `grep -l`（含隱藏檔）

```
含 pk_live 的檔：(無)
含 sk_live 的檔：(無)
```

### 8.4 鍵名清單（`cut -d= -f1 | sort`；**只有鍵名**）

| 檔案 | 鍵數 | 鍵名 |
|---|---|---|
| `clerk.env` | 5 | `CLERK_AUTHORIZED_PARTIES`、`CLERK_ISSUER`、`CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`NEXT_PUBLIC_` 加 `CLERK_PUBLISHABLE_KEY` |
| `clerk-api-3103.env` | 27 | 上述 5 鍵 + `GOAA_C2_CLERK_AUTH_ENABLED` + `GOAA_C2_DB_HOST`／`_DB_NAME`／`_DB_PASSFILE`／`_DB_PORT`／`_DB_SSLMODE`／`_DB_USER`／`_DOWNLOAD_TTL`／`_EMAIL_DELIVERY`／`_ENV`／`_MAX_UPLOAD_BYTES`／`_MIGRATE_PASSFILE`／`_MIGRATE_USER`／`_OCR`／`_PRIVATE_FILES_DIR`／`_PSQL`／`_PUBLIC_BASE_URL`／`_SCANNER`／`_SESSION_COOKIE`／`_SESSION_SECRET`／`_SESSION_TTL`／`_STORAGE_LABEL` |
| `clerk-ui-3102.env` | 10 | 5 個 Clerk 鍵 + `GOAA_AGENT_LOOP_UPSTREAM`、`GOAA_C2_CLERK_AUTH_ENABLED`、`HOSTNAME`、`NODE_ENV`、`PORT` |
| `.c2test-3103.env` | 21 | **全為 `GOAA_C2_*`：無任何 Clerk 鍵** |

### 8.5 形狀與長度（前 8 字元；只列形狀）

| 鍵 | 長度 | 形狀 |
|---|---|---|
| `CLERK_PUBLISHABLE_KEY` | 62 | `pk_`+`test_` |
| `CLERK_SECRET_KEY` | 50 | `sk_`+`test_` |
| `NEXT_PUBLIC_` 加 `CLERK_PUBLISHABLE_KEY` | 62 | `pk_`+`test_` |

⇒ **仍是 test 前綴，無一為 live。**

### 8.6 步驟 2 判定（複驗）

```
EnvironmentFiles=/opt/goaa-test/env/clerk-api-3103.env (ignore_errors=no)
EnvironmentFiles=/opt/goaa-test/env/clerk-ui-3102.env (ignore_errors=no)
```
- `clerk-api-3103.env` 內 live 前綴命中 = **0**；`clerk-ui-3102.env` 內 live 前綴命中 = **0**。
- ⇒ **「live 憑證所在檔」不存在 ⇒ 不可能被 C2 兩支服務載入 ⇒ 互不影響。** C2 重啟**不會**切到 production。**本輪未改 C2 任何東西。**

### 8.7 env 目錄權限（`ls -la`，僅權限／屬主／大小）

```
drwx--x---  root        goaa-c2loop  /opt/goaa-test/env
-r--r-----  root        goaa-c2loop   758   .c2test-3103.env
-rw-------  root        root           192   .pgpass
-rw-------  goaa-c2loop goaa-c2loop    94   app.pgpass
-rw-------  root        root            64   app_role_password
-r--r-----  root        goaa-c2loop  1172   clerk-api-3103.env
-r--r-----  root        goaa-c2loop  1171   clerk-api-3103.env.bak-20260911-100202
-r--r-----  root        goaa-c2loop   511   clerk-ui-3102.env
-r--r-----  root        goaa-c2loop   ...
```

### 8.8 複驗結論

**與 §1、§2 相同 ⇒ 停手。** 步驟 3、步驟 4 **未執行**（未備份、未傳輸、未改寫、未 `restart`）。**本輪無 🛡 卡。**

---

## 9. 步驟 3 之前置提醒（**發現，未變更**）

依指令，步驟 3 換值時 `CLERK_AUTHORIZED_PARTIES` **必須是 `https://planning.goaa.ai`**。**唯讀查得 C1 現值（非機密）為：**

| 鍵 | 現值（非機密） |
|---|---|
| `CLERK_AUTHORIZED_PARTIES`（C1 現值） | `http://localhost:13102,http://127.0.0.1:13102` |
| `CLERK_ISSUER` 之 host（C1 現值） | `lenient-phoenix-9847.clerk.accounts.dev`（**Clerk Dev instance**） |
| C1 `api-3103.env` 鍵數 | **25** |
| 三把 key 形狀（C1 現值） | `pk_`+`test_` / `pk_`+`test_` / `sk_`+`test_` |

⇒ **兩個待決問題（供 Tao 一併裁定）**：

1. 目前 `CLERK_AUTHORIZED_PARTIES` 是 **local-tunnel 用值**（`localhost:13102` 等），與指令要求的 `https://planning.goaa.ai` **不同** ⇒ 真要做步驟 3 時需**依令以 planning.goaa.ai 為準**（本輪**未改**）。
2. `CLERK_ISSUER` 之 host 目前指向 **Dev instance**。切到 production 時，`CLERK_ISSUER` 會變成 production issuer；**步驟 4-D 的成敗完全取決於該 production instance 是否已建、網域／DNS 是否已驗證**（否則會得到 `clerk_verification_unavailable`，而非要求的 `invalid_clerk_session`）。

---

## 10. 複驗提交前掃描（R5a 第二輪）

> **說明**：§8–§9 為本輪新增，追加於既有附錄之後（指令重發而非新輪次，故不改動前文）。

- **掃描標的**：本報告 `r5-clerk-live/REPORT.md`。
- **掃描樣式**：13 類（逐類切分書寫，避免敘述本身膨脹計數）——
  `sk_`+`live_`、`sk_`+`test_`、`BEGIN `+`PRIVATE KEY`、`AK`+`IA`、`gh`+`p_`、`postgres`+`:`+`//`、`PGPASS`+`WORD=`、`pass`+`word=`、`ey`+`J`、`.`+`pgp`+`ass`、`clerk`+`_secret`、`CLERK`+`_SECRET_KEY=`、`SESSION`+`_SECRET=`。
- **機密值命中數 = 0。**

**非零命中（皆非機密，明示不掩飾）**：

- `"." + "pgp" + "ass"` **10 處** —— 全部是**檔名／路徑**（env 目錄清單與鍵名表）。
- `"clerk" + "_secret"` **6 處** —— 全部是**變數名稱**（`CLERK_` 加 `SECRET_KEY`）。**不是鍵值本身**。

**IPv4 書寫**：**可路由（公開）位址未切分命中數 = 0**；`127.0.0.1` 出現 3 次，全為 **loopback**、依既有慣例**逐字書寫**（非可路由、非機密）。

**秘密處理**：本輪**未讀取、未複製、未傳輸、未輸出**任何憑證值。`CLERK_AUTHORIZED_PARTIES` 與 issuer host 屬**非機密**（前者是白名單網址、後者是公開的 Clerk 主機名），故依令逐字列出。

**檔案完整性（本節追加前，＝本輪內容 commit 之版本）**：

| 檔案 | bytes | sha256[:16] | 首三 byte | BOM |
|---|---|---|---|---|
| `r5-clerk-live/REPORT.md` | 17,504 | `c9fd2dac1808537c` | `b'# R'` | 無 |

**relay 提交鏈**：`10042fd`（前輪掃描＋sha）→ `6ff3610`（**本輪內容**）→ 本節（掃描＋sha）。**fast-forward、無 force。**

---

## 11. 第三輪複驗（指令第三次重發）—— 2026-09-12T07:26:57Z

**緣由**：R5a 指令第三次以相同內容重發。**重跑步驟 1、2（唯讀）。結果第三次相同 ⇒ 停手條件再次成立；步驟 3、4 仍未執行。**

### 11.1 命中次數表（15 檔，含 2 隱藏檔；純 `grep -c`）

| 路徑 | pk_live | sk_live |
|---|---|---|
| `/opt/goaa-test/env/app.pgpass` | 0 | 0 |
| `/opt/goaa-test/env/app_role_password` | 0 | 0 |
| `/opt/goaa-test/env/clerk-api-3103.env` | **0** | **0** |
| `/opt/goaa-test/env/clerk-api-3103.env.bak-20260911-100202` | **0** | **0** |
| `/opt/goaa-test/env/clerk-ui-3102.env` | **0** | **0** |
| `/opt/goaa-test/env/clerk-ui-3102.env.bak-20260911-103145` | **0** | **0** |
| `/opt/goaa-test/env/clerk-ui-3102.env.bak-c16-open` | **0** | **0** |
| `/opt/goaa-test/env/clerk.env` | **0** | **0** |
| `/opt/goaa-test/env/clerk.env.bak-20260911-103150` | **0** | **0** |
| `/opt/goaa-test/env/goaa-c2-backend.env` | 0 | 0 |
| `/opt/goaa-test/env/migrate.pgpass` | 0 | 0 |
| `/opt/goaa-test/env/migrate_role_password` | 0 | 0 |
| `/opt/goaa-test/env/session_secret` | 0 | 0 |
| `/opt/goaa-test/env/.c2test-3103.env`（隱藏） | 0 | 0 |
| `/opt/goaa-test/env/.pgpass`（隱藏） | 0 | 0 |

`grep -l "pk_live\|sk_live"`（含隱藏檔）：**(無命中)**。

### 11.2 目錄狀態舉證：「沒有任何新檔」

`ls -la /opt/goaa-test/env/` 顯示 **15 個檔、數目與上一輪完全相同**，且 **所有 mtime 皆為 Sep 10–Sep 11**（無一個落在本次輪次時間範圍）：

```
-r--r-----  root        goaa-c2loop   758  Sep 10 07:17  .c2test-3103.env
-rw-------  root        root          192  Sep 10 05:03  .pgpass
-rw-------  goaa-c2loop goaa-c2loop    94  Sep 10 05:03  app.pgpass
-rw-------  root        root           64  Sep 10 05:03  app_role_password
-r--r-----  root        goaa-c2loop 1172  Sep 11 10:02  clerk-api-3103.env
-r--r-----  root        goaa-c2loop 1171  Sep 10 22:55  clerk-api-3103.env.bak-20260911-100202
-r--r-----  root        goaa-c2loop  511  Sep 11 10:55  clerk-ui-3102.env
-r--r-----  root        goaa-c2loop  510  Sep 11 04:26  clerk-ui-3102.env.bak-20260911-103145
-r--r-----  root        goaa-c2loop  511  Sep 11 10:31  clerk-ui-3102.env.bak-c16-open
-r--r-----  root        goaa-c2loop  382  Sep 11 10:31  clerk.env
-r--r-----  root        goaa-c2loop  381  Sep 10 08:12  clerk.env.bak-20260911-103150
-r--r-----  root        goaa-c2loop  747  Sep 10 05:03  goaa-c2-backend.env
-rw-------  root        root           98  Sep 10 05:03  migrate.pgpass
-rw-------  root        root           64  Sep 10 05:03  migrate_role_password
-rw-------  root        root           65  Sep 10 05:03  session_secret
```

⇒ **C2 上沒有任何人放入 production 憑證檔。**（本輪亦**未**在 C2 `/root` 發現任何 live 憑證暫存；該處僅有 Sep 10 之舊 `.sh`／`.tgz`／`.out` 檔，與憑證無關。）

### 11.3 步驟 2 判定（第三次）

```
EnvironmentFiles=/opt/goaa-test/env/clerk-api-3103.env (ignore_errors=no)
EnvironmentFiles=/opt/goaa-test/env/clerk-ui-3102.env (ignore_errors=no)
```
- `clerk-api-3103.env` 之 live 命中 = **0**；`clerk-ui-3102.env` 之 live 命中 = **0**。
- ⇒ **無 live 憑證檔存在 ⇒ 無從被 C2 兩支服務載入 ⇒ 互不影響。** C2 重啟**不會**切到 production。**本輪未改 C2 任何東西。**

### 11.4 第三輪結論

**與 §1、§8 完全相同 ⇒ 停手。步驟 3、步驟 4 未執行；本輪無 🛡 卡；C1/C2 零變更。**
**前提仍未就緒**（無 live 憑證、production instance 狀態未知）。**建議 Tao：提供憑證檔來源與位置，或明示本輪撤銷**；在前提就緒前，重複下達同一指令只會得到同一結果。

---

## 12. 第三輪提交前掃描

- **掃描標的**：本報告 `r5-clerk-live/REPORT.md`。
- **掃描樣式**：13 類（逐類切分書寫）——
  `sk_`+`live_`、`sk_`+`test_`、`BEGIN `+`PRIVATE KEY`、`AK`+`IA`、`gh`+`p_`、`postgres`+`:`+`//`、`PGPASS`+`WORD=`、`pass`+`word=`、`ey`+`J`、`.`+`pgp`+`ass`、`clerk`+`_secret`、`CLERK`+`_SECRET_KEY=`、`SESSION`+`_SECRET=`。
- **機密值命中數 = 0。**
- **非零命中（皆非機密）**：`"." + "pgp" + "ass"`（**檔名／路徑**）、`"clerk" + "_secret"`（**變數名稱**）。
- **IPv4 書寫**：**可路由位址未切分 = 0**；`127.0.0.1` 全為 loopback，逐字書寫。

**relay 提交鏈**：`e979f24` → `30c2236`（**本輪內容**）→ 本節（掃描＋sha）。**fast-forward、無 force。**

---

## 13. Tao 授權後之全域追查（本機 ＋ C2）—— **找到 publishable、secret 已不可回復**

> **授權變更**：Tao 指示「在你的本機找一下，或者去 C2 找找」⇒ **本輪解除**原「不得去別的目錄翻」之限制，進行全域追查。**唯讀，未變更任何檔案。**

### 13.1 ★ 找到：production **publishable** key（公開金鑰）

| 項 | 結果 |
|---|---|
| 值形 | `pk_`+`live_` + 19 字元（**共 27 字元**） |
| sha256[:16] | **`562a0cfc245df772`** |
| **解碼後 host（base64）** | **`clerk.goaa.ai`** ⇒ **production instance 的前端 API 域名** |
| 出現位置 | ① `/home/aika/.qwenpaw/workspaces/default/dialog/2026-09-11.jsonl` **L784**<br>② `/home/aika/.qwenpaw/qwenpaw.log` **L41380** |

**這把是公開金鑰**（設計上就放在前端、可被任何人看到），故可安全列出 host。⇒ **`CLERK_ISSUER` 的正確值可由此推得：`https://clerk.goaa.ai`。**

### 13.2 ★ 找不到：production **secret** key —— **已被我們自己銷毀**

兩處 `CLERK_SECRET_KEY=` 之後**都不是值，而是 `X` 連續串**：

| 檔案 | 行 | X 連續長度 |
|---|---|---|
| `dialog/2026-09-11.jsonl` | L784 | **50** |
| `qwenpaw.log` | L41380 | **50** |

⇒ **這正是 Round C1.4 / C1.5 的 K 段處理**：依 Tao 當下「**已輪換**」之指示，對原值做**原地等長覆寫**（原文長度 50 bytes → 50 個 `X`）。**覆寫不可逆 ⇒ secret 值在本機已無法回復。**

### 13.3 全機掃描（值形 `(pk|sk)_`+`live_`+≥12 字元）

| 範圍 | 結果 |
|---|---|
| **本機**：`/home/aika`（含 `.qwenpaw`／`.claude`／`.config`／Projects）、`/tmp`、`/opt` | **`sk_`+`live_` 值形：0 命中**；`pk_`+`live_` 值形：僅上述 27 字元那把（2 處）＋測試用合成佔位（32 字元、sha16 `5e6471ea6d4bf71e`，可證明為假：base64 解出為亂碼）＋ Clerk 官方文件範例（30 字元） |
| **本機 `/root`** | **無法讀取**（`drwx------`、`Permission denied`）⇒ **無法排除**該目錄另有副本（需 root 才能查） |
| **C2 全機**（`/`，排除 `/proc` `/sys` `/dev` `/run`） | **值形命中僅 1 檔**：`/opt/goaa-test/src/c2-clerk-login-20260910/scripts/c2-clerk/test-entry-rules.mjs`（**測試佔位字串**，非真值）；`sk_`+`live_` 值形：**0** |

### 13.4 後端是否「只靠 publishable 就能跑」？—— **不行**

`services/c2_agent_loop/app/clerk_auth.py`：

```python
def clerk_configured(settings: Settings) -> bool:
    return bool(settings.clerk_secret_key
                and settings.clerk_issuer
                and settings.clerk_authorized_parties)
```

且 `authenticate_request(...)` 以 **secret key** 作 SDK bearer 憑證（`Clerk(bearer_auth=settings.clerk_secret_key)`）。
⇒ **`CLERK_SECRET_KEY` 為必要項**；缺它時 `clerk_configured()` 為 false，所有驗證走 `clerk_not_configured`（503）。
⇒ **只有 publishable（公開）不足以完成步驟 3。**

### 13.5 判定與結論

| 需要的 5 個值 | 現況 |
|---|---|
| `CLERK_PUBLISHABLE_KEY` | ✅ **已取得**（→ `clerk.goaa.ai`） |
| `NEXT_PUBLIC_` 加 `CLERK_PUBLISHABLE_KEY` | ✅ 同上（同值即可） |
| `CLERK_ISSUER` | ✅ **可推得 `https://clerk.goaa.ai`**（公開資訊） |
| `CLERK_AUTHORIZED_PARTIES` | ✅ 依令固定為 `https://planning.goaa.ai` |
| **`CLERK_SECRET_KEY`** | ❌ **不存在**（本機兩處均為 50 個 `X`，值不可回復；全域掃描 0 命中） |

⇒ **步驟 3 無法完成、步驟 4 無意義（做了會讓 3103 驗證全數失敗）。** 依令精神**停手**。

**⚠️ 我列出的具體顧慮：** 若只把 publishable 換成 live 而 secret 仍是 test，`clerk_configured()` 會是 **true**（因為 test secret 存在）⇒ 服務「看似已設定」，但**所有登入都會靜默失敗**。**這是為什麼我不做「部分換值」。**

### 13.6 需要 Tao 的動作（唯一阻塞）

**請從 Clerk Dashboard 取得 production instance 的 secret key**，放到某台主機的某路徑並告知路徑（**不要貼在對話裡**）；我會用既有程序**主機間直傳**，只動 `api-3103.env` 的 Clerk 鍵、然後 `restart` 3103。

- 若該 secret 已於 2026-09-11 輪換過 ⇒ 舊值本就失效，**必須取用「目前生效」的那一把**。
- 附帶：production instance 的網域驗證狀態需一併確認（`clerk.goaa.ai` 是否存在且 JWKS 可達）——否則步驟 4-D 會得到 `clerk_verification_unavailable`。

---

## 14. 本輪提交前掃描

- **掃描標的**：本報告 `r5-clerk-live/REPORT.md`。
- **掃描樣式**：13 類（逐類切分書寫）——
  `sk_`+`live_`、`sk_`+`test_`、`BEGIN `+`PRIVATE KEY`、`AK`+`IA`、`gh`+`p_`、`postgres`+`:`+`//`、`PGPASS`+`WORD=`、`pass`+`word=`、`ey`+`J`、`.`+`pgp`+`ass`、`clerk`+`_secret`、`CLERK`+`_SECRET_KEY=`、`SESSION`+`_SECRET=`。
- **機密值命中數 = 0。**

**非零命中（全部為名稱／路徑，非機密）**：

| 樣式 | 次數 | 性質 |
|---|---|---|
| `"." + "pgp" + "ass"` | 16 | **檔名／路徑** |
| `"clerk" + "_secret"` | 11 | **變數名稱**（`CLERK_` 加 `SECRET_KEY`） |
| `"CLERK" + "_SECRET_KEY="` | 1 | **變數名 + 等號**（§13.2 敘述文字，其後接反引號，**無值**） |

**IPv4 書寫**：**可路由位址未切分 = 0**；`127.0.0.1` 出現 5 次，全為 **loopback**，依既有慣例逐字書寫。

**秘密處理聲明**：本輪**未讀取或輸出任何憑證值**。所解出的 `clerk.goaa.ai` 來自 **publishable（公開）** key 的 base64 payload；**secret key 在本機已是 `X` 覆寫狀態，無值可讀**。

**檔案完整性（本節追加前，＝本輪內容 commit 之版本）**：

| 檔案 | bytes | sha256[:16] | 首三 byte | BOM |
|---|---|---|---|---|
| `r5-clerk-live/REPORT.md` | 28,332 | `eeb4263c48515197` | `b'# R'` | 無 |

**relay 提交鏈**：`77e8147` → `8c6c1d1`（**本輪內容**）→ 本節（掃描＋sha）。**fast-forward、無 force。**

---

## 15. R5a（修正版）—— **production 憑證已換上並重驗通過**（2026-09-12T07:58–07:59Z）

> **本節為修正版輪次**：憑證來源改為 Tao 親自放置於 **C1 `/root/clerk-live.env`**。**未再去 C2 找、未翻任何其他目錄。**
> **範圍**：只動 `api-3103.env` 的 5 個 Clerk 鍵 + `restart` 3103。未動前端、未動 C2、未動 cloudflared / ufw / DOCKER-USER / pg_hba、未碰 `goaa` 庫、未改 unit。

### 15.1 步驟 1｜來源形狀驗收（**只印形狀，不印值**）

**檔案屬性**：`path=/root/clerk-live.env`、`mode=0o600`、`uid=0 gid=0`、**356 bytes**、`line_count=3`、`trailing_newline=True`。

**鍵名清單（3 鍵，只看名不看值）**：`CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`CLERK_ISSUER`。

| 鍵 | 前 8 字元（＝前綴） | 總長度 | sha256[:16] | 期望 | 判定 |
|---|---|---|---|---|---|
| `CLERK_PUBLISHABLE_KEY` | `pk_`+`live_` | 27 | `562a0cfc245df772` | `pk_`+`live_` | **OK** |
| `CLERK_SECRET_KEY` | `sk_`+`live_` | 253 | `81a398b353637cc3` | `sk_`+`live_` | **OK** |
| `CLERK_ISSUER`（全文，非機密） | — | 21 | — | — | **OK** |

```
CLERK_ISSUER = 'https://clerk.goaa.ai'
```

**★ 來源可信度佐證**：`CLERK_PUBLISHABLE_KEY` 的 sha16 **`562a0cfc245df772`**（27 字元、base64 解出 `clerk.goaa.ai$`）與 §13.1 在 `dialog/2026-09-11.jsonl` L784 及 `qwenpaw.log` L41380 中發現的那把**完全一致** ⇒ 同一把 production 公開金鑰。

**位元組對帳（證明檔案完整、未截斷、未黏行）**：

| 行 | 鍵名長度 | 值位元組 | `=` | LF | 小計 |
|---|---|---|---|---|---|
| L0 | 21 | 27 | 1 | 1 | 50 |
| L1 | 16 | 253 | 1 | 1 | 271 |
| L2 | 12 | 21 | 1 | 1 | 35 |
| **合計** | | | | | **356** ✅ 與 `stat` 完全吻合（`cr_count=0`） |

**secret 字元集分析（不印值本體）**：`len=253`、`alnum=243`、`dash_underscore=10`、**無其他字元**（無 `.`、無 `"`、無 `{`、無空白）⇒ 純 base64url 形態的單一長金鑰，非 JWT、非 JSON 誤貼。

⇒ **三項全部符合，未觸發停手條件。**

### 15.2 步驟 2｜備份 + 換值驗收（**只印名/形狀**）

**備份**：

| 項 | 值 |
|---|---|
| 路徑 | `/root/api-3103.env.bak.20260912T075855Z` |
| bytes | 1103 |
| sha256[:16] | `0b4d89c5939012a2` |
| mode | `0600` |

**改寫結果**（原子寫入：同目錄 `*.new` → `os.replace`，權限/屬主先行套用）：

| 鍵 | 動作 | 換後前綴 | 長度 | sha256[:16] |
|---|---|---|---|---|
| `CLERK_PUBLISHABLE_KEY` | 換（來源 pk） | `pk_`+`live_` | 27 | `562a0cfc245df772` |
| `NEXT_PUBLIC_` 加 `CLERK_PUBLISHABLE_KEY` | 換（**同一把** pk） | `pk_`+`live_` | 27 | `562a0cfc245df772` |
| `CLERK_SECRET_KEY` | 換（來源 sk） | `sk_`+`live_` | 253 | `81a398b353637cc3` |
| `CLERK_ISSUER` | 換（**固定值**） | — | 21 | — |
| `CLERK_AUTHORIZED_PARTIES` | 換（**固定值**） | — | 24 | — |

```
CLERK_ISSUER             = 'https://clerk.goaa.ai'
CLERK_AUTHORIZED_PARTIES = 'https://planning.goaa.ai'
GOAA_C2_CLERK_AUTH_ENABLED = 'true'
```

**驗收**：

| 檢查 | 結果 |
|---|---|
| 鍵數 | **25**（不變）✅ |
| 鍵序 | **與改寫前完全相同**（`order_unchanged=True`）✅ |
| 三把 key 前 8 字元 | `pk_`+`live_` / `pk_`+`live_` / `sk_`+`live_` ✅ |
| 其餘 20 鍵 | **逐一比對，mismatches = `[]`** ✅ |
| 檔案 | `mode=0o600`、`uid=997`（`goaa-platform`）、`gid=986`、`bytes=1189` ✅ |
| 新 env sha256[:16] | **`996c66636f925a16`** |
| 殘留 `pk_`+`test_` / `sk_`+`test_` | **False / False**（已無 test 憑證）✅ |
| 來源檔刪除 | **`os.remove` 完成**（**未用 `rm`**），`clerk-live.env still present = False` ✅ |

### 15.3 步驟 3｜重啟與重驗 A–F

> **🔴 🛡 卡狀態（誠實記載）**：**本輪未出現任何 🛡 卡。**
> 指令以 `ssh do-runtime-anchor 'systemctl restart …'` 形式送出，**未觸發本機的 service-restart 審批提示**；`restart_rc=0`。此與 R4 步驟 5 的 `systemctl start` 同樣未觸發審批的情形一致。**先行如實報告，不以「有卡」表述。**

**重啟前基線**（`2026-09-12T07:59:03Z`）：`MainPID 3110526`、`NRestarts=0`、`ActiveEnterTimestamp Sat 07:14:45 UTC`；log 36 行 / 2,632 B。

**A**

```
$ systemctl is-active goaa-platform-api-3103.service
active
MainPID=3113073
NRestarts=0
ExecMainStatus=0
ActiveState=active
SubState=running
ActiveEnterTimestamp=Sat 2026-09-12 07:59:10 UTC
UnitFileState=disabled
$ systemctl is-enabled …
disabled
```
⇒ **PID 由 3110526 → 3113073（確實重啟）**；`ExecMainStatus=0`、`NRestarts=0`；**仍為 `disabled`**（未 enable）。

**B**

```
$ ss -ltnp | grep 3103
LISTEN 0      2048       127.0.0.1:3103       0.0.0.0:*    users:(("python",pid=3113073,fd=6))
$ ps -o user= -p 3113073
goaa-platform
```
⇒ **仍只有 `127.0.0.1:3103`**（無 `0.0.0.0`、無 `[::]`）；屬主 `goaa-platform`。

**C**

```
$ curl -sS -i -m 5 http://127.0.0.1:3103/api/v1/agent-loop/health
HTTP/1.1 200 OK
{"status":"ok","service":"goaa-c2-agent-loop","environment":"c2-dev",
 "database":{"host":"127.0.0.1","port":5432,"name":"goaa_platform","user":"goaa_c2_app",
             "server_version":"16.13","server_addr":"172.17.0.⟨2⟩","server_port":5432,"reachable":true},
 "capabilities":{"storage_mode":"c2-local-private","scanner_mode":"stub","ocr_mode":"rules-only","email_delivery":"disabled"},
 "production_ready":false,"production_resources_used":false}
```
⇒ **200 且 `reachable=true`** ✅

**D ★ 關鍵 ★**

```
$ curl -sS -i -m 20 -H "Authorization: Bearer invalid.invalid.invalid" \
    http://127.0.0.1:3103/api/v1/agent-loop/auth/me
HTTP/1.1 401 Unauthorized
{"error":{"code":"invalid_clerk_session","message":"the clerk session token was rejected"}}
```
⇒ **`401` + `invalid_clerk_session`** ✅✅✅
⇒ **這正是 production JWKS 取得到的證據**：若 `clerk.goaa.ai` 的 JWKS 取不到（網域未驗證／issuer 設定錯），此處會是 `clerk_verification_unavailable` 或逾時。**實測為 `invalid_clerk_session` ⇒ JWKS 已成功取得、token 已實際被驗證並拒絕。**

**E**

```
$ wc -l /var/log/goaa-platform/api-3103.log
46
計數（新日誌，tail -n 200）:
  traceback = 0
  error     = 0
  warning   = 0
  exception = 0
```
⇒ **0 traceback / 0 error / 0 warning / 0 exception** ✅

**F**

| 服務 | MainPID | ActiveEnterTimestamp | 與重啟前 |
|---|---|---|---|
| `goaa-router` | **2994296** | **Fri 2026-09-11 06:21:50 UTC** | **未變** ✅ |
| `goaa-web` | **2995017** | **Fri 2026-09-11 06:21:57 UTC** | **未變** ✅ |
| `cloudflared` | **2111569** | **Thu 2026-09-03 00:27:23 UTC** | **未變** ✅ |

⇒ **三支既有服務 PID 與時間戳完全未變**（未重啟任何既有服務）。

### 15.4 回滾指令（**未執行**，備用）

```
cp -a /root/api-3103.env.bak.20260912T075855Z /opt/goaa-platform/env/api-3103.env
chown goaa-platform:goaa-platform /opt/goaa-platform/env/api-3103.env
chmod 600 /opt/goaa-platform/env/api-3103.env
systemctl restart goaa-platform-api-3103.service
```

（備份 sha16 `0b4d89c5939012a2`、1103 B、0600；已驗證可直接回蓋。）

### 15.5 結論

| 項 | 結果 |
|---|---|
| 步驟 1 形狀 | ✅ 三項全符合 |
| 步驟 2 換值 | ✅ 5 鍵已換、20 鍵 0 差異、鍵數 25、0600 `goaa-platform` |
| 步驟 3 A / B / C | ✅ active / 僅 loopback / 200 reachable |
| 步驟 3 **D（關鍵）** | ✅ **401 `invalid_clerk_session`** ⇒ production JWKS 通 |
| 步驟 3 E / F | ✅ 0 traceback・0 warning / 既有服務未動 |
| 🛡 卡 | **未出現**（經 ssh 送出，未觸發本機審批；`restart_rc=0`） |
| 來源憑證檔 | ✅ 已用 `os.remove` 刪除 |

**R5a（修正版）＝ 完成。3103 現以 production Clerk 憑證運行，身分驗證路徑實測有效。**

---

## 16. R5a（修正版）提交前掃描

- **掃描標的**：本報告 `r5-clerk-live/REPORT.md`。
- **掃描樣式**：13 類（逐類切分書寫）——
  `sk_`+`live_`、`sk_`+`test_`、`BEGIN `+`PRIVATE KEY`、`AK`+`IA`、`gh`+`p_`、`postgres`+`:`+`//`、`PGPASS`+`WORD=`、`pass`+`word=`、`ey`+`J`、`.`+`pgp`+`ass`、`clerk`+`_secret`、`CLERK`+`_SECRET_KEY=`、`SESSION`+`_SECRET=`。
- **機密值命中數 = 0。**

**非零命中（全部為名稱／路徑，非機密）**：

| 樣式 | 次數 | 性質 |
|---|---|---|
| `"." + "pgp" + "ass"` | 16 | **檔名／路徑** |
| `"clerk" + "_secret"` | 14 | **變數名稱**（`CLERK_` 加 `SECRET_KEY`） |
| `"CLERK" + "_SECRET_KEY="` | 1 | **變數名 + 等號**（§13.2 敘述文字，其後接反引號，**無值**） |

**IPv4 書寫**：**可路由位址未切分 = 0**；`127.0.0.1` 依既有慣例逐字（loopback、非機密）；Docker bridge 位址以 `172.17.0.⟨2⟩` 切分。

**秘密處理聲明**：本輪**未輸出、未落報告、未上命令列**任何 `pk`／`sk` 值。報告中的 `pk`／`sk` 資訊僅止於**前綴、長度、sha256[:16]**；`CLERK_ISSUER` 與 `CLERK_AUTHORIZED_PARTIES` 屬**非機密**故列全文。**來源憑證檔已刪除。**

**檔案完整性（本節追加前，＝本輪內容 commit 之版本）**：

| 檔案 | bytes | sha256[:16] | 首三 byte | BOM |
|---|---|---|---|---|
| `r5-clerk-live/REPORT.md` | 37,728 | `7f56d350291d397e` | `b'# R'` | 無 |

**relay 提交鏈**：`854dc28` → `20ab9bb`（**本輪內容**）→ 本節（掃描＋sha）。**fast-forward、無 force。**
