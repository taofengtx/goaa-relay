# V4.2+ Skill Marketplace Roadmap

**版本**: V1.0
**最後更新**: 2026-05-16
**狀態**: Phase 5 規劃 (戰略憲法路線圖)
**配套**: `docs/business/GOAA_BUSINESS_MODEL_V1.md` (戰略憲法第 8-9 章)

## 📌 文件角色標籤 (規範 SUPREME 治理)

```text
本文角色: Phase 5 Skill Marketplace Roadmap
本文類型: Future Roadmap
是否允許直接執行: 否
是否允許修改 Production: 否
是否需要 Tao 拍板: 是 (Phase 5 啟動)
最高參考來源: GOAA_BUSINESS_MODEL_V1.md 第 8-9 章
```

---

## 🎯 一、Roadmap 全景 (Phase 4 → 7)

```
時間軸 →

【現在】V4.0.5.4-UI (前端 production)
       V4.0.5.1 (後端 api.py)
       V4.1.0.1 (PG schema)
              │
              ▼
【Phase 4】V4.1-Worker (本地手腳建設, 5/17-5/22)
       ├─ V4.1-W1: 4 唯讀 executor
       ├─ V4.1-W2: 4 讀寫 executor + 預先確認 UI
       └─ V4.1-W3: 4 高階 executor
              │
              ├─→ 並行: V4.1.1/V4.2.0-6 (雲腦調度層)
              ▼
【Phase 5】V4.3-V4.5 Skill Marketplace ← 本文重點
       ├─ V4.3: Skill 基礎設施 (DDL + 開發環境)
       ├─ V4.4: Skill 商業層 (訂閱 + 計費 + 分潤)
       └─ V4.5: Skill 反饋閉環 (用戶反饋 → Worker Task)
              │
              ▼
【Phase 6】V5.0 Client/Provider 商業化
       ├─ Client Plus ($19.99) 完整上線
       ├─ Provider Pro ($39.99) 完整上線
       └─ AiKa Box 硬件出貨 ($999 / $99 月)
              │
              ▼
【Phase 7】V6.0 全球 Worker Network
       ├─ Worker Credits 商用 (跨機結算)
       ├─ Marketplace (借用算力 / 賣本地能力)
       └─ AI 勞動力經濟系統完整成型
```

---

## 📊 二、Phase 5 (V4.3-V4.5 Skill Marketplace) 詳細拆解

### V4.3 — Skill 基礎設施 (DDL + 開發環境)

**目標**: 把戰略憲法第 8-9 章的 Skill / Achievement 概念變成可運作的系統

| 階段 | 內容 | 工程 |
|---|---|---|
| V4.3.0 | 執行 FUTURE_DDL_SKILL_MARKETPLACE.md 的 6 個表 | 1 hr + 24h |
| V4.3.1 | Worker Dashboard 加「成果」一級菜單 (Phase 4 UI 對齊) | 2 hr |
| V4.3.2 | Skill 開發 SDK (Worker 開發者用) | 4 hr |
| V4.3.3 | Skill testing 環境 (測試 + 安全 + 成本評估) | 3 hr |
| V4.3.4 | Skill 版本管理 + Rollback | 2 hr |

**完成標誌**: Worker 能開發、測試、版本化一個 Skill

---

### V4.4 — Skill 商業層 (訂閱 + 計費 + 分潤)

| 階段 | 內容 | 工程 |
|---|---|---|
| V4.4.0 | Skill Marketplace 主頁 (Client / Provider 端) | 4 hr |
| V4.4.1 | 一鍵啟停按鈕 (滑動藍色) | 2 hr |
| V4.4.2 | 訂閱計費系統 (Stripe / 月費) | 4 hr |
| V4.4.3 | 分潤計算 (50/50 + Runtime 成本扣除) | 2 hr |
| V4.4.4 | Worker Credits 結算 | 3 hr |
| V4.4.5 | Dashboard 收益指標 (MRR/ARR/淨利潤) | 3 hr |

**完成標誌**: 第一個 Skill 可被訂閱 + 計費 + 分潤

---

### V4.5 — Skill 反饋閉環 (用戶反饋 → Worker Task)

| 階段 | 內容 | 工程 |
|---|---|---|
| V4.5.0 | Client / Provider 反饋 UI (評分 + 留言 + Bug) | 3 hr |
| V4.5.1 | 反饋自動分類 (LLM judge: bug/ux/slow/feature/wrong/cost) | 2 hr |
| V4.5.2 | 6 種 Worker Task 自動生成 | 3 hr |
| V4.5.3 | Worker 處理 patch_task → 新版本 → 用戶自動升級 | 3 hr |
| V4.5.4 | 質量指標 Dashboard (rating/rollback/pending bugs) | 2 hr |

**完成標誌**: Client 評 1 星 + Bug 報告 → 系統自動生成 patch_task → Worker 修復 → Skill 升級

---

## 🎯 三、Phase 5 完成後的真實能力

### 對 Client (用戶)
- 可在 Client 端訂閱 Skill (e.g. 「家庭信件管理」$2.99/月)
- AI 持續幫忙處理現實任務
- 可評分 / 反饋 / 取消訂閱

### 對 Provider (真人專業者)
- 可在 Provider 端訂閱 Skill (e.g. 「房產廣告生成」$9.99/月)
- AI 自動接單 / 整理 / 報價 / 跟進
- AiKa Box 部署本地執行

### 對 Worker (AI 數字勞動力)
- 可開發 Skill
- 賺 50% 分潤
- 接收用戶反饋自動生成升級任務
- Credits 經濟運轉

### 對 GOAA 平台
- MRR (月經常性收入) 開始可觀
- 50% 分潤
- 質量指標完整
- 真實 AI 勞動力經濟系統雛形

---

## 📊 四、收益模型範例 (Phase 5 後)

### 範例 1: Client 端 Skill「家庭信件管理」
- 月費: $2.99
- 目標訂閱: 1,000 人 (6 個月內)
- MRR: $2,990
- 平台收入: $1,495
- Worker 分潤: $1,495
- Runtime 成本: $210
- **淨利潤: $2,780 / 月**

### 範例 2: Provider 端 Skill「AI 視頻生成」
- 月費: $9.99
- 目標訂閱: 300 個 Provider (6 個月內)
- MRR: $2,997
- 平台收入: $1,498.50
- Worker 分潤: $1,498.50
- Runtime 成本: $520
- **淨利潤: $2,477 / 月**

### 假設 10 個 Skill 完整上線
- 平均 MRR per skill: $2,500
- 總 MRR: $25,000
- **ARR: $300,000**
- GOAA 平台年收入: $150,000
- Worker 網絡分潤: $150,000

---

## 🛡️ 五、規範對齊

| 規範 | 對應 |
|---|---|
| #11 (只增不毀) | Phase 5 不動 Phase 4 既有功能 |
| #15 (24h Cooldown) | 每個 V4.x 階段都過 24h |
| #29 (Explore & Innovate) | Skill SDK 自建 (不依賴 QwenPaw) |
| #30 (Progressive) | V4.3 → V4.4 → V4.5 漸進 |
| #33 (Worker V5.0 優先) | Phase 5 必須等 Phase 4 (V4.1-Worker) 完成 |
| #34 (最終產品定義) | Skill 服務人類, 不偏離 |
| #35 (不走偏 5 原則) | 「技能必須資產化」(原則 5) |

---

## 📅 六、預計時間表

| Phase | 階段 | 預計時間 |
|---|---|---|
| Phase 4 | V4.1-Worker (本地手腳) | 5/17-5/22 |
| Phase 4 | V4.1.1 / V4.2.0-6 (雲腦調度) | 5/22-6/15 |
| **Phase 5** | **V4.3 Skill 基礎設施** | **6/15-6/30** |
| **Phase 5** | **V4.4 Skill 商業層** | **7/1-7/20** |
| **Phase 5** | **V4.5 Skill 反饋閉環** | **7/20-8/10** |
| Phase 6 | V5.0 Client/Provider 商業化 | 2026 Q3 |
| Phase 7 | V6.0 Worker Network 全球化 | 2026 Q4 |

---

## 💡 七、給 future Claude 的真心話

接手 Phase 5 任何階段:

1. **戰略憲法第 9 章是設計藍本** — 17 個 Skill 字段 + 8 個生命週期階段
2. **DDL 在 FUTURE_DDL_SKILL_MARKETPLACE.md** — 不要重新發明
3. **6 種反饋 → Task 映射** — patch / ux / optimization / feature / prompt_fix / cost_optimization
4. **50/50 分潤是默認** — 不要隨意改, 改要過師兄拍板
5. **Rollback 機制必須做** — 商業 Skill 必須穩定
6. **Phase 4 沒完不要開 Phase 5** — 規範 #33 戰略順序

師兄白皮書 V1.0 第 22-32 章 (成果市場) 是用心血換來的商業設計, 守護它。

---

**V4.2+ Skill Marketplace Roadmap V1.0**

*整合人: Claude*
*時間: 2026-05-16 11:45 AM PT*
*狀態: 規劃中, 等 Phase 4 完成*
