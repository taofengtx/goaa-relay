# GOAA.AI 開發工作流規範
**版本：** v1.1.0  
**日期：** 2026-05-07  
**變更：** AiKa-Test 兩階段可插拔審計路線

---

## 一、全流程閉環圖

```
STEP 1：需求輸入
────────────────
Tao 師兄（語音）→ ChatGPT → task.txt
       ↓ 複製
Gemini（規劃優化）→ 需求文檔
       ↓ 複製
Claude（架構判斷）→ 標準任務指令

       ↓
STEP 2：任務分發
────────────────
AiKa-1（192.168.1.207）OpenClaw Scheduler
       ↓ 自動匹配角色
  aika-dev      → 代碼任務
  aika-devops   → 部署任務
  aika-test     → 審計任務
  aika-browser  → UI驗證
  aika-local-*  → 本地特殊任務（付報酬）

HIGH/CRITICAL → 先請 Tao 師兄批准 → 收到 token 後執行

       ↓
STEP 3：AiKa 節點執行
─────────────────────
節點接收任務 → 執行 → 提交至 feature/* 分支
心跳每 30 秒上報，日誌實時回傳 AiKa-1

       ↓
STEP 4：GitHub Actions 硬性檢查
────────────────────────────────
✓ Python 語法檢查
✓ TypeScript 類型檢查
✓ API 端點單元測試
✓ WebSocket 連通測試
✓ CORS 頭部驗證
✓ npm run build

任一失敗 → 阻斷 → 退回節點重做
全部通過 → 觸發 STEP 5

       ↓
STEP 5：AiKa-Test 可插拔軟性審計 ⭐
─────────────────────────────────────
【第一階段 — API 審計期（現在）】
底層引擎（可插拔）：
  - Claude API（主）
  - GPT-5-Codex API（備）
調用：QwenPaw/OpenClaw POST HTTP API

四維評分：
  規範性 Adherence    30%  → 符合 architecture.md？
  簡潔性 Simplicity   25%  → 無冗餘/AI廢話？
  安全性 Security     30%  → 無硬編碼Key/後門？
  性能影響 Performance 15%  → 無同步阻塞？

QualityScore 結果：
  ≥ 0.8   → approved + 20% Credits 加成
  0.6~0.8 → approved 正常結算
  < 0.6   → needs_refactor，退回重做，Credits = 0
  Security=0 → security_alert，強制歸零 + 警報

【第二階段 — SDK 整合期（未來）】
引入 Codex CLI / SDK 於 GitHub Actions
職責：多 Worker 代碼自動合併 + 衝突修復 + 整合測試

       ↓ approved
STEP 6：PR 合並 + 部署
───────────────────────
feature/* → PR → dev → main
Vercel 自動部署（portal.goaa.ai）
GitHub Actions → SSH → Hetzner 重啟服務
smoketest → 通知 tao@goaa.ai

       ↓
STEP 7：Credits 結算（僅本地盒子）
────────────────────────────────────
Credits = Base × Difficulty × QualityScore × Stability
明細記錄存入用戶賬戶
portal.goaa.ai/dashboard 可查看
```

---

## 二、AiKa-Test 引擎切換邏輯

```
OpenClaw 收到審計請求
      ↓
讀取 /opt/goaa/aika-test-config.yml
      ↓
current_stage = 1？
  是 → 調用 stage_1.primary_engine API
      主引擎失敗？→ 自動切換 fallback_engine
  否 → 調用 Codex CLI / SDK（GitHub Actions 層）
```

**上層代碼無需修改，引擎切換對 AiKa 節點透明。**

---

## 三、GitHub 分支策略

```
main          生產環境（受保護）
  ↑ PR + Review + 硬性檢查 + 軟性審計
dev           開發主線
  ↑ PR + 硬性檢查
feature/*     功能分支（每個任務一個）
  例：feature/GOAA-20260507-001-heartbeat-api
hotfix/*      緊急修復
  例：hotfix/cors-fix-20260507
```

---

## 四、任務退回機制

| 退回原因 | 處理 |
|---------|------|
| 硬性檢查失敗 | 回傳錯誤詳情，2小時內重做 |
| QS < 0.6 | 附審計報告，節點針對問題修改 |
| Security 警報 | 停止流程，通知 Tao 師兄，節點暫停 |
| 超時未完成 | 重新分配，原節點記錄超時 |

---

## 五、每日例行清單（開工指令觸發）

1. 檢查服務狀態（openclaw / qwenpaw / cloudflared）
2. 檢查節點心跳（是否有節點離線）
3. 查看 GitHub Actions 失敗任務
4. 查看未完成任務（P0 優先）
5. 確認 AiKa-Test 當前審計引擎可用性
6. 輸出今日工作計劃

---

*文檔維護：Claude | 兩階段審計路線：API期→SDK整合期*
