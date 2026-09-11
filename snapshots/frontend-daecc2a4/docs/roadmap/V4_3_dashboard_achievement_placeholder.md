# GoaaDashboard.jsx 成果資產 Placeholder 規劃 V1.0

**版本**: V1.0
**最後更新**: 2026-05-16
**狀態**: ⚠️ **規劃文件, 不改 code** (規範 SUPREME 項 10)
**配套**: 戰略憲法主檔 第 9 章 + V4_2_PLUS_SKILL_MARKETPLACE.md

---

## 📌 文件角色標籤 (規範 SUPREME 治理)

```text
本文角色: 前端 Add-only 規劃 (Placeholder only)
本文類型: UI Placeholder Plan
是否允許直接執行: 否 (僅規劃, Tao 批准才動 code)
是否允許修改 Production: 否 (規範 #11 + #14 R2)
是否需要 Tao 拍板: 是 (絕對必要, 不可自主動)
最高參考來源: GOAA_BUSINESS_MODEL_V1.md 第 10 章 (成果市場) + V4_2_PLUS_SKILL_MARKETPLACE.md
```

---

## 🚨 一、執行前置條件 (SUPREME 項 10 強制)

> **本步需要 Tao 批准後做。若沒有批准, 只寫規劃, 不改 code。**

### 不批准 = 不動

- ❌ AI 不可自主動 `components/GoaaDashboard.jsx` (規範 #14 R2 + #35)
- ❌ AI 不可自主升級黃金版
- ❌ 凌晨不動 (規範 #20)

### 批准 = 走流程

師兄明確說「**批准動 GoaaDashboard, 加成果資產 placeholder**」才開工:
1. AiKa-1 規範 #13 接續校驗
2. Patch v6 設計 (preview branch, 規範 #26)
3. 師兄真實驗證 preview URL
4. Merge main + production deploy
5. **不**自動升級黃金版 (等師兄明確說 R2 觸發詞)

---

## 🔍 二、Mock fallback 檢查 (SUPREME 項 10.1)

### 2.1 目前需要檢查的 Mock 殘留

```bash
# 在當前 V4.0.5.4-UI 黃金版內 grep:
grep -n "MOCK_\|fallback.*mock\|mock.*revenue\|mock.*profit" \
    components/GoaaDashboard.jsx
```

如果存在以下任何一個, 視為違反 **Runtime Truth** (SUPREME 鐵律 1.4):
- `MOCK_WORKERS`
- `MOCK_METRICS`
- `MOCK_HEALTH`
- fallback mock revenue / cost / profit

### 2.2 正確的 State Init 模式

```javascript
// ✅ 正確: 真實零狀態
const [workers, setWorkers] = useState([]);
const [metrics, setMetrics] = useState({
  total_revenue_today: 0,
  total_cost_today: 0,
  total_profit_today: 0,
});
const [isInitialLoading, setIsInitialLoading] = useState(true);
const [apiStatus, setApiStatus] = useState("connecting");

// ❌ 錯誤: mock 假裝有數據
const [workers, setWorkers] = useState([
  { id: "aika-1", name: "AiKa-1", revenue: 99.99 },  // 假
  ...
]);
```

### 2.3 API 未連接時 UI 顯示

```jsx
{apiStatus === "connecting" && (
  <div>等待 Runtime 數據...</div>
)}
{apiStatus === "error" && (
  <div>Runtime 連線失敗, 請檢查 api.goaa.ai 狀態</div>
)}
{apiStatus === "ok" && workers.length === 0 && (
  <div>暫無 Worker 註冊</div>
)}
```

**不得**:
- 顯示假收益 / 假成本 / 假利潤
- 顯示假 Worker 狀態
- 用 mock data 偽裝 production

---

## 📊 三、成果資產一級入口 (SUPREME 項 10.2)

### 3.1 菜單項插入 (Add-only)

如果 Tao 批准, 在現有左側菜單**新增** (不刪既有):

```javascript
// 當前順序 (V4.0.5.4-UI 黃金版):
const menu = [
  { id: "dispatch", label: "AI 調度" },
  { id: "taskpool", label: "任務池" },
  { id: "workers", label: "節點監控" },
  { id: "finance", label: "損益審計" },
  { id: "logs", label: "日誌歷史" },
  { id: "settings", label: "系統設置" },
];

// 加入後 (新增 "成果資產"):
const menu = [
  { id: "dispatch", label: "AI 調度" },
  { id: "taskpool", label: "任務池" },
  { id: "workers", label: "節點監控" },
  { id: "finance", label: "損益審計" },
  { id: "achievements", label: "成果資產" },  // ← 新增
  { id: "logs", label: "日誌歷史" },
  { id: "settings", label: "系統設置" },
];
```

### 3.2 規範對齊
- ✅ 規範 #11 只增不毀 (現有 6 個項全保留)
- ✅ 規範 SUPREME 項 1.1 UI Freeze (Cyber-Noir 黑魂 + 德牧 Logo 不動)
- ✅ 規範 SUPREME 項 1.2 Add-only (不刪既有)

---

## 🎨 四、Placeholder Only (SUPREME 項 10.3)

### 4.1 重要警告

> ⚠️ **初版只能顯示 Placeholder**
> **不得顯示假 Skill、假 MRR、假訂閱、假收益**

### 4.2 Placeholder UI 設計

```jsx
{tab === "achievements" && (
  <div style={{
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    color: "#94a3b8",
    padding: 40,
  }}>
    <div style={{
      fontSize: 24,
      fontWeight: 600,
      color: "#60a5fa",
      marginBottom: 16,
    }}>
      💎 成果資產中心
    </div>
    
    <div style={{
      fontSize: 14,
      lineHeight: 1.8,
      maxWidth: 600,
      textAlign: "center",
      marginBottom: 24,
    }}>
      Worker V5.0 生產線預留模組。
      <br/><br/>
      目前尚未接入真實 Skill Marketplace 數據。
      <br/>
      完成 V4.1-Worker / V4.2 調度層後, 這裡將顯示:
    </div>
    
    <ul style={{
      fontSize: 13,
      lineHeight: 1.8,
      color: "#cbd5e1",
      listStyle: "none",
      padding: 0,
    }}>
      <li>• 已開發 Skill</li>
      <li>• 已發布 Skill</li>
      <li>• MRR (月經常性收入)</li>
      <li>• Worker 分潤</li>
      <li>• 訂閱人數</li>
      <li>• 用戶反饋</li>
      <li>• 版本狀態</li>
    </ul>
    
    <div style={{
      marginTop: 32,
      fontSize: 12,
      color: "#64748b",
    }}>
      Phase 5 規劃中 · 預計 2026 Q3 上線
    </div>
  </div>
)}
```

### 4.3 不得做的事

- ❌ 顯示假 Skill 列表 (`{name: "家庭信件管理", subscribers: 1000}`)
- ❌ 顯示假 MRR (`$28,450`)
- ❌ 顯示假評分 / 假反饋
- ❌ 用 mock data 偽裝 Phase 5 完成

---

## 🛡️ 五、規範對齊 (SUPREME 治理)

| 規範 | 對應 |
|---|---|
| #11 (只增不毀) | 6 → 7 個菜單項 (新增 achievements, 不刪) |
| #14 R2 | Tao 明確批准才動 jsx |
| #15 (24h Cooldown) | Production 後 24h 觀察 |
| #20 (Tao 健康) | 凌晨不動戰略 UI |
| #24 (不憑想像) | 動前 view + grep MOCK_ |
| #26 (preview branch) | `preview/v4-achievements-placeholder` |
| SUPREME 1.1 | UI Freeze, Cyber-Noir 風格不動 |
| SUPREME 1.2 | Add-only |
| SUPREME 1.4 | Runtime Truth (無 mock) |

---

## 📋 六、執行 checklist (Tao 批准後)

### Step 1: 接續校驗 (規範 #13)
- [ ] AiKa-1 跑 `git log --oneline -5 main` 確認 main HEAD
- [ ] 確認當前 jsx 行數 + MD5 跟黃金版一致
- [ ] grep 沒有 MOCK_ 殘留 (確認無需修)

### Step 2: 設計 Patch (規範 SUPREME 項 10)
- [ ] 加菜單項 `{ id: "achievements", label: "成果資產" }`
- [ ] 加 placeholder render block (上方範本)
- [ ] 確認無 mock data

### Step 3: 部署 Preview (規範 #26)
- [ ] preview branch `preview/v4-achievements-placeholder`
- [ ] Vercel auto-build preview
- [ ] 師兄真實打開 preview URL 驗證

### Step 4: Production (規範 #24 + #31)
- [ ] 師兄拍板 → AiKa-1 merge main
- [ ] AiKa-1 透傳真實 git log 確認 main HEAD
- [ ] Vercel auto-deploy production
- [ ] 師兄真實打開 portal.goaa.ai 驗證

### Step 5: 黃金版升級 (規範 #14 R2)
- [ ] **等師兄明確說「升級成黃金版本」才升**
- [ ] 不自主, 不假設

---

## 💡 七、給 future Claude / AiKa 的真心話

如果 Tao 批准動 GoaaDashboard:

1. **看完本文** — 不要憑想像加菜單
2. **規範 #13 嚴守** — main HEAD MD5 不對就停手
3. **Placeholder only** — 絕對不能加假數據
4. **規範 #11 嚴守** — 6 個既有菜單一個都不能少
5. **規範 #14 R2 嚴守** — 等師兄明確說才升黃金版
6. **規範 SUPREME 1.1 嚴守** — UI 風格 / Logo / 字體不動

---

**GoaaDashboard Placeholder 規劃 V1.0**

*整合人: Claude*
*時間: 2026-05-16 16:30 PT*
*狀態: 規劃文件, 不改 code, 等 Tao 批准*
