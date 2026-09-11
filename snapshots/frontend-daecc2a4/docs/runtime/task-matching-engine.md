# Task Matching Engine  
 
Version: 2.1  
 
## CPU Task Distribution  
 
Rule: Assign to node with lowest current CPU usage  
Minimum requirements: cpu_cores  
Preferred: stability_score greater than 0.8  
Multiplier: Base reward * stability_score  
 
## GPU Task Distribution  
 
Rule: Assign ONLY to nodes with gpu capability  
Check: capabilities contains "gpu"  
Requirements: CUDA available, memory  VRAM  
Multiplier: Base reward * 1.5x for GPU acceleration  
 
## Browser Automation Distribution  
 
Rule: Assign to browser_agent capable nodes  
Check: capabilities contains "browser_agent"  
Max concurrent: Limited by available RAM  
Stability requirement: 0.7+  
 
## Docker Task Distribution  
 
Rule: Assign to docker capable nodes  
Check: docker service running  
Verify: docker ps returns success  
Safety: Check disk_free_gb greater than 5  
 
## Document Task Distribution  
 
Rule: Assign to any online node  
Lowest load priority  
Base reward: Standard (5-10 credits)  
 
## Verification Task Distribution  
 
Rule: Coordinator (AiKa-1) only  
Purpose: Verify other nodes' results  
Reward: 20-50 credits per verification  
 
## High Risk Task Approval  
 
Tasks requiring explicit approval:  
- Delete operations  
- Security-related tasks  
- Full disk access  
- Network configuration  
Process: Generate approval_request, await Tao response  
