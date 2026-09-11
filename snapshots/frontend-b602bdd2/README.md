# goaa.ai Frontend - Local Development

本地开发环境，与 Framer 云端项目相辅相成的 Next.js 应用。

## 📋 项目概述

- **框架：** Next.js 14 (App Router)
- **语言：** TypeScript
- **UI：** React 18
- **API 集成：** OpenClaw Gateway (via Cloudflare Tunnel)
- **实时通信：** WebSocket (Token-based 认证)

## 🚀 快速开始

### 环境要求
- Node.js 18+
- npm 或 yarn

### 安装依赖
```bash
npm install
```

### 创建环境配置
复制 `.env.example` 到 `.env.local`：
```bash
cp .env.example .env.local
```

编辑 `.env.local`，设置正确的 OpenClaw URL：
```
NEXT_PUBLIC_OPENCLAW_URL=https://your-tunnel-url.trycloudflare.com
```

### 启动开发服务器
```bash
npm run dev
```

打开 [http://localhost:3000](http://localhost:3000) 查看应用。

## 📁 项目结构

```
app/
├── components/
│   └── ChatComponent.tsx           # 主聊天界面
├── lib/
│   └── openclaw.ts                 # OpenClaw API 客户端
├── page.tsx                        # 首页
├── layout.tsx                      # 根布局
└── globals.css                     # 全局样式

.env.local                          # 环境配置（本地，不推送）
.env.example                        # 环境配置示例
.gitignore                          # Git 忽略规则
```

## 🔌 API 集成

### OpenClaw Gateway
- **文档：** OpenClaw API Gateway（FastAPI）
- **端点：** `POST /api/v1/chat` 创建会话
- **通信：** WebSocket 双向通信
- **认证：** Token-based（自动处理）

### 使用示例
```typescript
import { chat } from '@/app/lib/openclaw'

// 一行代码调用 AI
const response = await chat("user_id", "你好")
```

## 🛠️ 开发指南

### 修改 API URL
当 Cloudflare Tunnel 重启时，URL 会改变。更新 `.env.local`：
```
NEXT_PUBLIC_OPENCLAW_URL=https://new-tunnel-url.trycloudflare.com
```

### 调试
- 打开浏览器开发者工具 (F12)
- 查看 Console 标签查看 API 日志
- 检查 Network 标签查看 WebSocket 连接

### 构建生产版本
```bash
npm run build
npm run start
```

## 📦 部署选项

### 选项 1：Vercel（推荐）
```bash
npm install -g vercel
vercel
```

### 选项 2：Docker
```bash
docker build -t goaa-ai-local .
docker run -p 3000:3000 goaa-ai-local
```

### 选项 3：自托管
```bash
npm run build
npm run start
```

## 🔗 相关资源

- **Framer 云端项目：** https://framer.com/projects
- **OpenClaw API：** OpenClaw main.py
- **QwenPaw Agent：** QwenPaw console
- **Cloudflare Tunnel：** https://www.cloudflare.com/products/tunnel/

## 📝 环境变量说明

| 变量 | 说明 | 示例 |
|------|------|------|
| `NEXT_PUBLIC_OPENCLAW_URL` | OpenClaw API 网关 URL | https://xxx.trycloudflare.com |

> 前缀 `NEXT_PUBLIC_` 表示这个变量会被暴露到浏览器客户端

## 🤝 贡献指南

1. Fork 此仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 💬 反馈

如有问题或建议，请提交 Issue 或联系 Tao。

---

**开发者：** Tao & AiKa  
**创建时间：** 2026-05-03  
**状态：** 🚀 生产就绪
