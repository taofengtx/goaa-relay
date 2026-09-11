# goaa.ai AiKa Ubuntu 一鍵部署 U 盤

## 製作步驟

### 第一步：下載 Ubuntu 24.04 LTS Server ISO
https://ubuntu.com/download/server
文件名：ubuntu-24.04-live-server-amd64.iso

### 第二步：使用 Rufus 製作 U 盤
1. 下載 Rufus：https://rufus.ie
2. 插入 U 盤（建議 16GB+）
3. 選擇 ISO 文件
4. 分區方案：GPT
5. 文件系統：FAT32
6. 點擊 START

### 第三步：複製 autoinstall 文件到 U 盤
將以下文件複製到 U 盤根目錄：
- autoinstall/user-data
- autoinstall/meta-data（空文件）
- scripts/setup.sh

### 第四步：部署到 AiKa 盒子
1. U 盤插入 AiKa
2. 開機按 F7/F11 選擇 USB 啟動
3. 選擇 "Autoinstall" 選項
4. 等待約 15-20 分鐘自動安裝完成
5. 重啟後自動進入 goaa.ai 登入頁面

## 批量生產流程
1. 準備好母程序 U 盤
2. 每台新 AiKa 插入 U 盤
3. 開機選擇 USB 啟動
4. 全程無人值守自動安裝
5. 完成後 U 盤可拔出，繼續下一台

## 文件清單

```
AiKa-ubuntu/
├── autoinstall/
│   ├── user-data        (Ubuntu Autoinstall 配置)
│   └── meta-data        (空文件)
├── scripts/
│   └── setup.sh         (核心安裝腳本)
└── README.md            (本文件)
```

## 部署後的系統配置

### 自動安裝的軟件包
- Python 3 + pip + venv
- Git, curl, wget
- Nginx (反向代理)
- Chromium (Kiosk 浏览器)
- Cloudflared (公网隧道)
- QwenPaw (AI Agent 引擎)
- Playwright (自動化工具)

### 自動啟用的服務
- openclaw.service - OpenClaw API Gateway (:18789)
- qwenpaw.service - QwenPaw Agent Engine (:8088)
- goaa-kiosk.service - Chromium Kiosk 浏览器
- goaa-heartbeat.service - 心跳監控進程

### 自動配置的功能
- ✅ 自動登入 (goaa 用戶)
- ✅ 開機自動啟動所有服務
- ✅ 開機自動打開 goaa.ai 登入頁面
- ✅ 心跳上報到 api.goaa.ai
- ✅ SSH 伺服器已啟用

## 部署完成後的訪問方式

### 本地訪問
```
http://localhost:18789         (OpenClaw API)
http://localhost:8088          (QwenPaw)
http://127.0.0.1/             (Chromium Kiosk - 自動打開)
```

### 遠程訪問（通過心跳）
```
https://api.goaa.ai/api/v1/AiKa/devices   (查看所有設備)
https://api.goaa.ai/api/v1/AiKa/heartbeat (上報心跳)
```

## 常見問題

### Q: 部署花時間多久？
A: 約 15-20 分鐘（取決於網速）

### Q: 可以無人值守部署嗎？
A: 是的，全程完全自動化，無需任何人工操作

### Q: 如何修改密碼？
A: user-data 中的 `password` 字段（需要生成 crypt 哈希）

### Q: 如何修改主機名？
A: user-data 中的 `hostname` 字段（建議 goaa-node-001, goaa-node-002 等）

### Q: 可以在生產環境中使用嗎？
A: 是的，系統經過驗證，已在 Hetzner 和開發機上測試

## 生產部署清單

- [ ] 修改 user-data 中的 hostname 和 password
- [ ] 測試 Rufus 製作的 U 盤（在一台設備上試安裝）
- [ ] 確認 api.goaa.ai 可正常接收心跳
- [ ] 準備好目標 AiKa 盒子的硬件清單
- [ ] 製作批量 U 盤（建議準備 5-10 個）
- [ ] 開始批量部署

## 技術支持

如有問題，請檢查：
1. /var/log/goaa-setup.log (部署日誌)
2. systemctl status openclaw (服務狀態)
3. systemctl status qwenpaw
4. curl http://localhost:18789/health (API 健康檢查)

---

**版本：** 1.0  
**更新時間：** 2026-05-06  
**維護者：** AiKa  
