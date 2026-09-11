# Node Presence Registry Schema  
 
Version: 2.1  
Database: SQLite - node_presence.db  
 
## Table: nodes  
 
Column: node_id (PRIMARY KEY)  
- Type: TEXT  
- Example: aika-1, aika-2, cloud-box-001  
 
Column: last_heartbeat  
- Type: TEXT (ISO 8601)  
- Format: 2026-05-09T12:55:00Z  
 
Column: status  
- ONLINE: Node is responsive  
- OFFLINE: No heartbeat for 15+ minutes  
- BUSY: CPU usage greater than 90 percent  
- IDLE: CPU usage less than 20 percent  
- DEGRADED: High error rate or instability  
 
Column: cpu_usage  
- Type: REAL (0.0 - 100.0)  
 
Column: ram_usage  
- Type: REAL (0.0 - 100.0)  
 
Column: active_tasks  
- Type: INTEGER  
- Number of currently running tasks  
 
Column: queue_status  
- Type: TEXT  
- empty, waiting, processing  
 
Column: uptime  
- Type: INTEGER (seconds)  
 
Column: capabilities  
- Type: TEXT (JSON array)  
- Example: ["docker", "python", "gpu"]  
 
Column: runtime_state  
- Type: TEXT  
- active, maintenance, recovery  
