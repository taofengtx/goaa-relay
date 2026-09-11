"""
GOAA.AI OpenClaw API Gateway v2.0
Rebuilt for DigitalOcean deployment
All 31 endpoints restored
"""
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging, json, os, uuid, time, asyncio, httpx, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from pathlib import Path

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('OpenClaw.main')

# ── Config ────────────────────────────────────────────────────
BASE_DIR     = Path("/opt/goaa")
USERS_FILE   = BASE_DIR / "users.json"
CREDITS_FILE = BASE_DIR / "credits_config.json"
DOWNLOADS_DIR= BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

QWENPAW_URL  = os.getenv("QWENPAW_URL",    "http://127.0.0.1:8088")
SMTP_HOST    = os.getenv("ZOHO_SMTP_HOST", "smtp.zoho.com")
SMTP_PORT    = int(os.getenv("ZOHO_SMTP_PORT", "587"))
SMTP_USER    = os.getenv("ZOHO_SMTP_USER", "aika@goaa.ai")
SMTP_PASS    = os.getenv("ZOHO_SMTP_PASSWORD", "")
NODE_ID      = os.getenv("NODE_ID", "AKC-DO-001")

# ── In-memory stores ──────────────────────────────────────────
sessions: Dict[str, dict]     = {}
aika_devices: Dict[str, dict] = {}
study_sessions: Dict[str, dict]= {}

# ── Users ─────────────────────────────────────────────────────
def load_users() -> list:
    try:
        with open(USERS_FILE) as f:
            data = json.load(f)
            return data.get("users", data.get("agents", []))
    except:
        return []

def save_users(users: list):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump({"users": users}, f, indent=2)
    except Exception as e:
        logger.error(f"Save users failed: {e}")

def load_credits() -> dict:
    try:
        with open(CREDITS_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_credits(data: dict):
    try:
        with open(CREDITS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except: pass

logger.info("✦ OpenClaw engine initialized")

# ── FastAPI ───────────────────────────────────────────────────
app = FastAPI(
    title="OpenClaw API Gateway",
    description="Bridge between Framer frontend and QwenPaw Agent backend",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://portal.goaa.ai",
        "https://api.goaa.ai",
        "https://goaa.ai",
        "https://www.goaa.ai",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"https://.*\.framer\.(app|com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for downloads
app.mount("/downloads", StaticFiles(directory=str(DOWNLOADS_DIR)), name="downloads")
logger.info("✦ StaticFiles mounted at /downloads")

# ── Schemas ───────────────────────────────────────────────────
class AgentLogin(BaseModel):
    email: str
    password: str

class AgentRegister(BaseModel):
    name: str
    email: str
    password: str
    license_number: Optional[str] = ""
    phone: Optional[str] = ""

class ClientLogin(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None
    context: Optional[dict] = {}

class AikaRegister(BaseModel):
    device_id: str
    user_id: str
    device_info: Optional[dict] = {}

class AikaHeartbeat(BaseModel):
    device_id: str
    status: Optional[str] = "active"
    info: Optional[dict] = {}

class CreditTopup(BaseModel):
    amount: int
    reason: Optional[str] = "manual_topup"

class CreditDeduct(BaseModel):
    amount: int
    reason: Optional[str] = "usage"
    task_id: Optional[str] = ""

class SkillUpload(BaseModel):
    name: str
    description: str
    category: str
    price_credits: int
    developer_id: str
    code: Optional[str] = ""

class EmailNotify(BaseModel):
    to: Optional[str] = None
    subject: str
    content: str
    smtp_password: Optional[str] = None

class WriteFile(BaseModel):
    path: str
    content: str

class QwenPawRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = "anonymous"
    context: Optional[dict] = {}

# ── Helpers ───────────────────────────────────────────────────
def get_user(email: str) -> Optional[dict]:
    for u in load_users():
        if u.get("email") == email:
            return u
    return None

def verify_password(stored: str, provided: str) -> bool:
    try:
        import bcrypt
        if stored.startswith("$2"):
            return bcrypt.checkpw(provided.encode(), stored.encode())
    except:
        pass
    return stored == provided

def create_session(user_id: str, role: str = "agent") -> str:
    token = str(uuid.uuid4())
    sessions[user_id] = {"token": token, "role": role,
                          "created_at": datetime.utcnow().isoformat()}
    return token

def send_email(to: str, subject: str, content: str, smtp_password: str = None) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"]    = SMTP_USER
        msg["To"]      = to
        msg.attach(MIMEText(content, "plain", "utf-8"))
        pw = smtp_password or SMTP_PASS
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, pw)
            s.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return False

# ── Routes ────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"service": "OpenClaw API Gateway", "version": "2.0.0",
            "node": NODE_ID, "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok", "node": NODE_ID,
            "time": datetime.utcnow().isoformat() + "Z",
            "version": "2.0.0"}

# ── Auth ──────────────────────────────────────────────────────
@app.post("/api/v1/agent/login")
def agent_login(req: AgentLogin):
    user = get_user(req.email)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    if not verify_password(user.get("password", ""), req.password):
        raise HTTPException(401, "Invalid credentials")
    if user.get("status") not in ("active", None, ""):
        raise HTTPException(403, "Account inactive")
    token = create_session(user["id"] if "id" in user else req.email, "agent")
    logger.info(f"✦ Agent demo ({user.get('name','')}) ✦ ✦ ✦")
    return {"status": "success", "token": token,
            "user": {k: v for k, v in user.items() if k != "password"}}

@app.post("/api/v1/agent/register")
def agent_register(req: AgentRegister):
    users = load_users()
    if any(u.get("email") == req.email for u in users):
        raise HTTPException(400, "Email already registered")
    new_user = {"id": str(uuid.uuid4()), "name": req.name, "email": req.email,
                "password": req.password, "phone": req.phone,
                "license_number": req.license_number,
                "role": "agent", "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "credits": 100}
    users.append(new_user)
    save_users(users)
    return {"status": "success", "message": "Agent registered",
            "user_id": new_user["id"]}

@app.post("/api/v1/client/login")
def client_login(req: ClientLogin):
    user = get_user(req.email)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    if not verify_password(user.get("password", ""), req.password):
        raise HTTPException(401, "Invalid credentials")
    token = create_session(req.email, "client")
    return {"status": "success", "token": token,
            "user": {k: v for k, v in user.items() if k != "password"}}

# ── Agents ────────────────────────────────────────────────────
@app.get("/api/v1/agents")
def list_agents():
    users = [u for u in load_users() if u.get("role") in ("agent", None)]
    return {"agents": [{k: v for k, v in u.items() if k != "password"} for u in users]}

@app.get("/api/v1/agents/{agent_id}")
def get_agent(agent_id: str):
    users = load_users()
    for u in users:
        if u.get("id") == agent_id or u.get("email") == agent_id:
            return {k: v for k, v in u.items() if k != "password"}
    raise HTTPException(404, "Agent not found")

@app.post("/api/v1/agents/{agent_id}/chat")
async def agent_chat(agent_id: str, req: ChatRequest):
    return await _forward_to_qwenpaw(req)

@app.post("/api/v1/agents/qwenpaw/execute")
async def execute_qwenpaw(req: QwenPawRequest):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{QWENPAW_URL}/execute",
                json={"prompt": req.prompt, "user_id": req.user_id,
                      "context": req.context})
            return r.json()
    except Exception as e:
        logger.error(f"QwenPaw execute error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/agents/study/start")
def study_start(req: ChatRequest):
    session_id = str(uuid.uuid4())
    study_sessions[req.user_id] = {"session_id": session_id,
                                    "status": "active",
                                    "started_at": datetime.utcnow().isoformat(),
                                    "messages": []}
    return {"status": "success", "session_id": session_id}

@app.get("/api/v1/agents/study/status/{user_id}")
def study_status(user_id: str):
    s = study_sessions.get(user_id, {"status": "inactive"})
    return s

@app.post("/api/v1/agents/study/stop/{user_id}")
def study_stop(user_id: str):
    study_sessions.pop(user_id, None)
    return {"status": "success", "message": "Study session stopped"}

# ── Chat ──────────────────────────────────────────────────────
@app.post("/api/v1/chat")
async def chat_proxy(req: ChatRequest):
    return await _forward_to_qwenpaw(req)

async def _forward_to_qwenpaw(req: ChatRequest) -> dict:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{QWENPAW_URL}/chat",
                json={"message": req.message, "user_id": req.user_id,
                      "session_id": req.session_id, "context": req.context})
            return r.json()
    except Exception as e:
        logger.warning(f"QwenPaw unavailable: {e}")
        return {"status": "success", "response": "AI 服務暫時不可用，請稍後再試。",
                "session_id": req.session_id or str(uuid.uuid4())}

# WebSocket for real-time chat
@app.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            req = ChatRequest(message=msg.get("message",""), user_id=user_id)
            resp = await _forward_to_qwenpaw(req)
            await websocket.send_json({"type": "response", "data": resp,
                                        "ts": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        logger.info(f"WS disconnected: {user_id}")

# ── Credits ───────────────────────────────────────────────────
@app.get("/api/v1/credits/{user_id}")
def get_credits(user_id: str):
    users = load_users()
    for u in users:
        if u.get("id") == user_id or u.get("email") == user_id:
            balance = u.get("credits", 0)
            logger.info(f"GET /api/v1/credits/{user_id} → {balance}")
            return {"user_id": user_id, "balance": balance,
                    "currency": "Credits", "ts": datetime.utcnow().isoformat()}
    return {"user_id": user_id, "balance": 0}

@app.post("/api/v1/credits/{user_id}/topup")
def topup_credits(user_id: str, req: CreditTopup):
    users = load_users()
    for u in users:
        if u.get("id") == user_id or u.get("email") == user_id:
            u["credits"] = u.get("credits", 0) + req.amount
            save_users(users)
            return {"status": "success", "balance": u["credits"],
                    "added": req.amount}
    raise HTTPException(404, "User not found")

@app.post("/api/v1/credits/{user_id}/deduct")
def deduct_credits(user_id: str, req: CreditDeduct):
    users = load_users()
    for u in users:
        if u.get("id") == user_id or u.get("email") == user_id:
            if u.get("credits", 0) < req.amount:
                raise HTTPException(400, "Insufficient credits")
            u["credits"] = u["credits"] - req.amount
            save_users(users)
            return {"status": "success", "balance": u["credits"],
                    "deducted": req.amount}
    raise HTTPException(404, "User not found")

# ── AiKa Devices ─────────────────────────────────────────────
@app.post("/api/v1/aika/register")
def aika_register(req: AikaRegister):
    aika_devices[req.device_id] = {
        "device_id": req.device_id, "user_id": req.user_id,
        "status": "active", "registered_at": datetime.utcnow().isoformat(),
        "last_heartbeat": datetime.utcnow().isoformat(),
        "device_info": req.device_info or {}
    }
    logger.info(f"✦ Device registered: {req.device_id}")
    return {"status": "success", "device_id": req.device_id,
            "message": f"Device {req.device_id} registered successfully",
            "deploy_script_url": f"/api/v1/aika/deploy-script/{req.user_id}",
            "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.get("/api/v1/aika/devices")
def list_aika_devices():
    return {"devices": list(aika_devices.values()),
            "count": len(aika_devices)}

@app.get("/api/v1/aika/devices/{device_id}")
def get_aika_device(device_id: str):
    d = aika_devices.get(device_id)
    if not d:
        raise HTTPException(404, "Device not found")
    return d

@app.post("/api/v1/aika/heartbeat")
def aika_heartbeat_global(req: AikaHeartbeat):
    if req.device_id in aika_devices:
        aika_devices[req.device_id]["last_heartbeat"] = datetime.utcnow().isoformat()
        aika_devices[req.device_id].update(req.info or {})
    else:
        aika_devices[req.device_id] = {"device_id": req.device_id,
                                        "status": req.status,
                                        "last_heartbeat": datetime.utcnow().isoformat(),
                                        **req.info}
    return {"status": "ok", "ts": datetime.utcnow().isoformat() + "Z"}

@app.post("/api/v1/aika/{device_id}/heartbeat")
def aika_device_heartbeat(device_id: str, req: Request):
    if device_id in aika_devices:
        aika_devices[device_id]["last_heartbeat"] = datetime.utcnow().isoformat()
    return {"status": "ok", "device_id": device_id}

@app.get("/api/v1/aika/{device_id}/status")
def aika_device_status(device_id: str):
    d = aika_devices.get(device_id, {"device_id": device_id, "status": "unknown"})
    return d

# ── Skills ────────────────────────────────────────────────────
_skills: Dict[str, dict] = {}

BUILTIN_SKILLS = [
    {"id":"skill_tax_001",   "name":"稅務規劃助手",  "category":"tax",      "price_credits":50,  "developer_id":"goaa_official", "downloads":1240},
    {"id":"skill_ins_001",   "name":"保險分析工具",  "category":"insurance","price_credits":30,  "developer_id":"goaa_official", "downloads":890},
    {"id":"skill_real_001",  "name":"房產投資計算",  "category":"realestate","price_credits":40, "developer_id":"goaa_official", "downloads":650},
    {"id":"skill_imm_001",   "name":"移民路徑規劃",  "category":"immigration","price_credits":60,"developer_id":"goaa_official", "downloads":420},
    {"id":"skill_edu_001",   "name":"升學申請顧問",  "category":"education","price_credits":35,  "developer_id":"goaa_official", "downloads":310},
]

@app.get("/api/v1/skills")
def list_skills():
    all_skills = BUILTIN_SKILLS + list(_skills.values())
    return {"skills": all_skills, "count": len(all_skills)}

@app.get("/api/v1/skills/{skill_id}")
def get_skill(skill_id: str):
    for s in BUILTIN_SKILLS:
        if s["id"] == skill_id:
            return s
    if skill_id in _skills:
        return _skills[skill_id]
    raise HTTPException(404, "Skill not found")

@app.post("/api/v1/skills/upload")
def upload_skill(req: SkillUpload):
    skill_id = f"skill_{req.category}_{str(uuid.uuid4())[:8]}"
    _skills[skill_id] = {"id": skill_id, **req.dict(),
                          "created_at": datetime.utcnow().isoformat(),
                          "downloads": 0}
    return {"status": "success", "skill_id": skill_id}

@app.get("/api/v1/skills/developer/{developer_id}")
def get_developer_skills(developer_id: str):
    skills = [s for s in _skills.values() if s.get("developer_id") == developer_id]
    return {"skills": skills}

@app.post("/api/v1/skills/{skill_id}/purchase")
def purchase_skill(skill_id: str, request: Request):
    skill = None
    for s in BUILTIN_SKILLS:
        if s["id"] == skill_id: skill = s; break
    if not skill: skill = _skills.get(skill_id)
    if not skill: raise HTTPException(404, "Skill not found")
    return {"status": "success", "skill_id": skill_id,
            "message": f"Skill {skill['name']} purchased"}

@app.post("/api/v1/skills/{skill_id}/use")
async def use_skill(skill_id: str, req: ChatRequest):
    return {"status": "success", "skill_id": skill_id,
            "result": f"Skill executed for: {req.message[:50]}"}

# ── Session ───────────────────────────────────────────────────
@app.delete("/api/v1/session/{user_id}")
def delete_session(user_id: str):
    sessions.pop(user_id, None)
    return {"status": "success", "message": "Session deleted"}

# ── Notify ────────────────────────────────────────────────────
@app.post("/api/v1/notify/email")
def notify_email(req: EmailNotify):
    to = req.to or "taofengtx@gmail.com"
    success = send_email(to, req.subject, req.content, req.smtp_password)
    return {"status": "success" if success else "error",
            "to": to, "subject": req.subject}

# ── Write File ────────────────────────────────────────────────
@app.post("/api/v1/write-file")
def write_file(req: WriteFile):
    try:
        p = Path(req.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success", "path": str(p), "size": len(req.content)}
    except Exception as e:
        raise HTTPException(500, str(e))

# ── Geekom/Worker Heartbeat (for Model Router) ────────────────
@app.post("/api/v1/geekom/heartbeat")
def geekom_heartbeat(request: dict = None):
    return {"status": "ok", "ts": datetime.utcnow().isoformat() + "Z"}

logger.info("✦ CORS middleware configured for Framer and goaa.ai")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18789, log_level="info")
