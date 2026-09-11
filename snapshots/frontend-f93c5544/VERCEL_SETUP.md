# Vercel 部署設置（手動步驟）

## 🎯 目標
將 goaa.ai 前端應用部署到 Vercel，實現全球 CDN 加速和自動化部署。

---

## 📋 部署前檢查清單

- ✅ Vercel CLI 已安裝
- ✅ GitHub 倉庫連接：https://github.com/taofengtx/goaa-ai-frontend
- ✅ Next.js 優化配置已完成（next.config.js）
- ✅ vercel.json 配置文件已創建
- ✅ 所有代碼已推送到 GitHub main 分支

---

## 🚀 部署步驟

### 第 1 步：Vercel 賬戶設置（一次性）

如果還沒有 Vercel 賬戶：

1. 訪問 https://vercel.com/signup
2. 使用 GitHub 賬號登錄（taofengtx）
3. 授權 Vercel 訪問你的 GitHub 倉庫

### 第 2 步：本地登錄 Vercel CLI

```bash
cd C:\Users\Administrator\Projects\goaa-ai-local
vercel login
```

- 選擇 "Continue with GitHub"
- 在瀏覽器中完成授權
- 返回終端確認

### 第 3 步：首次部署（關聯項目）

```bash
vercel
```

**Vercel 會詢問以下問題：**

```
? Set up and deploy "goaa-ai-local"? [Y/n] → Y
? Which scope do you want to deploy to? → 你的 GitHub 用戶名
? Link to existing project? [y/N] → N（首次部署選 N）
? What's your project's name? → goaa-ai-frontend
? In which directory is your code located? → .（當前目錄）
? Want to override the settings above? [y/N] → N
```

部署完成後，你會看到：
```
✓ Deployed to https://goaa-ai-frontend.vercel.app
```

### 第 4 步：生產環境部署

```bash
vercel --prod
```

這會將應用部署到生產 URL：
```
✓ Production: https://goaa-ai-frontend.vercel.app
```

### 第 5 步：驗證部署

部署完成後，在瀏覽器中測試：

1. **Agent 登入頁**
   ```
   https://goaa-ai-frontend.vercel.app/agent-login
   用戶: demo
   密碼: goaa2024
   ```

2. **客戶登入頁**
   ```
   https://goaa-ai-frontend.vercel.app/client-login
   用戶: demo_client
   密碼: goaa2024
   ```

3. **驗證 API 連接**
   - 打開瀏覽器開發者工具（F12）
   - 檢查 Network 標籤
   - 嘗試登入，確認請求發送到 https://api.goaa.ai

---

## 🔄 後續部署（自動化）

Vercel 默認會在你推送到 GitHub main 分支時自動部署：

```bash
# 修改代碼後
git add .
git commit -m "your message"
git push origin main

# Vercel 會自動檢測到變更並重新部署
# 部署狀態可在 https://vercel.com/dashboard 查看
```

---

## 🌐 自定義域名設置

### 連接 goaa.ai 域名

1. 訪問 Vercel 儀表板
2. 選擇項目 "goaa-ai-frontend"
3. 進入 "Settings" → "Domains"
4. 點擊 "Add Domain"
5. 輸入 `goaa.ai`
6. 按照提示更新 DNS 記錄（在你的域名提供商）

### DNS 配置（示例）

如果你的域名託管在 Cloudflare、GoDaddy 等：

```
CNAME 記錄：
名稱: @ (或 www)
目標: cname.vercel-dns.com
```

---

## 📊 監控和分析

部署後，你可以在 Vercel 儀表板中查看：

- **部署歷史**：每次推送的部署狀態
- **性能分析**：Core Web Vitals、頁面加載時間
- **錯誤日誌**：任何構建或運行時錯誤
- **流量分析**：每日訪問量、地理位置

---

## 🆘 常見問題解決

### 問題 1：部署失敗 - "Build failed"
**原因**：通常是 npm 依賴或 TypeScript 錯誤
**解決**：
```bash
npm ci
npm run build
```

### 問題 2：API 連接失敗
**原因**：NEXT_PUBLIC_OPENCLAW_URL 環境變量未正確設置
**解決**：
1. 在 Vercel 儀表板中進入項目
2. Settings → Environment Variables
3. 確保 NEXT_PUBLIC_OPENCLAW_URL = https://api.goaa.ai

### 問題 3：登入頁面白屏
**原因**：localStorage 跨域問題或 JavaScript 錯誤
**解決**：
1. 打開瀏覽器開發者工具（F12）
2. 查看 Console 標籤的錯誤信息
3. 檢查 Network 標籤的 API 調用

---

## 📞 需要幫助？

- Vercel 文檔：https://vercel.com/docs
- Next.js 部署指南：https://nextjs.org/docs/deployment
- GitHub 倉庫：https://github.com/taofengtx/goaa-ai-frontend

---

**最後更新**：2026-05-05
**準備就緒**：✅ 隨時可以部署
