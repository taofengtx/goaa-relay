#!/usr/bin/env python3
"""
GOAA.AI Queue Runtime Engine
Real-time task queue management and dispatch
"""

import json
import time
from collections import deque
from datetime import datetime
from pathlib import Path

class QueueRuntimeEngine:
    def __init__(self, log_dir="docs/logs"):
        self.log_dir = Path(log_dir)
        self.queue_log = self.log_dir / "queue-runtime.log"
        self.queue_state_file = self.log_dir / "queue-state.json"
        
        # Task queues
        self.pending_queue = deque()
        self.running_queue = deque()
        self.retry_queue = deque()
        self.failed_queue = deque()
        self.completed_queue = deque()
        
        self.task_count = 0
        self.dispatch_count = 0
    
    def enqueue_task(self, task_id, priority='P2', payload=None):
        """Add task to pending queue"""
        task = {
            'id': task_id,
            'priority': priority,
            'payload': payload,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'status': 'pending'
        }
        self.pending_queue.append(task)
        self.task_count += 1
        self.log_action('ENQUEUE', task_id, f"Priority: {priority}")
        return task
    
    def dispatch_task(self):
        """Dispatch next task from pending queue"""
        if not self.pending_queue:
            return None
        
        task = self.pending_queue.popleft()
        task['status'] = 'running'
        task['dispatch_at'] = datetime.utcnow().isoformat() + 'Z'
        self.running_queue.append(task)
        self.dispatch_count += 1
        
        self.log_action('DISPATCH', task['id'], f"To running queue")
        return task
    
    def complete_task(self, task_id):
        """Mark task as completed"""
        for task in list(self.running_queue):
            if task['id'] == task_id:
                self.running_queue.remove(task)
                task['status'] = 'completed'
                task['completed_at'] = datetime.utcnow().isoformat() + 'Z'
                self.completed_queue.append(task)
                self.log_action('COMPLETE', task_id, "Success")
                return True
        return False
    
    def fail_task(self, task_id, error=None):
        """Mark task as failed and move to retry/failed"""
        for task in list(self.running_queue):
            if task['id'] == task_id:
                self.running_queue.remove(task)
                task['status'] = 'failed'
                task['error'] = error
                task['failed_at'] = datetime.utcnow().isoformat() + 'Z'
                
                # Retry logic
                if task.get('retries', 0) < 3:
                    task['retries'] = task.get('retries', 0) + 1
                    self.retry_queue.append(task)
                    self.log_action('RETRY', task_id, f"Attempt {task['retries']}/3")
                else:
                    self.failed_queue.append(task)
                    self.log_action('FAILED', task_id, f"Max retries exceeded")
                return True
        return False
    
    def log_action(self, action, task_id, details):
        """Log queue action"""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().isoformat() + 'Z'
            entry = f"{timestamp} | {action:10} | {task_id:20} | {details}"
            print(entry)
            with open(self.queue_log, 'a') as f:
                f.write(entry + '\n')
        except:
            pass
    
    def get_stats(self):
        """Get queue statistics"""
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'queues': {
                'pending': len(self.pending_queue),
                'running': len(self.running_queue),
                'retry': len(self.retry_queue),
                'failed': len(self.failed_queue),
                'completed': len(self.completed_queue)
            },
            'metrics': {
                'total_tasks': self.task_count,
                'total_dispatches': self.dispatch_count,
                'completion_rate': self.dispatch_count / max(self.task_count, 1)
            }
        }
    
    def save_state(self):
        """Save queue state to file"""
        try:
            state = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'stats': self.get_stats(),
                'pending_count': len(self.pending_queue),
                'running_count': len(self.running_queue)
            }
            with open(self.queue_state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except:
            pass
    
    def run_cycle(self):
        """Execute one queue cycle"""
        # Dispatch pending tasks
        while len(self.running_queue) < 5 and self.pending_queue:  # Max 5 concurrent
            self.dispatch_task()
        
        # Save state
        self.save_state()
        
        # Log stats
        stats = self.get_stats()
        print(f"Queue Stats: Pending={stats['queues']['pending']}, "
              f"Running={stats['queues']['running']}, "
              f"Completed={stats['queues']['completed']}")
    
    def demo_run(self):
        """Demo run with sample tasks"""
        print("🟢 Queue Runtime Engine - Demo Mode")
        print("-" * 70)
        
        # Add sample tasks
        for i in range(5):
            self.enqueue_task(f"TASK-{i:03d}", priority='P1' if i % 2 == 0 else 'P2')
        
        # Dispatch and process
        for _ in range(3):
            self.run_cycle()
            time.sleep(1)
            
            # Complete some tasks
            if self.running_queue:
                task = list(self.running_queue)[0]
                self.complete_task(task['id'])
        
        print("-" * 70)
        stats = self.get_stats()
        print(f"\n✅ Queue Runtime - Final Stats:")
        print(f"  Completed: {stats['queues']['completed']}")
        print(f"  Running: {stats['queues']['running']}")
        print(f"  Pending: {stats['queues']['pending']}")

def main():
    engine = QueueRuntimeEngine()
    engine.demo_run()

if __name__ == '__main__':
    main()
