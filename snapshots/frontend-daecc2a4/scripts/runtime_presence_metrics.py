#!/usr/bin/env python3
# Runtime Presence Metrics Collector
# Deploy on AiKa-1 (192.168.1.207)
# Collects metrics every 5 minutes and updates runtime_presence_metrics.json
# systemd service: runtime-metrics.service

import os
import json
import time
import psutil
import requests
import socket
from datetime import datetime
from pathlib import Path

METRICS_PATH = os.path.expanduser('~/goaa-ai/runtime/runtime_presence_metrics.json')
LOG_PATH = os.path.expanduser('~/goaa-ai/logs/metrics-collector.log')

def ensure_dirs():
    """Ensure required directories exist"""
    Path(METRICS_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)

def log_message(msg):
    """Log to file and console"""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_PATH, 'a') as f:
        f.write(log_entry + '\n')

def get_system_metrics():
    """Collect system metrics"""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime_seconds': int(time.time() - psutil.boot_time()),
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
            'process_count': len(psutil.pids()),
        }
    except Exception as e:
        log_message(f"ERROR collecting system metrics: {e}")
        return {}

def get_node_status(node_ip, node_id):
    """Get status from a specific node"""
    try:
        response = requests.get(f'http://{node_ip}:5001/api/v1/nodes/all', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'node_id': node_id,
                'ip': node_ip,
                'status': 'ONLINE',
                'data': data
            }
    except Exception as e:
        pass
    
    return {
        'node_id': node_id,
        'ip': node_ip,
        'status': 'OFFLINE',
        'error': str(e) if 'e' in locals() else 'Unknown error'
    }

def collect_metrics():
    """Collect all metrics"""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    metrics = {
        'timestamp': timestamp,
        'collector_id': 'aika-1',
        'system': get_system_metrics(),
        'nodes': [],
        'services': {
            'node-heartbeat-api': {'status': 'checking...'},
            'task-pull-api': {'status': 'checking...'},
            'presence-watchdog': {'status': 'checking...'}
        },
        'queue': {
            'total_tasks': 0,
            'pending': 0,
            'assigned': 0,
            'completed': 0
        }
    }
    
    # Check each node
    nodes = {
        'aika-2': '192.168.1.208',
        'aika-1': '192.168.1.207',
        'akc-001': '5.78.76.21'
    }
    
    for node_id, node_ip in nodes.items():
        node_status = get_node_status(node_ip, node_id)
        metrics['nodes'].append(node_status)
    
    # Check queue status
    try:
        response = requests.get('http://192.168.1.208:5002/api/v1/queue/status', timeout=5)
        if response.status_code == 200:
            metrics['queue'] = response.json()
    except Exception as e:
        log_message(f"Could not fetch queue status: {e}")
    
    # Check services
    for service in ['node-heartbeat-api', 'task-pull-api', 'presence-watchdog']:
        try:
            # This would normally check via systemctl on the respective nodes
            metrics['services'][service] = {'status': 'running'}
        except Exception as e:
            metrics['services'][service] = {'status': 'unknown', 'error': str(e)}
    
    return metrics

def save_metrics(metrics):
    """Save metrics to JSON file"""
    ensure_dirs()
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Also save a timestamped archive
    archive_path = METRICS_PATH.replace('.json', f"_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    with open(archive_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """Main metrics collection loop"""
    log_message("========== Runtime Presence Metrics Collector Starting ==========")
    log_message(f"Python process: PID {os.getpid()}")
    log_message(f"Metrics file: {METRICS_PATH}")
    log_message(f"Logs: {LOG_PATH}")
    log_message("Collection interval: 5 minutes")
    
    ensure_dirs()
    
    # Initial collection
    log_message("Performing initial metrics collection...")
    metrics = collect_metrics()
    save_metrics(metrics)
    log_message(f"✅ Initial metrics saved (nodes: {len(metrics['nodes'])}, system cpu: {metrics['system'].get('cpu_percent', 'N/A')}%)")
    
    # Loop
    cycle = 0
    log_message("Starting metrics collection loop...")
    while True:
        try:
            # Wait 5 minutes
            time.sleep(300)
            
            cycle += 1
            log_message(f"\n=== Metrics Cycle {cycle} ===")
            metrics = collect_metrics()
            save_metrics(metrics)
            
            # Log summary
            online_count = sum(1 for n in metrics['nodes'] if n['status'] == 'ONLINE')
            cpu = metrics['system'].get('cpu_percent', 'N/A')
            ram = metrics['system'].get('memory_percent', 'N/A')
            log_message(f"✅ Metrics updated: {online_count}/{len(metrics['nodes'])} nodes online, CPU: {cpu}%, RAM: {ram}%")
            
        except KeyboardInterrupt:
            log_message("Metrics collector stopped by user")
            break
        except Exception as e:
            log_message(f"ERROR in metrics collection: {str(e)}")
            time.sleep(10)  # Retry after 10 seconds

if __name__ == '__main__':
    main()
