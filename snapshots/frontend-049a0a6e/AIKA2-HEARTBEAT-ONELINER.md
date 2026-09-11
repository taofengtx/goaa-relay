# AiKa-2 Heartbeat One-Liner Setup

## Execute this ONE command on AiKa-2 terminal:

```bash
bash <(curl -s https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/scripts/aika2-heartbeat-start.sh)
```

## Or manually step by step:

```bash
# 1. Install dependencies
pip3 install psutil requests -q

# 2. Create and start heartbeat (runs in background)
curl -s https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/scripts/aika2-heartbeat-setup.py -o /opt/goaa/heartbeat.py
nohup python3 /opt/goaa/heartbeat.py > /opt/goaa/logs/heartbeat.log 2>&1 &

# 3. Verify after 5 seconds
sleep 5
cat /opt/goaa/logs/heartbeat.log
```

## Verify from AiKa-1:

After running, check from any machine:

```bash
curl -s http://134.199.227.108:8080/workers/status
```

Look for `aika-2` with `last_heartbeat` not "never".
