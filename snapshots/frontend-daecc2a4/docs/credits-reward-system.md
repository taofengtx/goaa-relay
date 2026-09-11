# GOAA.AI 算力經濟與 Credits 報酬系統
**版本：** v1.1.0  
**日期：** 2026-05-07  
**變更：** 引入 AiKa-Test 軟性審計 + QualityScore 四維評分 + 防作弊機制

---

## 一、核心原則

- **只有本地盒子獲得報酬**（AiKa 雲盒 VPS 不計入）
- **暫不開放提現**（Credits 只能在平台內使用）
- **Credits 可抵扣月費**（$39.9/月 Agent 訂閱）
- **雙重驗收**：GitHub Actions 硬性檢查 + AiKa-Test 軟性審計，兩者均通過才結算
- **防作弊壁壘**：AI 評分 AI，QualityScore < 0.6 一律不予發放報酬

---

## 二、Credits 計算公式

$$Credits = Base \times Difficulty \times QualityScore \times Stability$$

> `QualityScore` 由 AiKa-Test（可插拔審計引擎）對代碼進行四維軟性審計後動態計算（0.0-1.0）。

---

## 三、QualityScore 四維評分體系

### 3.1 評分維度

| 維度 | 權重 | 說明 |
|------|------|------|
| 規範性 Adherence | 30% | 代碼是否嚴格遵守 `architecture.md` 定義的架構？ |
| 簡潔性 Simplicity | 25% | 是否有冗餘代碼、AI 幻覺生成的廢話、無用函數？ |
| 安全性 Security | 30% | 是否包含硬編碼 Key、惡意腳本、後門、明文密碼？ |
| 性能影響 Performance | 15% | 是否引入不必要的同步阻塞、高耗能循環、內存洩漏？ |

### 3.2 合成公式

```
QualityScore = (Adherence × 0.30) + (Simplicity × 0.25)
             + (Security × 0.30)  + (Performance × 0.15)
```

### 3.3 計算範例

```
Adherence   = 0.9  →  0.270
Simplicity  = 0.8  →  0.200
Security    = 1.0  →  0.300
Performance = 0.7  →  0.105

QualityScore = 0.875
Credits = 50 × 1.5 × 0.875 × 1.2 = 79 Credits  ✅
```

---

## 四、結算規則

| QualityScore | 結果 | Credits |
|-------------|------|---------|
| ≥ 0.8 | 優秀 | 正常 × 1.2（加成）|
| 0.6 ~ 0.8 | 良好 | 正常 × 1.0 |
| < 0.6 | 需重構 | 0（退回重做）|
| Security = 0 | 安全警報 | 0 + 節點降級 + 通知 tao@goaa.ai |

---

## 五、Base / Difficulty / Stability 定義

**Base（基礎分）**

| 任務類型 | Base |
|---------|------|
| AI 對話推理 | 10 |
| 文件處理/OCR | 20 |
| 瀏覽器自動化 | 30 |
| 視頻生成/剪輯 | 50 |
| 代碼執行/測試 | 25 |
| 報稅/法律文書 | 40 |
| 數據抓取 | 15 |

**Difficulty 係數**

| 難度 | 係數 |
|------|------|
| 簡單 | 1.0 |
| 中等 | 1.5 |
| 困難 | 2.0 |
| 專家 | 3.0 |

**Stability 係數**

| 連續在線天數 | 係數 |
|------------|------|
| 1-7 天 | 1.0 |
| 8-30 天 | 1.1 |
| 31-90 天 | 1.2 |
| 90+ 天 | 1.3 |

---

## 六、AiKa-Test 審計 API

```
POST /api/v1/tasks/{task_id}/audit

請求：
{
  "task_id": "GOAA-20260507-001",
  "pr_url": "https://github.com/taofengtx/goaa-ai-frontend/pull/42",
  "diff_content": "...",
  "architecture_ref": "docs/architecture.md",
  "engine_override": null    // null=用配置文件, 或指定 "claude"/"gpt-5-codex"
}

返回：
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
  "verdict": "approved",        // approved / needs_refactor / security_alert
  "issues": [
    {
      "dimension": "performance",
      "severity": "medium",
      "line": 142,
      "message": "同步讀取文件，建議改為 async"
    }
  ],
  "credits_eligible": true,
  "credits_preview": 79
}
```

---

## 七、Credits 使用方式（暫不提現）

| 用途 | Credits |
|------|---------|
| 抵扣 Agent 月費 | 3,990/月（= $39.9）|
| 購買技能 | 按技能定價 |
| AI 對話 | 5/次 |
| 視頻生成 | 165/條 |
| 文件存儲 | 10/GB/月 |
| 自動發布 | 30/次 |

**月費抵扣估算：**
```
輕度使用（2hr/天）  ≈ 1,500-2,000 Credits/月  約抵 50%
中度使用（6hr/天）  ≈ 4,000-5,000 Credits/月  可完全抵扣
重度使用（12hr/天） ≈ 8,000-10,000 Credits/月 有盈餘
```

---

## 八、未來規劃（提現功能）

**Phase 2（3個月後）：**
- 積累超過 50,000 Credits 可申請提現
- 提現比率：100 Credits = $0.8（保留 20% 平台費）
- 最低提現：10,000 Credits（$80）
- 支付：Zelle / PayPal / ACH

---

*文檔維護：Claude | 防作弊核心：AI 評分 AI，QS < 0.6 不發報酬*
