# GOAA 規範 #31 + #32 立規 (2026-05-15 晚班)

## 規範 #31 — AiKa 不自主修代碼 / STDOUT 透傳

**來源真實事件**:
- 2026-05-15 上午: V4.0-2A-1 部署時 AiKa 自主修了 2 個雷 (syntax error + r=_body bug)
- 2026-05-15 晚上: AiKa 摘要說「V4.0-2B 未 merge main」, 但 git log 真實顯示已 merge (52c0d2a)
- 兩次都是 AiKa「自主判斷/自主行動」, Claude 不知道線上真實狀態

**規範內容**:
AiKa 角色嚴守: 執行者, 不是修補者, 不是摘要員。

1. **不自主修代碼**:
   - Claude 出的批次發生錯誤時, AiKa 不自主修改 .py / .jsx / .json
   - AiKa 不對線上 api.py / GoaaDashboard.jsx 寫 hotfix
   - AiKa 立刻 STDOUT 原樣貼師兄, 由 Claude 出修補批次

2. **不自主摘要關鍵情報**:
   - git log / grep 結果 / PG schema 等真實情報必須原樣貼
   - 不允許「總結成表格」「省略 leading whitespace」
   - 「看起來相同」的行也不能省 (str_replace 對縮排嚴格)

3. **例外**:
   - 純粹 typo 修復 (如多了一個 `}`) 可自主修, 但必須先告知 Claude
   - 摘要長 STDOUT (>10000 字) 可分段貼, 但不能改字符

4. **違反後果**:
   - AiKa 自主修導致的問題, 由 AiKa 負責回滾
   - Claude 應拒絕「相信 AiKa 摘要」, 必須要求看真實程式碼

## 規範 #32 — 批次交付完整性 (4 步指令必備)

**來源真實事件**:
- 2026-05-15 上午: 師兄問「你沒給指令出來」, 我寫了批次但沒給執行指令

**規範內容**:
Claude 交付批次時必須含完整 4 步指令:

1. **Step 1: 下載**
   - 文件位置 ("從訊息上方 Download 連結")
   - 預設路徑 (C:\Users\Administrator\Downloads\batch_*.py)

2. **Step 2: MD5 校驗 (規範 #12)**
   - 完整 PowerShell command
   - 預期 MD5 值 (大寫)

3. **Step 3: 執行**
   - 完整 python command
   - 預估執行時間

4. **Step 4: 結果處理**
   - 提示 AiKa 不要自主修 (規範 #31)
   - 提示貼回 STDOUT 原樣 (含縮排/行號)
   - 提示分段貼如果太長

**範例**:
```
═══════════════════════════════════════════════════════
Step 1: 下載 batch_xxx.py
Step 2: MD5 校驗 (PS> Get-FileHash ...)
Step 3: 跑 (PS> python ...)
Step 4: STDOUT 原樣貼 Claude, AiKa 不要自主修
═══════════════════════════════════════════════════════
```

缺一不可。

## 規範體系現況 (2026-05-15 晚班)

22 條規範:
- #11 Baseline Freeze
- #12 Fingerprint Check  
- #13 Session Handoff
- #14 Golden Baseline
- #15 Infra Decommission 24h Cooldown
- #16 廣域 try/except 反模式
- #17 P1: model-router systemd unit (待補)
- #18 廣域 try/except 反模式 (重複, 待合併)
- #19 收工郵件規範 v2
- #20 開工健康度告警 Health Watch
- #21 指令長度限制 QwenPaw Window
- #22 機密訊息安全處理
- #23 systemd Secrets Audit
- #24 接口契約一致性 (重複, 待合併)
- #25 跨層型別約束 Type Boundary
- #26 jsx 部署預檢
- #27 架構哲學 Integration First
- #28 靜默失敗反模式 Silent Failure
- #29 探索與創新 Explore & Innovate
- #30 漸進式智能 Progressive Intelligence
- **#31 AiKa 不自主修 / STDOUT 透傳** ⭐ 今晚新立
- **#32 批次交付完整性** ⭐ 今晚新立

下次工作前: 規範 #16 vs #18 / #24 重複項可考慮合併
