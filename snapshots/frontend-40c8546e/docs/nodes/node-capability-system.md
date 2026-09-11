# Node Capability System  
 
Version: 2.1  
Last Updated: 2026-05-09  
 
## Physical Resources  
 
Each node declares: 
- cpu_cores: Physical CPU count  
- ram_gb: Total memory 
- gpu: GPU model if available  
- disk_free_gb: Available storage  
- network_bandwidth_mbps: Upload/download speed  
 
## Current Load  
 
Real-time metrics: 
- cpu_usage: Current %  
- ram_usage: Current %  
- running_tasks: Count  
- network_latency_ms: ms  
 
## Capabilities  
 
- docker: Can run containers  
- python: Python 3.x installed  
- gpu: CUDA capable  
- browser_agent: Chromium/Firefox installed  
- ssh: SSH server running  
- git: Git installed  
 
## Stability Score  
 
Calculation:  
StabilityScore = UptimeScore * 0.5 + TaskSuccessRate * 0.3 + HeartbeatReliability * 0.2  
 
Range: 0.0 - 1.0  
- 1.0: Perfect uptime, 100% success  
- 0.8: 99%% uptime, 95%% success  
- 0.5: 95%% uptime, 80%% success  
- 0.0: Unstable or failed  
 
## Trust Score  
 
Based on: 
- Historical task success  
- Uptime percentage  
- No security incidents  
 
## Credits Rate  
 
Multiplier based on: 
- Stability (0.8 - 1.2x)  
- Capability level (0.5 - 2.0x)  
- Node type (cloud vs local)  
