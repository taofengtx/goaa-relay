#!/usr/bin/env python3
"""
AiKa-2 Bootstrap Script (NODE-20260509-002-L1)
Execute on AiKa-2 (192.168.1.208)
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

def run_command(cmd, description=""):
    """Run command and return output"""
    try:
        if description:
            print(f"\n[*] {description}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"✅ {description}" if description else "✅ Command executed")
            return result.stdout.strip()
        else:
            print(f"⚠️  Warning: {description} returned code {result.returncode}")
            return result.stderr.strip()
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout: {description}")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    print("=" * 50)
    print("NODE-20260509-002-L1: AiKa-2 Bootstrap")
    print("=" * 50)
    
    # Step 1: System Update
    print("\n[1/6] System Update...")
    run_command("sudo apt-get update -y", "Updating apt cache")
    run_command("sudo apt-get install -y git curl python3 python3-pip python3-venv docker.io", 
                "Installing packages")
    
    # Step 2: Create directories
    print("\n[2/6] Creating directory structure...")
    os.makedirs("/opt/goaa", exist_ok=True)
    os.makedirs("/opt/goaa/logs", exist_ok=True)
    os.makedirs("/opt/goaa/data", exist_ok=True)
    os.makedirs("/opt/goaa/config", exist_ok=True)
    print("✅ Directory structure created")
    
    # Step 3: Clone repository
    print("\n[3/6] Cloning/updating repository...")
    if os.path.exists("/opt/goaa/repo"):
        run_command("cd /opt/goaa/repo && git pull origin main", "Updating repository")
    else:
        run_command("cd /opt/goaa && git clone https://github.com/taofengtx/goaa-ai-frontend.git repo", 
                    "Cloning repository")
    
    # Step 4: Python venv
    print("\n[4/6] Setting up Python virtual environment...")
    run_command("cd /opt/goaa && python3 -m venv venv", "Creating venv")
    run_command("cd /opt/goaa && source venv/bin/activate && pip install -q fastapi uvicorn httpx psutil requests flask", 
                "Installing Python packages")
    
    # Step 5: Create registration file
    print("\n[5/6] Creating node registration...")
    registration = {
        "node_id": "COORD-002",
        "hostname": "AiKa-2",
        "ip": "192.168.1.208",
        "role": "secondary_coordinator",
        "status": "active",
        "capabilities": {
            "cpu_cores": 4,
            "memory_gb": 8,
            "docker": True,
            "gpu": False
        },
        "services": {
            "heartbeat_api": {
                "port": 5001,
                "status": "ready_for_deployment"
            },
            "task_pull_api": {
                "port": 5002,
                "status": "ready_for_deployment"
            }
        },
        "registered_at": datetime.utcnow().isoformat() + "Z"
    }
    
    with open("/opt/goaa/registration.json", "w") as f:
        json.dump(registration, f, indent=2)
    print("✅ Node registration created")
    
    # Step 6: Verify
    print("\n[6/6] Verifying installation...")
    print("\n=== Node Registration ===")
    with open("/opt/goaa/registration.json", "r") as f:
        print(f.read())
    
    print("\n=== System Info ===")
    run_command("uname -a", "")
    
    print("\n=== Memory ===")
    run_command("free -h", "")
    
    print("\n=== Disk ===")
    run_command("df -h /", "")
    
    print("\n=== Python ===")
    run_command("/opt/goaa/venv/bin/python3 --version", "")
    
    print("\n" + "=" * 50)
    print("✅ NODE-20260509-002-L1 Bootstrap Complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("  1. Deploy Heartbeat API: systemctl start node-heartbeat-api")
    print("  2. Deploy Task Pull API: systemctl start task-pull-api")
    print("  3. Check logs: journalctl -u node-heartbeat-api -f")

if __name__ == "__main__":
    main()
