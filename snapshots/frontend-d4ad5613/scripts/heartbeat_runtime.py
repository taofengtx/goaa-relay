#!/usr/bin/env python3
"""
GOAA.AI Heartbeat Runtime Daemon
Real-time node status monitoring every 5 minutes
"""

import time
import json
import psutil
from datetime import datetime
from pathlib import Path

class HeartbeatRuntimeDaemon:
    def __init__(self, node_id="aika-1", log_dir=None):
        self.node_id = node_id
        self.log_dir = Path(log_dir or "docs/logs")
        self.heartbeat_log = self.log_dir / "heartbeat.log"
        self.metrics_file = self.log_dir / "runtime-metrics.json"
        self.start_time = time.time()
        self.beat_count = 0
        
    def get_system_metrics(self):
        """Collect real system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            uptime_hours = (time.time() - self.start_time) / 3600
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory.percent, 2),
                'memory_available_mb': round(memory.available / (1024**2), 2),
                'uptime_hours': round(uptime_hours, 2),
                'processes': len(psutil.pids())
            }
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            return {}
    
    def generate_heartbeat(self):
        """Generate heartbeat entry"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        metrics = self.get_system_metrics()
        
        heartbeat = {
            'timestamp': timestamp,
            'node_id': self.node_id,
            'beat_number': self.beat_count,
            'status': 'online',
            'metrics': metrics
        }
        return heartbeat
    
    def log_heartbeat(self, heartbeat):
        """Write heartbeat to log file"""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            entry = f"{heartbeat['timestamp']} | {self.node_id} | CPU:{heartbeat['metrics']['cpu_percent']}% | MEM:{heartbeat['metrics']['memory_percent']}% | Beat:{self.beat_count}"
            print(entry)
            with open(self.heartbeat_log, 'a') as f:
                f.write(entry + '\n')
            return True
        except Exception as e:
            print(f"Log write error: {e}")
            return False
    
    def save_metrics(self, heartbeat):
        """Save metrics to JSON for dashboard"""
        try:
            metrics_data = {
                'timestamp': heartbeat['timestamp'],
                'node_id': self.node_id,
                'status': 'online',
                'system': heartbeat['metrics']
            }
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Metrics save error: {e}")
            return False
    
    def heartbeat_cycle(self):
        """Execute one heartbeat cycle"""
        self.beat_count += 1
        heartbeat = self.generate_heartbeat()
        
        # Log and save
        self.log_heartbeat(heartbeat)
        self.save_metrics(heartbeat)
        
        return heartbeat
    
    def run(self, interval=300):
        """Run heartbeat daemon (interval in seconds)"""
        print(f"🟢 Heartbeat Runtime Daemon started - {self.node_id} - interval: {interval}s")
        
        try:
            while True:
                hb = self.heartbeat_cycle()
                print(f"   ✓ Heartbeat #{self.beat_count} sent")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Heartbeat daemon stopped")
        except Exception as e:
            print(f"Heartbeat daemon error: {e}")

def main():
    daemon = HeartbeatRuntimeDaemon(node_id="aika-1")
    daemon.run(interval=300)  # 5 minutes

if __name__ == '__main__':
    main()
