# goaa.ai Vercel 部署指南

## 🚀 快速部署步骤

### 步骤 1：安装 Vercel CLI
```bash
cd C:\Users\Administrator\Projects\goaa-ai-local
npm install -g vercel
```

### 步骤 2：连接 GitHub 账户
首先需要使用 GitHub 账户登录 Vercel：

```bash
vercel login
```

**选择选项：** "Continue with GitHub"
- 浏览器会自动打开 Vercel 授权页面
- 使用 GitHub 账户登录：**taofengtx**
- 授权 Vercel 访问你的 GitHub 仓库

### 步骤 3：首次部署（关联项目）
```bash
vercel
```

Vercel 会询问：
- **Project name**: 输入 `goaa-ai-frontend`
- **Directory**: 按 Enter（使用当前目录）
- **Build command**: 按 Enter（使用 next build）
- **Output directory**: 按 Enter（使用 .next）

### 步骤 4：生产环境部署
```bash
vercel --prod
```

## 📋 部署配置说明

### 环境变量
- **NEXT_PUBLIC_OPENCLAW_URL**: `https://api.goaa.ai`

### Next.js 优化
- ✅ SWC 最小化启用（更快编译）
- ✅ Standalone 输出（更小镜像）
- ✅ 生产源图禁用（更快加载）
- ✅ 图片优化禁用（适配 Vercel）

### vercel.json 配置
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_OPENCLAW_URL": "https://api.goaa.ai"
  }
}
```

## 🎯 部署后的 URL

部署成功后，你的应用将在以下 URL 可用：
- **默认 URL**: `https://goaa-ai-frontend.vercel.app`
- **自定义域名**: `https://goaa.ai`（需要配置）

## ✅ 验证部署

部署完成后，验证以下功能：

1. **Agent 登入页**
   - 访问: https://goaa-ai-frontend.vercel.app/agent-login
   - 登入账号: demo / goaa2024
   - 重定向到: /dashboard

2. **客户登入页**
   - 访问: https://goaa-ai-frontend.vercel.app/client-login
   - 登入账号: demo_client / goaa2024
   - 重定向到: /client-dashboard

3. **后端连接**
   - 验证 API 连接到 https://api.goaa.ai
   - 检查 WebSocket 连接状态

## 🔗 相关链接

- Vercel 仪表板: https://vercel.com/dashboard
- GitHub 仓库: https://github.com/taofengtx/goaa-ai-frontend
- OpenClaw API: https://api.goaa.ai

## 📝 常见问题

### Q: 部署失败怎么办？
A: 检查构建日志中的错误信息，常见原因：
- 环境变量未配置
- npm 依赖版本冲突
- TypeScript 编译错误

### Q: 如何修改已部署的应用？
A: 直接推送到 GitHub main 分支，Vercel 会自动重新部署。

### Q: 如何配置自定义域名？
A: 在 Vercel 仪表板中，项目设置 → Domains，添加 goaa.ai

---

**最后更新**: 2026-05-05
**部署版本**: Next.js 14 + React 18 + TypeScript
