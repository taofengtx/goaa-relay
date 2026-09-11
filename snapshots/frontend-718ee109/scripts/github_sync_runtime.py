#!/usr/bin/env python3
"""
GOAA.AI GitHub Sync Runtime - Real Daemon
Auto-commits and pushes changes to GitHub
"""

import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

class GitHubSyncRuntime:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or Path(__file__).parent.parent
        self.log_file = self.repo_path / "docs" / "logs" / "github-sync.log"
        self.running = False
        self.cycle_count = 0
        
    def log(self, level, message):
        """Log with timestamp"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        entry = f"{timestamp} | {level:8} | {message}"
        print(entry)
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, 'a') as f:
                f.write(entry + '\n')
        except:
            pass
    
    def check_changes(self):
        """Check if there are uncommitted changes"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            return bool(result.stdout.strip())
        except Exception as e:
            self.log('ERROR', f'Check changes failed: {e}')
            return False
    
    def git_add(self):
        """Stage changes"""
        try:
            subprocess.run(
                ['git', 'add', 'docs/', 'scripts/', '-A'],
                cwd=self.repo_path,
                check=True,
                timeout=10
            )
            self.log('INFO', 'git add: ✓')
            return True
        except Exception as e:
            self.log('WARN', f'git add failed: {e}')
            return False
    
    def git_commit(self):
        """Commit changes"""
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            message = f'runtime: auto-sync {timestamp}'
            subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.repo_path,
                check=True,
                timeout=10
            )
            self.log('INFO', f'git commit: ✓ ({message[:40]}...)')
            return True
        except Exception as e:
            self.log('WARN', f'git commit failed: {e}')
            return False
    
    def git_push(self, retries=3):
        """Push to GitHub with retry"""
        for attempt in range(retries):
            try:
                subprocess.run(
                    ['git', 'push', 'origin', 'main'],
                    cwd=self.repo_path,
                    check=True,
                    timeout=15
                )
                self.log('INFO', f'git push: ✓ (attempt {attempt+1})')
                return True
            except Exception as e:
                self.log('WARN', f'git push attempt {attempt+1}/{retries} failed: {e}')
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        return False
    
    def sync_cycle(self):
        """Execute one sync cycle"""
        self.cycle_count += 1
        self.log('INFO', f'=== SYNC CYCLE {self.cycle_count} START ===')
        
        # Check for changes
        has_changes = self.check_changes()
        if not has_changes:
            self.log('INFO', 'No changes detected - skipping cycle')
            return
        
        # Stage, commit, push
        if self.git_add() and self.git_commit():
            if self.git_push():
                self.log('INFO', f'=== SYNC CYCLE {self.cycle_count} SUCCESS ===')
                return True
        
        self.log('WARN', f'=== SYNC CYCLE {self.cycle_count} FAILED ===')
        return False
    
    def run(self, interval=300):
        """Run continuous sync loop (interval in seconds)"""
        self.running = True
        self.log('INFO', f'GitHub Sync Runtime started - interval: {interval}s')
        
        try:
            while self.running:
                self.sync_cycle()
                time.sleep(interval)
        except KeyboardInterrupt:
            self.log('INFO', 'GitHub Sync Runtime stopped by user')
        except Exception as e:
            self.log('ERROR', f'Runtime crashed: {e}')
        finally:
            self.running = False

def main():
    sync = GitHubSyncRuntime()
    sync.run(interval=300)  # 5 minutes

if __name__ == '__main__':
    main()
