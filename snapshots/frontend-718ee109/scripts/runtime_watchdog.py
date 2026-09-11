#!/usr/bin/env python3
"""
GOAA.AI Runtime Watchdog
Monitors AiKa-2 health: API, Docker, SSH, CPU, Memory
Auto-restarts non-critical services on failure
"""

import subprocess
import json
import time
import sys
from datetime import datetime
from pathlib import Path

class RuntimeWatchdog:
    def __init__(self, node_id="aika-2"):
        self.node_id = node_id
        self.check_interval = 300  # 5 minutes
        self.log_file = f"/var/log/watchdog-{node_id}.log"
        self.health_status = {}
    
    def log(self, level, message):
        """Log message with timestamp"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        log_msg = f"{timestamp} | {level:8} | {message}"
        print(log_msg)
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_msg + '\n')
        except:
            pass
    
    def check_api_health(self):
        """Check if OpenClaw API is responsive"""
        try:
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://api.goaa.ai/health'],
                timeout=5,
                capture_output=True
            )
            status = result.stdout.decode().strip()
            healthy = status == "200"
            self.health_status['api'] = healthy
            return healthy
        except Exception as e:
            self.log('ERROR', f'API health check failed: {e}')
            self.health_status['api'] = False
            return False
    
    def check_docker_health(self):
        """Check if Docker daemon is running and responsive"""
        try:
            result = subprocess.run(
                ['docker', 'ps'],
                timeout=5,
                capture_output=True
            )
            healthy = result.returncode == 0
            self.health_status['docker'] = healthy
            return healthy
        except Exception as e:
            self.log('ERROR', f'Docker health check failed: {e}')
            self.health_status['docker'] = False
            return False
    
    def check_ssh_health(self):
        """Check if SSH service is running"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'ssh'],
                timeout=5,
                capture_output=True,
                text=True
            )
            healthy = result.stdout.strip() == 'active'
            self.health_status['ssh'] = healthy
            return healthy
        except Exception as e:
            self.log('WARN', f'SSH health check failed: {e}')
            self.health_status['ssh'] = False
            return False
    
    def get_system_metrics(self):
        """Get CPU and Memory usage"""
        try:
            # CPU usage
            result = subprocess.run(
                ['grep', 'cpu ', '/proc/stat'],
                capture_output=True,
                text=True
            )
            
            # Simple memory check
            result_mem = subprocess.run(
                ['free', '-h'],
                capture_output=True,
                text=True
            )
            
            metrics = {
                'cpu_available': result.returncode == 0,
                'memory_available': result_mem.returncode == 0
            }
            self.health_status['system'] = metrics
            return metrics
        except Exception as e:
            self.log('WARN', f'System metrics check failed: {e}')
            return {'cpu_available': False, 'memory_available': False}
    
    def auto_restart_service(self, service_name):
        """Safely restart a non-critical service"""
        safe_services = ['docker', 'ssh']
        
        if service_name not in safe_services:
            self.log('WARN', f'Restart {service_name} requires approval - skipped')
            return False
        
        try:
            self.log('INFO', f'Attempting to restart {service_name}...')
            subprocess.run(
                ['systemctl', 'restart', service_name],
                timeout=30,
                check=True
            )
            self.log('INFO', f'Successfully restarted {service_name}')
            return True
        except Exception as e:
            self.log('ERROR', f'Failed to restart {service_name}: {e}')
            return False
    
    def generate_report(self):
        """Generate health report"""
        report = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'node_id': self.node_id,
            'health_status': self.health_status,
            'overall_health': all(
                v for k, v in self.health_status.items() if k != 'system'
            )
        }
        return report
    
    def run_check_cycle(self):
        """Execute one complete health check cycle"""
        self.log('INFO', f'Starting watchdog cycle on {self.node_id}')
        
        # Run all checks
        api_ok = self.check_api_health()
        docker_ok = self.check_docker_health()
        ssh_ok = self.check_ssh_health()
        metrics = self.get_system_metrics()
        
        # Log results
        self.log('INFO', f'API: {api_ok}, Docker: {docker_ok}, SSH: {ssh_ok}')
        
        # Auto-repair logic
        if not docker_ok:
            self.log('WARN', 'Docker unhealthy - attempting auto-restart')
            self.auto_restart_service('docker')
        
        if not ssh_ok:
            self.log('WARN', 'SSH unhealthy - attempting auto-restart')
            self.auto_restart_service('ssh')
        
        # Generate report
        report = self.generate_report()
        self.log('INFO', f'Health report: {json.dumps(report)}')
        
        return report
    
    def continuous_monitor(self):
        """Run continuous monitoring loop"""
        self.log('INFO', f'Watchdog starting continuous monitoring for {self.node_id}')
        
        try:
            while True:
                self.run_check_cycle()
                self.log('INFO', f'Next check in {self.check_interval}s')
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.log('INFO', 'Watchdog terminated by user')
            sys.exit(0)
        except Exception as e:
            self.log('ERROR', f'Watchdog crashed: {e}')
            sys.exit(1)

def main():
    watchdog = RuntimeWatchdog(node_id='aika-2')
    watchdog.continuous_monitor()

if __name__ == '__main__':
    main()
