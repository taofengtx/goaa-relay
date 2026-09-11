#!/usr/bin/env python3
"""
GOAA Local Runtime Console — main.py (V5.2.C-2 第一版骨架)
部署: /opt/goaa/local-console/main.py
綁定: 127.0.0.1:5188(不開公網)

安全邊界(對齊設計文檔):
  - 不返 secret / corpus 正文
  - 不讀/dump worker_secrets.env;secret 由進程環境注入(Tao 親手 source)
  - 不開危險 shell;/tasks/run 第一版只 allowlist(本骨架先不實作 run,只展示 results)
  - 密碼框第一版 mock / placeholder
  - 與 Worker 解耦:import worker 能力函數(topk_query),不重寫檢索邏輯

啟動(跑時碰 PG,需 Tao 親手 source secrets):
  set -a; . /etc/goaa/worker_secrets.env; set +a
  /opt/goaa/venv/bin/uvicorn main:app --host 127.0.0.1 --port 5188
"""

import os
import sys
import json
import uuid
import socket
import glob
import logging
import datetime

from fastapi import FastAPI, Request, Response, Cookie, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

# ── P1-T2-U3/P1-T2-U4: Intent Detector + Task Envelope ──
from intent_detector import detect_intent_from_message, build_envelope_from_detection, IntentDetectionResult
from task_envelope import TaskIntent, TaskEnvelope
# ── P4-T2/P4-T3/P4-T5: Task Gateway Data Models + Audit/Evidence ──
from task_gateway import (
    ExecutionMode,
    ApprovalState,
    Decision,
    TaskRiskLevel,
    TaskRunRequest,
    TaskRunResult,
    AuditLog,
    GatewayEvidencePackage,
    build_task_run_request,
    build_blocked_result,
    get_default_execution_mode,
    get_default_approval_state,
    is_effectively_blocked,
    # ── P5-T2/P5-T4: Execution Plan & Risk Classification Models ──
    RunnerTarget,
    ExecutionPlan,
    DryRunResult,
    TaskRiskClassification,
    classify_task_intent,
)
# ────────────────────────────────────────────────────────

sys.path.insert(0, "/opt/goaa/workers")  # 共用 worker 能力函數
sys.path.insert(0, os.path.dirname(__file__))  # 共用 auth 模組

import auth  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("local-console")

app = FastAPI(title="GOAA Local Runtime Console", version="5.2.C-2")

TASK_RESULTS_DIR = "/opt/goaa/task_results"
LOGS_DIR = "/opt/goaa/logs"
WORKER_ID = socket.gethostname()

# 第一版三角色 mock(設計文檔:login mock,密碼框 placeholder)
MOCK_ROLES = ["admin", "provider", "viewer"]

COOKIE_NAME = "goaa_console_session"


# ── 認證 helper ──
def _current_user(session_cookie):
    """從 cookie 取當前用戶;無效回 None。"""
    if not session_cookie:
        return None
    return auth.verify_session(session_cookie)


def _require_auth(session_cookie):
    """要求已登入,否則 401。回 {u, r}。"""
    u = _current_user(session_cookie)
    if not u:
        raise HTTPException(status_code=401, detail="authentication required")
    return u


def _require_role(session_cookie, *roles):
    """要求特定角色,否則 403。"""
    u = _require_auth(session_cookie)
    if u["r"] not in roles:
        raise HTTPException(status_code=403, detail="insufficient role")
    return u


@app.get("/login", response_class=HTMLResponse)
def login_page():
    """網頁登入表單。POST 到 /login API,成功後跳轉首頁。"""
    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GOAA Console — Login</title>
<style>
:root{--bg:#05080C;--panel:rgba(12,20,28,.86);--accent:#00C8FF;--success:#22C55E;
--danger:#EF4444;--txt:#F5F5F5;--txt2:#A1A1AA;--border:rgba(0,200,255,.25);
--mono:'JetBrains Mono','SF Mono',Menlo,monospace;--ui:Inter,system-ui,sans-serif;}
*{box-sizing:border-box}
body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;
background:radial-gradient(circle at 50% 0%,#0A0F14 0%,#05080C 70%);color:var(--txt);
font-family:var(--ui);overflow:hidden}
body::before{content:"";position:fixed;inset:0;background:
linear-gradient(rgba(0,200,255,.03) 1px,transparent 1px) 0 0/100% 3px;pointer-events:none}
.card{background:var(--panel);padding:2.5rem 2.2rem;border-radius:14px;width:330px;
border:1px solid var(--border);box-shadow:0 0 40px rgba(0,200,255,.08),inset 0 1px 0 rgba(255,255,255,.04);
backdrop-filter:blur(12px);position:relative;animation:rise .5s ease both}
@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.logo{font-family:var(--mono);font-size:.7rem;letter-spacing:.25em;color:var(--accent);
text-transform:uppercase;margin-bottom:1rem;opacity:.8}
h1{font-size:1.35rem;margin:0 0 .3rem;font-weight:600;letter-spacing:.01em}
.sub{color:var(--txt2);font-size:.82rem;margin:0 0 1.6rem;font-family:var(--mono)}
input{width:100%;padding:.7rem .85rem;margin:.35rem 0;background:#070B10;
border:1px solid var(--border);border-radius:8px;color:var(--txt);font-family:var(--mono);
font-size:.9rem;transition:border-color .2s,box-shadow .2s}
input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(0,200,255,.12)}
input::placeholder{color:#4a5560}
button{width:100%;padding:.75rem;margin-top:1.2rem;background:linear-gradient(135deg,var(--accent),#0095CC);
border:none;border-radius:8px;color:#04121A;font-size:.95rem;font-weight:700;cursor:pointer;
font-family:var(--mono);letter-spacing:.05em;transition:transform .15s,box-shadow .2s}
button:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(0,200,255,.3)}
#msg{color:var(--danger);font-size:.82rem;min-height:1.2rem;margin:.7rem 0 0;font-family:var(--mono)}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--success);
margin-right:.4rem;box-shadow:0 0 8px var(--success);animation:pulse 2s infinite}
@keyframes pulse{50%{opacity:.4}}
</style></head>
<body>
<div class="card">
<div class="logo">&#9670; AIKA-BOX EDGE RUNTIME</div>
<h1>GOAA Local Console</h1>
<p class="sub"><span class="dot"></span>本地主權入口 · Port 5188</p>
<input id="u" placeholder="username" autocomplete="username">
<input id="p" type="password" placeholder="password" autocomplete="current-password">
<button id="btn">登入 LOGIN</button>
<p id="msg"></p>
</div>
<script>
async function doLogin(){
  const u=document.getElementById('u').value, p=document.getElementById('p').value;
  const msg=document.getElementById('msg'); msg.textContent='';
  try{
    const r=await fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({username:u,password:p})});
    if(r.ok){ location.href='/'; }
    else{ msg.textContent='登入失敗:帳號或密碼錯誤'; }
  }catch(e){ msg.textContent='連線錯誤'; }
}
document.getElementById('btn').onclick=doLogin;
document.getElementById('p').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
</script>
</body></html>"""


@app.post("/login")
async def login(request: Request, response: Response):
    """本地登入:username+password → verify → 簽發 session cookie。"""
    body = await request.json()
    username = body.get("username", "")
    password = body.get("password", "")
    role = auth.verify_user(username, password)
    if not role:
        # 不洩漏是帳號錯還密碼錯
        return JSONResponse(status_code=401, content={"error": "invalid credentials"})
    token = auth.issue_session(username, role)
    response.set_cookie(
        key=COOKIE_NAME, value=token,
        httponly=True, samesite="strict", max_age=auth.SESSION_TTL,
        # secure=True 待 HTTPS 啟用後開(Tailscale Phase 1)
    )
    return {"authenticated": True, "role": role, "username": username}


@app.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


# ── 脫敏器(對齊 #45/log redaction:過濾 secret 模式) ──
import re
import httpx, uuid
from pydantic import BaseModel
_REDACT = re.compile(r'(?i)(password|passwd|pwd|secret|api[_\-]?key|token|DATABASE_URL|SMTP|PGPASSWORD)\s*[:=]\s*\S+')

def _redact(text: str) -> str:
    return _REDACT.sub(r'\1=[REDACTED]', text)


@app.get("/health")
def health():
    """控制台狀態,不返 secret。"""
    ollama_ok = False
    try:
        import urllib.request
        url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
        with urllib.request.urlopen(f"{url}/api/tags", timeout=3) as r:
            ollama_ok = r.status == 200
    except Exception:
        ollama_ok = False
    return {
        "status": "ok",
        "console": "GOAA Local Runtime Console",
        "version": "5.2.C-2",
        "hostname": WORKER_ID,
        "port": 5188,
        "ollama_available": ollama_ok,
    }


@app.get("/session")
def session(session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """讀真實 session cookie。"""
    u = _current_user(session_cookie)
    if not u:
        return {"authenticated": False, "role": None, "roles_available": MOCK_ROLES}
    return {"authenticated": True, "username": u["u"], "role": u["r"]}


@app.get("/rag/stats")
def rag_stats(session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """qwenpaw_memory_chunks 統計 + pgvector version。需登入。不返正文。"""
    _require_auth(session_cookie)
    try:
        from embed_worker import _pg_connect
        conn = _pg_connect()
        cur = conn.cursor()
        try:
            cur.execute("SELECT count(*), count(DISTINCT session_id) FROM qwenpaw_memory_chunks;")
            total, sessions = cur.fetchone()
            cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector';")
            row = cur.fetchone()
            pgv = row[0] if row else None
            cur.execute("SELECT min(vector_dims(embedding)), max(vector_dims(embedding)) FROM qwenpaw_memory_chunks;")
            dmin, dmax = cur.fetchone()
        finally:
            cur.close()
            conn.close()
        return {"total": total, "sessions": sessions, "pgvector_version": pgv,
                "dim_min": dmin, "dim_max": dmax}
    except Exception as e:
        log.error("rag_stats failed: %s", type(e).__name__)
        return JSONResponse(status_code=500, content={"error": type(e).__name__})


@app.post("/rag/topk")
async def rag_topk(request: Request, session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """RAG 檢索驗證。需登入。呼叫 worker 的 topk_query,不返正文。"""
    _require_auth(session_cookie)
    body = await request.json()
    query = body.get("query", "")
    top_k = int(body.get("top_k", 5))
    if not query:
        return JSONResponse(status_code=400, content={"error": "query required"})
    try:
        from topk_query import exec_topk_query_verify
        result = exec_topk_query_verify({"query_text": query, "top_k": top_k})
        return result.get("stats", {})   # 只含 metadata + distance,無正文
    except Exception as e:
        log.error("rag_topk failed: %s", type(e).__name__)
        return JSONResponse(status_code=500, content={"error": type(e).__name__})


@app.get("/tasks/results")
def tasks_results(session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """讀 task_results/ JSON 列表。需登入。不返正文/secret。"""
    _require_auth(session_cookie)
    items = []
    for p in sorted(glob.glob(os.path.join(TASK_RESULTS_DIR, "*.json")), reverse=True):
        try:
            with open(p, encoding="utf-8") as f:
                r = json.load(f)
            # 只挑安全欄位
            items.append({k: r.get(k) for k in
                          ("task_id", "task", "worker_id", "status", "processed",
                           "inserted", "failed", "duration_s", "started_at", "finished_at")})
        except Exception:
            continue
    return {"count": len(items), "results": items}


@app.get("/node/health")
def node_health(session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """本機節點健康(B 線)。需登入。只讀 telemetry cache, 不採集、不碰 secret。
    讀 /opt/goaa/run/telemetry_local.json, 算 age_sec, 判 online/stale/offline。
    cache 不存在 → unknown/offline; parse error → telemetry_error。端點不崩。"""
    _require_auth(session_cookie)
    cache_path = "/opt/goaa/run/telemetry_local.json"
    # 閾值(可配置, 非寫死規則)
    online_max = int(os.environ.get("NODE_HEALTH_ONLINE_MAX_SEC", "30"))
    stale_max = int(os.environ.get("NODE_HEALTH_STALE_MAX_SEC", "90"))
    if not os.path.exists(cache_path):
        return {"status": "offline", "reason": "no_telemetry_cache",
                "node_id": None, "age_sec": None}
    try:
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        # parse error → 標記但不崩, 不返 traceback
        return {"status": "telemetry_error", "reason": "cache_parse_error",
                "node_id": None, "age_sec": None}
    # 算 age_sec(優先用 collected_at_epoch)
    age = None
    try:
        epoch = data.get("collected_at_epoch")
        if epoch is not None:
            age = int(datetime.datetime.now().timestamp() - float(epoch))
    except Exception:
        age = None
    # stale/offline 判定
    if age is None:
        status = "unknown"
    elif age <= online_max:
        status = "online"
    elif age <= stale_max:
        status = "stale"
    else:
        status = "offline"
    # 只回傳 sanitized 欄位(cache 本身已 sanitized; 這裡再挑一層白名單)
    tel = data.get("telemetry", {}) if isinstance(data.get("telemetry"), dict) else {}
    svc = data.get("services", {}) if isinstance(data.get("services"), dict) else {}
    net = data.get("network", {}) if isinstance(data.get("network"), dict) else {}
    return {
        "status": status,
        "age_sec": age,
        "node_id": data.get("node_id"),
        "hostname": data.get("hostname"),
        "collected_at": data.get("collected_at"),
        "uptime_sec": data.get("uptime_sec"),
        "telemetry": {
            "cpu_pct": tel.get("cpu_pct"),
            "mem_pct": tel.get("mem_pct"),
            "disk_pct": tel.get("disk_pct"),
            "gpu_pct": tel.get("gpu_pct"),
        },
        "services": {
            "ollama": svc.get("ollama"),
            "worker_agent": svc.get("worker_agent"),
            "local_console": svc.get("local_console"),
        },
        "network": {
            "tailscale_ip": net.get("tailscale_ip"),
            "lan_ip": net.get("lan_ip"),
            "console_bind": net.get("console_bind"),
        },
        "thresholds": {"online_max_sec": online_max, "stale_max_sec": stale_max},
    }


@app.get("/tasks/results/{task_id}")
def task_result(task_id: str, session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """單個 task result。需登入。不顯 secret/正文。task_id 做基本清洗。"""
    _require_auth(session_cookie)
    safe_id = re.sub(r'[^A-Za-z0-9_\-]', '', task_id)   # 防路徑穿越
    p = os.path.join(TASK_RESULTS_DIR, f"{safe_id}.json")
    if not os.path.exists(p):
        return JSONResponse(status_code=404, content={"error": "not found"})
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": type(e).__name__})


@app.get("/logs/recent")
def logs_recent(session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """近期 runtime log 摘要。僅 admin。經脫敏器,最多 100 行,不返 secret/正文。"""
    _require_role(session_cookie, "admin")
    files = sorted(glob.glob(os.path.join(LOGS_DIR, "*.log")), reverse=True)
    if not files:
        return {"lines": []}
    lines = []
    try:
        with open(files[0], encoding="utf-8", errors="replace") as f:
            for line in f.readlines()[-100:]:
                lines.append(_redact(line.rstrip()))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": type(e).__name__})
    return {"log_file": os.path.basename(files[0]), "lines": lines}


REGISTRY_DIR = os.path.join(os.path.dirname(__file__), "registry")


def _read_registry(name, key):
    """讀 registry JSON,容錯回空。"""
    p = os.path.join(REGISTRY_DIR, name)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f).get(key, [])
    except Exception:
        return []


@app.get("/settings/models")
def settings_models(session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """Model Registry(只讀)。需登入。"""
    _require_auth(session_cookie)
    return {"models": _read_registry("models.json", "models")}


@app.get("/settings/skills")
def settings_skills(session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """Skill Registry(只讀)。需登入。"""
    _require_auth(session_cookie)
    return {"skills": _read_registry("skills.json", "skills")}


@app.get("/settings/agents")
def settings_agents(session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """Agent Registry(只讀)。需登入。candidate 狀態不可調用。"""
    _require_auth(session_cookie)
    return {"agents": _read_registry("agents.json", "agents")}


@app.post("/rag/chat")
async def rag_chat(request: Request, session_cookie: str = Cookie(default=None, alias=COOKIE_NAME)):
    """C2 RAG Chat。對照 GOAA_C2_DATA_PRIVACY_SPEC.md。
    §6 限 admin/provider;§13 ENABLE_RAG_CHAT 開關;正文只進內存,回 answer+metadata 不回正文。"""
    _require_role(session_cookie, "admin", "provider")           # §6
    if os.environ.get("ENABLE_RAG_CHAT", "false").lower() != "true":  # §13 disable 開關
        return JSONResponse(status_code=403, content={"error": "rag_chat disabled"})
    body = await request.json()
    query = body.get("query", "")
    if not query.strip():
        return JSONResponse(status_code=400, content={"error": "query required"})
    try:
        from rag_context_fetch import exec_rag_context_fetch
        result = exec_rag_context_fetch({
            "query_text": query,
            "top_k": body.get("top_k", 3),
            "max_chunks": body.get("max_chunks", 3),
        })
        # 只回 answer + sources(metadata) + model + redaction;不回正文/audit 內部
        return {"answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "model": result.get("model"),
                "redaction": result.get("redaction"),
                "status": result.get("status")}
    except Exception as e:
        # §11 異常脫敏:不 log raw
        import logging
        logging.getLogger("console.rag_chat").error(
            "rag_chat failed", extra={"error_type": type(e).__name__})
        return JSONResponse(status_code=500, content={"error": "internal error", "error_type": type(e).__name__})


# ═══════════════════════════════════════════════════════
# C.1 Patch — Console /ai/chat endpoint
# 規範 #11 only-add: 純新增, 不改既有
# 對齊 V5.3 Cyber-Noir + V5.1.B Router /chat
# ═══════════════════════════════════════════════════════

ROUTER_BASE_URL = os.getenv("GOAA_ROUTER_URL", "http://134.199.227.108:8080")
ROUTER_CHAT_TIMEOUT = float(os.getenv("GOAA_CHAT_TIMEOUT", "30.0"))


class AIChatReq(BaseModel):
    """C.1: Console AI 工作區對話請求"""
    prompt: str
    session_id: str | None = None


class AIChatResp(BaseModel):
    """C.1: Console AI 工作區對話回應"""
    ok: bool
    answer: str
    session_id: str
    model: str = "deepseek-v4-flash"
    duration_ms: int = 0
    cost_usd: float = 0.0
    mock: bool = False
    route: dict | None = None
    # ── P1-T2-U4: Task Detection + Envelope Preview ──
    task_detection: dict | None = None
    task_envelope_preview: dict | None = None
    # ── P1-T2-U6: Tao Approval Gate ──
    task_approval_gate: dict | None = None
    # ── P1-T2-U7: Readonly Dry-run Evidence Preview ──
    task_evidence_preview: dict | None = None
    # ── P4-T6: Task Gateway Result in Chat UX ──
    task_gateway_result: dict | None = None
    # ─────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# P4-T3: /tasks/run endpoint skeleton
# ═══════════════════════════════════════════════════════

class TaskRunReq(BaseModel):
    """P4-T3: /tasks/run 請求骨架。最小輸入,其餘從 intent policy 獲取默認值。"""
    task_id: str
    envelope_id: str = ""
    intent: str = "pure_chat"
    execution_mode: str | None = None
    approval_state: str | None = None
    actor_id: str = ""


class TaskRunResp(BaseModel):
    """P4-T3/P4-T5: /tasks/run 響應骨架。含 audit 與 evidence metadata。"""
    ok: bool
    run: dict
    blocked_reason: str = ""
    note: str = "No task executed, no executor, no DO, no Runtime mutation"
    audit_log: dict | None = None
    evidence_package: dict | None = None


# ═══════════════════════════════════════════════════════


# ── P2-T3: Align AI response copy with detected task intent ──
_ALIGNMENT_COPY = {
    TaskIntent.TASK_STATUS.value:
        "已识别为任务状态查询。\n"
        "当前为只读预览，不会执行真实任务。\n"
        "下面是系统生成的 Task Preview 与 Evidence Preview。\n",
    TaskIntent.TOPK_VERIFY.value:
        "已识别为知识库查询 / Top-K 验证请求。\n"
        "当前只生成 readonly dry-run evidence preview，不会执行真实 RAG 查询或任务。\n",
    TaskIntent.EMBED.value:
        "这是高风险索引操作。\n"
        "系统已通过 Tao Approval Gate 阻断。\n"
        "当前不会执行重建索引、不会调用 executor、不会修改 Runtime。\n",
    TaskIntent.APPROVE_TASK.value:
        "已识别为任务批准请求。\n"
        "当前为 preview-only，不会执行真实审批操作。\n"
        "真实批准必须等待 Tao 明确授权。\n",
    TaskIntent.REJECT_TASK.value:
        "已识别为任务拒绝请求。\n"
        "当前为 preview-only，不会执行真实拒绝操作。\n"
        "真实拒绝必须等待 Tao 明确授权。\n",
    TaskIntent.MEMORY_FETCH.value:
        "已识别为记忆读取请求。\n"
        "当前为 preview-only，不会执行真实记忆查询。\n",
}


_NO_TOOL_PATTERNS = (
    "没有工具",
    "沒有工具",
    "没有查询知识库工具",
    "沒有查詢知識庫工具",
    "我目前沒有「查詢知識庫」的工具",
    "我目前没有「查询知识库」的工具",
    "tool is unavailable",
    "don't have a tool",
)


def _contains_no_tool_message(answer: str) -> bool:
    """Check if the answer contains a 'no tool' message from the Router.

    These messages are misleading for topk_verify because the system has
    intent detection and evidence preview — it's not that there is no tool,
    it's that we're in readonly preview mode.
    """
    a = (answer or "").lower()
    return any(pattern.lower() in a for pattern in _NO_TOOL_PATTERNS)


def align_answer_with_task_intent(
    answer: str,
    detection_result: IntentDetectionResult,
) -> str:
    """Post-process AI answer to align with detected task intent.

    For non-pure_chat intents, prepend product-facing copy that explains
    the preview-only nature of the response. For pure_chat, return as-is.

    For topk_verify specifically: if the Router returned a "no tool" message,
    suppress it entirely and return only the alignment copy — the system
    has intent detection and readonly evidence preview, so "no tool" is
    misleading.

    This is a pure string operation — no LLM calls, no tool calls, no shell.
    """
    if answer is None:
        return ""
    if detection_result.intent == TaskIntent.PURE_CHAT.value:
        return answer
    copy = _ALIGNMENT_COPY.get(detection_result.intent)
    if not copy:
        return answer
    if (
        detection_result.intent == TaskIntent.TOPK_VERIFY.value
        and _contains_no_tool_message(answer)
    ):
        return copy
    return copy + answer


@app.post("/ai/chat")
async def ai_chat(req: AIChatReq, request: Request):
    """C.1: Console AI 工作區接真實 DeepSeek (透過 DO Router)

    V5.0 Master Plan「Las Vegas 場景」:
      Console (aika-core-01) → DO Router /chat → DeepSeek
    """
    session_id = req.session_id or f"console-{uuid.uuid4().hex[:8]}"
    try:
        async with httpx.AsyncClient(timeout=ROUTER_CHAT_TIMEOUT) as client:
            resp = await client.post(
                f"{ROUTER_BASE_URL}/chat",
                json={"prompt": req.prompt, "session_id": session_id, "enable_tools": True}
            )
            resp.raise_for_status()
            data = resp.json()
            r = data.get("response", {})

        # ── P1-T2-U4: Intent Detection + Task Envelope Preview ──
        detection_result: IntentDetectionResult = detect_intent_from_message(req.prompt)
        is_executable = detection_result.intent != TaskIntent.PURE_CHAT.value

        task_detection = {
            "intent": detection_result.intent,
            "detection_method": detection_result.detection_method,
            "confidence": detection_result.confidence,
            "params": detection_result.params,
            "is_executable_task": is_executable,
        }

        task_envelope_preview = None
        task_approval_gate = None
        if is_executable:
            envelope: TaskEnvelope = build_envelope_from_detection(
                detection_result,
                session_id=session_id,
                target_node="local-aika-core-01",
            )
            task_envelope_preview = envelope.to_dict()
            task_envelope_preview["preview_only"] = True

            # ── P1-T2-U6: Tao Approval Gate ──
            approval_required = bool(task_envelope_preview.get("approval_required", False))
            task_approval_gate = {
                "required": approval_required,
                "gate_status": "awaiting_tao_approval" if approval_required else "not_required",
                "reason": "risk_level=4 requires Tao approval" if approval_required
                          else "risk_level below approval threshold",
                "approved_by_tao": False,
                "execution_allowed": False,
            }
        # ── P1-T2-U7: Readonly Dry-run Evidence Preview ──
        # Only task_status and topk_verify generate dry_run_ready evidence
        READONLY_EVIDENCE_PREVIEW_INTENTS = {
            TaskIntent.TASK_STATUS.value,
            TaskIntent.TOPK_VERIFY.value,
        }
        task_evidence_preview = None
        if (
            is_executable
            and task_approval_gate
            and not task_approval_gate.get("required", True)
            and detection_result.intent in READONLY_EVIDENCE_PREVIEW_INTENTS
        ):
            intent = detection_result.intent
            summary_map = {
                TaskIntent.TASK_STATUS.value: "Task status readonly preview: No task executed. Runtime unchanged.",
                TaskIntent.TOPK_VERIFY.value: "Knowledge / Top-K readonly preview: No real RAG query executed, No task executed. Dry-run only.",
            }
            task_evidence_preview = {
                "preview_only": True,
                "task_executed": False,
                "runtime_mutation": False,
                "envelope_id": task_envelope_preview.get("envelope_id", "") if task_envelope_preview else "",
                "intent": intent,
                "node": "local-aika-core-01",
                "status": "dry_run_ready",
                "result_summary": summary_map.get(intent, "Readonly preview generated. No task executed."),
                "duration_ms": 0,
                "safety_flags": {
                    "readonly": True,
                    "worker_started": False,
                    "executor_enabled": False,
                    "do_connected": False,
                    "secret_read": False,
                    "private_key_read": False,
                    "runtime_mutation": False,
                },
            }
        elif is_executable and task_approval_gate and task_approval_gate.get("required", False):
            task_evidence_preview = {
                "preview_only": True,
                "task_executed": False,
                "runtime_mutation": False,
                "envelope_id": task_envelope_preview.get("envelope_id", "") if task_envelope_preview else "",
                "intent": detection_result.intent,
                "node": "local-aika-core-01",
                "status": "blocked_by_approval",
                "result_summary": "Blocked by Tao Approval Gate. High-risk task requires Tao approval. No task executed. Runtime unchanged.",
                "duration_ms": 0,
                "safety_flags": {
                    "readonly": True,
                    "worker_started": False,
                    "executor_enabled": False,
                    "do_connected": False,
                    "secret_read": False,
                    "private_key_read": False,
                    "runtime_mutation": False,
                },
            }
        # ─────────────────────────────────────────────────────────

        # ── P4-T6: Build Task Gateway Result for Chat UX ──
        task_gateway_result = None
        if is_executable and detection_result and envelope:
            # Determine gateway behavior based on intent and approval state
            _PREVIEW_SAFE_INTENTS = frozenset({"pure_chat", "task_status", "topk_verify"})
            _HIGH_RISK_INTENTS = frozenset({"embed"})

            gw_intent = detection_result.intent
            gw_approved = (task_approval_gate and not task_approval_gate.get("required", True))

            if gw_intent in _HIGH_RISK_INTENTS or (gw_intent in _PREVIEW_SAFE_INTENTS and not gw_approved):
                # Blocked
                reason = (
                    f"Intent '{gw_intent}' is high-risk" if gw_intent in _HIGH_RISK_INTENTS
                    else f"Intent '{gw_intent}' requires approval"
                )
                gw_result = build_blocked_result(
                    request_id=f"ux-{session_id}",
                    denial_reason=reason,
                )
                gw_decision = Decision.BLOCKED.value
                gw_note = f"Blocked: {reason}. No task executed. No executor. No DO. No Runtime mutation."
                gw_exec_mode = ExecutionMode.BLOCKED.value
            elif gw_intent in _PREVIEW_SAFE_INTENTS and gw_approved:
                # Preview-only (approved or not_required)
                approval_state = task_approval_gate.get("gate_status", "not_required") if task_approval_gate else "not_required"
                gw_run_id = f"GOAA-GTWY-RUN-{uuid.uuid4().hex[:12]}"
                gw_now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                gw_result = TaskRunResult(
                    run_id=gw_run_id,
                    request_id=f"ux-{session_id}",
                    status="preview_only",
                    execution_mode=ExecutionMode.PREVIEW_ONLY.value,
                    task_executed=False,
                    mutation_performed=False,
                    worker_started=False,
                    executor_enabled=False,
                    do_connected=False,
                    real_rag_query_executed=False,
                    embedding_rebuild_executed=False,
                    started_at_utc=gw_now_utc,
                    completed_at_utc=gw_now_utc,
                    result_summary=(
                        f"Preview-only for intent '{gw_intent}' "
                        f"with approval_state='{approval_state}'. No execution. Runtime unchanged."
                    ),
                )
                gw_decision = Decision.PREVIEW_ONLY.value
                gw_note = "Preview-only via approval gate. No task executed. No executor. No DO. No Runtime mutation."
                gw_exec_mode = ExecutionMode.PREVIEW_ONLY.value
            else:
                # Non-preview-safe → blocked
                reason = f"Intent '{gw_intent}' is not preview-safe"
                gw_result = build_blocked_result(
                    request_id=f"ux-{session_id}",
                    denial_reason=reason,
                )
                gw_decision = Decision.BLOCKED.value
                gw_note = f"Blocked: {reason}. No task executed. No executor. No DO. No Runtime mutation."
                gw_exec_mode = ExecutionMode.BLOCKED.value

            # Baton 8 fix: map gate_status to valid Task 4 approval_state values
            gw_approval_state = (
                "required"
                if task_approval_gate and task_approval_gate.get("required", False)
                else "not_required"
            )

            mock_req = TaskRunReq(
                task_id=session_id,
                envelope_id=envelope.envelope_id if envelope else "",
                intent=gw_intent,
                execution_mode=gw_exec_mode,
                approval_state=gw_approval_state,
                actor_id="ai_chat_ux",
            )
            gw_gateway_req = build_task_run_request(
                task_id=mock_req.task_id,
                envelope_id=mock_req.envelope_id,
                intent=gw_intent,
                execution_mode=gw_exec_mode,
                approval_state=gw_approval_state,
                actor_id="ai_chat_ux",
            )

            audit_dict, evid_dict = _build_audit_evidence(mock_req, gw_gateway_req, gw_result, gw_decision)

            task_gateway_result = {
                "execution_mode": gw_exec_mode,
                "status": gw_result.status,
                "blocked_reason": gw_result.error_message or "",
                "note": gw_note,
                "audit_log": audit_dict,
                "evidence_package": evid_dict,
            }

        # ── P2-T3: Align AI answer copy with detected intent ──
        raw_answer = r.get("text", data.get("error", "no response"))
        aligned_answer = align_answer_with_task_intent(raw_answer, detection_result)

        return AIChatResp(
            ok=data.get("ok", True),
            answer=aligned_answer,
            session_id=data.get("session_id", session_id),
            model=r.get("model", "deepseek-v4-flash"),
            duration_ms=data.get("duration_ms", 0),
            mock=r.get("mock", False),
            route=data.get("route"),
            task_detection=task_detection,
            task_envelope_preview=task_envelope_preview,
            task_approval_gate=task_approval_gate,
            task_evidence_preview=task_evidence_preview,
            task_gateway_result=task_gateway_result,
        )
    except httpx.TimeoutException:
        log.error("ai_chat timeout")
        return AIChatResp(ok=False, answer=f"⏱️ timeout ({ROUTER_CHAT_TIMEOUT}s)", session_id=session_id)
    except httpx.HTTPError as e:
        log.error("ai_chat http error", extra={"error": str(e)[:200]})
        return AIChatResp(ok=False, answer=f"❌ Router error", session_id=session_id)
    except Exception as e:
        log.exception("ai_chat unexpected error")
        return AIChatResp(ok=False, answer="❌ internal error", session_id=session_id)


# ═══════════════════════════════════════════════════════
# P4-T3: /tasks/run endpoint skeleton (blocked/preview-only)
# ═══════════════════════════════════════════════════════

def _build_audit_evidence(
    req: TaskRunReq,
    gateway_req: TaskRunRequest,
    result: TaskRunResult,
    decision: str,
) -> tuple[dict, dict]:
    """Build AuditLog and GatewayEvidencePackage metadata dicts for a /tasks/run response.

    Returns (audit_log_dict, evidence_package_dict).
    Both are response-only (no persistence, no DB, no file write).

    Baton 8 fix: enrich returned dicts with explicit Task 5 safety metadata.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    audit_id = f"GOAA-AUDIT-{uuid.uuid4().hex[:12]}"
    evid_id = f"GOAA-EVID-{uuid.uuid4().hex[:12]}"

    is_preview = (decision == Decision.PREVIEW_ONLY.value)
    event_type = "task_run_preview_only" if is_preview else "task_run_blocked"

    audit = AuditLog(
        audit_log_id=audit_id,
        request_id=gateway_req.request_id,
        actor_id=req.actor_id or "console-user",
        intent=req.intent,
        risk_level=gateway_req.risk_level,
        approval_state=req.approval_state or "not_required",
        decision=decision,
        denial_reason=result.error_message or "",
        created_at_utc=now_utc,
    )

    evidence = GatewayEvidencePackage(
        evidence_package_id=evid_id,
        request_id=gateway_req.request_id,
        run_id=result.run_id,
        readonly=False,
        preview_only=is_preview,
        task_executed=False,
        runtime_mutation=False,
        worker_started=False,
        executor_enabled=False,
        do_connected=False,
        real_rag_query_executed=False,
        embedding_rebuild_executed=False,
        evidence_summary=result.result_summary or "",
        created_at_utc=now_utc,
    )

    # Baton 8 fix: enrich audit dict with explicit safety metadata
    audit_dict = audit.to_dict()
    audit_dict.update({
        "event_type": event_type,
        "task_id": req.task_id,
        "persisted": False,
        "source": "tasks_run_gateway",
    })

    # Baton 8 fix: enrich evidence dict with explicit safety metadata
    evidence_dict = evidence.to_dict()
    evidence_dict.update({
        "task_id": req.task_id,
        "intent": req.intent,
        "decision": decision,
        "approval_state": req.approval_state or "not_required",
        "blocked_reason": result.error_message or "",
        "no_execution": True,
        "no_persistence": True,
        "source": "tasks_run_gateway",
    })

    return audit_dict, evidence_dict


@app.post("/tasks/run")
def task_run(req: TaskRunReq, request: Request):
    """P4-T3/P4-T4/P4-T5: /tasks/run — approval gate + audit/evidence metadata.

    Task 4 (approval enforcement):
      - approval_state=required              → blocked
      - approval_state=rejected_by_tao         → blocked
      - approval_state=expired                 → blocked
      - approval_state=approved_by_tao          → preview_only only (never executes)
      - approval_state=not_required            → preview_only (if preview-safe intent)
      - missing/invalid approval_state         → blocked
      - high-risk/unknown intent               → blocked regardless of approval

    Task 5 (response-only audit/evidence):
      - AuditLog metadata returned in every response (not persisted)
      - GatewayEvidencePackage metadata returned in every response (not persisted)
      - All execution flags remain False
      - No persistence, no DB, no file write
    """
    # ── Build TaskRunRequest from input + defaults ──
    gateway_req = build_task_run_request(
        task_id=req.task_id,
        envelope_id=req.envelope_id or f"auto-{req.task_id}",
        intent=req.intent,
        execution_mode=req.execution_mode,
        approval_state=req.approval_state,
        actor_id=req.actor_id or "console-user",
    )

    # Intent classification for response behavior
    _PREVIEW_SAFE_INTENTS = frozenset({
        "pure_chat",
        "task_status",
        "topk_verify",
    })
    _HIGH_RISK_INTENTS = frozenset({
        "embed",
    })

    # ── P4-T4: Approval gate helper ──
    def _check_approval_gate(intent: str, approval_state_value: str | None) -> tuple[bool, str]:
        """Return (is_blocked, reason). is_blocked=True means the request is denied."""
        if not approval_state_value or approval_state_value not in (
            "not_required", "required", "approved_by_tao", "rejected_by_tao", "expired"
        ):
            return True, f"Invalid or missing approval_state: '{approval_state_value}'"
        if approval_state_value == "required":
            return True, "Approval is required but not yet granted"
        if approval_state_value == "rejected_by_tao":
            return True, "Request was rejected by Tao"
        if approval_state_value == "expired":
            return True, "Approval has expired"
        # approved_by_tao or not_required → allowed (preview-only only, no execution)
        return False, ""

    # ── Step 1: High-risk intent → always blocked ──
    if req.intent in _HIGH_RISK_INTENTS:
        result = build_blocked_result(
            request_id=gateway_req.request_id,
            denial_reason=f"Intent '{req.intent}' is high-risk and blocked",
        )
        audit_dict, evid_dict = _build_audit_evidence(req, gateway_req, result, Decision.BLOCKED.value)
        return TaskRunResp(
            ok=False,
            run=result.to_dict(),
            blocked_reason=result.error_message,
            note="Blocked: high-risk intent. No task executed. No executor. No DO. No Runtime mutation.",
            audit_log=audit_dict,
            evidence_package=evid_dict,
        )

    # ── Step 2: Preview-safe intents → apply approval gate ──
    if req.intent in _PREVIEW_SAFE_INTENTS:
        is_blocked, reason = _check_approval_gate(req.intent, req.approval_state)
        if is_blocked:
            result = build_blocked_result(
                request_id=gateway_req.request_id,
                denial_reason=reason,
            )
            audit_dict, evid_dict = _build_audit_evidence(req, gateway_req, result, Decision.BLOCKED.value)
            return TaskRunResp(
                ok=False,
                run=result.to_dict(),
                blocked_reason=result.error_message,
                note=f"Blocked by approval gate: {reason}",
                audit_log=audit_dict,
                evidence_package=evid_dict,
            )
        # Approval passed → preview_only (never executes)
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        run_id = f"GOAA-GTWY-RUN-{int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)}"
        result = TaskRunResult(
            run_id=run_id,
            request_id=gateway_req.request_id,
            status="preview_only",
            execution_mode=ExecutionMode.PREVIEW_ONLY.value,
            task_executed=False,
            mutation_performed=False,
            worker_started=False,
            executor_enabled=False,
            do_connected=False,
            real_rag_query_executed=False,
            embedding_rebuild_executed=False,
            started_at_utc=now_utc,
            completed_at_utc=now_utc,
            result_summary=(
                f"Preview-only for intent '{req.intent}' "
                f"with approval_state='{req.approval_state}'. No execution. Runtime unchanged."
            ),
        )
        audit_dict, evid_dict = _build_audit_evidence(req, gateway_req, result, Decision.PREVIEW_ONLY.value)
        return TaskRunResp(
            ok=True,
            run=result.to_dict(),
            note="Preview-only via approval gate. No task executed. No executor. No DO. No Runtime mutation.",
            audit_log=audit_dict,
            evidence_package=evid_dict,
        )

    # ── Step 3: Non-preview-safe, non-high-risk intents → blocked ──
    result = build_blocked_result(
        request_id=gateway_req.request_id,
        denial_reason=f"Intent '{req.intent}' is not preview-safe and requires real execution, which is blocked",
    )
    audit_dict, evid_dict = _build_audit_evidence(req, gateway_req, result, Decision.BLOCKED.value)
    return TaskRunResp(
        ok=False,
        run=result.to_dict(),
        blocked_reason=result.error_message,
        note="Blocked: non-preview-safe intent. No task executed. No executor. No DO. No Runtime mutation.",
        audit_log=audit_dict,
        evidence_package=evid_dict,
    )


# ═══════════════════════════════════════════════════════
# P5-T3: /tasks/plan endpoint skeleton
# ═══════════════════════════════════════════════════════

class TaskPlanReq(BaseModel):
    """P5-T3: /tasks/plan 請求。最小輸入,其餘從 spec policy 矩陣獲取默認值。"""
    task_id: str
    intent: str = "pure_chat"
    envelope_id: str = ""
    actor_id: str = ""


class TaskPlanResp(BaseModel):
    """P5-T3/T4: /tasks/plan response.

    Top-level safety and classification fields are intentionally duplicated so UI / runner bridge
    consumers never need to infer safety from nested plan/dry_run objects.
    """
    ok: bool
    status: str = "plan_only"
    execution_mode: str = "plan_only"
    risk_level: str = "L0_information"
    strategy: str = "plan_only"
    execution_policy: str = "no_mutation"
    approval_required: bool = False
    blocked_reason: str | None = None
    risk_classification: dict | None = None
    task_executed: bool = False
    mutation_performed: bool = False
    audit_persisted: bool = False
    database_written: bool = False
    executor_enabled: bool = False
    real_execution_allowed: bool = False
    source: str = "execution_plan_gateway"
    plan: dict | None = None
    dry_run: dict | None = None
    note: str = "Plan-only endpoint — no task executed, no executor, no DO, no Runtime mutation"


def _build_execution_plan(req: TaskPlanReq, plan_id: str, request_id: str) -> ExecutionPlan | None:
    """Build an ExecutionPlan using static strategy matrix / risk classification."""
    classification = classify_task_intent(req.intent)

    if req.intent == "pure_chat" or classification.strategy == "preview_only":
        return None

    steps_map = {
        "task_status": ["resolve task status", "return status card"],
        "topk_verify": ["resolve query", "run top-k verification", "return evidence preview"],
    }
    steps = steps_map.get(req.intent, [])

    mode = ExecutionMode.PLAN_ONLY if classification.strategy == "plan_only" else ExecutionMode.BLOCKED
    approval = ApprovalState.REQUIRED if classification.approval_required else ApprovalState.NOT_REQUIRED

    return ExecutionPlan(
        plan_id=plan_id,
        request_id=request_id,
        task_id=req.task_id,
        intent=req.intent,
        actor_id=req.actor_id or "console-user",
        approval_state=approval,
        execution_mode=mode,
        risk_level=classification.risk_level.value,
        strategy=classification.strategy,
        execution_policy=classification.execution_policy.value,
        approval_required=classification.approval_required,
        blocked_reason=classification.blocked_reason,
        risk_classification=classification,
        runner_target=RunnerTarget(
            target_type="disabled",
            target_node=None,
            target_runtime=None,
            executor_required=False,
            executor_enabled=False,
            real_execution_allowed=False,
        ),
        planned_steps=steps,
        required_capabilities=[],
        forbidden_capabilities=[],
        expected_inputs=[],
        expected_outputs=[],
        rollback_hint=None,
        no_execution=True,
        source="execution_plan_gateway",
    )


def _build_dry_run_result(plan: ExecutionPlan) -> DryRunResult:
    """Build a non-executing DryRunResult from an ExecutionPlan."""
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return DryRunResult(
        dry_run_id=f"DRY-{uuid.uuid4().hex[:12].upper()}",
        plan_id=plan.plan_id,
        status="dry_run_only",
        simulated=True,
        task_executed=False,
        mutation_performed=False,
        risk_classification=plan.risk_classification,
        evidence_package=GatewayEvidencePackage(
            evidence_package_id=f"EVID-{uuid.uuid4().hex[:12].upper()}",
            request_id=plan.request_id,
            run_id=f"PLAN-{plan.plan_id}",
            readonly=True,
            preview_only=(plan.execution_mode == ExecutionMode.PLAN_ONLY),
            task_executed=False,
            runtime_mutation=False,
            worker_started=False,
            executor_enabled=False,
            do_connected=False,
            real_rag_query_executed=False,
            embedding_rebuild_executed=False,
            evidence_summary=(
                f"Plan-only summary for intent '{plan.intent}'. "
                f"Mode: {plan.execution_mode.value}. No execution occurred."
            ),
            created_at_utc=now_utc,
        ),
        audit_log=AuditLog(
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            request_id=plan.request_id,
            actor_id=plan.actor_id or "console-user",
            intent=plan.intent,
            risk_level=plan.risk_level,
            approval_state=plan.approval_state.value,
            decision=(
                Decision.BLOCKED.value
                if plan.execution_mode == ExecutionMode.BLOCKED
                else Decision.PLAN_ONLY.value
            ),
            denial_reason=(
                plan.blocked_reason
                or (
                    f"Blocked: intent '{plan.intent}' not allowed in Package 5"
                    if plan.execution_mode == ExecutionMode.BLOCKED
                    else ""
                )
            ),
            created_at_utc=now_utc,
        ),
    )


@app.post("/tasks/plan")
def task_plan(req: TaskPlanReq, request: Request):
    """P5-T3/T4: /tasks/plan — plan-only endpoint with strategy matrix & risk classification.

    Returns an ExecutionPlan and non-executing DryRunResult.
    Never executes real tasks. Never enables executor. Never mutates Runtime.
    """
    plan_id = f"PLAN-{uuid.uuid4().hex[:12].upper()}"
    request_id = f"REQ-{uuid.uuid4().hex[:12].upper()}"

    classification = classify_task_intent(req.intent)
    plan = _build_execution_plan(req, plan_id, request_id)

    if plan is None:
        # pure_chat — no plan needed
        return TaskPlanResp(
            ok=True,
            status="preview_only",
            execution_mode="preview_only",
            risk_level=classification.risk_level.value,
            strategy=classification.strategy,
            execution_policy=classification.execution_policy.value,
            approval_required=classification.approval_required,
            blocked_reason=classification.blocked_reason,
            risk_classification=classification.model_dump(),
            task_executed=False,
            mutation_performed=False,
            audit_persisted=False,
            database_written=False,
            executor_enabled=False,
            real_execution_allowed=False,
            source="execution_plan_gateway",
            plan=None,
            dry_run=None,
            note="No plan needed for pure chat messages. No execution. Runtime unchanged.",
        )

    dry_run = _build_dry_run_result(plan)

    return TaskPlanResp(
        ok=True,
        status=plan.execution_mode.value,
        execution_mode=plan.execution_mode.value,
        risk_level=classification.risk_level.value,
        strategy=classification.strategy,
        execution_policy=classification.execution_policy.value,
        approval_required=classification.approval_required,
        blocked_reason=classification.blocked_reason,
        risk_classification=classification.model_dump(),
        task_executed=False,
        mutation_performed=False,
        audit_persisted=False,
        database_written=False,
        executor_enabled=False,
        real_execution_allowed=False,
        source="execution_plan_gateway",
        plan=plan.model_dump(),
        dry_run=dry_run.model_dump(),
        note=(
            f"Plan for intent '{req.intent}': mode={plan.execution_mode.value}. "
            "No task executed. No executor. No DO. No Runtime mutation."
        ),
    )


@app.get("/", response_class=HTMLResponse)
def index():
    """本地 Console 首頁(飽滿版,重現雲端內容 + Cyber-Noir + 5 條改名,只增不減)。"""
    return r"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GOAA Local Runtime Console</title>
<style>
:root{--bg:#05080C;--bg2:#0A0F14;--panel:rgba(12,20,28,.86);--accent:#00C8FF;
--success:#22C55E;--warn:#FACC15;--danger:#EF4444;--purple:#A855F7;
--txt:#F5F5F5;--txt2:#A1A1AA;--border:rgba(0,200,255,.22);
--mono:'JetBrains Mono','SF Mono',Menlo,monospace;--ui:Inter,system-ui,sans-serif;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:var(--ui);display:flex;min-height:100vh}
body::before{content:"";position:fixed;inset:0;background:linear-gradient(rgba(0,200,255,.02) 1px,transparent 1px) 0 0/100% 3px;pointer-events:none;z-index:1}
/* 側欄 */
.side{width:216px;flex-shrink:0;background:linear-gradient(180deg,#070B10,#05080C);border-right:1px solid var(--border);padding:1.4rem 0;display:flex;flex-direction:column;position:relative;z-index:2}
.brand{padding:0 1.3rem 1.2rem;border-bottom:1px solid rgba(0,200,255,.1);text-align:center}
/* 呼吸燈 LOGO */
.logo{width:88px;height:88px;margin:0 auto .7rem;border-radius:20px;border:1px solid var(--accent);
display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;
background:radial-gradient(circle at 50% 45%,#f4f6f8 0%,#dfe6ec 75%,#c8d2da 100%);
box-shadow:0 0 14px rgba(0,200,255,.25)}
.logo img{width:80%;height:80%;object-fit:contain;animation:breathe 3s ease-in-out infinite}
@keyframes breathe{0%,100%{opacity:.78;transform:scale(.96)}50%{opacity:1;transform:scale(1.04)}}
.brand h2{font-family:var(--mono);font-size:1.15rem;margin:.2rem 0 0;letter-spacing:.08em}
.brand .ver{font-family:var(--mono);font-size:.62rem;color:var(--txt2);letter-spacing:.15em;margin-top:.2rem}
.brand .live{font-family:var(--mono);font-size:.66rem;color:var(--success);margin-top:.35rem}
.brand .live .d{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--success);box-shadow:0 0 8px var(--success);margin-right:.35rem;animation:pulse 2s infinite}
@keyframes pulse{50%{opacity:.35}}
nav{margin-top:1rem;flex:1;overflow-y:auto}
nav a{display:flex;align-items:center;gap:.6rem;padding:.55rem 1.3rem;color:var(--txt2);text-decoration:none;font-size:.84rem;border-left:2px solid transparent;cursor:pointer;transition:all .15s}
nav a:hover{color:var(--txt);background:rgba(0,200,255,.05)}
nav a.on{color:var(--accent);border-left-color:var(--accent);background:rgba(0,200,255,.08)}
nav a .ico{font-family:var(--mono);font-size:.85rem;width:1rem;text-align:center}
nav a .soon{font-size:.55rem;color:var(--txt2);margin-left:auto;border:1px solid rgba(161,161,170,.3);padding:0 .3rem;border-radius:3px;font-family:var(--mono)}
.side .foot{padding:.9rem 1.3rem 0;border-top:1px solid rgba(0,200,255,.1);font-family:var(--mono);font-size:.64rem;color:var(--txt2)}
.side .foot .pl{color:var(--danger);font-size:1rem;font-weight:700;margin-top:.2rem}
/* 主區 */
.main{flex:1;padding:1.4rem 1.8rem;position:relative;z-index:2;overflow-y:auto}
.main::after{content:"";position:fixed;left:216px;right:0;top:0;height:2px;pointer-events:none;z-index:3;
background:linear-gradient(90deg,transparent,rgba(0,200,255,.55),transparent);
box-shadow:0 0 12px rgba(0,200,255,.5);animation:scan 4s linear infinite}
@keyframes scan{0%{top:0;opacity:0}8%{opacity:1}92%{opacity:1}100%{top:100%;opacity:0}}
.top{display:flex;align-items:flex-start;justify-content:space-between;border-bottom:1px solid var(--border);padding-bottom:.9rem}
.top h1{font-family:var(--mono);font-size:1.3rem;margin:0;letter-spacing:.02em}
.top h1 small{font-size:.68rem;color:var(--accent);font-weight:400}
.pnl{display:flex;gap:1.5rem;font-family:var(--mono);font-size:.78rem;text-align:right}
.pnl .lbl{color:var(--txt2);font-size:.6rem;display:block}
.pnl .rev{color:var(--success)}.pnl .cost{color:var(--danger)}.pnl .prof{color:var(--accent)}
.hdrline{height:2px;margin:.7rem 0 1.3rem;border-radius:2px;position:relative;overflow:hidden;background:rgba(0,200,255,.12)}
.hdrline::after{content:"";position:absolute;top:0;left:0;height:100%;width:40%;
background:linear-gradient(90deg,transparent,var(--accent),transparent);
animation:flow 2.5s linear infinite}
@keyframes flow{0%{transform:translateX(-100%)}100%{transform:translateX(350%)}}
#authbar{font-size:.76rem;color:var(--txt2);font-family:var(--mono)}
#authbar a{color:var(--accent);text-decoration:none}
.page{display:none}.page.show{display:block}
/* 卡片 */
.row{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin-bottom:1.2rem}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:1rem 1.1rem;backdrop-filter:blur(8px)}
.card .h{font-family:var(--mono);font-size:.7rem;color:var(--txt2);letter-spacing:.05em;margin-bottom:.5rem;text-transform:uppercase}
.card .big{font-family:var(--mono);font-size:1.5rem;font-weight:700}
.sec-h{font-family:var(--mono);font-size:.82rem;color:var(--accent);letter-spacing:.06em;text-transform:uppercase;margin:1.3rem 0 .7rem}
.toggle{display:inline-block;width:38px;height:20px;border-radius:10px;background:var(--accent);position:relative;vertical-align:middle}
.toggle::after{content:"";position:absolute;right:2px;top:2px;width:16px;height:16px;border-radius:50%;background:#04121A}
/* 對話區 */
.chat{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:1rem;min-height:280px;display:flex;flex-direction:column}
.chat .hd{font-family:var(--mono);font-size:.8rem;color:var(--txt2);border-bottom:1px solid rgba(255,255,255,.05);padding-bottom:.6rem;margin-bottom:.6rem}
.chat .body{flex:1;display:flex;align-items:center;justify-content:center;color:var(--txt2);font-family:var(--mono);font-size:.82rem;text-align:center}
.chat .inp{display:flex;gap:.6rem;margin-top:.6rem}
.chat .inp input{flex:1;padding:.6rem .8rem;background:#070B10;border:1px solid var(--border);border-radius:8px;color:var(--txt);font-family:var(--mono);font-size:.84rem}
.chat .inp input:focus{outline:none;border-color:var(--accent)}
/* 任務 preview (P1-T2-U5) */
.tp-card{margin-top:.5rem;padding:.5rem .7rem;background:rgba(0,200,255,.04);border:1px solid rgba(0,200,255,.15);border-radius:8px;font-size:.78rem;line-height:1.5;font-family:var(--mono);align-self:flex-start;max-width:90%;animation:rise .3s ease}
.tp-card .tp-h{font-weight:700;color:var(--accent);font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.2rem}
.tp-card .tp-r{display:inline-block;padding:0 .35rem;border-radius:3px;font-size:.7rem}
.tp-risk-0{background:rgba(34,197,94,.15);color:var(--success)}
.tp-risk-1{background:rgba(250,204,21,.12);color:var(--warn)}
.tp-risk-2{background:rgba(250,204,21,.18);color:var(--warn)}
.tp-risk-3{background:rgba(239,68,68,.15);color:var(--danger)}
.tp-risk-4{background:rgba(239,68,68,.25);color:var(--danger)}
.tp-approve{color:var(--warn);font-weight:700}
.tp-preview{opacity:.6}
.btn-exec{padding:.6rem 1.1rem;background:linear-gradient(135deg,var(--success),#16A34A);border:none;border-radius:8px;color:#04140A;font-weight:700;font-family:var(--mono);cursor:pointer}
.btn-send{padding:.6rem 1.1rem;background:linear-gradient(135deg,var(--accent),#0095CC);border:none;border-radius:8px;color:#04121A;font-weight:700;font-family:var(--mono);cursor:pointer}
/* 節點卡 */
.node{background:var(--panel);border:1px solid var(--success);border-radius:12px;padding:1rem;position:relative}
.node .nm{font-family:var(--mono);font-weight:700;font-size:.95rem}
.node .ip{font-family:var(--mono);font-size:.72rem;color:var(--txt2)}
.node .on{position:absolute;top:1rem;right:1rem;font-family:var(--mono);font-size:.7rem;color:var(--success)}
.node .on .d{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--success);box-shadow:0 0 7px var(--success);animation:pulse 2s infinite;margin-right:.3rem}
.bar{margin:.5rem 0}.bar .l{display:flex;justify-content:space-between;font-family:var(--mono);font-size:.72rem;color:var(--txt2)}
.bar .t{height:4px;background:rgba(255,255,255,.08);border-radius:2px;margin-top:.2rem;overflow:hidden}
.bar .f{height:100%;background:var(--accent);border-radius:2px}
.bar .f.hot{background:var(--danger)}
.ep{display:block;color:var(--txt);text-decoration:none;font-family:var(--mono);font-size:.82rem;padding:.32rem 0;border-bottom:1px solid rgba(255,255,255,.04)}
.ep:hover{color:var(--accent)}.ep .lock{color:var(--txt2);font-size:.7rem}
.note{color:var(--txt2);font-size:.75rem;font-family:var(--mono)}
.step-row{display:flex;align-items:center;gap:.6rem;padding:.5rem 0;border-bottom:1px solid rgba(255,255,255,.04);font-family:var(--mono);font-size:.82rem}
.step-row .nm{color:var(--txt);font-weight:600}.step-row .id{color:var(--txt2);font-size:.72rem}.step-row .st{margin-left:auto;font-size:.72rem;color:var(--success)}
</style></head>
<body>
<aside class="side">
  <div class="brand">
    <div class="logo"><img src="data:image/png;base64,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UVJltyx0Pp9P08fbWFtto14DKjVyrZ7VJpMJoVAIX331lQYHfuutt6JFixa888l76dGjBz9v1apVmmNMb0yDBg3iex49epRbAMrvsWHDBm7XkpOTg549e/JxJmtGh8OBn376CX379sWXX36pQdwSIjQrKwuNGjVCq1at0KpVKzRs2BBZWVkaCgX67N27F+PHj8fUqVN1naN4PI7MzEwMGDCgxljl1jjRaBR//PEHnxK9evViVITqkNDRTkc3OVhXXXUVxwKzsrLgdDoxbtw4JCcns8O1Z88e/PHHHxxwVo17dW3VrnXq7+UQEedk9RKosnCpZ6tKkKKGCsxmMzZt2oTNmzczm4vVakXdunXx3nvv4eDBg2jUqBHGjRsHg8GAq6++Gt999x2MRiP+/PNPHD9+HC1atGCUqZro7dixI5o3b47jx48jEolg69at6N27t6ZSZuPGjbzLunbtioYNG2rsOxrn5s2bccstt3A/SCLOGzp0KLp3746WLVvyDiWBIRMhEAjg/PnzOHLkCNavX49ff/2VK6Kogeqbb77J8SjZTuzTpw/ee+89AMCBAwdw5swZjg2aTCYUFRXhwIEDPOcDBgzgo0s2aWRI+rJly3gO2rdvj06dOiEej2PLli1Yu3YtUlNTcfnll6Nt27as3SORCD777DP07t1bN6ui51nKzk0iHJns1UKm6ybCfyrdl2kFqB+R3F6EevTI1AOxWEyMGDFCw89KLVVkqsj7779fCCHEmTNnRHZ2NnONPvTQQ9yipKioiBshyH2O7rjjDr7PkCFDRFFREVNqu1wu0bRpU/77iy++KDwejzh//jyX/EejUeHz+bipgcViESkpKeKVV16pQc0djUaZg55oIeU2O/RZv349l/cTR+wvv/yioR93uVyipKREHDhwQMPR+sknnzCBcUVFhfjxxx+Z0pPK/eX7VFdX8/yXlZWJvXv3ct8nAOKFF14QQgixbt06kZycXKMxhUzHkJaWJjZv3sy8r1T2r1IHUB8nem5+fr4udYDX62WKgaKiImGUvUQ5iUmqWg//pVKWy/ROf/31F1avXs1/k9MeFosFdrsdJpMJu3btQiQSQZMmTTBq1CjenZ999hnOnDmD5ORk3VQGHRn0+euvv1BUVMQ7+8CBAzh//jyHB3r06KFJyVA94/Lly7F37142+hctWoSZM2fC6XQiEAgg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" alt="Aika"></div>
    <h2>Aika-Box</h2>
    <div class="ver">Worker Runtime OS V5.3</div>
    <div class="live"><span class="d"></span>API Live</div>
  </div>
  <nav id="nav">
    <a class="on" data-p="overview"><span class="ico">&#9632;</span>總覽</a>
    <a data-p="workspace"><span class="ico">&#9671;</span>AI 工作區</a>
    <a data-p="taskpool"><span class="ico">&#9638;</span>任務池</a>
    <a data-p="health"><span class="ico">&#9829;</span>Node Health</a>
    <a data-p="finance"><span class="ico">&#9826;</span>損益審計</a>
    <a href="/rag/stats"><span class="ico">&#9636;</span>RAG 狀態</a>
    <a data-p="memory"><span class="ico">&#9673;</span>Aika Memory<span class="soon">SOON</span></a>
    <a data-p="stepper"><span class="ico">&#9656;</span>Stepper</a>
    <a href="/settings/models"><span class="ico">&#9826;</span>Models</a>
    <a href="/settings/skills"><span class="ico">&#9001;</span>Skills</a>
    <a href="/settings/agents"><span class="ico">&#9678;</span>AI Agents</a>
    <a data-p="logs"><span class="ico">&#9636;</span>日誌歷史<span class="soon">SOON</span></a>
    <a data-p="settings"><span class="ico">&#9881;</span>系統設置<span class="soon">SOON</span></a>
    <a data-p="cloud"><span class="ico">&#9729;</span>Cloud Binding<span class="soon">SOON</span></a>
  </nav>
  <div class="foot">aika-core-01 · 127.0.0.1:5188<div class="note" style="margin-top:.3rem">今日淨利潤(placeholder)</div><div class="pl">$0.00</div></div>
</aside>
<div class="main">
  <div class="top">
    <div><h1 id="ptitle">總覽 <small>Local Console 5.2.C-2</small></h1>
      <p class="note">AiKa-Box Edge Runtime · 本地主權入口</p></div>
    <div style="display:flex;gap:1.5rem;align-items:center">
      <div class="pnl"><div><span class="lbl">收益</span><span class="rev">$0.00</span></div>
      <div><span class="lbl">成本</span><span class="cost">$0.00</span></div>
      <div><span class="lbl">淨利潤</span><span class="prof">$0.00</span></div></div>
      <div id="authbar"></div>
    </div>
  </div>
  <div class="hdrline"></div>

  <!-- 總覽 -->
  <div class="page show" id="p-overview">
    <div class="row">
      <div class="card"><div class="h">&#9670; 端點 Endpoints</div>
        <a class="ep" href="/health">/health</a>
        <a class="ep" href="/rag/stats">/rag/stats <span class="lock">&#128274;</span></a>
        <a class="ep" href="/tasks/results">/tasks/results <span class="lock">&#128274;</span></a>
        <a class="ep" href="/session">/session</a></div>
      <div class="card"><div class="h">&#9826; 註冊表 Registry</div>
        <a class="ep" href="/settings/models">Models <span class="lock">&#128274;</span></a>
        <a class="ep" href="/settings/skills">Skills <span class="lock">&#128274;</span></a>
        <a class="ep" href="/settings/agents">AI Agents <span class="lock">&#128274;</span></a></div>
    </div>
    <div class="card"><div class="h">&#9656; Workflow Status (Stepper)</div>
      <p class="note">輕量狀態監控,非節點編輯器。不顯 RAG 正文 / secret / 原始節點圖。</p>
      <div id="stepper" class="note">登入後載入最近任務…</div></div>
  </div>

  <!-- AI 工作區(原 AI調度,內容重現,只增不減)-->
  <div class="page" id="p-workspace">
    <div class="row">
      <div class="card"><div class="h">用戶參與調度</div><label><input type="checkbox" checked> 我參與對話與調度</label></div>
      <div class="card"><div class="h">AI AGENT(默認)</div><div style="font-family:var(--mono)">&#10022; DeepSeek-V4-Flash <span style="color:var(--success)">&#9679; 在線</span></div></div>
      <div class="card"><div class="h">執行 AI AGENT(AIKA)</div><div style="font-family:var(--mono);color:var(--success)">全部在線 AI AGENT(3/6)</div></div>
      <div class="card"><div class="h">自動調度</div>自動分發與執行 <span class="toggle"></span></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 320px;gap:1rem">
      <div class="chat">
        <div class="hd">&#128172; 對話 GOAA · session 跨裝置同步 · 0 msgs</div>
        <div class="body">&#128161; 開始跟 GOAA AI AGENT 對話(DeepSeek-V4-Flash)<br>可請求執行任務、查詢服務狀態</div>
        <div class="inp"><input placeholder="跟 GOAA AI AGENT 對話… (Enter 發送)"><button class="btn-send">發送</button></div>
      </div>
      <div class="card"><div class="h">AI AGENT 實時回報</div>
        <div id="agents-live" class="note">等待 AI AGENT 回報中…</div></div>
    </div>
  </div>

  <!-- 任務池(重現,只增不減)-->
  <div class="page" id="p-taskpool">
    <div class="row">
      <div class="card"><div class="h">隊列</div><div class="big" style="color:var(--warn)">0</div></div>
      <div class="card"><div class="h">運行</div><div class="big" style="color:var(--accent)">0</div></div>
      <div class="card"><div class="h">完成</div><div class="big" style="color:var(--success)">0</div></div>
      <div class="card"><div class="h">失敗</div><div class="big" style="color:var(--danger)">0</div></div>
    </div>
    <div class="card"><div class="h">任務明細(讀本地 /tasks/results)</div>
      <div id="taskpool-list" class="note">登入後載入…</div></div>
  </div>

  <!-- Node Health(原節點監控,重現,只增不減)-->
  <div class="page" id="p-health">
    <div class="sec-h">ACTIVE NODES</div>
    <div class="row" id="nodes">
      <div class="node" id="node-self"><span class="on" id="self-status"><span class="d"></span>—</span>
        <div class="nm">aika-core-01</div><div class="ip" id="self-ip">本機 · 即時</div>
        <div class="bar"><div class="l"><span>CPU</span><span id="self-cpu-v">—</span></div><div class="t"><div class="f" id="self-cpu-b" style="width:0%"></div></div></div>
        <div class="bar"><div class="l"><span>MEM</span><span id="self-mem-v">—</span></div><div class="t"><div class="f" id="self-mem-b" style="width:0%"></div></div></div>
        <div class="bar"><div class="l"><span>DISK</span><span id="self-disk-v">—</span></div><div class="t"><div class="f" id="self-disk-b" style="width:0%"></div></div></div>
        <div class="bar"><div class="l"><span>GPU</span><span id="self-gpu-v">—</span></div><div class="t"><div class="f" id="self-gpu-b" style="width:0%"></div></div></div>
        <div class="note" id="self-svc" style="margin-top:.5rem">讀取中…</div></div>
      <div class="node"><span class="on"><span class="d"></span>—</span>
        <div class="nm">aika-2</div><div class="ip">192.168.1.208</div>
        <div class="bar"><div class="l"><span>CPU</span><span>—</span></div><div class="t"><div class="f" style="width:0%"></div></div></div>
        <div class="bar"><div class="l"><span>MEM</span><span>—</span></div><div class="t"><div class="f" style="width:0%"></div></div></div>
        <div class="bar"><div class="l"><span>DISK</span><span>—</span></div><div class="t"><div class="f" style="width:0%"></div></div></div>
        <div class="note" style="margin-top:.5rem">佔位 · 待 Fleet(B-2)</div></div>
      <div class="node"><span class="on"><span class="d"></span>—</span>
        <div class="nm">do-cloud-1</div><div class="ip">134.199.227.108</div>
        <div class="bar"><div class="l"><span>CPU</span><span>—</span></div><div class="t"><div class="f" style="width:0%"></div></div></div>
        <div class="bar"><div class="l"><span>MEM</span><span>—</span></div><div class="t"><div class="f" style="width:0%"></div></div></div>
        <div class="bar"><div class="l"><span>DISK</span><span>—</span></div><div class="t"><div class="f" style="width:0%"></div></div></div>
        <div class="note" style="margin-top:.5rem">佔位 · 待 Fleet(B-2)</div></div>
    </div>
    <p class="note">aika-core-01 為本機真實數據(/node/health, 每 ~8s 更新); aika-2 / do-cloud-1 為佔位, 待 B-2 Fleet 匯總接入。</p>
  </div>

  <!-- 損益審計(保留,重現,只增不減)-->
  <div class="page" id="p-finance">
    <div class="row">
      <div class="card"><div class="h">今日收益</div><div class="big rev" style="color:var(--success)">$0.00</div></div>
      <div class="card"><div class="h">今日成本</div><div class="big" style="color:var(--danger)">$0.00</div></div>
      <div class="card"><div class="h">淨利潤</div><div class="big" style="color:var(--danger)">$0.00</div></div>
      <div class="card"><div class="h">利潤率</div><div class="big" style="color:var(--accent)">N/A</div></div>
    </div>
    <div class="card"><div class="h">任務池財務</div>
      <div class="row" style="margin:.5rem 0 0">
        <div><div class="h">待處理</div><div class="big" style="color:var(--warn)">0</div></div>
        <div><div class="h">運行中</div><div class="big" style="color:var(--accent)">0</div></div>
        <div><div class="h">完成</div><div class="big" style="color:var(--success)">0</div></div>
        <div><div class="h">失敗</div><div class="big" style="color:var(--danger)">0</div></div>
      </div></div>
    <p class="note">損益為 placeholder; 本地 Console 不做 billing, 數字非真實運營數據。</p>
  </div>

  <!-- Stepper -->
  <div class="page" id="p-stepper">
    <div class="card"><div class="h">&#9656; Workflow Status (Stepper)</div>
      <p class="note">輕量狀態監控,非節點編輯器。不顯 RAG 正文 / secret。</p>
      <div id="stepper2" class="note">登入後載入…</div></div>
  </div>

  <!-- SOON 頁 -->
  <div class="page" id="p-memory"><div class="card"><div class="h">Aika Memory Context</div><p class="note">COMING SOON · C2 記憶補給(局部片段, 非完整記憶恢復)</p></div></div>
  <div class="page" id="p-logs"><div class="card"><div class="h">日誌歷史</div><p class="note">COMING SOON</p></div></div>
  <div class="page" id="p-settings"><div class="card"><div class="h">系統設置</div><p class="note">COMING SOON</p></div></div>
  <div class="page" id="p-cloud"><div class="card"><div class="h">Cloud Binding</div><p class="note">COMING SOON · 雲端綁定(可選)</p></div></div>
</div>

<script>
// 導航切換
var navTitle={overview:'總覽',workspace:'AI 工作區',taskpool:'任務池',health:'Node Health',finance:'損益審計',memory:'Aika Memory',stepper:'Stepper',logs:'日誌歷史',settings:'系統設置',cloud:'Cloud Binding'};
document.querySelectorAll('#nav a[data-p]').forEach(function(a){
  a.onclick=function(){
    var p=a.getAttribute('data-p');
    document.querySelectorAll('#nav a').forEach(function(x){x.classList.remove('on')});
    a.classList.add('on');
    document.querySelectorAll('.page').forEach(function(x){x.classList.remove('show')});
    var el=document.getElementById('p-'+p); if(el)el.classList.add('show');
    document.getElementById('ptitle').innerHTML=navTitle[p]+' <small>Local Console 5.2.C-2</small>';
  };
});
// authbar
async function loadAuthbar(){
  try{
    var r=await fetch('/session'); var s=await r.json();
    var bar=document.getElementById('authbar');
    if(s.authenticated){
      bar.innerHTML='已登入:<b style="color:var(--accent)">'+s.username+'</b> ('+s.role+') <a href="#" id="logout" style="color:var(--danger);margin-left:.5rem">登出</a>';
      document.getElementById('logout').onclick=async function(e){e.preventDefault();await fetch('/logout',{method:'POST'});location.reload();};
    }else{ bar.innerHTML='<a href="/login">登入 &rarr;</a>'; }
  }catch(e){}
}
loadAuthbar();
// Stepper(讀 /tasks/results,不取正文)
async function loadStepper(){
  try{
    var r=await fetch('/tasks/results');
    var tgt=[document.getElementById('stepper'),document.getElementById('stepper2'),document.getElementById('taskpool-list')];
    if(r.status===401){ tgt.forEach(function(e){if(e)e.textContent='需登入才能查看任務狀態。'}); return; }
    var data=await r.json();
    if(!data.results||!data.results.length){ tgt.forEach(function(e){if(e)e.textContent='暫無任務記錄。'}); return; }
    var html=data.results.slice(0,8).map(function(t){
      var icon=t.status==='success'?'\u2705':(t.status==='failed'?'\u274C':(t.status==='STATUS_HELD_FOR_REVIEW'?'\u26A0\uFE0F':'\u23F3'));
      return '<div class="step-row"><span>'+icon+'</span> <span class="nm">'+(t.task||'?')+'</span> <span class="id">'+(t.task_id||'')+'</span> <span class="st">'+(t.status||'')+'</span>'+(t.duration_s!=null?' <span class="id">'+t.duration_s+'s</span>':'')+'</div>';
    }).join('');
    tgt.forEach(function(e){if(e)e.innerHTML=html});
  }catch(e){}
}
loadStepper();

// B-4: Node Health 本機卡接真實數據(讀 /node/health, 每 ~8s)
function _setBar(vId, bId, val){
  var v=document.getElementById(vId), b=document.getElementById(bId);
  if(!v||!b) return;
  if(val==null){ v.textContent='—'; b.style.width='0%'; return; }
  v.textContent=val+'%';
  var w=Math.max(0,Math.min(100,Number(val)));
  b.style.width=w+'%';
  b.className='f'+(w>=80?' hot':'');
}
async function loadNodeHealth(){
  try{
    var r=await fetch('/node/health');
    if(r.status===401){ var s=document.getElementById('self-status'); if(s)s.innerHTML='<span class="d"></span>需登入'; return; }
    var d=await r.json();
    var st=document.getElementById('self-status');
    if(st) st.innerHTML='<span class="d"></span>'+(d.status||'—')+(d.age_sec!=null?' ('+d.age_sec+'s)':'');
    var ip=document.getElementById('self-ip');
    if(ip) ip.textContent=(d.network&&d.network.lan_ip?d.network.lan_ip:'本機')+' · 即時';
    var t=d.telemetry||{};
    _setBar('self-cpu-v','self-cpu-b',t.cpu_pct);
    _setBar('self-mem-v','self-mem-b',t.mem_pct);
    _setBar('self-disk-v','self-disk-b',t.disk_pct);
    _setBar('self-gpu-v','self-gpu-b',t.gpu_pct);
    var sv=d.services||{};
    var svc=document.getElementById('self-svc');
    if(svc) svc.textContent='Ollama:'+(sv.ollama||'?')+' · Worker:'+(sv.worker_agent||'?')+' · Console:'+(sv.local_console||'?');
  }catch(e){}
}
loadNodeHealth();
setInterval(loadNodeHealth, 8000);

// ── D.1: AI 工作區聊天框接 /ai/chat (Phase D UI) ──
(function(){
  var inp=document.querySelector('#p-workspace .chat .inp input');
  var btn=document.querySelector('#p-workspace .chat .btn-send');
  var body=document.querySelector('#p-workspace .chat .body');
  var hd=document.querySelector('#p-workspace .chat .hd');
  var sessionId=null, msgCount=0;

  function addMsg(text, isUser){
    var d=document.createElement('div');
    d.style.cssText='padding:.5rem .7rem;margin-bottom:.4rem;border-radius:8px;font-size:.85rem;line-height:1.4;max-width:90%;word-break:break-word;animation:rise .3s ease;'+(isUser?'align-self:flex-end;background:var(--accent);color:#000;':'align-self:flex-start;background:var(--panel);color:var(--txt);border:1px solid var(--border);');
    if(!isUser) d.innerHTML=text.replace(/\n/g,'<br>');
    else d.textContent=text;
    body.parentNode.insertBefore(d, body.nextSibling);
    d.scrollIntoView({behavior:'smooth',block:'end'});
    msgCount++;
    if(hd) hd.innerHTML='&#128172; 對話 GOAA · session 跨裝置同步 · '+msgCount+' msgs'+(sessionId?' · '+sessionId.slice(0,8):'');
  }

  function showLoading(){
    var l=document.createElement('div');
    l.id='chat-loading';
    l.style.cssText='padding:.5rem .7rem;margin-bottom:.4rem;border-radius:8px;font-size:.85rem;color:var(--txt2);align-self:flex-start;animation:rise .3s ease;';
    l.textContent='⏳ AI AGENT thinking…';
    body.parentNode.insertBefore(l, body.nextSibling);
  }
  function hideLoading(){
    var l=document.getElementById('chat-loading');
    if(l) l.remove();
  }

  // ── P1-T2-U5: Render Task Preview Card ──
  function escapeHtml(v){
    return String(v === undefined || v === null ? '' : v)
      .replace(/&/g,'&amp;')
      .replace(/</g,'&lt;')
      .replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;')
      .replace(/'/g,'&#39;');
  }

  function renderTaskPreview(td, ep, ag){
    if(!td) return;
    // ── P2-T2: Hide task preview for pure_chat ──
    if(td.intent==='pure_chat') return;
    var d=document.createElement('div');
    d.className='tp-card';
    var html='<div class="tp-h">&#128220; Task Preview</div>';
    html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Intent: </span><span>'+escapeHtml(td.intent)+'</span><br>';
    html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Method: </span><span>'+escapeHtml(td.detection_method)+'</span><br>';
    html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Confidence: </span><span>'+(td.confidence*100).toFixed(0)+'%</span><br>';
    if(ep){
      var riskLabels=['INFORMATION','LOW','MEDIUM','HIGH','CRITICAL'];
      var ri=Number(ep.risk_level);
      if(isNaN(ri)||ri<0||ri>4) ri=0;
      var rl=riskLabels[ri]||'UNKNOWN';
      html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Risk: </span><span class="tp-r tp-risk-'+ri+'">'+rl+' (L'+ri+')</span><br>';
      html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Status: </span><span>'+escapeHtml(ep.status)+'</span><br>';
      html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Node: </span><span>'+escapeHtml(ep.target_node)+'</span><br>';
      if(td.params&&Object.keys(td.params).length){
        html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Params: </span><span class="tp-preview">'+escapeHtml(JSON.stringify(td.params))+'</span><br>';
      }
      // ── P1-T2-U6: Tao Approval Gate ──
      if(ag){
        var req=ag.required===true;
        html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Gate: </span><span'+(req?' class="tp-approve"':'')+'>'+escapeHtml(String(ag.gate_status))+'</span><br>';
        html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Reason: </span><span class="tp-preview">'+escapeHtml(String(ag.reason))+'</span><br>';
        if(req){
          html+='<div style="margin-top:.3rem;padding:.3rem .5rem;background:rgba(239,68,68,.18);border:1px solid rgba(239,68,68,.3);border-radius:6px;font-size:.78rem;color:var(--danger)">';
          html+='&#9888; Tao Approval Required<br><span style="font-size:.72rem;opacity:.8">Awaiting Tao approval — task blocked by approval gate</span></div>';
        } else {
          html+='<div style="margin-top:.3rem;padding:.2rem .4rem;background:rgba(34,197,94,.08);border-radius:4px;font-size:.72rem;color:var(--success)">&#10003; No approval required (preview only)</div>';
        }
      }
      html+='<div class="tp-preview" style="margin-top:.2rem;font-size:.7rem">&#128274; Preview only — no task executed</div>';
    } else {
      html+='<div class="tp-preview">Non-executable intent (pure chat)</div>';
    }
    d.innerHTML=html;
    body.parentNode.insertBefore(d, body.nextSibling);
    d.scrollIntoView({behavior:'smooth',block:'end'});
  }

  // ── P2-T4: Evidence preview intent label helper ──
  function evidenceIntentLabel(ev){
    var labels={
      'task_status':'Task status readonly preview',
      'topk_verify':'Knowledge / Top-K readonly preview'
    };
    return labels[ev.intent]||'Readonly preview';
  }

  function evidenceSafetyLine(ev){
    var line='';
    if(ev.safety_flags){
      line+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Safety: </span><span style="color:var(--success)">readonly</span>';
      if(!ev.safety_flags.worker_started) line+=' / <span style="color:var(--success)">no worker</span>';
      if(!ev.safety_flags.executor_enabled) line+=' / <span style="color:var(--success)">no executor</span>';
      if(!ev.safety_flags.do_connected) line+=' / <span style="color:var(--success)">no DO</span>';
      line+='<br>';
    }
    return line;
  }

  // ── P1-T2-U7: Render Evidence Preview Card ──
  function renderEvidencePreview(ev){
    if(!ev) return;
    // ── P2-T2: Hide evidence preview for pure_chat ──
    if(ev.intent==='pure_chat') return;
    var d=document.createElement('div');
    d.className='tp-card';
    var headerLabel, intentLabel, previewNote;
    if(ev.status==='blocked_by_approval'){
      headerLabel='Evidence Preview · Blocked by Approval';
      intentLabel='<span style="color:var(--error)">&#10060; Blocked by Tao Approval Gate</span><br><span class="tp-h">High-risk task requires Tao approval.</span><br>';
      previewNote='&#128274; No task executed. Runtime unchanged.';
    } else {
      headerLabel='Evidence Preview · Readonly Dry-run';
      intentLabel='<span class="tp-h">&#128200; '+escapeHtml(evidenceIntentLabel(ev))+'</span><br>';
      previewNote='&#128274; Preview only: no task executed. Runtime mutation: false. Executor: disabled. DO: not used.';
    }
    var html='<div class="tp-h">'+escapeHtml(headerLabel)+'</div>';
    html+=intentLabel;
    html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Status: </span><span>'+escapeHtml(String(ev.status))+'</span><br>';
    html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Summary: </span><span class="tp-preview">'+escapeHtml(String(ev.result_summary))+'</span><br>';
    if(ev.envelope_id){
      html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Envelope: </span><span>'+escapeHtml(String(ev.envelope_id))+'</span><br>';
    }
    html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Node: </span><span>'+escapeHtml(String(ev.node))+'</span><br>';
    html+=evidenceSafetyLine(ev);
    html+='<div class="tp-preview" style="margin-top:.2rem;font-size:.7rem">'+previewNote+'</div>';
    d.innerHTML=html;
    body.parentNode.insertBefore(d, body.nextSibling);
    d.scrollIntoView({behavior:'smooth',block:'end'});
  }

  // ── P4-T6: Render Task Gateway Result Card ──
  function renderTaskGatewayResult(gw){
    if(!gw) return;
    var d=document.createElement('div');
    d.className='tp-card';
    var isBlocked = (gw.execution_mode==='blocked' || gw.status==='blocked');
    var headerIcon = isBlocked ? '&#128308;' : '&#128200;';
    var headerLabel = isBlocked ? 'Task Gateway · Blocked' : 'Task Gateway · Preview Only';
    var html='<div class="tp-h">'+headerIcon+' '+escapeHtml(headerLabel)+'</div>';
    html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Status: </span><span>'+(isBlocked?'<span style="color:var(--danger)">blocked</span>':'<span style="color:var(--success)">preview_only</span>')+'</span><br>';
    html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Execution Mode: </span><span>'+escapeHtml(gw.execution_mode)+'</span><br>';
    if(gw.blocked_reason){
      html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Blocked Reason: </span><span style="color:var(--danger)">'+escapeHtml(gw.blocked_reason)+'</span><br>';
    }
    if(gw.note){
      html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">Note: </span><span class="tp-preview">'+escapeHtml(gw.note)+'</span><br>';
    }
    var aud=gw.audit_log;
    if(aud){
      html+='<div style="margin-top:.3rem;padding:.2rem .4rem;background:rgba(0,0,0,.15);border-radius:4px;font-size:.72rem">';
      html+='<span class="tp-h" style="font-size:.72rem">Audit Log</span><br>';
      html+='event: '+escapeHtml(aud.event_type||'')+'<br>';
      html+='persisted: '+(aud.persisted===false?'false':'<span style="color:var(--danger)">'+escapeHtml(String(aud.persisted))+'</span>')+'<br>';
      html+='source: '+escapeHtml(aud.source||'')+'<br>';
      html+='</div>';
    }
    var ev=gw.evidence_package;
    if(ev){
      html+='<div style="margin-top:.3rem;padding:.2rem .4rem;background:rgba(0,0,0,.15);border-radius:4px;font-size:.72rem">';
      html+='<span class="tp-h" style="font-size:.72rem">Evidence Package</span><br>';
      html+='decision: '+escapeHtml(ev.decision||'')+'<br>';
      html+='no_execution: '+escapeHtml(String(ev.no_execution))+'<br>';
      html+='no_persistence: '+escapeHtml(String(ev.no_persistence))+'<br>';
      html+='source: '+escapeHtml(ev.source||'')+'<br>';
      html+='</div>';
    }
    html+='<div class="tp-preview" style="margin-top:.2rem;font-size:.7rem;color:var(--txt2)">&#128274; No task executed. No Runtime mutation. No audit persistence. No database write.</div>';
    d.innerHTML=html;
    body.parentNode.insertBefore(d, body.nextSibling);
    d.scrollIntoView({behavior:'smooth',block:'end'});
  }

  // ── P5-T5: Render Task Plan (Strategy & Risk) Card ──
  function renderTaskPlan(tp){
    if(!tp) return;
    // pure_chat / preview_only carries no plan — keep the workspace quiet.
    if(tp.execution_mode==='preview_only' || tp.status==='preview_only') return;
    var isBlocked = (tp.execution_mode==='blocked' || tp.status==='blocked' || !!tp.blocked_reason);
    var d=document.createElement('div');
    d.className='tp-card';
    var headerIcon = isBlocked ? '&#128308;' : '&#128202;';
    var html='<div class="tp-h">'+headerIcon+' '+escapeHtml('Task Plan · Strategy & Risk')+'</div>';
    function row(label, val){
      return '<span class="tp-h" style="font-size:.78rem;text-transform:none">'+escapeHtml(label)+': </span><span>'+escapeHtml(String(val))+'</span><br>';
    }
    html+=row('status', tp.status);
    html+=row('execution_mode', tp.execution_mode);
    html+=row('risk_level', tp.risk_level);
    html+=row('strategy', tp.strategy);
    html+=row('execution_policy', tp.execution_policy);
    html+=row('approval_required', tp.approval_required);
    if(isBlocked && tp.blocked_reason){
      html+='<span class="tp-h" style="font-size:.78rem;text-transform:none">blocked_reason: </span><span style="color:var(--danger)">'+escapeHtml(String(tp.blocked_reason))+'</span><br>';
    }
    html+='<div style="margin-top:.3rem;padding:.2rem .4rem;background:rgba(0,0,0,.15);border-radius:4px;font-size:.72rem">';
    html+='<span class="tp-h" style="font-size:.72rem">Safety State</span><br>';
    html+=row('task_executed', tp.task_executed);
    html+=row('mutation_performed', tp.mutation_performed);
    html+=row('audit_persisted', tp.audit_persisted);
    html+=row('database_written', tp.database_written);
    html+=row('executor_enabled', tp.executor_enabled);
    html+=row('real_execution_allowed', tp.real_execution_allowed);
    html+='</div>';
    if(isBlocked){
      html+='<div style="margin-top:.3rem;padding:.3rem .5rem;background:rgba(239,68,68,.18);border:1px solid rgba(239,68,68,.3);border-radius:6px;font-size:.78rem;color:var(--danger)">&#9888; '+escapeHtml('Blocked — Plan only. No task executed.')+'</div>';
    }
    html+='<div class="tp-preview" style="margin-top:.2rem;font-size:.7rem;color:var(--txt2)">&#128274; '+escapeHtml('Plan only · No task executed · Runtime unchanged · Executor disabled')+'</div>';
    d.innerHTML=html;
    body.parentNode.insertBefore(d, body.nextSibling);
    d.scrollIntoView({behavior:'smooth',block:'end'});
  }

  // ── P5-T5: Fetch plan-only strategy/risk for task-like input (tolerant) ──
  async function fetchTaskPlan(td){
    if(!td || td.intent==='pure_chat') return;
    try{
      var r=await fetch('/tasks/plan',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({task_id:'CONSOLE-'+(td.intent||'task'), intent:td.intent})
      });
      if(!r.ok) return;
      var tp=await r.json();
      if(tp&&tp.ok) renderTaskPlan(tp);
    }catch(e){
      // Tolerant: /tasks/plan failure must never break the chat flow.
    }
  }

  async function sendMsg(){
    var text=inp?inp.value.trim():'';
    if(!text) return;
    inp.value='';
    addMsg(text, true);
    showLoading();
    try{
      var r=await fetch('/ai/chat',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({prompt:text,session_id:sessionId})
      });
      var d=await r.json();
      hideLoading();
      if(d.ok){
        sessionId=d.session_id;
        var answer=d.answer+(d.duration_ms?'<br><small style="opacity:.5">✨ '+d.model+' · '+(d.duration_ms/1000).toFixed(2)+'s'+(d.cost_usd>0?' · $'+d.cost_usd.toFixed(5):'')+(d.route&&d.route.task_id?' · task:'+d.route.task_id.slice(-8):'')+'</small>':'');
        addMsg(answer, false);
        // ── P1-T2-U5: Render Task Preview below AI answer ──
        renderTaskPreview(d.task_detection, d.task_envelope_preview, d.task_approval_gate);
        // ── P1-T2-U7: Render Evidence Preview ──
        renderEvidencePreview(d.task_evidence_preview);
        // ── P4-T6: Render Task Gateway Result ──
        renderTaskGatewayResult(d.task_gateway_result);
        // ── P5-T5: Plan-only strategy & risk card (task-like input only) ──
        fetchTaskPlan(d.task_detection);
      } else {
        addMsg('⚠️ '+d.answer, false);
      }
    }catch(e){
      hideLoading();
      addMsg('❌ 連線錯誤, 請重試', false);
    }
  }

  if(btn) btn.onclick=sendMsg;
  if(inp){
    inp.addEventListener('keydown',function(e){
      if(e.key==='Enter'){ e.preventDefault(); sendMsg(); }
    });
  }
})();

</script>
</body></html>"""
