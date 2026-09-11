#!/usr/bin/env python3
# Presence Watchdog - Monitor all nodes and their status
# Deploy on AiKa-1 (192.168.1.207)
# systemd service: presence-watchdog.service

import os
import json
import time
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

LOG_PATH = os.path.expanduser('~/goaa-ai/logs/presence-watchdog.log')
REGISTRY_PATH = os.path.expanduser('~/goaa-ai/runtime/presence_registry.json')

def ensure_dirs():
    """Ensure required directories exist"""
    Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(REGISTRY_PATH).parent.mkdir(parents=True, exist_ok=True)

def log_message(msg):
    """Log to file and console"""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_PATH, 'a') as f:
        f.write(log_entry + '\n')

def load_registry():
    """Load presence registry"""
    if Path(REGISTRY_PATH).exists():
        with open(REGISTRY_PATH, 'r') as f:
            return json.load(f)
    return {'nodes': {}, 'services': {}, 'last_updated': None}

def save_registry(registry):
    """Save presence registry"""
    ensure_dirs()
    registry['last_updated'] = datetime.utcnow().isoformat() + 'Z'
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)

def check_node_health(node_ip, node_id):
    """Check if node is healthy"""
    try:
        response = requests.get(f'http://{node_ip}:5001/health', timeout=5)
        if response.status_code == 200:
            return True, 'ONLINE'
    except requests.exceptions.RequestException:
        pass
    return False, 'OFFLINE'

def monitor_nodes():
    """Monitor all known nodes"""
    log_message("========== Presence Watchdog Cycle Start ==========")
    
    registry = load_registry()
    nodes_checked = 0
    nodes_online = 0
    nodes_offline = 0
    
    # Check AiKa-2
    nodes = {
        'aika-2': '192.168.1.208',
        'aika-1': '192.168.1.207',
        'akc-001': '5.78.76.21'
    }
    
    for node_id, node_ip in nodes.items():
        try:
            is_healthy, status = check_node_health(node_ip, node_id)
            nodes_checked += 1
            
            if is_healthy:
                nodes_online += 1
                log_message(f"✅ {node_id} ({node_ip}): ONLINE")
                registry['nodes'][node_id] = {
                    'ip': node_ip,
                    'status': 'ONLINE',
                    'last_check': datetime.utcnow().isoformat() + 'Z',
                    'consecutive_failures': 0
                }
            else:
                nodes_offline += 1
                if node_id in registry['nodes']:
                    registry['nodes'][node_id]['consecutive_failures'] += 1
                    log_message(f"❌ {node_id} ({node_ip}): OFFLINE (failures: {registry['nodes'][node_id]['consecutive_failures']})")
                else:
                    log_message(f"❌ {node_id} ({node_ip}): OFFLINE")
                    registry['nodes'][node_id] = {
                        'ip': node_ip,
                        'status': 'OFFLINE',
                        'last_check': datetime.utcnow().isoformat() + 'Z',
                        'consecutive_failures': 1
                    }
        except Exception as e:
            log_message(f"⚠️  Error checking {node_id}: {str(e)}")
            nodes_offline += 1
    
    # Update registry
    save_registry(registry)
    
    # Summary
    log_message(f"========== Summary: {nodes_online}/{nodes_checked} nodes ONLINE ==========")
    return registry

def main():
    """Main watchdog loop"""
    log_message("========== Presence Watchdog Starting ==========")
    log_message(f"Python process: PID {os.getpid()}")
    log_message(f"Registry: {REGISTRY_PATH}")
    log_message(f"Logs: {LOG_PATH}")
    
    ensure_dirs()
    
    # Initial check
    log_message("Performing initial presence check...")
    monitor_nodes()
    
    # Loop
    log_message("Starting monitoring loop (60 second intervals)...")
    cycle = 0
    while True:
        try:
            cycle += 1
            time.sleep(60)  # Check every 60 seconds
            log_message(f"\n=== Monitoring Cycle {cycle} ===")
            monitor_nodes()
        except KeyboardInterrupt:
            log_message("Watchdog stopped by user")
            break
        except Exception as e:
            log_message(f"ERROR in monitoring cycle: {str(e)}")
            time.sleep(60)

if __name__ == '__main__':
    main()
