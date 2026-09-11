"""
═══════════════════════════════════════════════════════════════════
  DEPRECATED — Phase 3 Frozen Snapshot
═══════════════════════════════════════════════════════════════════

  Status:        🔴 DEPRECATED (frozen 2026-05-19, last update 5/11 commit 2bb74c8)
  Phase:         3 (early task dispatch, no PG persistence, no tool calling)
  Replacement:   infra/router/api.py (Phase 4.1, 830 lines)

  This file is retained for historical reference only.
  It is NOT imported by any module.
  It is NOT deployed to production.

  Deploy script scripts/do-deploy-model-router-api.sh now sources from
  infra/router/api.py (see commit aa65f65 "snapshot DO production").

  本檔為 Phase 3 凍結快照, 已棄用。
  正式版本: infra/router/api.py (Phase 4.1, 含 multi-turn + tools + PG)

  ─── 規範依據 ────────────────────────────────────────────────
    #11 only-add  : 不刪不改名, 保留為歷史快照
    #14 v2        : 路徑名穩定避免 docs 引用失效
    #36 v2        : Runtime Truth — 此檔零生產依賴 (E.1 法醫鑑識)
    #47           : DO ↔ git 一致性 — 不在 deploy 路徑中
  ──────────────────────────────────────────────────────────────

  歷史鑑識報告: docs/architecture/PHASE_4_1_RECONSTRUCTION__v1__975ddc09.md

DEPRECATION_NOTICE = "This module is deprecated. Use infra/router/api.py instead."
"""

"""
GOAA.AI Model Router + Task Dispatch API v3.0
Phase 3: Real Task Scheduling Engine
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import requests, json, os, time, platform, uuid, threading, asyncio, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenClaw.Router")

app = FastAPI(title="GOAA Task Router v3", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Paths ──────────────────────────────────────────────────────
BASE = "/opt/goaa" if platform.system() != "Windows" else r"C:\opt\goaa"
LOGS = os.path.join(BASE, "logs")
for d in ["router","tasks","revenue","profit","circuit-breaker","errors","workers","dispatch"]:
    os.makedirs(os.path.join(LOGS, d), exist_ok=True)

def log_path(sub): return os.path.join(LOGS, sub, datetime.utcnow().strftime("%Y-%m-%d") + ".jsonl")
def append_log(sub, data):
    data.setdefault("ts", datetime.utcnow().isoformat() + "Z")
    with open(log_path(sub), "a") as f: f.write(json.dumps(data, ensure_ascii=False) + "\n")
def read_log(sub):
    p = log_path(sub)
    if not os.path.exists(p): return []
    lines = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                try: lines.append(json.loads(line))
                except: pass
    return lines

# ── Config ─────────────────────────────────────────────────────
DEFAULT_MODEL  = "deepseek-v4-flash"
LIMITS = {"claude_hourly":2.0,"claude_daily":20.0,"task_default":0.05,"task_p0p1":1.0}
PRICING = {
    "claude-sonnet-4-6":  {"input":0.003,   "output":0.015},
    "deepseek-v4-flash":  {"input":0.00014, "output":0.00028},
    "ollama-qwen2.5-7b":  {"input":0.0,     "output":0.0},
}
DEEPSEEK_KEY  = os.getenv("DEEPSEEK_API_KEY",  "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

WORKER_REGISTRY = {
    "aika-1":     {"ip":"192.168.1.207","role":"primary_coordinator",  "os":"Windows 11",   "max_concurrent":3},
    "aika-2":     {"ip":"192.168.1.208","role":"secondary_coordinator","os":"Xubuntu 24.04","max_concurrent":3},
    "do-cloud-1": {"ip":"134.199.227.108","role":"cloud_worker",       "os":"Ubuntu 24.04", "max_concurrent":5},
}

# ── In-memory State ────────────────────────────────────────────
task_pool:    Dict[str, dict] = {}   # task_id → task
task_queue:   List[str]       = []   # ordered list of pending task_ids
worker_tasks: Dict[str, list] = {w: [] for w in WORKER_REGISTRY}  # worker_id → [task_ids]
worker_hb:    Dict[str, dict] = {}
_task_seq:    Dict[str, int]  = {}
_cb_until:    Optional[datetime] = None
_dispatcher_running = False

# ── Task Types ─────────────────────────────────────────────────
TASK_REVENUE = {
    "health_check":  {"revenue":0.10,"cost":0.001,"risk":1},
    "ollama_status": {"revenue":0.10,"cost":0.001,"risk":1},
    "docker_status": {"revenue":0.10,"cost":0.001,"risk":1},
    "system_status": {"revenue":0.15,"cost":0.001,"risk":1},
    "ping_test":     {"revenue":0.05,"cost":0.001,"risk":1},
    "log_summary":   {"revenue":0.50,"cost":0.003,"risk":2},
    "chat":          {"revenue":0.50,"cost":0.003,"risk":1},
    "security_scan": {"revenue":2.00,"cost":0.045,"risk":4},
    "code_review":   {"revenue":1.50,"cost":0.020,"risk":3},
    "ops":           {"revenue":1.00,"cost":0.003,"risk":1},
    "report":        {"revenue":1.50,"cost":0.004,"risk":1},
    "planning":      {"revenue":0.50,"cost":0.002,"risk":1},
}

# ── Helpers ────────────────────────────────────────────────────
def gen_task_id() -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    _task_seq[today] = _task_seq.get(today, 0) + 1
    return f"task_{today}_{_task_seq[today]:04d}"

def est_cost(model, tokens=1000):
    p = PRICING.get(model, {})
    return round(tokens/1000*(p.get("input",0)+p.get("output",0)*0.5), 6)

def claude_hourly():
    cutoff = datetime.utcnow() - timedelta(hours=1)
    return sum(e.get("cost_usd",0) for e in read_log("router")
               if e.get("model")=="claude-sonnet-4-6"
               and datetime.fromisoformat(e["ts"].replace("Z","")) > cutoff)

def claude_daily():
    return sum(e.get("cost_usd",0) for e in read_log("router") if e.get("model")=="claude-sonnet-4-6")

def claude_ok():
    global _cb_until
    if _cb_until and datetime.utcnow() < _cb_until: return False
    if claude_hourly() >= LIMITS["claude_hourly"]:
        _cb_until = datetime.utcnow() + timedelta(hours=1)
        append_log("circuit-breaker", {"reason":"hourly_limit"})
        return False
    if claude_daily() >= LIMITS["claude_daily"]:
        _cb_until = datetime.utcnow().replace(hour=0,minute=0,second=0) + timedelta(days=1)
        append_log("circuit-breaker", {"reason":"daily_limit"})
        return False
    return True

def ollama_up():
    try: return requests.get(f"{OLLAMA_URL}/api/tags", timeout=3).status_code == 200
    except: return False

def select_model(priority, risk, cost):
    if claude_hourly() >= LIMITS["claude_hourly"]:
        return {"model":"ollama-qwen2.5-7b","reason":"circuit_breaker","cb":True}
    if priority <= 1 and risk >= 4 and claude_ok():
        return {"model":"claude-sonnet-4-6","reason":"p0p1_risk4","cb":False}
    if cost > LIMITS["task_default"] and not (priority <= 1 and risk >= 4):
        return {"model":"ollama-qwen2.5-7b","reason":"cost_exceeded","cb":True}
    return {"model":DEFAULT_MODEL,"reason":"default","cb":False}

def call_deepseek(prompt):
    if not DEEPSEEK_KEY: return {"text":f"[Mock-DeepSeek] {prompt[:80]}","model":"deepseek-v4-flash","mock":True}
    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"},
            json={"model":"deepseek-chat","messages":[{"role":"user","content":prompt}]},
            timeout=30)
        r.raise_for_status()
        return {"text":r.json()["choices"][0]["message"]["content"],"model":"deepseek-v4-flash"}
    except Exception as e:
        return {"text":f"[Error] {e}","model":"deepseek-v4-flash","error":True}

def get_idle_worker(task_type="ops", priority=2):
    """Find worker with fewest active tasks."""
    best = None; best_load = 999
    for wid, info in WORKER_REGISTRY.items():
        hb = worker_hb.get(wid, {})
        if hb.get("status") == "offline": continue
        active = len([t for t in worker_tasks.get(wid,[])
                     if task_pool.get(t,{}).get("status") in ("running","assigned")])
        if active < info["max_concurrent"] and active < best_load:
            best = wid; best_load = active
    return best

def task_score(task):
    """Higher score = dispatch first."""
    p_weight = {0:100, 1:80, 2:50, 3:30, 4:10}.get(task.get("priority",2), 50)
    rev = task.get("estimated_revenue_usd", 0)
    cost = task.get("estimated_cost_usd", 0)
    return p_weight + rev - cost

# ── Auto Dispatcher ────────────────────────────────────────────
def auto_dispatcher_loop():
    global _dispatcher_running
    _dispatcher_running = True
    logger.info("Auto Dispatcher started")
    while True:
        try:
            pending = [tid for tid in task_queue
                      if task_pool.get(tid,{}).get("status") == "pending"]
            pending.sort(key=lambda tid: task_score(task_pool.get(tid,{})), reverse=True)

            for tid in pending:
                task = task_pool.get(tid)
                if not task: continue
                # Block P0/P1 high-risk
                if task.get("priority",2) <= 1 and task.get("risk_level",1) >= 4:
                    task["status"] = "awaiting_approval"
                    task["note"] = "Requires manual approval (P0/P1 + high risk)"
                    continue
                # Block zero-profit
                rev  = task.get("estimated_revenue_usd",0)
                cost = task.get("estimated_cost_usd",0)
                if rev - cost <= 0 and task.get("task_type") not in ("health_check","ping_test","system_status","ollama_status","docker_status"):
                    task["status"] = "blocked"
                    task["note"] = "Blocked: estimated profit <= 0"
                    continue
                # Find idle worker
                worker = task.get("target_worker") or get_idle_worker(task.get("task_type","ops"))
                if not worker: break
                # Assign
                task["status"] = "assigned"
                task["assigned_worker"] = worker
                task["assigned_at"] = datetime.utcnow().isoformat() + "Z"
                if worker not in worker_tasks: worker_tasks[worker] = []
                if tid not in worker_tasks[worker]: worker_tasks[worker].append(tid)
                append_log("dispatch", {"task_id":tid,"worker":worker,"type":task.get("task_type")})
        except Exception as e:
            logger.error(f"Dispatcher error: {e}")
        time.sleep(5)

@app.on_event("startup")
async def startup():
    t = threading.Thread(target=auto_dispatcher_loop, daemon=True)
    t.start()
    logger.info("GOAA Router v3 started with auto-dispatcher")

# ══════════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════════
class DispatchReq(BaseModel):
    task_type: str = "ops"
    prompt: str = ""
    priority: int = 2
    risk_level: int = 1
    target_worker: Optional[str] = None
    estimated_revenue_usd: Optional[float] = None
    estimated_cost_usd: Optional[float] = None
    max_cost_usd: float = 0.05
    context: Optional[dict] = {}
    submitted_by: str = "tao"

class TaskComplete(BaseModel):
    worker_id: str
    task_id: Optional[str] = None
    task_type: str = "ops"
    model_used: str
    status: str
    revenue_usd: float = 0.0
    cost_usd: float = 0.0
    credits_charged: int = 0
    duration_ms: int = 0
    logs: Optional[str] = ""
    error_msg: str = ""

class PoolAddReq(BaseModel):
    task_type: str
    prompt: str = ""
    priority: int = 2
    risk_level: int = 1
    target_worker: Optional[str] = None
    estimated_revenue_usd: Optional[float] = None
    estimated_cost_usd: Optional[float] = None

class PoolBatchReq(BaseModel):
    tasks: List[PoolAddReq]

class WorkerHB(BaseModel):
    worker_id: str
    cpu: float = 0.0
    memory: float = 0.0
    disk: float = 0.0
    docker: bool = False
    ollama: bool = False
    status: str = "online"

class ChatReq(BaseModel):
    prompt: str
    priority: int = 2
    risk_level: int = 1
    worker_id: str = "aika-1"
    estimated_tokens: int = 1000

# ══════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════
@app.get("/health")
def health():
    return {"status":"ok","version":"3.0.0","node":"AKC-DO-001",
            "time":datetime.utcnow().isoformat()+"Z",
            "default_model":DEFAULT_MODEL,
            "claude_available":claude_ok(),
            "deepseek_available":bool(DEEPSEEK_KEY),
            "ollama_available":ollama_up(),
            "dispatcher":"running" if _dispatcher_running else "stopped",
            "tasks_in_pool":len(task_pool),
            "tasks_pending":len([t for t in task_pool.values() if t.get("status")=="pending"]),
            "tasks_running":len([t for t in task_pool.values() if t.get("status") in ("running","assigned")])}

# ══════════════════════════════════════════════════════════════
# TASK DISPATCH
# ══════════════════════════════════════════════════════════════
@app.post("/tasks/dispatch")
def dispatch_task(req: DispatchReq):
    task_id = gen_task_id()
    tr = TASK_REVENUE.get(req.task_type, {"revenue":0.50,"cost":0.003,"risk":1})
    model_sel = select_model(req.priority, req.risk_level, req.estimated_cost_usd or tr["cost"])

    # Decompose with DeepSeek if prompt given
    decomposed = None
    if req.prompt and len(req.prompt) > 10:
        ds_resp = call_deepseek(f"Analyze this task and provide execution plan in 2-3 bullet points:\n{req.prompt}")
        decomposed = ds_resp.get("text")

    task = {
        "task_id": task_id,
        "task_type": req.task_type,
        "prompt": req.prompt,
        "priority": req.priority,
        "risk_level": req.risk_level,
        "target_worker": req.target_worker,
        "assigned_worker": None,
        "status": "pending",
        "model": model_sel["model"],
        "estimated_revenue_usd": req.estimated_revenue_usd or tr["revenue"],
        "estimated_cost_usd": req.estimated_cost_usd or tr["cost"],
        "actual_revenue_usd": 0,
        "actual_cost_usd": 0,
        "actual_profit_usd": 0,
        "max_cost_usd": req.max_cost_usd,
        "circuit_breaker": model_sel.get("cb", False),
        "decomposed_plan": decomposed,
        "submitted_by": req.submitted_by,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "logs": [],
    }
    task_pool[task_id] = task
    task_queue.append(task_id)
    append_log("dispatch", {"event":"dispatched","task_id":task_id,"type":req.task_type})
    return {"ok":True,"task_id":task_id,"status":"pending","model":model_sel["model"],
            "decomposed_plan":decomposed,"estimated_profit":task["estimated_revenue_usd"]-task["estimated_cost_usd"]}

@app.get("/tasks/status/{task_id}")
def task_status(task_id: str):
    t = task_pool.get(task_id)
    if not t: raise HTTPException(404, "Task not found")
    return t

@app.get("/tasks/queue")
def get_queue(status: str = None, worker_id: str = None, limit: int = 50):
    tasks = list(task_pool.values())
    if status: tasks = [t for t in tasks if t.get("status") == status]
    if worker_id: tasks = [t for t in tasks if t.get("assigned_worker") == worker_id or t.get("target_worker") == worker_id]
    tasks.sort(key=lambda t: task_score(t), reverse=True)
    return {"tasks": tasks[:limit], "total": len(task_pool),
            "by_status": {
                "pending":   len([t for t in task_pool.values() if t.get("status")=="pending"]),
                "assigned":  len([t for t in task_pool.values() if t.get("status")=="assigned"]),
                "running":   len([t for t in task_pool.values() if t.get("status")=="running"]),
                "done":      len([t for t in task_pool.values() if t.get("status")=="done"]),
                "failed":    len([t for t in task_pool.values() if t.get("status")=="failed"]),
                "cancelled": len([t for t in task_pool.values() if t.get("status")=="cancelled"]),
                "awaiting_approval": len([t for t in task_pool.values() if t.get("status")=="awaiting_approval"]),
            }}

@app.post("/tasks/cancel/{task_id}")
def cancel_task(task_id: str):
    t = task_pool.get(task_id)
    if not t: raise HTTPException(404, "Task not found")
    if t["status"] in ("done","failed"): raise HTTPException(400, "Cannot cancel completed task")
    t["status"] = "cancelled"
    t["updated_at"] = datetime.utcnow().isoformat() + "Z"
    if task_id in task_queue: task_queue.remove(task_id)
    return {"ok":True,"task_id":task_id,"status":"cancelled"}

@app.get("/tasks/next/{worker_id}")
def get_next_task(worker_id: str):
    """Worker agent polls this to get its next task."""
    for tid in task_queue:
        t = task_pool.get(tid, {})
        if t.get("status") == "assigned" and t.get("assigned_worker") == worker_id:
            t["status"] = "running"
            t["started_at"] = datetime.utcnow().isoformat() + "Z"
            return t
    return {"task_id": None}

@app.post("/task/complete")
def task_complete(req: TaskComplete):
    task_id = req.task_id or gen_task_id()
    profit = round(req.revenue_usd - req.cost_usd, 6)
    # Update pool
    if task_id in task_pool:
        t = task_pool[task_id]
        t["status"] = req.status
        t["actual_revenue_usd"] = req.revenue_usd
        t["actual_cost_usd"]    = req.cost_usd
        t["actual_profit_usd"]  = profit
        t["duration_ms"]        = req.duration_ms
        t["completed_at"]       = datetime.utcnow().isoformat() + "Z"
        t["updated_at"]         = datetime.utcnow().isoformat() + "Z"
        if req.logs: t["logs"].append(req.logs)
        if task_id in task_queue: task_queue.remove(task_id)
    entry = {"task_id":task_id,"worker_id":req.worker_id,"task_type":req.task_type,
             "model_used":req.model_used,"status":req.status,
             "revenue_usd":req.revenue_usd,"cost_usd":req.cost_usd,"profit_usd":profit,
             "duration_ms":req.duration_ms}
    append_log("tasks",   entry)
    append_log("revenue", {"task_id":task_id,"worker_id":req.worker_id,
                            "revenue_usd":req.revenue_usd,"cost_usd":req.cost_usd,"profit_usd":profit})
    return {"ok":True,"task_id":task_id,"profit_usd":profit}

# ══════════════════════════════════════════════════════════════
# TASK POOL
# ══════════════════════════════════════════════════════════════
@app.post("/tasks/pool/add")
def pool_add(req: PoolAddReq):
    task_id = gen_task_id()
    tr = TASK_REVENUE.get(req.task_type, {"revenue":0.50,"cost":0.003,"risk":1})
    task = {
        "task_id": task_id,
        "task_type": req.task_type,
        "prompt": req.prompt,
        "priority": req.priority,
        "risk_level": req.risk_level,
        "target_worker": req.target_worker,
        "assigned_worker": None,
        "status": "pending",
        "model": DEFAULT_MODEL,
        "estimated_revenue_usd": req.estimated_revenue_usd or tr["revenue"],
        "estimated_cost_usd":    req.estimated_cost_usd    or tr["cost"],
        "actual_revenue_usd": 0, "actual_cost_usd": 0, "actual_profit_usd": 0,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "logs": [],
    }
    task_pool[task_id] = task
    task_queue.append(task_id)
    return {"ok":True,"task_id":task_id}

@app.post("/tasks/pool/add-batch")
def pool_add_batch(req: PoolBatchReq):
    created = []
    for item in req.tasks:
        r = pool_add(item)
        created.append(r["task_id"])
    return {"ok":True,"created":created,"count":len(created)}

@app.get("/tasks/pool")
def get_pool(status: str = None, limit: int = 100):
    tasks = list(task_pool.values())
    if status: tasks = [t for t in tasks if t.get("status") == status]
    tasks.sort(key=lambda t: task_score(t), reverse=True)
    return {"tasks": tasks[:limit], "total": len(tasks)}

@app.get("/tasks/pool/stats")
def pool_stats():
    today_tasks = read_log("tasks")
    rev  = sum(e.get("revenue_usd",0) for e in today_tasks)
    cost = sum(e.get("cost_usd",0)    for e in today_tasks)
    return {
        "total_in_pool":   len(task_pool),
        "pending":         len([t for t in task_pool.values() if t.get("status")=="pending"]),
        "assigned":        len([t for t in task_pool.values() if t.get("status")=="assigned"]),
        "running":         len([t for t in task_pool.values() if t.get("status")=="running"]),
        "done":            len([t for t in task_pool.values() if t.get("status")=="done"]),
        "failed":          len([t for t in task_pool.values() if t.get("status")=="failed"]),
        "cancelled":       len([t for t in task_pool.values() if t.get("status")=="cancelled"]),
        "awaiting_approval": len([t for t in task_pool.values() if t.get("status")=="awaiting_approval"]),
        "today_revenue_usd": round(rev, 4),
        "today_cost_usd":    round(cost, 4),
        "today_profit_usd":  round(rev-cost, 4),
        "today_completed":   len([e for e in today_tasks if e.get("status")=="success"]),
        "worker_utilization": {
            wid: len([t for t in task_pool.values()
                      if t.get("assigned_worker")==wid and t.get("status") in ("running","assigned")])
            for wid in WORKER_REGISTRY
        }
    }

# ══════════════════════════════════════════════════════════════
# CHAT / ROUTE (kept for compatibility)
# ══════════════════════════════════════════════════════════════
@app.post("/route")
def route(req: ChatReq):
    c = est_cost(DEFAULT_MODEL, req.estimated_tokens)
    sel = select_model(req.priority, req.risk_level, c)
    task_id = gen_task_id()
    cost = est_cost(sel["model"], req.estimated_tokens)
    return {"task_id":task_id,"selected_model":sel["model"],"estimated_cost_usd":cost,
            "reason":sel["reason"],"circuit_breaker":sel.get("cb",False),"worker_id":req.worker_id}

@app.post("/chat")
def chat(req: ChatReq):
    t0 = time.time()
    r = route(req)
    resp = call_deepseek(req.prompt)
    dur = int((time.time()-t0)*1000)
    return {"route":r,"response":resp,"duration_ms":dur}

# ══════════════════════════════════════════════════════════════
# WORKERS
# ══════════════════════════════════════════════════════════════
@app.post("/worker/heartbeat")
def heartbeat(req: WorkerHB):
    worker_hb[req.worker_id] = {**req.dict(), "ts": datetime.utcnow().isoformat()+"Z"}
    append_log("workers", req.dict())
    return {"ok":True}

@app.get("/workers/status")
def workers_status():
    today = read_log("tasks")
    result = []
    for wid, info in WORKER_REGISTRY.items():
        wt   = [t for t in today if t.get("worker_id")==wid]
        rev  = sum(t.get("revenue_usd",0) for t in wt)
        cost = sum(t.get("cost_usd",0)    for t in wt)
        hb   = worker_hb.get(wid, {})
        active = len([t for t in task_pool.values()
                     if t.get("assigned_worker")==wid and t.get("status") in ("running","assigned")])
        result.append({
            "worker_id":wid,"ip":info["ip"],"role":info["role"],"os":info["os"],
            "status":"online" if wid != "hetzner-1" else "retiring",
            "cpu":hb.get("cpu",0),"memory":hb.get("memory",0),"disk":hb.get("disk",0),
            "docker":hb.get("docker",True),"ollama":hb.get("ollama",wid=="aika-1"),
            "tasks_today":len(wt),"success_today":sum(1 for t in wt if t.get("status")=="success"),
            "failed_today": sum(1 for t in wt if t.get("status")=="failed"),
            "revenue_today":round(rev,4),"cost_today":round(cost,4),"profit_today":round(rev-cost,4),
            "active_tasks":active,"max_concurrent":info["max_concurrent"],
            "last_heartbeat":hb.get("ts","never"),
        })
    return {"workers":result,"ts":datetime.utcnow().isoformat()+"Z"}

@app.get("/workers/metrics")
def workers_metrics():
    ws = workers_status()["workers"]
    return {"total_workers":len(ws),"online":sum(1 for w in ws if w["status"]=="online"),
            "total_tasks_today":sum(w["tasks_today"] for w in ws),
            "total_revenue_today":round(sum(w["revenue_today"] for w in ws),4),
            "total_cost_today":   round(sum(w["cost_today"]    for w in ws),4),
            "total_profit_today": round(sum(w["profit_today"]  for w in ws),4),
            "most_profitable":    max(ws, key=lambda w: w["profit_today"])["worker_id"] if ws else None,
            "ts":datetime.utcnow().isoformat()+"Z"}

# ══════════════════════════════════════════════════════════════
# P&L
# ══════════════════════════════════════════════════════════════
@app.get("/revenue/status")
def revenue_status():
    entries = read_log("revenue")
    rev  = sum(e.get("revenue_usd",0) for e in entries)
    cost = sum(e.get("cost_usd",0)    for e in entries)
    p    = rev - cost
    return {"today_revenue_usd":round(rev,4),"today_cost_usd":round(cost,4),
            "today_profit_usd":round(p,4),"margin":round(p/rev,4) if rev>0 else 0,
            "task_count":len(entries),"ts":datetime.utcnow().isoformat()+"Z"}

@app.get("/profit/status")
def profit_status(): return revenue_status()

@app.get("/cost/status")
def cost_status():
    cb = read_log("circuit-breaker")
    return {"claude_hourly_usd":round(claude_hourly(),4),"claude_daily_usd":round(claude_daily(),4),
            "hourly_limit":LIMITS["claude_hourly"],"daily_limit":LIMITS["claude_daily"],
            "claude_available":claude_ok(),"default_model":DEFAULT_MODEL,
            "ollama_available":ollama_up(),"circuit_breaker_today":len(cb),
            "last_cb_event":cb[-1] if cb else None}

@app.get("/models/status")
def models_status():
    return {"default_model":DEFAULT_MODEL,"fallback":"ollama-qwen2.5-7b",
            "models":{
                "claude-sonnet-4-6":  {"available":claude_ok(),"role":"p0p1_risk4_only","hourly_used":round(claude_hourly(),4)},
                "deepseek-v4-flash":  {"available":bool(DEEPSEEK_KEY),"role":"default_85pct"},
                "ollama-qwen2.5-7b":  {"available":ollama_up(),"role":"local_fallback","url":OLLAMA_URL},
            }}

@app.get("/tasks/history")
def task_history(worker_id: str = None, limit: int = 50):
    entries = read_log("tasks")
    if worker_id: entries = [e for e in entries if e.get("worker_id")==worker_id]
    return {"tasks":entries[-limit:],"total":len(entries)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
