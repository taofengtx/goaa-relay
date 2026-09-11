#!/usr/bin/env python3
# Task Pull API - Node pulls tasks from queue
# Deploy on AiKa-2 (192.168.1.208)
# systemd service: task-pull-api.service

import flask
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

app = flask.Flask(__name__)

# Database path
DB_PATH = os.path.expanduser('~/goaa-ai/runtime/task_queue.db')
LOG_PATH = os.path.expanduser('~/goaa-ai/logs/task-pull-api.log')

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
            CREATE TABLE IF NOT EXISTS task_queue (
                task_id TEXT PRIMARY KEY,
                task_name TEXT,
                status TEXT,
                node_id TEXT,
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                priority INTEGER,
                payload TEXT,
                result TEXT
            )
        ''')
        conn.commit()
        conn.close()
        log_message("Task database initialized successfully")
    except Exception as e:
        log_message(f"ERROR: Task database init failed: {e}")

@app.route('/api/v1/task/pull', methods=['POST'])
def pull_task():
    """Node pulls task from queue"""
    try:
        data = flask.request.json
        node_id = data.get('node_id', 'unknown')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get pending task
        cursor.execute('''
            SELECT task_id, task_name, priority, payload FROM task_queue
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        ''')
        
        task = cursor.fetchone()
        
        if task:
            task_id, task_name, priority, payload = task
            # Mark as assigned
            cursor.execute('''
                UPDATE task_queue
                SET status = 'assigned', node_id = ?, started_at = ?
                WHERE task_id = ?
            ''', (node_id, datetime.utcnow().isoformat() + 'Z', task_id))
            conn.commit()
            
            log_message(f"Task {task_id} pulled by {node_id}: {task_name}")
            
            conn.close()
            return flask.jsonify({
                'task_id': task_id,
                'task_name': task_name,
                'priority': priority,
                'payload': json.loads(payload) if payload else {},
                'status': 'assigned'
            }), 200
        
        conn.close()
        log_message(f"No tasks available for {node_id}")
        return flask.jsonify({'task_id': None, 'status': 'no_tasks'}), 204
        
    except Exception as e:
        log_message(f"ERROR in pull_task: {str(e)}")
        return flask.jsonify({'error': str(e)}), 500

@app.route('/api/v1/task/submit', methods=['POST'])
def submit_task_result():
    """Node submits completed task result"""
    try:
        data = flask.request.json
        task_id = data.get('task_id')
        node_id = data.get('node_id')
        result = data.get('result')
        status = data.get('status', 'completed')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE task_queue
            SET status = ?, result = ?, completed_at = ?
            WHERE task_id = ?
        ''', (status, json.dumps(result), datetime.utcnow().isoformat() + 'Z', task_id))
        conn.commit()
        conn.close()
        
        log_message(f"Task {task_id} completed by {node_id}")
        
        return flask.jsonify({'status': 'submitted', 'task_id': task_id}), 200
    except Exception as e:
        log_message(f"ERROR in submit_task_result: {str(e)}")
        return flask.jsonify({'error': str(e)}), 500

@app.route('/api/v1/queue/status', methods=['GET'])
def queue_status():
    """Get queue status"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM task_queue WHERE status = 'pending'")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM task_queue WHERE status = 'assigned'")
        assigned = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM task_queue WHERE status = 'completed'")
        completed = cursor.fetchone()[0]
        
        conn.close()
        
        log_message(f"Queue status: pending={pending}, assigned={assigned}, completed={completed}")
        
        return flask.jsonify({
            'pending': pending,
            'assigned': assigned,
            'completed': completed,
            'total': pending + assigned + completed
        }), 200
    except Exception as e:
        log_message(f"ERROR in queue_status: {str(e)}")
        return flask.jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return flask.jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat() + 'Z'}), 200

def main():
    """Main entry point"""
    log_message("========== Task Pull API Starting ==========")
    log_message(f"Python process: PID {os.getpid()}")
    log_message(f"Database: {DB_PATH}")
    log_message(f"Logs: {LOG_PATH}")
    init_db()
    log_message("Starting Flask on 0.0.0.0:5002...")
    app.run(host='0.0.0.0', port=5002, debug=False, threaded=True)

if __name__ == '__main__':
    main()
