# Docker Environment Configuration

## Base Services

### OpenClaw API Gateway
```yaml
container_name: openclaw-api-gateway
image: goaa/openclaw:0.1.0
ports:
  - "18789:18789"
environment:
  - LOG_LEVEL=info
  - CORS_ORIGINS=https://portal.goaa.ai
  - ALLOW_CREDENTIALS=true
volumes:
  - ./logs/openclaw:/opt/goaa/logs
restart: always
```

### QwenPaw Console
```yaml
container_name: qwenpaw-console
image: goaa/qwenpaw:latest
ports:
  - "8088:8088"
environment:
  - OPENCLAW_URL=http://openclaw:18789
depends_on:
  - openclaw
restart: always
```

### Database Services
```yaml
postgres:
  image: postgres:15-alpine
  environment:
    - POSTGRES_PASSWORD=secure_password
  volumes:
    - postgres_data:/var/lib/postgresql/data

redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

## Network Configuration

```yaml
networks:
  goaa-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Volume Management

```yaml
volumes:
  openclaw-logs:
  qwenpaw-logs:
  postgres_data:
    driver: local
```

## Development vs Production

### Development
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
# With TLS termination
# Health monitoring
# Auto-scaling
```

## Health Checks

All services configured with health probes:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

**Version:** 2.0  
**Status:** Active  
**Last Updated:** 2026-05-08
