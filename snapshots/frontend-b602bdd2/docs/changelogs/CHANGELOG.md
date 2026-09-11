# GOAA.AI Changelog

## [2.0.0] - 2026-05-08

### Phase 2: Multi-Agent Orchestration & Production Hardening

#### 🎉 Major Features
- **Multi-Agent Pipeline**: Concurrent task execution across agents
- **CORS Security**: White-list based cross-origin access control
- **HA Architecture**: Zero-downtime deployments with Cloudflare Tunnel
- **AiKa-Test v1.0**: Pluggable audit role for test automation
- **Node Registry**: Dynamic service discovery and management

#### 🔧 Infrastructure
- ✅ Cloudflare Tunnel (goaa-api-v2) configured and verified
- ✅ Docker Compose base configuration for local dev
- ✅ GitHub Actions CI pipeline scaffolding
- ✅ Hetzner CCX33 optimized deployment

#### 🛡️ Security Enhancements
- CORS: Upgraded from `["*"]` to explicit white-list
  ```
  - https://portal.goaa.ai
  - https://api.goaa.ai
  - https://goaa.ai
  - https://www.goaa.ai
  - http://localhost:3000
  ```
- Token-based authentication verified
- WebSocket security (wss://) enabled

#### 📚 Documentation
- Master Protocol v2.0
- Business Model v2.0
- HA Architecture guide
- Memory & Context Governance
- AiKa-Test Specification
- Docker Environment Setup
- Homepage Design Guidelines

#### 🐛 Bug Fixes
- Fixed: CORS 404 on public endpoints
- Fixed: WebSocket URL hardcoding (localhost → wss://api.goaa.ai)
- Fixed: users.json encoding issues
- Fixed: Tunnel configuration mismatch

#### 📊 Performance
- OpenClaw Health: Healthy
- API Response Time: <100ms
- WebSocket Latency: <50ms
- Tunnel Redundancy: 4 connections (PDX, SEA)

---

## [1.0.0] - 2026-05-06

### Phase 1: Initial Release & Platform Stabilization

#### ✅ Core Features
- OpenClaw API Gateway operational
- Portal frontend (Vercel deployment)
- QwenPaw Console interface
- Cloudflare Tunnel integration
- Demo user authentication (demo/goaa2024)

#### 📈 Deployment
- Hetzner Cloud CCX33 (24 cores, 64GB)
- Cloudflare DDoS protection
- Zero Trust access control
- systemd service management

#### 🎯 Status
- Production Ready: YES
- SLA: 99.9% target
- Monitoring: Active

---

## Release Notes

### Known Issues
- GitHub Actions workflow requires `workflow` scope token
- Demo user credentials hardcoded (production: use vault)
- Performance monitoring dashboard (planned for v2.1)

### Upgrade Path
- v1.0 → v2.0: Non-breaking changes
- Backward compatible APIs
- Existing deployments: In-place upgrade recommended

### Support
- Email: support@goaa.ai
- Issues: github.com/taofengtx/goaa-ai-frontend/issues
- Documentation: /docs

---

**Last Updated:** 2026-05-08  
**Maintainer:** Tao (taofengtx)  
**Status:** 🟢 Stable
