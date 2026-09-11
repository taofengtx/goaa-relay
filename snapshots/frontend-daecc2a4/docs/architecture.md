# GOAA.AI 系統總架構
**版本：** v1.2.0  
**日期：** 2026-05-07  
**變更：** AiKa-Test 角色解耦為可插拔審計層；引入兩階段 AI 審計路線

---

## 一、全鏈路架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                     規劃層（人類 + AI）                       │
│  Tao 師兄（語音）→ ChatGPT → task.txt                        │
│         ↓ 複製                                               │
│  Gemini（規劃優化）→ 結構化需求文檔                           │
│         ↓ 複製                                               │
│  Claude（架構總控 + 任務拆解）→ 結構化指令                    │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│           AiKa-1 調度中心（本地開發機）                       │
│           IP: 192.168.1.207                                  │
│  - 接收 Claude 指令                                          │
│  - 調用 OpenClaw 分發任務至各節點                            │
│  - 監控心跳、收集結果、觸發結算                              │
└──────┬──────────────┬──────────────────────┬────────────────┘
       ↓              ↓                      ↓
 AiKa 雲盒       AiKa 雲盒           AiKa 本地盒子
 Hetzner VPS     Hetzner VPS         用戶購買 💰
 aika-dev-01     aika-devops-01      aika-local-xxx
       └──────────────┴──────────────────────┘
                          ↓ 提交代碼至 feature/* 分支
┌─────────────────────────────────────────────────────────────┐
│               GitHub Actions 硬性檢查層                      │
│  語法/類型/API/WebSocket/Build — 全部通過才進入下一層         │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│          AiKa-Test 可插拔審計層 ⭐ 防作弊核心                 │
│                                                             │
│  【第一階段 — API 審計期】                                   │
│  底層可選：Claude API  或  GPT-5-Codex API（Responses API）  │
│  職責：讀取 PR diff + architecture.md → 產出 QualityScore    │
│                                                             │
│  【第二階段 — SDK 整合期】                                   │
│  引入：Codex CLI / SDK 進入 GitHub Actions 流水線            │
│  職責：多 Worker 代碼自動合併、衝突修復、整合測試             │
│                                                             │
│  QwenPaw/OpenClaw：負責調用 HTTP API（最易自動化）           │
│  Codex CLI/SDK：在 GitHub Actions 層級執行複雜整合動作       │
└─────────────────────────┬───────────────────────────────────┘
                          ↓ QualityScore ≥ 0.6
┌─────────────────────────────────────────────────────────────┐
│               PR 合並 → main → 生產部署                      │
│  Vercel（portal.goaa.ai）+ Hetzner（api.goaa.ai）           │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│           Credits 結算（僅本地盒子）                          │
│  Credits = Base × Difficulty × QualityScore × Stability     │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、AiKa-Test 可插拔設計原則

AiKa-Test 是一個**邏輯角色**，不綁定特定模型。底層審計引擎可依需求切換：

```yaml
# aika-test-config.yml
aika_test:
  stage_1:                          # API 審計期
    engine: claude                  # claude / gpt-5-codex / gemini
    api_endpoint: https://api.anthropic.com/v1/messages
    model: claude-sonnet-4-6
    fallback: gpt-5-codex           # 主引擎不可用時自動切換

  stage_2:                          # SDK 整合期
    engine: codex-cli
    entry: github-actions
    tasks:
      - merge_conflicts
      - integration_test
      - pr_generation
```

**切換邏輯：**
- QwenPaw/OpenClaw 只需 `POST /api/v1/tasks/{id}/audit`
- 內部自動路由至當前配置的審計引擎
- 更換底層模型無需修改上層代碼

---

## 三、AI 角色分工

| AI | 角色 | 介入層級 |
|----|------|---------|
| ChatGPT | 語音秘書 | 規劃層 |
| Gemini | 規劃師 | 規劃層 |
| Claude | 架構總控 | 規劃層 + 審計層（第一階段）|
| GPT-5-Codex | 審計/整合 | 審計層（可插拔）|
| QwenPaw | Agent 引擎 | 執行層 |
| OpenClaw | API Gateway | 執行層 + 調度 |
| AiKa 節點 | Worker | 執行層 |
| GitHub Actions | CI/CD | 測試層 |
| Codex CLI/SDK | 代碼整合 | 測試層（第二階段）|

---

## 四、SaaS 中央層 vs 邊緣節點

```
中央 SaaS（goaa.ai）負責：        邊緣 AiKa 盒子負責：
- 用戶登入/認證                    - 本地文件處理
- 計費/Credits 管理                - 瀏覽器自動化
- Agent 訂單管理                   - 視頻/圖片處理
- API Gateway                     - 本地模型推理
- AiKa-Test 審計調度               - OCR/PDF 處理
- 技能市場                         - 報稅軟件自動化
```

---

## 五、安全審批與回滾

```
風險等級    審批          回滾方式
LOW        自動執行       git revert
MEDIUM     記錄日誌       cp main.py.bak + restart
HIGH       Tao 師兄批准   git revert + Vercel rollback
CRITICAL   雙重確認       完整環境回滾
```

---

*文檔維護：Claude | AiKa-Test = 可插拔邏輯角色，非綁定模型*
