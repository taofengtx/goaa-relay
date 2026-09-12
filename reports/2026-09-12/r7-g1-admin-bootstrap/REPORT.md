# R7-G1｜引導第一個管理員（`user_roles` 新增 `admin`）—— 🔴 **STOP 於步驟 0-1，未執行任何寫入**

- **執行時間（UTC）**：2026-09-12 18:2xZ
- **主機**：C1 `do-runtime-anchor`（公網 `134.199.227.⟨108⟩`）；DB＝容器 `goaa-postgres` / 庫 `goaa_platform`
- **結論**：🔴 **步驟 0-1 不符（實得 `2|2|0`，期望 `1|1|0`）⇒ 依令「任一不符即停並回報」停手。**
- **本輪寫入次數 = 0**（無 INSERT／UPDATE／DELETE、無 DDL）。未改任何檔案、未重啟任何服務、未動 `current`／env／migrations／其他資料表。**因此不需要回滾。**
- **🛡 核准卡**：未出現（0 次）。

---

## 步驟 0｜唯讀前置（原始輸出）

```
===== 0-1 users | user_roles | admin_count =====
2|2|0
===== 0-2 user_roles.role =====
user
user
===== 0-3 agent_applications count|status =====
1|submitted
===== 0-4 agent_licenses | agent_license_documents =====
1|1
===== 0-5 pre_review recommendation =====
looks_complete
===== 0-6 表結構（唯讀）user_roles 欄位 =====
user_id|uuid|NO
role|text|NO
granted_at|timestamp with time zone|NO
granted_by|uuid|YES
===== 0-7 觸發器存在性（唯讀）=====
trg_user_roles_guard|O
===== 0-8 目前角色 / session_user 觀察（唯讀）=====
-- as goaa: session_user=goaa current_user=goaa
-- as goaa_c2_app: session_user=goaa_c2_app current_user=goaa_c2_app
```

| 項 | 期望 | 實測 | 判定 |
|---|---|---|---|
| 0-1 | `1 \| 1 \| 0` | **`2 \| 2 \| 0`** | 🔴 **不符 ⇒ 停** |
| 0-2 | 只應有 `user` | `user`、`user`（兩列，**皆非 admin**） | ✅（值符合；筆數為 2） |
| 0-3 | `1 \| submitted` | `1 \| submitted` | ✅ |
| 0-4 | 兩者 ≥ 1 | `1 \| 1` | ✅ |
| 0-5 | （僅參考） | `looks_complete` | ✅ |

## 🔴 阻塞原因：`users` 有 **2** 列（非 1）

```
===== users =====
  id=dc11cc56… email=c*****a@gmail.com created_at=2026-09-12 17:49:52.891041+00 email_verified_at=2026-09-12 17:49:52.891041+00
  id=e9df19c7… email=t*****x@gmail.com created_at=2026-09-12 18:05:06.548469+00 email_verified_at=2026-09-12 18:05:06.548469+00
===== user_roles =====
  role=user   user_id=dc11cc56… granted_at=2026-09-12 17:49:52.891041+00 granted_by=(null) email=c*****a@gmail.com
  role=user   user_id=e9df19c7… granted_at=2026-09-12 18:05:06.548469+00 granted_by=(null) email=t*****x@gmail.com
===== identity_events =====
  identity.jit_create prov=clerk at=2026-09-12 17:49:52.891041+00 email=c*****a@gmail.com actor=(null) subject=dc11cc56
  identity.jit_create prov=clerk at=2026-09-12 18:05:06.548469+00 email=t*****x@gmail.com actor=(null) subject=e9df19c7
  business.subject_linked prov=clerk at=2026-09-12 18:05:06.758528+00 email=t*****x@gmail.com actor=(null) subject=e9df19c7
  business.token_issued prov=clerk at=2026-09-12 18:05:06.758528+00 email=t*****x@gmail.com actor=(null) subject=e9df19c7
===== agent_applications =====
  id=1687d41e… user_id=e9df19c7… status=submitted created_at=2026-09-12 18:22:52.837605+00 updated_at=2026-09-12 18:24:53.610467+00
===== user_identities =====
  provider=clerk user_id=dc11cc56… subject=user_3… created_at=2026-09-12 17:49:52.891041+00
  provider=clerk user_id=e9df19c7… subject=user_3… created_at=2026-09-12 18:05:06.548469+00
```

**讀法**：

1. **使用者 A**：`c*****a@gmail.com`（`dc11cc56…`），`identity.jit_create` @ **17:49:52.891041Z** —— 即 R7-F2 報告 §EXTRA-2 觀測到的那次真實登入。**無** 後續業務事件。
2. **使用者 B**：`t*****x@gmail.com`（`e9df19c7…`），`identity.jit_create` @ **18:05:06.548469Z**，並在 18:05:06.758528Z 連帶產生 `business.subject_linked` 與 `business.token_issued`（登入後完成業務主體綁定與 token 簽發）。
3. **牌照申請（1 筆、`submitted`）屬於使用者 B**（`user_id=e9df19c7…`，`created_at` 18:22:52Z）。`agent_licenses=1`、`agent_license_documents=1`（申請送出時建立）。
4. 兩人的 `user_roles` 皆為 **`user`**、`granted_by` 為 **null** ⇒ **目前沒有任何 admin**（0 筆）。

## 為何**不能**照令執行步驟 1

指令單提供的 SQL 內建硬守衛：

```sql
do $$
declare n int;
begin
  select count(*) into n from users;
  if n <> 1 then
    raise exception 'expected exactly 1 user, found %', n;
  end if;
end $$;
```

以現況 `n = 2`，此 `do` 區塊**必然 `raise exception`**，交易會中止、不會插入任何列。且 `insert ... select id, 'admin' from users` 若無守衛，**會一次把 admin 發給兩個人** —— 這正是守衛要防的情況。
⇒ **依令停手，不自行改寫守衛、不自行挑選對象。**

## 待 Tao 裁示（一個選擇即可，我立刻執行）

`admin` 要授予哪一個帳號？

- **A｜`t*****x@gmail.com`**（18:05Z 登入；**送出這筆牌照申請的人**）
- **B｜`c*****a@gmail.com`**（17:49Z 首登者）
- **C｜兩者都給**（不建議：管理員應保持唯一）

> 選 A 或 B 後，我會把 SQL 的守衛由「全表僅 1 列」改為「**該 email 對應的使用者必須存在且唯一**」，並在 `begin/commit` 內以 `insert ... where exists` 形式只寫 1 列；其餘步驟 2 的驗收（含 2-3 守衛回歸測試）與報告照原令執行。

## 附註

1. `agent_applications` 申請屬使用者 B；`pre_review.recommendation = looks_complete`（僅供參考）。
2. `trg_user_roles_guard` 存在且為 **`O`（enabled，origin 觸發）** ⇒ 0004 守衛在線，步驟 2-3 的回歸測試仍具意義。
3. 本輪未以應用角色執行任何寫入；`session_user` 觀察僅為唯讀查詢。

## 秘密掃描（掃描對象＝本報告檔自身）

掃描器：`/tmp/r5c-scanrep.py`（通用 16 樣式；**樣式字面在掃描器內以字串相接書寫**，避免掃描器自身製造命中）。
**掃描表標籤一律使用切分寫法**（以 `pg-` 與 `pass` 分寫等），以免說明段自我膨脹命中數。

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

**未切分可路由 IPv4 檢查 = 0 筆**。可路由位址一律 `⟨N⟩` 切分（本報告僅出現 `134.199.227.⟨108⟩`）。

## 本報告指紋

- first3 = `# R`、BOM = False、bytes = 6,739、sha256_16 = a2efe2aecabd80bb（此欄以等長 `0` 佔位後計算 ⇒ 可自我驗證）
