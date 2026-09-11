from fastapi import FastAPI, HTTPException
from datetime import datetime
import time
import json

app = FastAPI(title="GOAA Cloud Worker", version="1.0.0")

# Global state
START_TIME = time.time()
NODE_ID = "AKC-DO-001"
COORDINATOR_IP = "192.168.1.207"

@app.get("/health")
def health():
    """Task 2: Health check endpoint"""
    return {
        "status": "ok",
        "node": NODE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": int(time.time() - START_TIME),
        "runtime_version": "1.0.0",
        "services": {
            "openclaw": "healthy",
            "heartbeat": "active"
        }
    }

@app.post("/heartbeat")
def heartbeat(data: dict):
    """Task 3: Heartbeat endpoint"""
    return {
        "received": True,
        "node_id": NODE_ID,
        "next_heartbeat_interval": 30,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/v1/node/info")
def node_info():
    """Node information endpoint"""
    return {
        "node_id": NODE_ID,
        "ip": "134.199.227.108",
        "role": "cloud_worker",
        "capabilities": ["python", "docker", "linux", "git"],
        "status": "active",
        "uptime_seconds": int(time.time() - START_TIME)
    }

@app.post("/api/v1/node/register")
def register_node(data: dict):
    """Task 4: Worker registration API"""
    required_fields = ["node_id", "hostname", "role", "capabilities", "ip"]
    if not all(field in data for field in required_fields):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    return {
        "registered": True,
        "node_id": data.get("node_id"),
        "status": "active",
        "coordinator_ip": COORDINATOR_IP,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/v1/task/pull")
def pull_tasks(node_id: str = NODE_ID, max_tasks: int = 5):
    """Task 7: Task pull system"""
    return {
        "node_id": node_id,
        "tasks": [],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.post("/api/v1/task/result")
def submit_result(data: dict):
    """Submit task execution result"""
    return {
        "received": True,
        "task_id": data.get("task_id"),
        "node_id": NODE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "GOAA Cloud Worker",
        "version": "1.0.0",
        "node": NODE_ID,
        "status": "ready"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18789)
