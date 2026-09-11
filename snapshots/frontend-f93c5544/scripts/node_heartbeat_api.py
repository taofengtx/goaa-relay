#!/usr/bin/env python3
# Node Heartbeat API - Real Persistent Runtime
# Deploy on AiKa-2 (192.168.1.208)
# systemd service: node-heartbeat-api.service

import flask
import sqlite3
import json
import os
import psutil
from datetime import datetime
from pathlib import Path

app = flask.Flask(__name__)

# Database path
DB_PATH = os.path.expanduser('~/goaa-ai/runtime/node_presence.db')
LOG_PATH = os.path.expanduser('~/goaa-ai/logs/heartbeat-api.log')

def ensure_dirs():
    """Ensure required directories exist"""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)

def log_message(msg):
    """Log to file and console"""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_PATH, 'a') as f:
        f.write(log_entry + '\n')

def init_db():
    """Initialize SQLite database"""
    ensure_dirs()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                last_heartbeat TEXT,
                status TEXT,
                cpu_usage REAL,
                ram_usage REAL,
                active_tasks INTEGER,
                queue_status TEXT,
                uptime INTEGER,
                capabilities TEXT,
                runtime_state TEXT,
                created_at TEXT
            )
        ''')
        conn.commit()
        conn.close()
        log_message("Database initialized successfully")
    except Exception as e:
        log_message(f"ERROR: Database init failed: {e}")

@app.route('/api/v1/node/heartbeat', methods=['POST'])
def heartbeat():
    """Receive node heartbeat"""
    try:
        data = flask.request.json
        node_id = data.get('node_id', 'unknown')
        timestamp = datetime.utcnow().isoformat() + 'Z'
        cpu_usage = float(data.get('cpu_usage', 0))
        ram_usage = float(data.get('ram_usage', 0))
        
        # Determine status
        if cpu_usage > 90:
            status = 'BUSY'
        elif cpu_usage > 70:
            status = 'DEGRADED'
        else:
            status = 'ONLINE'
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO nodes
            (node_id, last_heartbeat, status, cpu_usage, ram_usage, active_tasks, queue_status, uptime, capabilities, runtime_state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            node_id,
            timestamp,
            status,
            cpu_usage,
            ram_usage,
            data.get('active_tasks', 0),
            data.get('queue_status', 'empty'),
            data.get('uptime', 0),
            json.dumps(data.get('capabilities', [])),
            data.get('runtime_state', 'active'),
            datetime.utcnow().isoformat() + 'Z'
        ))
        conn.commit()
        conn.close()
        
        log_message(f"Heartbeat received from {node_id}: status={status}, cpu={cpu_usage}%, ram={ram_usage}%")
        
        return flask.jsonify({
            'status': 'received',
            'node_id': node_id,
            'timestamp': timestamp
        }), 200
    except Exception as e:
        log_message(f"ERROR in heartbeat: {str(e)}")
        return flask.jsonify({'error': str(e)}), 500

@app.route('/api/v1/node/status', methods=['GET'])
def get_node_status():
    """Get node status"""
    try:
        node_id = flask.request.args.get('node_id')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM nodes WHERE node_id = ?', (node_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            log_message(f"Status query for {node_id}: {row[2]}")
            return flask.jsonify({
                'node_id': row[0],
                'last_heartbeat': row[1],
                'status': row[2],
                'cpu': row[3],
                'ram': row[4],
                'active_tasks': row[5],
                'uptime': row[7]
            }), 200
        
        log_message(f"Status query failed: Node {node_id} not found")
        return flask.jsonify({'error': 'Node not found'}), 404
    except Exception as e:
        log_message(f"ERROR in get_node_status: {str(e)}")
        return flask.jsonify({'error': str(e)}), 500

@app.route('/api/v1/nodes/all', methods=['GET'])
def get_all_nodes():
    """Get all nodes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT node_id, last_heartbeat, status, cpu_usage, ram_usage, active_tasks FROM nodes')
        rows = cursor.fetchall()
        conn.close()
        
        nodes = []
        for row in rows:
            nodes.append({
                'node_id': row[0],
                'last_heartbeat': row[1],
                'status': row[2],
                'cpu': row[3],
                'ram': row[4],
                'tasks': row[5]
            })
        
        log_message(f"All nodes query: {len(nodes)} nodes found")
        return flask.jsonify({'nodes': nodes}), 200
    except Exception as e:
        log_message(f"ERROR in get_all_nodes: {str(e)}")
        return flask.jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return flask.jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat() + 'Z'}), 200

def main():
    """Main entry point"""
    log_message("========== Node Heartbeat API Starting ==========")
    log_message(f"Python process: PID {os.getpid()}")
    log_message(f"Database: {DB_PATH}")
    log_message(f"Logs: {LOG_PATH}")
    init_db()
    log_message("Starting Flask on 0.0.0.0:5001...")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)

if __name__ == '__main__':
    main()
