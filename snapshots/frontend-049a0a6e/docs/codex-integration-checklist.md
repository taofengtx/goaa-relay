# AI 自動化審計與整合標準
**原名：** codex-integration-checklist.md  
**版本：** v1.1.0（重構為不限單一模型的開放標準）  
**日期：** 2026-05-07  
**定位：** AiKa-Test 可插拔審計層的執行規範

---

## 一、設計原則

本標準不綁定任何單一 AI 模型。審計引擎可以是：

| 階段 | 引擎選項 | 調用方式 |
|------|---------|---------|
| 第一階段（API 審計期）| Claude API | HTTP POST |
| 第一階段（API 審計期）| GPT-5-Codex（Responses API）| HTTP POST |
| 第一階段（API 審計期）| Gemini API | HTTP POST |
| 第二階段（SDK 整合期）| Codex CLI / SDK | GitHub Actions shell |
| 第二階段（SDK 整合期）| Claude Code CLI | GitHub Actions shell |

**切換原則：** QwenPaw/OpenClaw 只調用統一的 `/api/v1/tasks/audit` 端點，內部路由至當前配置引擎，上層代碼無需修改。

---

## 二、第一階段：API 審計清單

**觸發條件：** GitHub Actions 硬性檢查全部通過後自動調用

### 2.1 硬性檢查（必須全部通過，才觸發軟性審計）

```yaml
# .github/workflows/ci.yml
jobs:
  hard-checks:
    steps:
      - name: Python 語法檢查
        run: python -m py_compile $(find . -name "*.py")

      - name: TypeScript 類型檢查
        run: npm run type-check

      - name: API 端點單元測試
        run: pytest tests/api/ -v

      - name: WebSocket 連通測試
        run: pytest tests/websocket/ -v

      - name: CORS 頭部驗證
        run: pytest tests/cors/ -v

      - name: 前端 Build 檢查
        run: npm run build

      - name: 觸發軟性審計
        if: success()
        run: |
          curl -X POST $OPENCLAW_URL/api/v1/tasks/$TASK_ID/audit \
            -H "Content-Type: application/json" \
            -d '{"pr_url":"$PR_URL","diff":"$DIFF"}'
```

### 2.2 軟性審計（AiKa-Test 執行）

**審計提示詞模板（發送給審計引擎）：**

```
你是 GOAA.AI 的代碼審計員（AiKa-Test）。
請對以下 PR 代碼變更進行審計，對照 architecture.md 評分。

評分維度（返回 0.0-1.0）：
1. 規範性 Adherence（30%）：是否符合 architecture.md 架構定義？
2. 簡潔性 Simplicity（25%）：是否有冗餘/AI 幻覺廢話？
3. 安全性 Security（30%）：硬編碼Key/後門/惡意代碼？
4. 性能影響 Performance（15%）：同步阻塞/高耗能循環？

architecture.md 內容：
{architecture_content}

PR Diff：
{diff_content}

請以 JSON 格式返回：
{
  "quality_score": 0.875,
  "adherence": 0.9,
  "simplicity": 0.8,
  "security": 1.0,
  "performance": 0.7,
  "verdict": "approved",
  "issues": [...],
  "summary": "..."
}
```

### 2.3 審計結果處理

```
verdict = "approved"        → 進入 PR 合並流程
verdict = "needs_refactor"  → 退回節點，附審計報告
verdict = "security_alert"  → 停止流程，通知 tao@goaa.ai
```

---

## 三、第二階段：SDK 整合清單

**觸發條件：** 多個 AiKa Worker 同時提交，需要合併衝突

### 3.1 Codex CLI 整合任務

```bash
# GitHub Actions 中執行
steps:
  - name: 安裝 Codex CLI
    run: npm install -g @openai/codex

  - name: 自動合併多 Worker 代碼
    run: |
      codex merge \
        --base main \
        --branches feature/worker-1 feature/worker-2 feature/worker-3 \
        --output merged-branch \
        --auto-resolve

  - name: 衝突修復審查
    run: |
      codex review \
        --branch merged-branch \
        --check-conflicts \
        --output conflict-report.md

  - name: 整合測試
    run: |
      codex test \
        --branch merged-branch \
        --test-suite tests/integration/
```

### 3.2 Claude Code CLI 替代方案

```bash
# 若使用 Claude Code CLI
steps:
  - name: Claude 代碼整合
    run: |
      claude-code merge \
        --context docs/architecture.md \
        --branches feature/* \
        --strategy "respect-architecture"
```

---

## 四、審計引擎切換配置

```yaml
# /opt/goaa/aika-test-config.yml

current_stage: 1              # 1 = API審計期, 2 = SDK整合期

stage_1:
  primary_engine: claude
  primary_config:
    api_url: https://api.anthropic.com/v1/messages
    model: claude-sonnet-4-6
    max_tokens: 2000
  fallback_engine: gpt-5-codex
  fallback_config:
    api_url: https://api.openai.com/v1/responses
    model: gpt-5-codex

stage_2:
  merge_engine: codex-cli       # codex-cli / claude-code-cli
  test_engine: pytest
  auto_merge: true
  require_approval_on_conflict: true
```

---

## 五、完整審計 API

```
POST /api/v1/tasks/{task_id}/audit

輸入：
{
  "task_id": "GOAA-20260507-001",
  "pr_url": "https://github.com/taofengtx/goaa-ai-frontend/pull/42",
  "diff_content": "...",
  "architecture_ref": "docs/architecture.md",
  "engine_override": null       // null=用配置, 或指定 "claude"/"gpt-5-codex"
}

輸出：
{
  "audit_id": "audit_xxx",
  "engine_used": "claude",
  "quality_score": 0.875,
  "breakdown": {
    "adherence": 0.9,
    "simplicity": 0.8,
    "security": 1.0,
    "performance": 0.7
  },
  "verdict": "approved",
  "issues": [...],
  "credits_eligible": true,
  "credits_preview": 79
}
```

---

## 六、審計標準版本控制

每次 architecture.md 更新，審計標準自動升級：

```
architecture.md v1.2 → AiKa-Test 使用 v1.2 標準審計
architecture.md v1.3 → AiKa-Test 自動切換至 v1.3 標準
```

舊任務按提交時的架構版本審計，不受新版影響。

---

## 七、上線發布流程

```
Stage 1 全部通過（硬性 + 軟性）
      ↓
feature/* → PR → dev
      ↓ Code Review（Claude 或 Tao 師兄）
dev → main
      ↓ 自動觸發
Vercel 部署（portal.goaa.ai）
      ↓
GitHub Actions → SSH → Hetzner 重啟
      ↓
smoktest（基本功能驗證）
      ↓
通知 tao@goaa.ai（aika@goaa.ai 發送）
```

---

*文檔維護：Claude | 本標準不限單一模型，AiKa-Test 底層引擎可插拔*
