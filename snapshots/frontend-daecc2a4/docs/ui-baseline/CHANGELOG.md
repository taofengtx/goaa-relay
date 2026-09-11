
---

## V5.1.0-INFRA (黃金版 R3 升級) - 2026-05-30 23:33 PT

**Commit**: `0e8841b`
**Trigger**: 師兄 5/29 21:27 戰略指示（對齊規範 #14 R3：基礎設施黃金版）
**新黃金版文件**: `docs/ui-baseline/api_py.golden.py` + `goaa-router.service.golden`
**UI 黃金版不變**: `GoaaDashboard.golden.jsx` 維持 R2（774 行 / MD5 9b4fb15d）

### 新增黃金版基準

**api_py.golden.py** — DO production router（V5.0+V5.1.B 真實狀態）
- **行數**: 1082 | **MD5**: `1254d011918b1694e5b8d1e8694faeed` | **位元組**: 52,442
- **起點**: Phase 4.1 DO snapshot（830 行, MD5 567B3073, commit aa65f65, 5/21）
- **差異**: +252 行（V5.1.B dispatch_task LLM tool spec + register endpoint + tailscale_ip）
- **關鍵增量**:
  + 3 個新 endpoint: `/health`、`/workers/register`、`/workers/register/{worker_id}`
  + dispatch_task function spec 硬編碼到 `/chat` LLM tools（V5.1.B）
  + tool_calls 處理新增 `elif dispatch_task` 分支
  + WORKER_REGISTRY 新增 lan_ip + tailscale_ip 欄位
  + /workers/status 回傳 tailscale_ip
  + `select_with_instance` / `update_with_instance` helper 函數

**goaa-router.service.golden** — systemd 單元文件（規範 #23 落地）
- **行數**: 99 | **MD5**: `2f9475fb40ed7ba9ad95f8bbaf848c35` | **位元組**: 2,908
- **起點**: 無（5/29 前 router 以 nohup 執行，無 systemd unit）
- **使用 EnvironmentFile=/etc/goaa/secrets.env**（DEEPSEEK_KEY 正確載入）
- 5/14 立規 #23 最終解：DEEPSEEK_API_KEY 首次真實進入 process environ

### 規範對齊
- **#11（只增不毀）**: 所有舊 api.py 函數保留，僅增量新增
- **#14 R3（基礎設施黃金版）**: 首次將 production infrastructure 納入黃金版範圍
- **#14 R5（Copy-Item 覆蓋）**: 本文件為 snapshot，部署用 `do-deploy-model-router-api.sh v2` 比對
- **#42（三端鐵律）**: 三端 HEAD 一致（GitHub 0e8841b = DO 0e8841b = AiKa-1 0e8841b）
- **#45 v5（師兄拍板）**: CHANGELOG 草案待師兄確認後 commit

### 真實來源
- **獲取方式**: DO production → scp → AiKa-2 → base64 pipe → AiKa-1
- **MD5 一致性驗證**: AiKa-1 == AiKa-2 == DO production（三端一致）

---

## V4.0.5.4-UI (黃金版升級) - 2026-05-16 11:00 PT

**Commit**: `f1b0168` (merge V4.0.5.3-UI + V4.0.5.4-UI)
**Lines**: 774
**MD5**: `9b4fb15d78bc364ee7d0f7566d826f61`
**Trigger**: Tao 師兄明確說「升級成黃金版本」 (規範 #14 R2)

### 改動摘要

**V4.0.5.3-UI** (commit be16b15, 一次到位):
- 對話 GOAA card 加 flex:1 + display:flex + flexDirection:column + minHeight:0
- chatHistory area maxHeight:260 → flex:1 + minHeight:0
- 刪除 dispHistory render 整段 (L570-628, 59 行)
- L378 外層 overflow:auto **未動** (其他 tab 保護)

**V4.0.5.4-UI** (commit 3b3697a, autoscroll fix):
- 加新 useRef chatHistoryRef
- useEffect 依賴 [dispHistory] → [chatHistory]
- L495 chatHistory area 加 ref={chatHistoryRef}

### 真實驗證 (Tao 親手, 規範 #24 + #31)

- ✅ 1 個 scrollbar (chatHistory area 內單一)
- ✅ 對話 GOAA card 撐滿空間 (不再懸浮)
- ✅ dispHistory render 消失
- ✅ 對話 + 🔧 ON 工具調用正常
- ✅ 上方 widgets 全在
- ✅ 其他 5 個 tab 滾動正常
- ✅ 對話回應後自動滾到底

### 規範對齊

- #11 (只增不毀): 全部函數/state/tab 保留, chatRef 也保留沒移除
- #14 R2 (Tao 觸發): 師兄明確說「升級成黃金版本」
- #14 R3 (必寫 CHANGELOG): 本條目
- #14 R5 (Copy-Item 覆蓋): 已用 Copy-Item, 不直接編輯
- #15 (24h Cooldown): production 從本次升黃金版時間開始計
- #24 (真實源碼): 基於 AiKa-1 真實 STDOUT 確認 main HEAD MD5
- #29 (廢棄 V4.0.5.2-UI): 不完整方案不勉強保留

### 規範 #31 違反 ledger 教訓

- 昨晚 V4.0.5.2-UI「merge 完成」是 AiKa 自主結論 (錯)
- 這次每個 merge + push 後都看真實 git log origin/main 確認
- 師兄真實驗證 production 才升黃金版

## 2026-05-15 - V4.0 portal 真實上線 🎊

- **HEAD**: 4bf8505 (含 V4.0-2B merge from v4-tools-ui)
- **Lines**: 846
- **MD5**: `3f05c4b241af9ed72a0c74e6b295a36c`
- **改動摘要**:
  - V4.0-2B 5 patches: enableTools state / body enable_tools / response tool_calls / dispHistory isTool render / 🔧 Tools toggle button
  - 跨裝置驗證 3 設備 (iPhone / Galaxy Z Fold / 桌機)
  - 後端工具調用閉環 (DeepSeek function calling + task_status)
- **規範符合**:
  - #11 Baseline Freeze: 5 個其他菜單完整保留
  - #14 黃金版升級: 在師兄收工確認後
  - #24 規範: V4.0-2B-v2 用真實字符 dry-run, 5/5 patches 成功
  - #26 preview branch: v4-tools-ui → main 安全 merge


# UI Golden Baseline Changelog

## 2026-05-15 — V3.0 ChatOps 上線

**Commit**: 38e5764  
**Lines**: 814 (原 649 → +144)  
**MD5**: `2cec3e47fae0806aae0084c0684badb2`

### 改動摘要
- ✅ Phase 4 V3.0: 加 ChatOps 對話卡片 (跟 GOAA 對話)
- ✅ 修 1B.3 兩個 bug:
  - `now()` 函數提到 component scope
  - chat card 移出 `dispHistory.length===0` 條件塊 (永遠顯示)
- ✅ 新增 4 個 chat state: chatHistory / chatMsg / chatSending / chatSessionId
- ✅ localStorage 持久化 session_id
- ✅ sendChatMessage 用原生 fetch + 60 秒 timeout (規範 #28 立規)
- ✅ resetChatSession (新對話按鈕)

### 規範 #11 「只增不毀」驗證
- 保留: 左側 menu 6 項 / dispatchTask / dispHistory 群組會話 / 節點實時回報面板
- 新增: 對話 GOAA 卡片 + 4 chat state + sendChatMessage + resetChatSession
- 兩個對話框並存 (上對話 / 下任務派發), 不互相干擾

### 立規範
- 規範 #27: Integration First「不創造新的, 只是接通已有的, 整合最好的」
- 規範 #28: Silent Failure 反模式 (catch{return null} 禁止)

---


所有黃金版升級的歷史紀錄。最新的在最上面。

格式：
```
## [yyyy-mm-dd] commit <hash> — 簡述
- Lines: NNN  MD5: xxxxxxxx (位元組數)
- 起點: 上一個 commit hash
- 改動:
  + 新增 ...
  ~ 修正 ...
  − 移除 ... (應極少使用)
- 驗收: 師兄確認 / 自動化驗證項
```

---

## [2026-05-12] commit `de6f425` — 04f17ba 合併版（首個固化黃金版）

- **Lines**: 649  **MD5**: `83fd0dff181a49e2d70c4e7dc1e44a01`
- **起點**: c0f0d24（錯誤的 Phase 4 ChatOps 版本，已 revert 邏輯上覆蓋）
- **真實基底**: 04f17ba（炸窗前工作版本）
- **改動摘要**:
  + 新增 fmtHb 心跳格式化 helper（紅/黃/綠分級）
  + 新增 SPEAKERS_BG + speakerBg/speakerBorder 訊息氣泡配色 helpers
  + 節點卡片底部新增 ♥ 心跳標籤（規範 #11 第 12 欄）
  + 訊息氣泡背景 + 左邊框美化（從樸素 border-bottom 升級為氣泡式）
  ~ 菜單命名對齊規範 #11：任務中心→任務池 / 日誌流→日誌歷史 / 設置→系統設置
- **保留**:
  - AI 調度 4 控制框 + 群組會話 + 訊息流 + 右側可隱藏 QwenPaw 面板
  - 節點監控 translateY 懸停 + ACTIVE NODES 統計 + 新增節點按鈕
  - workers state inline fallback（`workers.length>0?workers:[3 節點]`）
  - dispatchTask 真實後端派發邏輯（非 mock）
  - 13 個 state + 1 ref 完整保留
- **驗收**:
  - ✅ esbuild JSX syntax pass
  - ✅ 6 tab 條件式齊備
  - ✅ 規範 #11 12 欄位齊備
  - ✅ 師兄真實瀏覽器驗收 5 點全 ✅
- **commit chain**:
  ```
  c4d7c3a (Claude 合併版交付，菜單命名錯)
   ↓ AiKa 改 1 label (任務中心→任務池)
  7e25588
   ↓ AiKa 改 2 labels (日誌流→日誌歷史 + 設置→系統設置)
  de6f425  ← 本黃金版起始點
  ```

## 2026-05-13
- 黃金版未升級 (jsx 0 改動)
- 後端: tasks PG 持久化, 5 worker, TASK ID fix
