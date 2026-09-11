# High Availability Architecture

## System Overview

```
┌─────────────────────────────────────────────────┐
│  Cloudflare Global Network (CDN + DDoS)        │
│  ├─ Edge Caching                               │
│  ├─ WAF Protection                             │
│  └─ Zero Trust Access                          │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │  Cloudflared    │
        │   Tunnel v2     │
        │  (Encrypted)    │
        └────────┬────────┘
                 │
    ┌────────────┴────────────┐
    │  Hetzner Cloud (DE)     │
    │  CCX33 (24 cores, 64GB) │
    │                         │
    │  ┌─────────────────┐   │
    │  │ OpenClaw API    │   │
    │  │ :18789          │   │
    │  └────────┬────────┘   │
    │           │            │
    │  ┌────────┴────────┐   │
    │  │ QwenPaw Console │   │
    │  │ :8088           │   │
    │  └─────────────────┘   │
    │                         │
    │  ┌─────────────────┐   │
    │  │ PostgreSQL      │   │
    │  │ Redis Cache     │   │
    │  └─────────────────┘   │
    └─────────────────────────┘
            │
    ┌───────┴────────┐
    │ Vercel Frontend │
    │ portal.goaa.ai  │
    └─────────────────┘
```

## Reliability Features

### Network Level
- **Cloudflare DDoS Protection**: Automatic attack mitigation
- **Global CDN**: Edge caching for static assets
- **Encrypted Tunnel**: Zero Trust access control
- **Auto-failover**: 4 redundant tunnel connections

### Application Level
- **Health Checks**: Continuous service monitoring
- **Auto-restart**: systemd service recovery
- **CORS Security**: White-list based access control
- **Token Authentication**: Session-based security

### Data Level
- **PostgreSQL**: ACID compliance and durability
- **Redis Cache**: In-memory consistency
- **Backup Strategy**: Daily snapshots

## Disaster Recovery

| Scenario | RTO | RPO | Status |
|----------|-----|-----|--------|
| Service Restart | 5s | 0s | ✅ Verified |
| Config Rollback | 30s | 0s | ✅ Tested |
| Full System Recovery | 15m | 1h | 🔄 Planned |

---

**Version:** 2.0  
**Status:** Production Ready  
**Last Updated:** 2026-05-08
