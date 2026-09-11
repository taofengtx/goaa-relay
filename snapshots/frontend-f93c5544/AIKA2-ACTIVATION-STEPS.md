# GOAA-20260510-RUNTIME-ACTIVATE - Manual Steps for AiKa-2

Execute each step on AiKa-2 (192.168.1.208)

## Step 1: Sync Repository
```bash
mkdir -p /opt/goaa/{runtime,logs}
cd /opt/goaa/repo 2>/dev/null && git pull origin main -q || git clone https://github.com/taofengtx/goaa-ai-frontend.git /opt/goaa/repo -q
echo Step 1 OK
```

