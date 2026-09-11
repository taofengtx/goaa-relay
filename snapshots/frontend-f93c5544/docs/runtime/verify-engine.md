# Runtime Persistent Verification Engine  
 
Version: 2.1  
 
## Verification Checklist  
 
[ ] 1. Process Exists - systemctl status SERVICE  
[ ] 2. Service Active - ps aux shows python process  
[ ] 3. Logs Updating - journalctl shows recent entries  
[ ] 4. Metrics Changing - runtime-metrics.json updates  
[ ] 5. Survive Reboot - systemctl enable SERVICE  
[ ] 6. Restart Success - systemctl restart recovers  
 
## Services to Verify  
 
1. heartbeat-daemon.service  
2. runtime-scheduler.service  
3. metrics-collector.service  
4. persistent-github-sync.service  
5. runtime-supervisor.service  
 
## Success Criteria  
 
All services:  
- Running continuously for 24+ hours  
- Auto-restart on failure  
- Start automatically on system boot  
- Generate logs every cycle  
- Update metrics in real-time  
