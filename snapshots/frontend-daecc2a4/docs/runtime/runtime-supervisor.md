# P3-7 Runtime Process Supervisor  
 
## Process Monitoring  
 
### Background Services  
- runtime_watchdog.py (API/Docker/SSH health)  
- heartbeat_daemon.py (5min metrics)  
- runtime_scheduler_exec.py (Task scheduling)  
- metrics_collector.py (System metrics)  
 
### Supervision Rules  
- Process dies: Auto-restart within 10s  
- Memory  Trigger cleanup  
- Zombie processes: Clean every 1h  
- Queue stuck: Reassign tasks  
- CPU  Rate-limit new tasks  
 
## Implementation  
- systemd timer for supervisor loop  
- ps/pgrep for process detection  
- kill -9 for cleanup  
