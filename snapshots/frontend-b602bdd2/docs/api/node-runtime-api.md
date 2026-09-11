# Node Runtime API  
 
Version: 2.1  
Base URL: https://api.goaa.ai/api/v1  
 
## POST /node/register  
 
Register a new node with the system.  
 
Request: 
- node_id: string  
- node_type: aika-1/aika-2/cloud-box/local-box  
- ip: IPv4 address  
- cpu_cores: integer  
- ram_gb: float  
- capabilities: [string]  
 
Response: {status: success, node_id: string, token: string}  
 
## POST /node/heartbeat  
 
Send heartbeat and current metrics.  
Interval: 5 minutes  
 
Request body: 
- node_id: string  
- cpu_usage: 0-100  
- ram_usage: 0-100  
- running_tasks: integer  
- disk_free_gb: number  
 
## POST /task/request  
 
Node requests work from coordinator.  
Request: {node_id, available_slots, max_cpu_usage, preferred_task_types}  
Response: [task_list] or empty  
 
## POST /task/assign  
 
Coordinator assigns task to node.  
Request: {task_id, node_id, task_spec, deadline}  
Response: {status: assigned, task_id, deadline}  
 
## POST /task/report  
 
Node reports task completion.  
Request: {task_id, status: completed/failed, execution_time_sec, result}  
Response: {status: received, credits_earned: number}  
 
## POST /credits/settle  
 
Settle credits for completed tasks.  
Request: {node_id, period: daily/weekly/monthly}  
Response: {total_credits, completed_tasks, next_settlement_date}  
