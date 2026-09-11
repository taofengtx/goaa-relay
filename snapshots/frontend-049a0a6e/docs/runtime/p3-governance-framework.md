# P3 Governance: AI Decision Framework  
 
## Risk Classification  
 
### GREEN: Auto-Execute  
- Create missing .md/.json files  
- Update timestamps  
- Fix markdown syntax  
- Rotate old logs  
- Add missing heartbeat records  
- Rebalance queue (if saturation  
 
### YELLOW: Log + Notify  
- Restart non-critical services  
- Modify .gitignore rules  
- Update node capabilities  
- Escalate: Console notification  
 
### RED: Approval Required  
- Delete any files  
- Modify SSH keys  
- Change credentials  
- Reset queue state  
- Escalate: Email to Tao  
 
### BLACK: Blocked  
- Security policy changes  
- Bootstrap process modifications  
- Master protocol violations  
- Force-terminate running tasks  
