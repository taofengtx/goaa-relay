# GOAA 里程碑检查表 — 2026-06-14

## 今日完成
- [x] `aika-core-01` 成为唯一主开发入口
- [x] `aika-1` 冻结为只读历史迁移源
- [x] GitHub SSH 权限配置完成
- [x] 新主开发仓库 `/home/aika/Projects/goaa-ai-main` 建立
- [x] Env 治理完成
- [x] F-lite 2a 历史里程碑恢复并修订
- [x] Node.js `v22.22.3` / npm `10.9.8` 安装完成
- [x] `npm ci` 通过
- [x] ESLint 工具链完成
- [x] lint 通过：0 errors / 2 warnings
- [x] production build 通过
- [x] PR #2 创建并合并
- [x] GitHub main 更新到迁移合并基线 `a5e8c6e`
- [x] `HANDOFF.md` 更新完成
- [x] 正式 Roadmap v1.3 新建并发布
- [x] 文档收尾 commit `01ffcef` 推送到 main
- [x] QwenPaw 安装并通过最小调用
- [x] QwenPaw Tailscale 入口 `100.114.37.90:8088` 可访问
- [x] Ollama 原生性能诊断完成
- [x] “开工”与“收工”协议固定
- [x] 收工邮件收件人固定为 `taofengtx@gmail.com`

## 当前权威基线
- **GitHub main（收工文档提交前）**：`01ffcef`
- **aika-core-01 main**：`01ffcef`
- **迁移历史分支**：`migration/aika-core-01 @ 9793cdc`
- **Runtime repo**：`/opt/goaa/repo @ 53f599f`
- **Runtime 状态**：clean
- **服务状态**：
  - `goaa-local-console`：active
  - `goaa-worker-agent`：active
  - `goaa-telemetry-writer`：active
- **生产部署**：未执行

## 节点角色
- [x] `aika-core-01`：唯一主开发入口
- [x] `aika-1`：只读历史迁移源
- [ ] `aika-2`：下次开工重新核验
- [ ] `do-cloud-1`：下次开工重新核验
- [ ] `do-cloud-2`：下次开工重新核验
- [ ] `do-cloud-3`：下次开工重新核验

> 六节点是权威拓扑，不代表当前全部在线。

## Worker Runtime OS 路线
- [x] QwenPaw 过渡备用环境完成
- [x] 本地 Ollama 断网备用能力验证
- [ ] Worker Runtime OS Shell Capability
- [ ] Shell 执行分级与审批策略
- [ ] FastAPI → DO OpenClaw 执行契约
- [ ] Provider Review Hold
- [ ] 外部 API 成本网闸
- [ ] Run in Cloud / Run on My AiKa-Box / Auto Route

## P1
- [ ] 修复两个 lint warning
- [ ] 确定 Vercel 与 `aika@goaa.ai` 的长期身份关联策略
- [ ] Roadmap / DevLog / Milestone 自动交叉索引
- [ ] 优化 QwenPaw 本地 Agent 工具循环
- [ ] 规划 DeepSeek 在线主模型 + Ollama 断网备用切换

## 下次开工第一步
- [ ] 在 `aika-core-01` 核验 GitHub main 最新 SHA
- [ ] `git fetch origin main`
- [ ] `git merge --ff-only origin/main`
- [ ] 确认本地 main 与 GitHub main 一致
- [ ] 盘点六节点状态
- [ ] 对齐 GitHub / Runtime / HANDOFF / Roadmap / DevLog / Milestone

## 收工交付
- [x] DevLog 已生成
- [x] Milestone 已生成
- [x] GitHub main 收工文档 commit
- [ ] 收工邮件发送到 `taofengtx@gmail.com`
- [x] 附件：DevLog + Milestone 已准备

*GOAA 主开发迁移收工里程碑 — 2026-06-14*
