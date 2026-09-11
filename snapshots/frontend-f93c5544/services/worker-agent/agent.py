#!/usr/bin/env python3
"""GOAA.AI Worker Agent v1.0 — runs on each AiKa node"""
import requests, json, time, os, platform, subprocess, psutil, socket, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AiKa.Agent")

WORKER_ID  = os.getenv("WORKER_ID",  "aika-1")
ROUTER_URL = os.getenv("ROUTER_API", "http://134.199.227.108:8080")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
POLL_SEC   = int(os.getenv("POLL_SEC", "5"))
IS_WIN     = platform.system() == "Windows"

def send_heartbeat():
    try:
        try:
            r = subprocess.run(["docker","ps"],capture_output=True,timeout=5)
            docker_ok = r.returncode==0
        except: docker_ok = False
        try: ollama_ok = requests.get(f"{OLLAMA_URL}/api/tags",timeout=3).status_code==200
        except: ollama_ok = False
        disk_path = "C:\\" if IS_WIN else "/"
        requests.post(f"{ROUTER_URL}/worker/heartbeat", timeout=8, json={
            "worker_id":WORKER_ID, "cpu":psutil.cpu_percent(interval=1),
            "memory":psutil.virtual_memory().percent,
            "disk":psutil.disk_usage(disk_path).percent,
            "docker":docker_ok, "ollama":ollama_ok, "status":"online"})
    except Exception as e: logger.warning(f"HB failed: {e}")

def fetch_next_task():
    try:
        r = requests.get(f"{ROUTER_URL}/tasks/next/{WORKER_ID}", timeout=8)
        if r.status_code == 200:
            d = r.json()
            if d.get("task_id"): return d
    except: pass
    return None

def exec_health_check(t):
    cpu = psutil.cpu_percent(interval=1); mem = psutil.virtual_memory().percent
    return {"status":"success","result":f"Health OK — {socket.gethostname()} CPU:{cpu}% MEM:{mem}%","revenue":0.10,"cost":0.001}

def exec_ollama_status(t):
    try:
        models = [m["name"] for m in requests.get(f"{OLLAMA_URL}/api/tags",timeout=5).json().get("models",[])]
        return {"status":"success","result":f"Ollama OK — {', '.join(models) or 'no models'}","revenue":0.10,"cost":0.001}
    except Exception as e: return {"status":"failed","result":f"Ollama offline: {e}","revenue":0,"cost":0.001}

def exec_docker_status(t):
    try:
        r = subprocess.run(["docker","ps","--format","{{.Names}}: {{.Status}}"],capture_output=True,text=True,timeout=10)
        return {"status":"success","result":r.stdout.strip() or "No containers","revenue":0.10,"cost":0.001}
    except Exception as e: return {"status":"failed","result":str(e),"revenue":0,"cost":0.001}

def exec_system_status(t):
    cpu = psutil.cpu_percent(interval=2); mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\" if IS_WIN else "/")
    return {"status":"success","result":f"CPU:{cpu}% RAM:{mem.percent}% Disk:{disk.percent}% Free:{disk.free//1073741824}GB","revenue":0.15,"cost":0.001}

def exec_ping_test(t):
    target = (t.get("prompt","") or "134.199.227.108").strip()
    try:
        r = subprocess.run(["ping","-n"if IS_WIN else"-c","3",target],capture_output=True,text=True,timeout=15)
        ok = r.returncode == 0
        return {"status":"success"if ok else"failed","result":f"Ping {target}: {'OK'if ok else'FAILED'}","revenue":0.05,"cost":0.001}
    except Exception as e: return {"status":"failed","result":str(e),"revenue":0,"cost":0.001}

def exec_log_summary(t):
    log_dir = os.path.join("/opt/goaa/logs"if not IS_WIN else r"C:\opt\goaa\logs","tasks")
    try:
        log_file = os.path.join(log_dir, time.strftime("%Y-%m-%d")+".jsonl")
        if os.path.exists(log_file):
            lines = open(log_file).readlines()
            s = sum(1 for l in lines if'"success"'in l)
            result = f"Today: {len(lines)} tasks, {s} success, {len(lines)-s} failed"
        else: result = "No tasks logged today"
        return {"status":"success","result":result,"revenue":0.50,"cost":0.003}
    except Exception as e: return {"status":"failed","result":str(e),"revenue":0,"cost":0.003}

def exec_chat(t):
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate",
            json={"model":"qwen2.5:7b","prompt":t.get("prompt","Hello"),"stream":False},timeout=60)
        return {"status":"success","result":r.json().get("response",""),"revenue":0.50,"cost":0.003}
    except Exception as e: return {"status":"failed","result":str(e),"revenue":0,"cost":0.003}

EXECUTORS = {
    "health_check":exec_health_check,"ollama_status":exec_ollama_status,
    "docker_status":exec_docker_status,"system_status":exec_system_status,
    "ping_test":exec_ping_test,"log_summary":exec_log_summary,"chat":exec_chat,
}

def execute_task(task):
    t0 = time.time()
    ttype = task.get("task_type","ops")
    logger.info(f"Executing {task['task_id']} type={ttype}")
    executor = EXECUTORS.get(ttype)
    result = executor(task) if executor else {"status":"failed","result":f"Unknown: {ttype}","revenue":0,"cost":0.001}
    dur = int((time.time()-t0)*1000)
    try:
        requests.post(f"{ROUTER_URL}/task/complete", timeout=10, json={
            "worker_id":WORKER_ID,"task_id":task["task_id"],"task_type":ttype,
            "model_used":"ollama-qwen2.5-7b","status":result.get("status","failed"),
            "revenue_usd":result.get("revenue",0),"cost_usd":result.get("cost",0.001),
            "duration_ms":dur,"logs":result.get("result","")})
        logger.info(f"Done {task['task_id']} → {result.get('status')} {dur}ms")
    except Exception as e: logger.error(f"Report failed: {e}")

def main():
    logger.info(f"Worker Agent started — {WORKER_ID} → {ROUTER_URL}")
    hb = 0
    while True:
        hb += 1
        if hb >= 6: send_heartbeat(); hb = 0
        task = fetch_next_task()
        if task: execute_task(task)
        else: time.sleep(POLL_SEC)

if __name__ == "__main__":
    main()
