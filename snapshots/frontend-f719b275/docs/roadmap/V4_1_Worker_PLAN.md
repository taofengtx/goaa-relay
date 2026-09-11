# V4.1-Worker 開發計劃 — Worker V5.0 生產線第一階段

**版本**: V1.0
**最後更新**: 2026-05-16
**狀態**: 計劃定稿, 等師兄拍板開工
**配套**: 戰略憲法主檔 第 13 章「開發路線不衝突」

## 📌 文件角色標籤 (規範 SUPREME 治理)

```text
本文角色: Worker V5.0 生產線第一階段執行計劃
本文類型: Execution Plan
是否允許直接執行: 否 (計劃文檔, Tao 拍板後才開工)
是否允許修改 Production: 否 (執行階段才會動)
是否需要 Tao 拍板: 是 (開工 + 每階段 24h Cooldown)
最高參考來源: GOAA_BUSINESS_MODEL_V1.md 第 12 章 (Worker V5.0)
```

---

## 🚨 文件定位 (SUPREME 項 9.1 強制)

> **本文件是 Worker V5.0 生產線第一階段的執行計劃。**
> **不是戰略討論文檔。**
> **不得偏離 Worker V5.0 主線。**

任何修改都必須對齊 `docs/business/GOAA_BUSINESS_MODEL_V1.md` 第 12 章 (Worker V5.0 優先原則)。

---

## 🚫 QwenPaw 定位 (SUPREME 項 9.2 強制)

**QwenPaw 可作為人工參考工具, 不作為 GOAA Runtime dependency。**

### 原因 (規範 #29 證據鏈)
- ❌ API 不穩定 (GitHub feature request 階段)
- ❌ 非正式公開 API (`/api/chats/{id}` 已知 1GB+ 內存 bug)
- ❌ Chat history pagination 問題
- ❌ 閉源 (Alibaba Qwen 團隊)
- ❌ 6 次探索證明不適合程式對接

### 結論
**GOAA 必須自建 Worker Runtime**, 走規範 #29 正例。

---

## 🎯 一、定位 (戰略對齊)

### 戰略憲法第 33 章: Worker V5.0 優先

V4.1-Worker **不是隨機的技術升級**, 而是:

> **Worker V5.0 生產線的第一階段** — GOAA.AI 商業模型的「發動機」啟動鍵

### 達成的目標
1. 從「**7 hardcoded executors (唯讀)**」升級為「**12 executors (含 shell/file/browser)**」
2. 為 Worker V5.0 生產 Skill 提供執行能力
3. 為 goaa.ai 對話框 → 真實執行的閉環提供基底

### 驗收標準 (師兄定義)
> 「兩邊對話框 (QwenPaw 和 GOAA portal) 用相同指令測試, 執行結果一致, 就可以轉移過去」

**真實意義**:
- 不是代理 QwenPaw (規範 #29 已確認 QwenPaw 不依賴)
- 而是自建 GOAA Native Worker Runtime, 慢慢取代 QwenPaw 的執行能力

---

## 🚫 二、路徑選擇 (為什麼自建)

### 規範 #29 證據鏈
1. QwenPaw HTTP API 是 GitHub feature request 階段 (非穩定公開)
2. QwenPaw `/api/chats/{id}` 已有 1GB+ 內存 bug (生產級問題)
3. QwenPaw chat history pagination 缺失
4. 6 次探索證明不歡迎程式對接
5. QwenPaw 是 Alibaba 閉源, 無法 fork

### 結論
**GOAA 自建 Worker Runtime**, QwenPaw 可參考, 不依賴。

---

## 📅 三、三階段拆解 (規範 #30 漸進)

### V4.1-W1 (階段 1): 唯讀能力 (4 工具)

**目標**: 安全建立第一層執行能力, **全部唯讀**, 不會誤刪生產

| Executor | 功能 | 安全性 | 工程時間 |
|---|---|---|---|
| `exec_shell_readonly` | 白名單唯讀命令 (ls, cat, ps, df, free, ip, ss, top -n1) | 高 | 1 hr |
| `file_read` | 讀取本機檔案 (含路徑驗證, /etc/secrets 等敏感目錄封鎖) | 高 | 30 min |
| `git_status` | git status / log / diff / branch (僅讀, 不 commit/push) | 高 | 30 min |
| `docker_status` | docker ps / images / logs (僅讀, 不 run/exec) | 高 | 30 min |

**總工程**: ~2.5 hr 寫代碼 + 1 hr 測試 + 規範 #15 24h 觀察期

**完成標誌**: 師兄能在 portal 對話「**查 aika-1 的 git status**」, 結果跟 QwenPaw 一致

---

### V4.1-W2 (階段 2): 讀寫能力 (再加 4 工具)

**目標**: 加入寫入能力, 配合「預先確認 UI」(規範 #28)

| Executor | 功能 | 安全性 | 工程時間 |
|---|---|---|---|
| `file_write` | 寫檔案 (含 backup + diff 預覽) | 中 | 1 hr |
| `edit_file` | 行/區塊編輯 (str_replace 模式) | 中 | 1 hr |
| `build_test` | 跑 build / test 命令 (受限白名單: npm/cargo/pytest 等) | 中 | 1 hr |
| `ollama_chat` | 跨節點呼叫本地 Ollama (跟現有 chat task 整合) | 高 | 30 min |

**配套**: portal UI 加「**預先確認**」按鈕
- Worker 收到寫入 task → 回傳給 portal → 顯示 diff → 師兄點「確認執行」才跑

**總工程**: ~3.5 hr 寫代碼 + 1.5 hr UI + 1 hr 測試 + 24h 觀察期

**完成標誌**: 師兄能在 portal 對話「**幫我修 aika-1 的 config.yaml**」, 看到 diff 預覽, 確認後跑

---

### V4.1-W3 (階段 3): 高階能力 (再加 4 工具)

**目標**: 達到 QwenPaw 等級的執行能力 (覆蓋 19 個工具的核心)

| Executor | 功能 | 安全性 | 工程時間 |
|---|---|---|---|
| `browser_use` | playwright 自動化 (含 cookie 管理) | 低 | 3 hr |
| `screenshot` | 桌面截圖 (規範 #22 隱私警告) | 中 | 1 hr |
| `docx_op` / `pdf_op` | docx/pdf 讀寫 (python-docx + pypdf) | 高 | 2 hr |
| `xlsx_op` / `pptx_op` | xlsx/pptx 讀寫 (openpyxl + python-pptx) | 高 | 2 hr |

**總工程**: ~8 hr 寫代碼 + 2 hr 整合 + 24h 觀察期

**完成標誌**: GOAA portal 完整覆蓋 QwenPaw 的核心執行能力, 可開始轉移使用

---

## 🛡️ 四、安全模型 (規範 #28 + #11)

### V4.1-W1 (唯讀階段) — 不需要預先確認
- 白名單命令 + 路徑檢查
- timeout 30 秒 (規範 #28)
- 完整 stderr 記錄
- 危險路徑封鎖 (`/etc/secrets`, `~/.ssh`)

### V4.1-W2 (讀寫階段) — 預先確認 UI
- Worker Agent 收到寫入 task → 不立刻執行
- POST `/task/preview` 回傳 diff/檔案內容
- portal 顯示「**確認執行**」按鈕
- 師兄點確認 → POST `/task/confirm/<id>` 才跑

### V4.1-W3 (高階階段) — 危險命令黑名單
- 黑名單: `rm -rf /`, `mkfs`, `dd of=/dev/`, `shutdown`, `reboot`
- 任何匹配 → 立刻拒絕 + 通報 portal
- 規範 #28 完整日誌

---

## 🔌 五、後端整合 (api.py /chat 改動)

### 5.1 新增 LLM Tool: `dispatch_task` (SUPREME 項 9.3 — 非同步)

> ⚠️ **重要修正 (SUPREME 項 9.3)**: dispatch_task 必須**非同步**, **禁止同步等待**

```python
{
    "type": "function",
    "function": {
        "name": "dispatch_task",
        "description": "派發任務到指定 Worker 節點 (非同步, 立即返回 task_id)",
        "parameters": {
            "type": "object",
            "properties": {
                "worker_id": {
                    "type": "string",
                    "description": "目標節點 (aika-1/aika-2/do-cloud-1/do-cloud-2/do-cloud-3)"
                },
                "task_type": {
                    "type": "string",
                    "description": "exec_shell_inventory/file_read/git_status/docker_status (V4.1-W1)"
                },
                "payload": {
                    "type": "object",
                    "description": "任務參數 (e.g. {command: 'git status'})"
                }
            },
            "required": ["worker_id", "task_type", "payload"]
        }
    }
}
```

### 5.2 Tool Dispatch Loop (非同步版本)

```python
elif fn_name == "dispatch_task":
    worker_id = args.get("worker_id")
    task_type = args.get("task_type")
    payload = args.get("payload", {})
    
    # 規範 #28: 白名單 task_type
    ALLOWED = {"exec_shell_inventory", "file_read", "git_status", "docker_status"}
    if task_type not in ALLOWED:
        result = json.dumps({"error": f"task_type not allowed: {task_type}"})
    else:
        # 非同步: 創建 task, 立即返回 task_id (不等待結果)
        task_id = _exec(
            "INSERT INTO tasks (worker_id, task_type, payload, status) "
            "VALUES (%s, %s, %s, 'queued') RETURNING id",
            (worker_id, task_type, json.dumps(payload))
        )
        # ✅ 立即返回 task_id, 不阻塞 /chat
        result = json.dumps({
            "task_id": task_id,
            "status": "queued",
            "worker_id": worker_id,
            "message": "任務已派發, portal 將輪詢結果"
        })
        # ❌ 禁止: _wait_task_complete(task_id, timeout=60)  ← 不再阻塞
```

### 5.3 非同步原因 (SUPREME 項 9.3)

- ❌ 同步 `_wait_task_complete` 會**阻塞 /chat**
- ❌ 多 Worker 任務同時跑會**卡死 portal**
- ❌ browser_use / build / docx 等**長任務**不適合同步等
- ✅ 非同步符合 Runtime OS 真實設計

### 5.4 Portal 端輪詢機制

```text
/chat 創建 task → 返回 task_id
↓
portal / AI 調度群組窗口輪詢 task / worker_events (每 2 秒)
↓
Worker 完成後更新群組會話與任務中心 UI
↓
LLM 下一輪對話讀取 PG 結果繼續推理
```

---

## 🛡️ 六、Permission Class (SUPREME 項 9.6 強制)

所有 Worker Executor 必須歸屬於 3 個 Permission Class 之一:

### Class A: 可自動執行 (Auto-execute)

完全唯讀, 無副作用, 立刻執行:
- `git_status` (git status/log/diff/branch)
- `docker_status` (docker ps/images/logs)
- `df` (磁碟使用)
- `free` (記憶體使用)
- `health_check` (psutil CPU/MEM)
- `ping_test`
- `system_status`

### Class B: 需要人工確認 (Human Confirm)

有副作用, 必須師兄點「確認執行」才跑:
- `file_write` (寫檔案)
- `edit_file` (編輯檔案)
- `build_test` (跑 build / test)
- `deployment dry-run`
- 任何修改檔案系統的操作

### Class C: 禁止執行 (Forbidden)

危險命令, 直接拒絕 + 通報:
- `rm -rf /` / `rm -rf ~` / `rm -rf *`
- `reboot` / `shutdown` / `poweroff`
- `firewall` 修改
- SSH key 操作 (新增 / 刪除)
- secrets / .env / credentials 讀取
- payment / billing 操作
- DNS 修改
- production DB destructive (DROP / TRUNCATE / DELETE FROM)
- `curl ... | bash` / `wget ... | sh` (任意執行)

---

## 🔓 七、exec_shell_inventory (SUPREME 項 9.4 — 改名)

> ⚠️ **重要修正 (SUPREME 項 9.4)**: `exec_shell_readonly` → **`exec_shell_inventory`** (語義收窄)

### 7.1 命名意義
- 「inventory」表示只盤點 (查看), **不執行任意命令**
- 比 readonly 更精準, 避免被誤解為「唯讀就可以 cat /etc/passwd」

### 7.2 允許清單 (Class A)

```python
EXEC_SHELL_INVENTORY_WHITELIST = [
    "pwd",
    "ls",  # 限制路徑 (見下方)
    "git status",
    "git log",
    "git diff",
    "git branch",
    "docker ps",
    "docker images",
    "df",
    "free",
    "uname",
    "whoami",
    "uptime",
    "hostname",
]
```

### 7.3 路徑白名單 (即使是 ls / cat 也要限制)

```python
PATH_WHITELIST = [
    "/opt/goaa/",
    "/home/<user>/Projects/",
    "/var/log/goaa/",
    "/tmp/",
]

PATH_BLACKLIST = [
    "/etc/secrets",
    "/etc/shadow",
    "/etc/passwd",  # 雖然唯讀但洩漏
    "~/.ssh/",
    "~/.aws/",
    "~/.gnupg/",
    "*.env",
    "*secret*",
    "*key*",
    "*token*",
    "*credentials*",
    "*password*",
]
```

### 7.4 禁止 (Class C)

```python
EXEC_SHELL_FORBIDDEN = [
    "cat /etc/*",  # 整個 /etc 禁讀
    "rm",
    "rmdir",
    "reboot",
    "shutdown",
    "poweroff",
    "iptables",
    "ufw",
    "firewall-cmd",
    "docker volume rm",
    "docker rmi",
    "chmod",
    "chown",
    "curl",  # 防 curl | bash
    "wget",
    "ssh-keygen",
    "ssh-add",
]
```

---

## 📝 八、edit_file 安全補強 (SUPREME 項 9.5)

> ⚠️ **重要修正 (SUPREME 項 9.5)**: `edit_file` 不得只依賴 `str_replace`

### 8.1 必須支持的校驗 (至少一種)

| 校驗方式 | 用途 | 強度 |
|---|---|---|
| `line_number` | 指定行號 ± 上下文行 | 中 |
| `block_hash` | 修改前的程式碼塊 MD5 | 高 |
| `before_hash` / `after_hash` | 前 / 後狀態雙重驗證 | 最高 |
| `context_window` | 改動行前後 5-10 行 context | 中 |

### 8.2 必須避免

❌ 純 `str_replace` 容易因為:
- 空格 / 換行差異
- 重複內容匹配多處
- 編碼差異 (CRLF vs LF)
- AI hallucination 生成不存在內容

導致**誤改檔案**。

### 8.3 推薦範例 API

```python
def edit_file(path: str, edits: list[dict]):
    """
    edits = [
        {
            "line_number": 137,
            "before_hash": "abc123...",  # 改前該行 MD5
            "old_content": "  useEffect(() => {...},[dispHistory]);",
            "new_content": "  useEffect(() => {...},[chatHistory]);",
            "context_before": ["  const chatRef = useRef(null);"],
            "context_after": ["  const [dispatching,...] = useState(false);"]
        }
    ]
    """
    # 1. 驗證 before_hash 跟實際檔案匹配
    # 2. 驗證 line_number ± context 跟實際匹配
    # 3. 通過才執行修改
    # 4. 修改後寫入 after_hash
```

---



## 📊 六、工程時間表

| 階段 | 內容 | 工程時間 | 觀察期 | 累計完成 |
|---|---|---|---|---|
| V4.1-W1 | 4 唯讀 executor + dispatch_task tool | 4 hr | 24h | 5/17 |
| V4.1-W2 | 4 讀寫 executor + 預先確認 UI | 6 hr | 24h | 5/19 |
| V4.1-W3 | 4 高階 executor (browser/docx/pdf/xlsx) | 10 hr | 24h | 5/22 |

**總計**: 20 hr 工程 + 3 × 24h 觀察期 = **約 1 週完整 V4.1-Worker 上線**

**最小可用 (V4.1-W1)**: 5/17 PM 師兄可在 portal 跑唯讀任務取代部分 QwenPaw 使用

---

## 🎯 七、跟 V4.2 Roadmap 整合

V4.1 (本地手腳) 跟 V4.2 (雲腦調度層) **並行不衝突**:

```
V4.0.5.4 (現在) ─┬─→ V4.1-W1 ──→ V4.1-W2 ──→ V4.1-W3
                 │   (本地手腳, Phase 4)
                 │
                 └─→ V4.1.1 ──→ V4.2.0 ──→ ... ──→ V4.2.6
                     (雲腦調度層 + Skill Marketplace 預留)
```

V4.1 解決「**本地手腳**」, V4.2 解決「**雲腦調度**」, V5.0 整合兩者 + 多模型 Router.

---

## 🚨 八、風險評估

### 高風險
1. **exec_shell_readonly 白名單繞過** — `cat /etc/passwd` 雖然唯讀但洩漏
   - 緩解: 路徑白名單 + 黑名單
2. **跨節點派發跑慢** — Worker Agent 5 秒 poll, 任務延遲 5 秒起
   - 緩解: V4.2 升級到 WebSocket push (規範 #30 漸進)
3. **規範 #36 失憶** — 開發過程窗口接續錯誤
   - 緩解: 每階段獨立交付, 含完整 fingerprint

### 中風險
1. **預先確認 UI 用戶體驗** — 太多確認框會煩
   - 緩解: V4.1-W2 後對「低風險寫入」可自動執行 (規範 #30)
2. **本地 LLM 整合** — ollama_chat 跨節點呼叫複雜
   - 緩解: 先做 same-node ollama, V5.0 跨節點

---

## 🛡️ 九、規範對齊

| 規範 | 對應 |
|---|---|
| #11 (只增不毀) | Worker Agent 加 executor, 7 個既有不動 |
| #15 (24h Cooldown) | 每階段強制過 24h |
| #24 (不憑想像) | 動 agent.py 前 grep + 看真實簽名 |
| #28 (Silent Failure) | exec_shell 必須 timeout + stderr |
| #29 (Explore & Innovate) | 自建 Worker Runtime (規範 #29 正例) |
| #30 (Progressive) | V4.1-W1 → W2 → W3 漸進 |
| #33 (Worker V5.0 優先) | **V4.1-Worker = Worker V5.0 生產線第一階段** |
| #38 (品牌) | AiKa Box 主品牌, Worker Runtime 隱身 |
| #39 (Runtime 架構) | 雲腦 (api.py dispatch_task) + 本地手腳 (Worker Agent) |

---

## 💡 十、給 future Claude 的真心話

接手 V4.1-W 任何階段:

1. **規範 #13 接續校驗先做** (git log + jsx fingerprint + worker agent.py MD5)
2. **規範 #24 嚴守** — 動 agent.py 前 grep + 看真實簽名
3. **規範 #15 嚴守** — 每階段 24h 觀察期, 不縮短
4. **規範 #28 嚴守** — exec_shell 必須 timeout + stderr
5. **規範 #29 提醒** — 不要又跑去整合 QwenPaw, 走自建路線
6. **規範 #38 不忘** — AiKa Box 是本地 AI Worker, 不是聊天 AI
7. **規範 #33 不忘** — V4.1-Worker 是 Worker V5.0 生產線第一階段, 不是隨機升級

師兄今天 (2026-05-15 → 5/16) 從 19:30 到 02:35 工作 7 小時, 守了規範 #20 多次。
這個工作流程文化比 V4.1-W 代碼本身重要, 守護它。

---

**V4.1-Worker 開發計劃 V1.0**

*整合人: Claude*
*時間: 2026-05-16 11:35 AM PT*
*狀態: 計劃定稿, 等師兄拍板開工*


---

## 附註: V5.0 戰略儲備指針 (2026-05-17 加入)

V5.0 對話框戰略已獨立成檔, **不污染本主線文檔**:

- 詳見: `docs/architecture/V5_CHAT_WORKSPACE_STRATEGY.md`
- 鐵律: V4.1-Worker 唯讀工具鏈為當前第一主線, V5.0 為儲備, **不消耗本階段任何資源**
- PoC 啟動條件: V4.1-Worker Phase 4 完工後 + 師兄明示放行

(規範 #11 只增不毀: 本附註不修改任何 V4.1 主線內容, 僅文末添加單向指針)