"""
GOAA.AI Model Router + Task Dispatch API v3.0
Phase 3: Real Task Scheduling Engine
"""
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import requests, json, os, time, platform, uuid, threading, asyncio, logging
import uuid
from db import init_pool, _exec, task_upsert, task_stats, task_worker_stats, task_rebuild_pool, session_ensure, message_insert, messages_get, session_create, sessions_list, task_get_session_message, tool_invocation_insert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenClaw.Router")

app = FastAPI(title="GOAA Task Router v3", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Paths ──────────────────────────────────────────────────────
BASE = "/opt/goaa" if platform.system() != "Windows" else r"C:\opt\goaa"
import sys
sys.path.insert(0, os.path.join(BASE, "services/rag"))
from f_lite_redact import f_lite_sanitize
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
    "do-cloud-2": {"ip":"143.198.224.71","role":"cloud_worker","os":"Ubuntu 24.04","max_concurrent":5},
    "do-cloud-3": {"ip":"64.23.166.121","role":"cloud_worker","os":"Ubuntu 24.04","max_concurrent":5},
    "aika-core-01": {"ip":"100.114.37.90","lan_ip":"192.168.1.24","tailscale_ip":"100.114.37.90","role":"aika-box-pro-alpha","os":"Ubuntu 26.04","max_concurrent":5}
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

def call_deepseek(prompt="", messages=None, model="deepseek-chat", tools=None, tool_choice=None):
    """Phase 4: 支援 multi-turn messages + usage tracking
    向後兼容: 沒傳 messages 時用 prompt 構造單輪
    """
    if not DEEPSEEK_KEY:
        return {"text":f"[Mock-DeepSeek] {prompt[:80]}","model":"deepseek-v4-flash","mock":True,"usage":{}}
    
    # 構造 messages
    if messages is None or len(messages) == 0:
        messages = [{"role":"user","content":prompt}]
    
    try:
        import requests
        _body = {"model": model or "deepseek-chat", "messages": messages, "stream": False}
        if tools:
            _body["tools"] = tools
            _body["tool_choice"] = tool_choice or "auto"
        r = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json"
            },
            json=_body,
            timeout=60
        )
        if r.status_code != 200:
            return {"text":f"[DeepSeek HTTP {r.status_code}] {r.text[:200]}","model":"deepseek-v4-flash","mock":False,"error":True,"usage":{}}
        
        j = r.json()
        choice = j.get("choices", [{}])[0]
        msg = choice.get("message", {})
        text = msg.get("content", "")
        usage = j.get("usage", {})
        
        return {
            "text": text,
            "model": j.get("model", "deepseek-v4-flash"),
            "mock": False,
            "usage": {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "finish_reason": choice.get("finish_reason", ""),
            "tool_calls": msg.get("tool_calls"),
        }
    except requests.exceptions.Timeout:
        return {"text":"[DeepSeek timeout]","model":"deepseek-v4-flash","mock":False,"error":True,"usage":{}}
    except Exception as e:
        return {"text":f"[DeepSeek error: {type(e).__name__}: {e}]","model":"deepseek-v4-flash","mock":False,"error":True,"usage":{}}

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
                    try:
                        task_upsert(tid, task)
                    except Exception as e:
                        logger.error(f"[dispatcher] PG persist awaiting_approval failed tid={tid}: {e}")
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
    # Phase 4: PG init + rebuild incomplete tasks
    if init_pool():
        incomplete = task_rebuild_pool()
        for t in incomplete:
            tid = t["task_id"]
            task_pool[tid] = {
                "task_id":tid,
                "task_type":t.get("task_type","ops"), "worker_id":t.get("worker_id"),
                "status":t.get("status","pending"), "payload":t.get("payload",{}),
                "priority":t.get("priority",5),
                "created_at":str(t.get("created_at","")),
            }
            if t["status"] == "pending":
                task_queue.append(tid)
        logger.info("Rebuilt %d tasks from PG", len(incomplete))

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
    # P1.2.1 v2: 新增 session_id / message_id Optional 欄位 (規範 #25 跨層型別)
    # 規範 #18: Optional 保持向後相容, 舊呼叫方仍 work (走 hook 內 fallback)
    session_id: Optional[str] = None
    message_id: Optional[str] = None
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


class ApproveReq(BaseModel):
    task_id: str
    approved_by: str
    note: str = Field(default="", max_length=2000)

class WorkerHB(BaseModel):
    worker_id: str
    cpu: float = 0.0
    memory: float = 0.0
    disk: float = 0.0
    docker: bool = False
    ollama: bool = False
    status: str = "online"

class ChatReq(BaseModel):
    prompt: str = ""
    messages: list = []  # Phase 4: multi-turn support
    session_id: str = ""  # Phase 4: session tracking
    model: str = ""  # Phase 4: model override (空字串=用默認)
    priority: int = 2
    risk_level: int = 1
    worker_id: str = "aika-1"
    estimated_tokens: int = 1000
    enable_tools: bool = False  # Phase 4 V4.0: 啟用工具調用

# ══════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════


class WorkerRegisterReq(BaseModel):
    """V4.6 動態註冊 payload"""
    worker_id: str
    ip_address: Optional[str] = None
    tailscale_ip: Optional[str] = None
    hostname: Optional[str] = None
    node_type: Optional[str] = "aika-box-pro"
    os_info: Optional[Dict[str, Any]] = None
    ollama_enabled: Optional[bool] = False
    ollama_model: Optional[str] = None

    class Config:
        extra = "allow"


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

    # === P1.2.0 hook 1: PG 持久化 (規範 #36 v2 Runtime Truth) ===
    try:
        # P1.2.1 v2 hook: propagate session_id/message_id to tasks.payload
        # 規範 #11 only-add: 純新增 payload 鍵, 不動既有邏輯
        # 規範 #14 v2 + #36 v2: 真實 session_id 經 dispatch chain 傳入 task['payload']
        # 規範 #18: req.session_id 為 None 時, payload 缺對應鍵, hook 走 uuid5 fallback (向後相容)
        _p121v2_existing = task.get('payload', {}) if isinstance(task.get('payload'), dict) else {}
        task['payload'] = {
            **_p121v2_existing,  # 保留原有 payload 內容 (規範 #11)
            'context': req.context or {},  # 規範 #25 顯式型別
            'session_id': req.session_id,  # 規範 #25 顯式 Optional[str]
            'message_id': req.message_id,  # 規範 #25 顯式 Optional[str]
        }
        # P1.2.1 v2 hook END

        task_upsert(task_id, task)  # P1.2.0: PG dispatch persist
    except Exception as _p120_e:
        logging.exception(f"P1.2.0 hook 1 (dispatch) task_upsert failed: {_p120_e}")
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
    task_upsert(task_id, t)  # Phase 4: PG persist
    if task_id in task_queue: task_queue.remove(task_id)
    return {"ok":True,"task_id":task_id,"status":"cancelled"}


@app.post("/task/approve")
def task_approve(req: ApproveReq):
    """
    F-lite 2a: awaiting_approval -> approved + audit + note redaction.
    本刀不做：assigned / requeue / resume / 持久化 / reject。
    approved status is recorded; automatic resume depends on dispatcher
    support and is NOT guaranteed in this slice. Resume/requeue is next slice.
    task_pool is in-memory; status change is lost on process restart.
    approved_by is caller-provided; authenticated identity binding is future slice.
    """
    task = task_pool.get(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.get("status") != "awaiting_approval":
        raise HTTPException(status_code=400, detail=f"Task not awaiting approval (current: {task.get('status')})")
    safe_note = f_lite_sanitize(req.note)
    safe_actor = f_lite_sanitize(req.approved_by)
    prev = task["status"]
    try:
        task["status"] = "approved"
        _exec(
            "UPDATE tasks SET status='approved', approved_by=%s, approved_at=NOW(), approval_note=%s WHERE id=%s",
            (safe_actor, safe_note, req.task_id),
            fetch=False,
        )
        _exec(
            "INSERT INTO audit_log (action, target_type, target_id, operator, details) VALUES (%s, %s, NULL, %s, %s)",
            ("task_approve", "task", safe_actor, json.dumps({"task_id": req.task_id, "risk_level": task.get("risk_level"), "note": safe_note, "previous_status": prev, "new_status": "approved"})),
            fetch=False,
        )
    except Exception:
        task["status"] = prev
        raise
    append_log("tasks", {"event": "task_approve", "task_id": req.task_id, "new_status": "approved"})
    return {"ok": True, "task_id": req.task_id, "previous_status": prev, "new_status": "approved", "audit_written": True, "resume_behavior": "pending_dispatcher_support"}

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
        task_upsert(task_id, t)  # Phase 4: PG persist
        if req.logs: t["logs"].append(req.logs)
        if task_id in task_queue: task_queue.remove(task_id)
    entry = {"task_id":task_id,"worker_id":req.worker_id,"task_type":req.task_type,
             "model_used":req.model_used,"status":req.status,
             "revenue_usd":req.revenue_usd,"cost_usd":req.cost_usd,"profit_usd":profit,
             "duration_ms":req.duration_ms}
    append_log("tasks",   entry)
    append_log("revenue", {"task_id":task_id,"worker_id":req.worker_id,
                            "revenue_usd":req.revenue_usd,"cost_usd":req.cost_usd,"profit_usd":profit})
    # ════════════════════════════════════════════════
    # P1.2.1 hook: tool_invocations dual-write
    # 規範 #11 #18 #24 #25 #28 #36 v2 嚴守
    # ════════════════════════════════════════════════
    try:
        _P121_TOOL_IDS = ("health_check","ollama_status","docker_status",
                          "system_status","ping_test","log_summary")
        if req.task_type in _P121_TOOL_IDS:
            _p121_lookup = task_get_session_message(task_id)
            if _p121_lookup and _p121_lookup.get("session_id"):
                _p121_session_id = _p121_lookup["session_id"]
                _p121_message_id = _p121_lookup.get("message_id")
            else:
                import uuid as _p121_uuid
                _p121_session_id = str(_p121_uuid.uuid5(
                    _p121_uuid.NAMESPACE_DNS,
                    f"p121-fallback:{task_id}",
                ))
                _p121_message_id = None
            _p121_inv_id = tool_invocation_insert(
                message_id=_p121_message_id,
                session_id=_p121_session_id,
                tool_id=req.task_type,
                tool_call_id=f"{task_id}::001",
                args={"task_type": req.task_type},
            )
            if _p121_inv_id:
                logging.getLogger(__name__).info(
                    f"P1.2.1 hook: inv_id={_p121_inv_id[:12]} "
                    f"tool={req.task_type} task={task_id[:16]}"
                )
    except Exception as _p121_e:
        logging.getLogger(__name__).exception(
            f"P1.2.1 hook FAILED for task_id={task_id}: {_p121_e}"
        )
    # P1.2.1 hook END
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
    task_upsert(task_id, task)  # Phase 4: PG persist
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
    """Phase 4: multi-turn ChatOps + PG persistence (跨裝置同步)"""
    t0 = time.time()
    r = route(req)
    
    # session_id 自動生成: string → UUID5 (確定性) 或全新 UUID
    raw_sid = req.session_id or str(uuid.uuid4())
    try:
        sid = str(uuid.UUID(raw_sid))  # 已是合法 UUID
    except ValueError:
        # string ID 透過 UUID5 轉為確定性 UUID
        sid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"goaa-chat-{raw_sid}"))
    
    # 從 PG 拉歷史 messages (如有 session_id)
    history = []
    if req.session_id:
        history_rows = messages_get(sid, limit=20)
        for h in history_rows:
            # V4.0.5.1: 過濾 tool/assistant-tool_calls 訊息 (PG schema 沒存 tool_call_id, 重建會被 DeepSeek 拒)
            # 規範 #25 跨層型別: V4.1 PG migration 時根治, 現在先繞
            _role = h["role"]
            _content = h.get("content")
            if _role == "tool":
                continue  # 缺 tool_call_id, 無法重建
            if _role == "assistant" and (_content is None or _content == "" or _content == "null"):
                continue  # 缺 tool_calls 結構, 無法重建
            history.append({"role": _role, "content": _content})
    
    # 構造完整 messages
    if req.messages and len(req.messages) > 0:
        # 客戶端傳了 messages, 直接用 (前端可選擇是否帶 history)
        msgs = list(req.messages)
        # 確保最後一條是 user
        if req.prompt and (not msgs or msgs[-1].get("role") != "user"):
            msgs.append({"role": "user", "content": req.prompt})
    elif req.prompt:
        # 自動 prepend 歷史
        msgs = history + [{"role": "user", "content": req.prompt}]
    else:
        return {"error": "prompt or messages required", "ok": False}
    
    # 取得最後一條 user message (用於寫 PG)
    last_user_msg = ""
    for m in reversed(msgs):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break
    
    # ===== Phase 4 V4.0: tools 邏輯 =====
    # 規範 #11: enable_tools=False (預設) 走 V3.0 100% 老路
    tools = None
    tool_msgs_for_pg = []
    if req.enable_tools:
        tools = [{
            "type": "function",
            "function": {
                "name": "task_status",
                "description": "查詢 GOAA 最近任務的狀態, 含任務 ID/類型/狀態/收益",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "返回幾個任務, 預設 5", "default": 5}
                    }
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "tasks_by_type",
                "description": "查詢 GOAA 特定類型的最近任務, 例如 health_check / ollama_status / docker_status 等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_type": {"type": "string", "description": "任務類型, 如 health_check, ollama_status, docker_status, system_status, ping_test, log_summary, chat, ops, report, planning, code_review, security_scan"},
                        "limit": {"type": "integer", "description": "返回幾個任務, 預設 5, 最大 50", "default": 5}
                    },
                    "required": ["task_type"]
                }
            }
        }]
    
    # Round 1: 調用 LLM
    resp = call_deepseek(prompt=req.prompt, messages=msgs, model=req.model, tools=tools)
    
    # 若 LLM 想用工具 → 執行 + Round 2
    tool_calls = resp.get("tool_calls") if isinstance(resp, dict) else None
    if req.enable_tools and tool_calls:
        tool_msgs = []
        for tc in tool_calls:
            fn_name = tc.get("function", {}).get("name", "")
            args_str = tc.get("function", {}).get("arguments", "{}")
            try:
                args = json.loads(args_str) if isinstance(args_str, str) else (args_str or {})
            except Exception:
                args = {}
            
            # 執行工具 (DO 本機, 規範 #30 階段 0)
            if fn_name == "task_status":
                _limit = max(1, min(int(args.get("limit", 5)), 50))
                try:
                    _rows = _exec(
                        "SELECT id, task_type, status, worker_id, "
                        "(COALESCE(revenue_usd,0) - COALESCE(cost_usd,0)) AS profit, "
                        "duration_ms, created_at "
                        "FROM tasks ORDER BY created_at DESC LIMIT %s",
                        (_limit,)
                    )
                    if _rows is False or _rows is None:
                        result = json.dumps({"error": "task query returned no result (PG pool may be unavailable)"})
                    else:
                        result = json.dumps({"tasks": _rows, "count": len(_rows)}, default=str, ensure_ascii=False)
                except Exception as e:
                    result = json.dumps({"error": f"task_status failed: {type(e).__name__}: {e}"})
            elif fn_name == "tasks_by_type":
                # V4.0.5: 按類型查最近任務 (規範 #28 白名單)
                _ALLOWED_TYPES = {"health_check", "ollama_status", "docker_status", "system_status", "ping_test", "log_summary", "chat", "ops", "report", "planning", "code_review", "security_scan"}
                _task_type = str(args.get("task_type", "")).strip().lower()
                _limit = max(1, min(int(args.get("limit", 5)), 50))
                if not _task_type:
                    result = json.dumps({"error": "tasks_by_type: missing required parameter 'task_type'"})
                elif _task_type not in _ALLOWED_TYPES:
                    result = json.dumps({"error": f"tasks_by_type: unknown task_type '{_task_type}'. Allowed: {sorted(_ALLOWED_TYPES)}"})
                else:
                    try:
                        _rows = _exec(
                            "SELECT id, task_type, status, worker_id, "
                            "(COALESCE(revenue_usd,0) - COALESCE(cost_usd,0)) AS profit, "
                            "duration_ms, created_at "
                            "FROM tasks WHERE task_type = %s ORDER BY created_at DESC LIMIT %s",
                            (_task_type, _limit)
                        )
                        if _rows is False or _rows is None:
                            result = json.dumps({"error": f"tasks_by_type returned no result for type '{_task_type}' (PG pool may be unavailable)"})
                        else:
                            result = json.dumps({"task_type": _task_type, "tasks": _rows, "count": len(_rows)}, default=str, ensure_ascii=False)
                    except Exception as e:
                        result = json.dumps({"error": f"tasks_by_type failed: {type(e).__name__}: {e}"})
            else:
                result = json.dumps({"error": f"unknown tool: {fn_name}"})
            
            tool_msgs.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result
            })
        
        # Round 2: 把工具結果送回 LLM 整合成自然語言
        msgs2 = msgs + [{"role": "assistant", "content": None, "tool_calls": tool_calls}] + tool_msgs
        resp = call_deepseek(prompt=req.prompt, messages=msgs2, model=req.model)
        tool_msgs_for_pg = tool_msgs
    # ===== Phase 4 V4.0 邏輯結束 =====
    
    dur = int((time.time()-t0)*1000)
    
    # 寫 messages 表 (失敗不影響 chat)
    usage = resp.get("usage", {})
    # V4.0: 寫 tool messages (規範 #11 PG schema role 無 CHECK)
    for tm in tool_msgs_for_pg:
        try:
            message_insert(sid, "tool", tm.get("content", ""),
                           model=resp.get("model"))
        except Exception:
            pass  # 規範 #28: 不阻塞 chat, 但記錄
    if last_user_msg:
        message_insert(sid, "user", last_user_msg,
                       model=resp.get("model"),
                       tokens_in=usage.get("input_tokens", 0))
    if resp.get("text") and not resp.get("error"):
        message_insert(sid, "assistant", resp.get("text", ""),
                       model=resp.get("model"),
                       tokens_in=usage.get("input_tokens", 0),
                       tokens_out=usage.get("output_tokens", 0))
    
    return {
        "route": r,
        "response": resp,
        "duration_ms": dur,
        "session_id": sid,  # 客戶端記下這個用於後續對話
        "history_count": len(history),
        "ok": not resp.get("error", False),
    }

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
            "worker_id":wid,"ip":info["ip"],"tailscale_ip":info.get("tailscale_ip"),"role":info["role"],"os":info["os"],
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



@app.post("/workers/register")
def workers_register(req: WorkerRegisterReq):
    """
    V4.6 動態註冊: AiKa-Box 啟動時 POST 自己的資訊到 router.
    對齊師兄揭露: Tailscale IP 是 AiKa-Box 第一公民 (印在包裝上).
    
    規範 #28 反模式: 獨立 try/except.
    規範 #11 v3: nodes 表 schema only-add (含 tailscale_ip INET).
    規範 #24 接口契約: with _exec() as cur.
    """
    if not req.worker_id or len(req.worker_id) < 3:
        raise HTTPException(400, "worker_id must be >= 3 chars")
    
    is_new = False
    node_uuid = None
    
    try:
        # 1. 看 worker_id 是否已存在
        rows = _exec("SELECT id FROM nodes WHERE worker_id = %s", (req.worker_id,))
        existing = rows[0] if rows else None
        if existing:
            node_uuid = str(existing["id"])
            _exec(
                """
                UPDATE nodes SET
                    tailscale_ip = COALESCE(%s::inet, tailscale_ip),
                    ip_address = COALESCE(%s::inet, ip_address),
                    os_info = COALESCE(%s::jsonb, os_info),
                    node_type = COALESCE(%s, node_type),
                    is_active = TRUE,
                    updated_at = NOW()
                WHERE worker_id = %s
                """,
                (req.tailscale_ip, req.ip_address or req.tailscale_ip,
                 json.dumps(req.os_info) if req.os_info else None,
                 req.node_type, req.worker_id),
                fetch=False
            )
        else:
            is_new = True
            result = _exec(
                """
                INSERT INTO nodes (
                    worker_id, tailscale_ip, ip_address, os_info,
                    node_type, is_active, created_at, updated_at
                ) VALUES (
                    %s, %s::inet, %s::inet, %s::jsonb,
                    %s, TRUE, NOW(), NOW()
                ) RETURNING id
                """,
                (req.worker_id, req.tailscale_ip,
                 req.ip_address or req.tailscale_ip,
                 json.dumps(req.os_info) if req.os_info else "{}",
                 req.node_type or "aika-box-pro")
            )
            node_uuid = str(result[0]["id"]) if result else None
    except Exception as e:
        raise HTTPException(500, f"DB error: {type(e).__name__}: {str(e)[:200]}")
    
    return {
        "success": True,
        "worker_id": req.worker_id,
        "node_uuid": node_uuid,
        "is_new": is_new,
        "message": f"Worker {req.worker_id} {'registered' if is_new else 'updated'}",
        "timestamp": datetime.utcnow().isoformat() + "Z" if 'datetime' in globals() else None
    }


@app.get("/workers/register/{worker_id}")
def workers_register_status(worker_id: str):
    """V4.6 看 worker 註冊狀態 (debug 用)"""
    try:
        rows = _exec(
            """
            SELECT id, worker_id, tailscale_ip, ip_address,
                   node_type, os_info, is_active,
                   created_at, updated_at
            FROM nodes WHERE worker_id = %s
            """,
            (worker_id,)
        )
        if not rows:
            raise HTTPException(404, f"Worker {worker_id} not registered")
        row = rows[0]
        return {
            "id": str(row["id"]),
            "worker_id": row["worker_id"],
            "tailscale_ip": str(row["tailscale_ip"]) if row["tailscale_ip"] else None,
            "ip_address": str(row["ip_address"]) if row["ip_address"] else None,
            "node_type": row["node_type"],
            "os_info": row["os_info"],
            "is_active": row["is_active"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"DB error: {type(e).__name__}: {str(e)[:200]}")


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


@app.get("/sessions/{sid}/messages")
def get_session_messages(sid: str, limit: int = 50):
    """Phase 4: 拉 session 的對話歷史"""
    msgs = messages_get(sid, limit=limit)
    return {"session_id": sid, "messages": msgs, "count": len(msgs)}

@app.get("/sessions")
def list_sessions(project_id: str = "", limit: int = 50):
    """Phase 4: 列出所有 sessions"""
    sessions = sessions_list(project_id=project_id or None, limit=limit)
    return {"sessions": sessions, "count": len(sessions)}

@app.post("/sessions/new")
def new_session(req: dict = None):
    """Phase 4: 創建新 session"""
    req = req or {}
    title = req.get("title", "Untitled")
    project_id = req.get("project_id")
    sid = session_create(title=title, project_id=project_id)
    if sid:
        return {"session_id": sid, "title": title, "ok": True}
    return {"error": "Failed to create session", "ok": False}
