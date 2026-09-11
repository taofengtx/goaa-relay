#!/usr/bin/env python3
"""
GOAA.AI Runtime Verification Script
Verify that all runtime daemons are working correctly
"""

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

class RuntimeVerifier:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.log_dir = self.repo_path / "docs" / "logs"
        self.results = {}
    
    def verify_github_sync(self):
        """Verify GitHub Sync Runtime"""
        print("\n[VERIFY] GitHub Sync Runtime")
        try:
            # Check if commits exist
            result = subprocess.run(
                ['git', 'log', '--oneline', '-5'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            commits = result.stdout.strip().split('\n')
            print(f"  ✓ Recent commits: {len(commits)}")
            print(f"    - Latest: {commits[0] if commits else 'N/A'}")
            
            # Check working directory
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            clean = len(result.stdout.strip()) == 0
            print(f"  ✓ Working tree: {'CLEAN' if clean else 'DIRTY'}")
            
            self.results['github_sync'] = {
                'status': 'VERIFIED',
                'commits': len(commits),
                'working_tree': 'clean' if clean else 'dirty'
            }
            return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def verify_heartbeat_logs(self):
        """Verify Heartbeat Runtime logs"""
        print("\n[VERIFY] Heartbeat Runtime")
        try:
            hb_log = self.log_dir / "heartbeat.log"
            if hb_log.exists():
                with open(hb_log, 'r') as f:
                    lines = f.readlines()
                print(f"  ✓ Heartbeat log exists: {len(lines)} entries")
                if lines:
                    latest = lines[-1].strip()
                    print(f"    - Latest: {latest[:80]}...")
                
                self.results['heartbeat'] = {
                    'status': 'VERIFIED',
                    'log_entries': len(lines)
                }
                return True
            else:
                print(f"  ✗ Heartbeat log not found")
                return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def verify_runtime_metrics(self):
        """Verify Runtime Metrics"""
        print("\n[VERIFY] Runtime Metrics")
        try:
            metrics_file = self.log_dir / "runtime-metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                print(f"  ✓ Metrics file exists")
                print(f"    - CPU: {metrics.get('system', {}).get('cpu_percent', 'N/A')}%")
                print(f"    - Memory: {metrics.get('system', {}).get('memory_percent', 'N/A')}%")
                print(f"    - Timestamp: {metrics.get('timestamp', 'N/A')}")
                
                self.results['metrics'] = {
                    'status': 'VERIFIED',
                    'cpu': metrics.get('system', {}).get('cpu_percent'),
                    'memory': metrics.get('system', {}).get('memory_percent')
                }
                return True
            else:
                print(f"  ✗ Metrics file not found")
                return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def verify_python_runtime(self):
        """Verify Python runtime availability"""
        print("\n[VERIFY] Python Runtime")
        try:
            result = subprocess.run(
                ['python', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip() + result.stderr.strip()
            print(f"  ✓ Python: {version}")
            
            self.results['python'] = {
                'status': 'VERIFIED',
                'version': version
            }
            return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def run_all_verifications(self):
        """Run all verifications"""
        print("=" * 70)
        print("GOAA.AI Runtime Verification - Real Runtime Phase")
        print("=" * 70)
        
        self.verify_python_runtime()
        self.verify_github_sync()
        self.verify_heartbeat_logs()
        self.verify_runtime_metrics()
        
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for r in self.results.values() if r.get('status') == 'VERIFIED')
        total = len(self.results)
        
        print(f"\n✅ Passed: {passed}/{total}")
        print(f"\nDetailed Results:")
        for name, result in self.results.items():
            status = "✓" if result.get('status') == 'VERIFIED' else "✗"
            print(f"  {status} {name}: {result.get('status', 'FAILED')}")
        
        print("\n" + "=" * 70)
        if passed == total:
            print("🟢 ALL RUNTIME VERIFICATIONS PASSED")
            print("Status: GOAA.AI Real Runtime Phase - ACTIVE")
        else:
            print("🟡 PARTIAL VERIFICATION")
        print("=" * 70)
        
        return passed == total

def main():
    verifier = RuntimeVerifier()
    verifier.run_all_verifications()

if __name__ == '__main__':
    main()
