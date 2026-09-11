# GOAA.AI Agent 角色定義
**版本：** v1.0.0  
**日期：** 2026-05-07

---

## 一、角色總覽

```
規劃層                執行層                審計層
──────               ──────               ──────
Tao + Gemini         AiKa-Dev             AiKa-Test
ChatGPT              AiKa-DevOps          （可插拔）
Claude               AiKa-Browser
                     AiKa-Security
                     AiKa-Docs
                     AiKa-Data
```

---

## 二、AiKa Worker 角色定義

### AiKa-Dev（代碼開發）
```
職責：代碼開發、功能實現、Bug 修復
技能要求：
  - can_python: true
  - can_node: true
  - can_github: true
典型任務：
  - 實現新 API 端點
  - 修復 Bug
  - 重構代碼
分支命名：feature/GOAA-{id}-{描述}
```

### AiKa-DevOps（服務器部署）
```
職責：服務器配置、服務部署、環境管理
技能要求：
  - can_ssh: true
  - can_docker: true（可選）
典型任務：
  - 重啟 Hetzner 服務
  - 更新環境變量
  - 配置 systemd 服務
風險等級：通常 MEDIUM-HIGH，需記錄審批
```

### AiKa-Test（審計員）⭐ 可插拔角色
```
職責：代碼軟性審計、QualityScore 計算
重要原則：這是邏輯角色，底層引擎可插拔

【第一階段 — API 審計期】
  底層引擎（任選其一）：
  - Claude API（claude-sonnet-4-6）
  - GPT-5-Codex API（OpenAI Responses API）
  - Gemini API
  調用方式：QwenPaw/OpenClaw POST HTTP API

【第二階段 — SDK 整合期】
  底層引擎：
  - Codex CLI / SDK
  調用方式：GitHub Actions 層級執行
  職責擴展：
  - 多 Worker 代碼自動合併
  - 衝突修復
  - 整合測試
  - PR 自動生成

評分輸出：QualityScore（0.0-1.0）
  = Adherence(30%) + Simplicity(25%)
  + Security(30%) + Performance(15%)
```

### AiKa-Browser（瀏覽器自動化）
```
職責：UI 驗證、網頁操作、自動填表
技能要求：
  - can_browser: true
  - Playwright 已安裝
典型任務：
  - 驗證 portal.goaa.ai 登入流程
  - 自動填寫加州首付援助申請
  - 截圖驗證 UI 正確性
```

### AiKa-Security（安全審查）
```
職責：安全掃描、漏洞檢測、密鑰審查
典型任務：
  - 掃描硬編碼 API Key
  - 檢查 CORS 配置
  - 驗證 SQL 注入防護
觸發條件：
  - 每次 HIGH/CRITICAL 任務前
  - 每週定期掃描
輸出：security_report.md
```

### AiKa-Docs（文檔撰寫）
```
職責：技術文檔、changelog、架構說明
典型任務：
  - 更新 DEVELOPMENT.md
  - 生成 API 文檔
  - 撰寫用戶手冊
觸發條件：每次功能完成後
```

### AiKa-Data（數據處理）
```
職責：數據分析、報表生成、數據抓取
典型任務：
  - 生成月度 Credits 報表
  - 抓取房產數據
  - 處理稅務文件
技能要求：
  - can_python: true
  - 本地文件訪問權限
```

---

## 三、節點類型與報酬

| 節點類型 | 位置 | 報酬 | 說明 |
|---------|------|------|------|
| AiKa-1 | 192.168.1.207 | 無 | 調度中心 |
| AiKa 雲盒 | Hetzner VPS | 無 | 平台自有 |
| AiKa 本地盒子 | 用戶辦公室 | ✅ Credits | 邊緣貢獻 |

---

## 四、能力自檢報告格式

每個節點初始化時提交：

```json
{
  "node_id": "aika-local-001",
  "node_type": "local",
  "hostname": "fq168-sm",
  "os": "Ubuntu 26.04 LTS",
  "capabilities": {
    "can_ssh": true,
    "can_browser": true,
    "can_github": true,
    "can_python": true,
    "can_node": true,
    "can_docker": false,
    "can_ffmpeg": true,
    "has_gpu": false
  },
  "security_limits": {
    "max_risk_level": "HIGH",
    "requires_approval": ["HIGH", "CRITICAL"],
    "blocked_actions": ["rm -rf /", "format disk"]
  },
  "recommended_roles": ["aika-dev", "aika-test", "aika-browser"],
  "aika_version": "1.0.4"
}
```

---

*文檔維護：Claude | AiKa-Test 是邏輯角色，底層引擎可插拔*
