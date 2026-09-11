#!/usr/bin/env python3
"""
GOAA AiKa-Box — Local Telemetry Writer (B 線 B-2)

獨立採集腳本。不碰 agent.py / main.py。
每 INTERVAL 秒採集本機 sanitized telemetry, atomic write 到 cache 檔。
Local Console (5188) 只讀此 cache 檔, 不直接採集。

安全:只採脫敏運行指標 —— 不讀 secret / env / RAG 正文 / raw prompt。
容錯:任何單項採集失敗 → 該欄位 null/unknown, 腳本不崩。

部署: /opt/goaa/workers/telemetry_writer.py
cache:  /opt/goaa/run/telemetry_local.json
run as: aika:aika (與 worker-agent / local-console 同用戶)
python: /opt/goaa/venv/bin/python (psutil 7.2.2 已驗)
"""

import os
import json
import time
import socket
import subprocess
from datetime import datetime, timezone

try:
    import psutil
except Exception:
    psutil = None  # 不應發生(venv 已驗), 但防禦性處理

# ---- 可配置(環境變數覆蓋, 不寫死)----
INTERVAL = int(os.environ.get("TELEMETRY_INTERVAL_SEC", "10"))
RUN_DIR = os.environ.get("TELEMETRY_RUN_DIR", "/opt/goaa/run")
CACHE_PATH = os.path.join(RUN_DIR, "telemetry_local.json")
TMP_PATH = CACHE_PATH + ".tmp"
NODE_ID = os.environ.get("NODE_ID", socket.gethostname() or "aika-core-01")
DISK_PATH = os.environ.get("TELEMETRY_DISK_PATH", "/")

# 採集哪些 service 的 is-active(只輸出 active/inactive/unknown, 不輸出 PID/cmdline/env)
SERVICES = {
    "ollama": "ollama.service",
    "worker_agent": "goaa-worker-agent.service",
    "local_console": "goaa-local-console.service",
}


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def collect_cpu():
    if psutil is None:
        return None
    try:
        # interval=None 用上次調用以來的差值, 不阻塞
        return round(float(psutil.cpu_percent(interval=None)), 1)
    except Exception:
        return None


def collect_mem():
    if psutil is None:
        return None
    try:
        return round(float(psutil.virtual_memory().percent), 1)
    except Exception:
        return None


def collect_disk():
    if psutil is None:
        return None
    try:
        return round(float(psutil.disk_usage(DISK_PATH).percent), 1)
    except Exception:
        return None


def collect_gpu():
    """nvidia-smi 取 GPU 利用率(%); 不可用回 None。只取數值, 不取序號/driver。"""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode != 0:
            return None
        line = out.stdout.strip().splitlines()[0].strip()
        return round(float(line), 1)
    except Exception:
        return None


def collect_uptime():
    if psutil is None:
        return None
    try:
        return int(time.time() - psutil.boot_time())
    except Exception:
        return None


def service_status(unit):
    """systemctl is-active; 只回 active/inactive/unknown。不輸出其他文本。"""
    try:
        out = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True, text=True, timeout=5,
        )
        s = out.stdout.strip()
        if s == "active":
            return "active"
        if s in ("inactive", "failed", "activating", "deactivating"):
            return s
        return "unknown"
    except Exception:
        return "unknown"


def collect_lan_ip():
    """取本機 LAN IP(連一個不發包的 UDP socket 取 local addr); 失敗回 None。"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("192.168.1.1", 80))  # 不真的發資料, 只為取 local addr
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def collect_tailscale_ip():
    """tailscale ip -4; 不可用回 None。"""
    try:
        out = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode != 0:
            return None
        ip = out.stdout.strip().splitlines()[0].strip()
        return ip or None
    except Exception:
        return None


def build_payload():
    cpu = collect_cpu()
    mem = collect_mem()
    disk = collect_disk()
    gpu = collect_gpu()
    services = {k: service_status(u) for k, u in SERVICES.items()}
    return {
        "node_id": NODE_ID,
        "hostname": socket.gethostname(),
        "status": "online",
        "collected_at": _now_iso(),
        "collected_at_epoch": int(time.time()),
        "uptime_sec": collect_uptime(),
        "telemetry": {
            "cpu_pct": cpu,
            "mem_pct": mem,
            "disk_pct": disk,
            "gpu_pct": gpu,  # None if nvidia-smi 不可用
        },
        "services": services,
        "network": {
            "tailscale_ip": collect_tailscale_ip(),
            "lan_ip": collect_lan_ip(),
            "console_bind": "127.0.0.1:5188",
        },
        "safety": {
            "contains_secret": False,
            "contains_rag_text": False,
            "contains_env": False,
            "source": "sanitized_local_telemetry",
        },
    }


def atomic_write(payload):
    """atomic write: 寫 .tmp → fsync → rename。避免 console 讀到半截 JSON。"""
    os.makedirs(RUN_DIR, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    fd = os.open(TMP_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, data.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(TMP_PATH, CACHE_PATH)  # atomic on same filesystem


def run_once():
    """採集一次並寫 cache。回 payload(供 --once 列印)。"""
    payload = build_payload()
    atomic_write(payload)
    return payload


def main():
    import sys
    # --once: 採一次就退出(供手動驗證), 否則 loop
    if "--once" in sys.argv:
        p = run_once()
        # 列印時不含 secret(本來就沒有), 供人工檢視
        print(json.dumps(p, ensure_ascii=False, indent=2))
        return
    # psutil.cpu_percent 第一次調用回 0.0, 先 warm up 一次
    if psutil is not None:
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass
    while True:
        try:
            run_once()
        except Exception:
            # 寫失敗不讓腳本崩; 下一輪重試。不印 traceback(可能含路徑)。
            pass
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
