# Round D0.4 — 停用 `goaa-model-router`（先查後改，改完立刻驗）

- **主機**：`do-runtime-anchor`（C1，`goaa-aika-cloud-1`）
- **執行窗口**：2026-09-12T02:04:51Z（前置）→ 02:05:02Z（變更）→ 02:11:28Z（驗收 A–F 完成，含 5 分鐘觀察窗）
- **結論**：**已完成並驗收通過**。`goaa-model-router` 自 `enabled + activating`（重啟迴圈）→ **`disabled + inactive`**；`goaa-router` 全程未受影響（**同一 PID、從未重啟**）。
- **轉寫聲明**：IPv4 末段一律以 `⟨N⟩` 切分；sha256 只取前 16 位。

---

## 0. 一頁看懂

| 項目 | 改前 | 改後 |
|---|---|---|
| `systemctl is-enabled goaa-model-router` | `enabled` | **`disabled`** |
| `systemctl is-active goaa-model-router` | `activating`（`rc=3`） | **`inactive`**（`rc=3`） |
| `NRestarts` | **245,246** | 0（重置） |
| `UnitFileState` | `enabled` | `disabled` |
| unit 檔 `/etc/systemd/system/goaa-model-router.service` | 存在（332 B） | **存在（未刪）** |
| mask symlink | 無 | **無（未 mask）** |
| `.timer` / `.socket` | 無 | 無 |
| 8080 listener | `uvicorn pid=2994296`（= `goaa-router`） | **同一 `uvicorn pid=2994296`** |
| `goaa-router` | active、health 200 | **active、health 200（未重啟）** |

**唯一變更指令**：`systemctl disable --now goaa-model-router`

## 1. 步驟 1 — 前置（唯讀）

```
$ systemctl is-enabled goaa-model-router ; systemctl is-active goaa-model-router
enabled
activating          # rc=3

$ NRestarts = 245244        # 重啟迴圈已跑了 24 萬多次
$ MainPID   = 0             # 沒有穩定主進程（一直在重啟）
$ ActiveEnterTimestamp = Sat 2026-09-12 02:04:48 UTC
```

```
$ systemctl cat goaa-model-router | grep -E '^(ExecStart|ExecStartPre|Restart|RestartSec|WantedBy|After|Requires)='
After=network.target
ExecStart=/opt/goaa/venv/bin/python3 /opt/goaa/venv/bin/uvicorn api:app --host 0.0.0.⟨0⟩ --port 8080
Restart=always
RestartSec=5
WantedBy=multi-user.target
```

```
$ systemctl list-dependencies --reverse goaa-model-router --no-pager
goaa-model-router.service
● └─multi-user.target
●   └─graphical.target            # 只被 target 拉起，無其他服務依賴

$ systemctl list-unit-files --no-pager | grep -i model-router
goaa-model-router.service    enabled    enabled     # 無 .timer / .socket
```

```
$ journalctl -u goaa-model-router --since "10 min ago" --no-pager | tail -20
Sep 12 02:04:43 ... Main process exited, code=exited, status=1/FAILURE
Sep 12 02:04:48 ... Scheduled restart job, restart counter is at 245244.
Sep 12 02:04:48 ... Started goaa-model-router.service - GOAA Model Router API.
Sep 12 02:04:49 ... Application startup complete.
Sep 12 02:04:49 ... ERROR: [Errno 98] error while attempting to bind on address ('0.0.0.⟨0⟩', 8080): address already in use
Sep 12 02:04:49 ... Waiting for application shutdown. → Application shutdown complete.
Sep 12 02:04:49 ... Main process exited, code=exited, status=1/FAILURE
```

⇒ **與 D0.1 的判斷一致**：每 5 秒搶一次 8080、搶不到就死、`Restart=always` 再拉起來 ⇒ 無限迴圈。

```
$ ss -ltnp | grep 8080
LISTEN 0 2048 0.0.0.⟨0⟩:8080 0.0.0.⟨0⟩:* users:(("uvicorn",pid=2994296,fd=7))
```

```
$ systemctl is-active goaa-router ; curl -s -o /dev/null -m 5 -w "router_health=%{http_code}\n" http://127.0.0.⟨1⟩:8080/health
active
router_health=200
```

```
$ systemctl cat goaa-router | grep -E '^(ExecStart|ExecStartPre)='
ExecStartPre=-/bin/sh -c 'fuser -k 8080/tcp'        # ← 衝突來源：它會主動殺 8080 佔用者
ExecStart=/opt/goaa/venv/bin/uvicorn api:app --host 0.0.0.⟨0⟩ --port 8080
```

**前置判斷**：8080 由 `goaa-router`（PID 2994296）正常持有；`goaa-model-router` 是純粹的無效重啟迴圈，且其搶埠行為與 `goaa-router` 的 `ExecStartPre fuser -k` 構成互搶風險 ⇒ **可安全 `disable --now`**。

## 2. 步驟 2 — 變更

```
=== BEFORE (t0) 2026-09-12T02:05:02Z ===
is-enabled: enabled
is-active : active
NRestarts : 245246

=== CHANGE: systemctl disable --now goaa-model-router ===
Removed "/etc/systemd/system/multi-user.target.wants/goaa-model-router.service".
rc=0
```

- **只做了這一條**：`disable`（取消開機自啟）＋ `--now`（停掉當下那個迴圈）。
- **未** mask、**未** 刪 unit 檔、**未** 碰 `goaa-router`。

### 🛡 審批卡說明
本輪**未出現 🛡 審批卡** —— 該指令直接執行完成，未經 approve 流程；**Aika 端未看到卡片、未經 Tao approve**（本輪亦未重啟 `goaa-router` 等任何服務）。

## 3. 步驟 3 — 驗收 A–F

各家輸出（2026-09-12T02:05:03Z 變更後立即；E 為 +5 分鐘）：

**A** `systemctl is-enabled goaa-model-router`
```
disabled
rc=1
```

**B** `systemctl is-active goaa-model-router`
```
inactive
rc=3
NRestarts  : 0
UnitFileState: disabled
```

**C** `ss -ltnp | grep 8080`
```
LISTEN 0 2048 0.0.0.⟨0⟩:8080 0.0.0.⟨0⟩:* users:(("uvicorn",pid=2994296,fd=7))
```
⇒ 仍只有 `goaa-router` 的 uvicorn（**同一 PID 2994296**，未變）。

**D**
```
goaa-router is-active: active
router_health=200
```

**E** 觀察 5 分鐘（`sleep 300`）後再查：
```
=== E (t+5min) 2026-09-12T02:11:06Z ===
is-enabled : disabled
is-active  : inactive
NRestarts  : 0
UnitFileState: disabled
MainPID    : 0
--- 8080 ---
LISTEN 0 2048 0.0.0.⟨0⟩:8080 0.0.0.⟨0⟩:* users:(("uvicorn",pid=2994296,fd=7))
--- goaa-router ---
is-active: active
router_health=200
--- journal -u goaa-model-router since 02:05:03Z ---
（只有 02:05:03 的關閉 5 行；**無新啟動**）
```
⇒ **沒有別的東西把它拉起來。**（若又變 activating/active，依令停手回報，不自行 mask —— 本輪未發生。）

**F** 日誌乾淨：
```
$ journalctl -u goaa-router --since "5 min ago" --no-pager | tail -20
（全部是正常的 worker 輪詢，皆 200 OK）
02:11:10 ... "GET /tasks/next/do-cloud-3 HTTP/1.1" 200 OK
02:11:15 ... "POST /worker/heartbeat HTTP/1.1" 200 OK
02:11:18 ... "GET /tasks/next/aika-1 HTTP/1.1" 200 OK
02:11:26 ... "GET /tasks/next/do-cloud-1 HTTP/1.1" 200 OK

$ journalctl -u goaa-router --since "15 min ago" | grep -iE 'fuser|address already in use|Errno 98|8080'
（無任何匹配）
```

### 補充量化（F7b）— 「迴圈真的停了」
```
log lines 01:50:00Z–02:05:00Z（改前 15 分鐘）: 2105 行，其中 'address already in use' 142 次
log lines 02:05:03Z–now（改後）              : 5 行（全為關閉訊息）
'Started goaa-model-router' after the change : 0 次
```

### 補充（F8）— `goaa-router` 未受影響的最強證據
```
PID    STARTED                ELAPSED     CMD
2994296 Fri Sep 11 06:21:50 2026  19:49:50  ...uvicorn api:app --host 0.0.0.⟨0⟩ --port 8080
```
⇒ 進程自 2026-09-11 06:21:50 起**連續存活近 20 小時**，本輪**未重啟**。

### 補充（F9/F10）— 周邊未被誤動（唯讀複核）
```
DOCKER-USER 規則數: 6 行（D0.2 的 5 條規則 ＋ 鏈宣告，原樣）
/etc/ufw/after.rules: 40 行、sha256 前16 f6a1794c355b50db（與 D0.2 套用後逐位元相同）
ufw status: active；8080/tcp ALLOW IN（v4+v6）仍在原樣（D0.3 已撤銷 ⇒ 不動）
```

## 4. 改前改後對照表

| 檢查項 | 改前 | 改後 | 判定 |
|---|---|---|---|
| is-enabled | `enabled` | `disabled` | ✅ A |
| is-active | `activating` | `inactive` | ✅ B |
| NRestarts | 245,246 | 0 | ✅ |
| UnitFileState | `enabled` | `disabled` | ✅ |
| multi-user.target.wants symlink | 存在 | **已移除** | ✅ |
| unit 檔本體 | 332 B 存在 | **332 B 仍在** | ✅ 未刪 |
| mask | 無 | **無** | ✅ 未 mask |
| 8080 owner | uvicorn 2994296 | uvicorn 2994296 | ✅ C 同一 PID |
| goaa-router health | 200 | 200 | ✅ D |
| +5 分鐘後 A/B | — | disabled／inactive | ✅ E |
| goaa-router 日誌搶埠錯誤 | — | 0 | ✅ F |
| D0.2 DOCKER-USER／after.rules | 6 行／40 行 `f6a1794c355b50db` | 同 | ✅ 未動 |

## 5. 回滾

```
systemctl enable --now goaa-model-router
```
（回到原狀：`enabled` ＋ 立刻拉起。還原後預期會**再次**進入 5 秒重啟迴圈，因為 8080 仍由 `goaa-router` 持有 —— 這是原本的狀態，不是新問題。）

其他未動的殘留：unit 檔 `/etc/systemd/system/goaa-model-router.service` 從頭到尾保持原樣，無需還原。

## 6. 本輪紀律自證

未動 `goaa-router` / `goaa-web` / `cloudflared` / `goaa-postgres`；未碰資料庫；未刪 unit 檔；未 mask；未裝套件；未對外發起任何掃描（全部指令皆走 `ssh do-runtime-anchor` 本機操作）；**未碰 ufw、未碰 `DOCKER-USER`、未碰任何 worker**（D0.3 已由 Tao 撤銷）；env 與金鑰只列變數名（本輪未讀取任何 env／金鑰值）。

## 7. 未做（等令）

- `reports/2026-09-12/d0-3-ufw8080/CANCELLED.md` —— 同輪新建（見同 commit）。
- 其餘收口項（`17879` 另輪等）未動。

---
relay main: `<SHA_PLACEHOLDER>`（本輪報告 commit；其後僅有一筆子提交用於寫入本行）
