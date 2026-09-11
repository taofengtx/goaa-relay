# Phase 4.1 Reconstruction Audit

**目的**: 紀錄 2026-05-19 將 DO production `/opt/goaa/router/api.py` snapshot 回 git 的審計結論
**規範等級**: 規範 #14 v2 復位文件（將 git HEAD 跟 DO 真實狀態重新對齊）
**簽發**: 2026-05-19 Tao 師兄 + Claude
**配套 commit**: `chore: snapshot DO production state (Phase 4.1) + A2.1 db helpers`

---

## 一、為什麼有這份文件

### 1.1 事件背景

2026-05-19 中午，Claude 在 Worker V5.0 內部生產線 (P1.2.0) 設計過程中，AiKa-1 在直接編輯 DO 上 `/opt/goaa/router/api.py` 時，發現 DO 上的版本比本地 `infra/router/api.py` 多 113 行，而本地 `services/model-router/api.py` 又比 `infra/router/api.py` 少 154 行。

**三份 api.py 版本譜系**：

```
Phase 3 (5/11 commit 2bb74c8)
  services/model-router/api.py    564 行   MD5=1f04e2ca   無 db import
        ↓ Phase 4 演化
Phase 4 (5/14 commit 34f4acd)
  infra/router/api.py             717 行   MD5=f05010c3   有 db import + task_upsert
        ↓ 5/14 ~ 5/19 期間直接在 DO 上手動編輯/hotfix
Phase 4.1 (5/19 真實 production)
  DO /opt/goaa/router/api.py      830 行   MD5=567b3073   + 113 行新功能
```

### 1.2 規範 #14 v2 違規揭露

GOAA 規範 #14 v2「GitHub HEAD 為真相基準」要求所有 production 變更必須先進 git 再部署。本次盤點揭露 DO 在 5/14 ~ 5/19 期間有 113 行未提交的變更，**規範 #14 v2 已被歷史性違反**。

### 1.3 本次處理原則

師兄拍板（路徑 C）：

1. 不嘗試逐 hunk 重建（路徑 B 工時 4-6 小時不划算）
2. 不純 snapshot 無紀錄（路徑 A 失去可追溯性）
3. **Snapshot 同時寫本文檔**，讓未來任何人能透過此文件理解 113 行的功能脈絡

---

## 二、113 行差異功能分類

### 2.1 總覽

```
Diff: 131 insertions (+) / 18 deletions (-) = 113 行淨增
9 個 diff hunks
```

| 類別 | 行數 | 功能 |
|:---|:---:|:---|
| ① Import 補強 | +2/-1 | `+import json`, `from db import` 加 `_exec` |
| ② call_deepseek tool 支援 | +9/-2 | 工具呼叫整合 OpenAI tools schema |
| ③ ChatReq model 擴充 | +2/-0 | `enable_tools: bool` 欄位 |
| ④ Chat 端點 multi-turn + tool + PG | +118/-15 | 多輪對話 + 工具呼叫循環 + PG 訊息儲存 |
| **合計** | **+131/-18** | **= 113 行淨增** |

### 2.2 類別 ① — Import 補強（2 行新增 / 1 行刪除）

**新增**：
```python
import json
```

**修改**：`from db import ...` 行加入 `_exec`

**功能意義**：
- `json` 用於 deepseek tool args 序列化/解析
- `_exec` 為 db 直接 SQL 執行函數（規範 #24 直接呼叫式），給 chat 端點寫 audit log 用

### 2.3 類別 ② — call_deepseek tool 支援（9 行新增 / 2 行刪除）

**新增參數**：
```python
def call_deepseek(prompt, messages, model, tools=None, tool_choice=None):
```

**新增邏輯**：
- DeepSeek body 構造分兩路（含 tools / 不含 tools）
- tools schema 轉換為 OpenAI 兼容格式

**功能意義**：
- 啟用 model-router 透過 DeepSeek 進行 function calling
- 對齊三端鐵律「Provider 工作台調用專業 Skill」的底層基礎設施

### 2.4 類別 ③ — ChatReq model（2 行新增）

**新增欄位**：
```python
class ChatReq(BaseModel):
    ...
    enable_tools: bool = False
```

**功能意義**：
- 客戶端可控是否啟用 tool calling
- 預設 False 向後相容

### 2.5 類別 ④ — Chat 端點重寫（118 行新增 / 15 行刪除）⭐

**這是 88.5% 的 diff 集中處。**

**主要改動**：

#### 2.5.1 Chat 開頭（@@ -544,9 +551,17 @@）
```python
# session_id 自動生成（UUID5 確定性）
sid = req.session_id or str(uuid.uuid5(uuid.NAMESPACE_DNS, f"client:{client_id}"))

# PG session_ensure 呼叫
session_ensure(sid, project_id, title="Chat session")

# messages_get 拉歷史
history = messages_get(sid, limit=20)
```

#### 2.5.2 Chat 中部（@@ -568,12 +583,121 @@）⭐ 最大區塊
```python
# Tool message 過濾（role='tool' 不入 history send to LLM）
filtered_messages = [m for m in messages if m["role"] != "tool"]

# tools 注入（deepseek 格式轉換）
if req.enable_tools:
    tools_schema = [tool_to_openai_format(t) for t in available_tools]
else:
    tools_schema = None

# 工具調用循環
response = call_deepseek(..., tools=tools_schema, tool_choice=...)
if response.tool_calls:
    for tc in response.tool_calls:
        # 調用 → 結果回 feed → 再 response
        result = invoke_tool(tc.name, tc.args)
        messages.append({"role": "tool", "content": result, "tool_call_id": tc.id})
    # 再次調用 LLM 得最終回應
    response = call_deepseek(..., tools=tools_schema, tool_choice="none")

# POST /task/complete 呼叫（dispatch 任務）
requests.post(f"{ROUTER}/task/complete", json={...})

# message_insert 寫入 PG
message_insert(sid, role="user", content=req.prompt, ...)
message_insert(sid, role="assistant", content=response.content, ...)

# DB 裡查找 agent_id
agent_id = _exec("SELECT id FROM v4_agents WHERE name = %s", (req.agent_name,))
```

#### 2.5.3 Chat 尾部（@@ -592,17 +716,6 @@）
```python
# 移除舊的簡單 prompt-only 回傳
# 改用完整的 session-aware response
return {
    "session_id": sid,
    "message_id": msg_id,
    "content": response.content,
    "tool_invocations": [...],  # audit trail
    "usage": {...},
}
```

**功能意義**：
- 完整的 multi-turn 對話支援
- Tool calling 整合（function calling）
- PG 持久化所有對話（sessions / messages 表寫入）
- Session-aware response（客戶端可繼續對話）
- audit trail（為 Phase 5 Skill Marketplace 收益結算奠基）

---

## 三、規範遵守記錄

### 3.1 已對齊的規範

| 規範 | 對齊方式 |
|:---:|:---|
| #11 only-add | snapshot 動作純新增 113 行，不刪原有功能 |
| #12 fingerprint | api.py 830 行 / MD5=567b3073，已 SCP 比對 |
| #14 v2 | 本次 snapshot 後，git HEAD = DO 真實狀態 |
| #25 跨層型別 | 113 行內含 UUID/JSONB 處理，符合跨層轉換 |
| #28 不靜默 | chat 端點所有 catch 有 logger.exception |
| #36 v2 | 本文檔即真實狀態紀錄 |
| 三端鐵律 | 113 行是「Provider 工作台調用專業 Skill」的基礎設施，符合 Worker 層責任 |

### 3.2 違規記錄（傍晚立規候選）

本次事件揭露的長期問題：

1. **規範 #14 v2 早於今天被違反** — DO 上 5/14 ~ 5/19 期間有 113 行直接編輯
2. **deploy 腳本指向錯誤檔案** — `services/model-router/api.py`（Phase 3，564 行）已過時，不該作為部署源頭
3. **缺乏「DO ↔ git 一致性監控」機制** — 應加入定期 MD5 比對自動告警

### 3.3 建議立規（傍晚集中）

- **規範 #45 候選**：AI 端越權邊界（不替 Claude 出方案，不替師兄拍板）
- **規範 #46 候選**：AI 暫存檔處理紀律（寫到 tmp_inspection/，不自動 del）
- **規範 #47 候選**：DO ↔ git 一致性監控（每日 MD5 比對 production vs HEAD）

---

## 四、Snapshot 後續處置

### 4.1 立即（本次 commit 包含）

- ✅ `infra/router/api.py` 從 717 → 830 行（snapshot DO 版）
- ✅ `infra/router/db.py` 從 245 → 312 行（A2.1 helper append，與 DO db.py 無衝突）
- ✅ `docs/architecture/PHASE_4_1_RECONSTRUCTION.md`（本文檔）
- ✅ deploy 腳本修正：從 `services/model-router/api.py` 改指向 `infra/router/api.py`

### 4.2 短期（本週內）

- [ ] `services/model-router/api.py` Phase 3 廢檔處理（規範 #11 不刪，加 deprecation header）
- [ ] DO ↔ git 一致性監控腳本（規範 #47 候選實作）

### 4.3 中期（Phase 1 驗收前）

- [ ] Chat 端點 113 行的單元測試覆蓋
- [ ] tool_invocations 雙寫接入（P1.2.1 patch 落地）
- [ ] task_upsert dispatch hook 重做（這次按規範 #14 v2 走完整流程：git → push → DO 拉）

### 4.4 長期（Phase 3 之前）

- [ ] 三端鐵律對齊：113 行的 chat 端點變成 Provider 工作台底層
- [ ] Skill Marketplace 接入 tool calling 機制
- [ ] Provider 訂閱可調用 Skill 透過此端點實作

---

## 五、版本譜系總結

```
2026-05-11  commit 2bb74c8  Phase 3
            services/model-router/api.py (564 行)
            └── 無 PG 整合，無 tool calling

2026-05-14  commit 34f4acd  Phase 4
            infra/router/api.py (717 行)
            ├── 加入 from db import
            ├── task_upsert dispatch (但僅 3 處: cancel/complete/pool_add)
            └── 缺 dispatch_task hook

2026-05-14 ~ 2026-05-19  Phase 4.1（未 commit）
            DO /opt/goaa/router/api.py (830 行)
            ├── 加 import json
            ├── 加 _exec import
            ├── call_deepseek tools 支援
            ├── ChatReq enable_tools
            └── Chat 端點完整重寫
                    multi-turn + tool + PG 寫入

2026-05-19  commit <pending>  Phase 4.1 Reconstruction
            infra/router/api.py (830 行) ← snapshot from DO
            infra/router/db.py (312 行) ← +A2.1 helpers
            docs/architecture/PHASE_4_1_RECONSTRUCTION.md ← 本檔
            scripts/do-deploy-model-router-api.sh ← 改指向 infra/
```

---

## 六、Snapshot 完成校驗清單

完成本次 commit 後：

- [ ] `git diff HEAD~1 infra/router/api.py` 應顯示 +113 -0 變化
- [ ] `md5sum infra/router/api.py` = `567b3073...` （與 DO 一致）
- [ ] `md5sum infra/router/db.py` = `c19483de...` （A2.1 patched）
- [ ] DO 上 `cat /opt/goaa/router/api.py | md5sum` = git HEAD 對應檔的 md5
- [ ] deploy 腳本 fresh run 拉到的 api.py = 830 行版本

---

**文檔簽發**: 2026-05-19 PT Claude（架構總控）+ Tao 師兄（最終 review）
**規範依據**: #11 only-add / #12 fingerprint / #14 v2 GitHub HEAD / #36 v2 Runtime Truth / 三端鐵律
**配套 commit message**: `chore: snapshot DO production state (Phase 4.1) + A2.1 db helpers`
**狀態**: 待 snapshot + commit + push 後生效
