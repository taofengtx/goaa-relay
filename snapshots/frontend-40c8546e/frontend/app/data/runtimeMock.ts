// Mock Runtime Data  
export const runtimeCards = [  
  { id: 'aika-1', name: 'AiKa-1', role: 'Control Tower', type: 'Node', ip: '192.168.1.207', status: 'ONLINE', cpu: 45.2, memory: 62.5, runningTasks: 5, lastHeartbeat: '2 mins ago', credits: 125 },
  { id: 'aika-2', name: 'AiKa-2', role: 'Linux Worker', type: 'Node', ip: '192.168.1.208', status: 'BUSY', cpu: 92.3, memory: 78.4, runningTasks: 12, lastHeartbeat: '30 secs ago', credits: 87 },
  { id: 'akc-001', name: 'AKC-001', role: 'Cloud Worker', type: 'Node', ip: '5.78.76.21', status: 'ONLINE', cpu: 52.1, memory: 68.3, runningTasks: 8, lastHeartbeat: '1 min ago', credits: 234 },
  { id: 'openclaw', name: 'OpenClaw', role: 'API Gateway', type: 'Service', status: 'ONLINE', cpu: 28.5, memory: 42.1, runningTasks: 45, lastHeartbeat: '10 secs ago', credits: 0 },
  { id: 'qwenpaw', name: 'QwenPaw', role: 'Agent Runtime', type: 'Service', status: 'ONLINE', cpu: 35.2, memory: 55.7, runningTasks: 23, lastHeartbeat: '15 secs ago', credits: 0 },
  { id: 'github-sync', name: 'GitHub Sync', role: 'Auto Commit', type: 'Runtime', status: 'IDLE', cpu: 0.5, memory: 12.3, runningTasks: 0, credits: 45 },
  { id: 'task-queue', name: 'Task Queue', role: 'Pending', type: 'Queue', status: 'ONLINE', pending: 28, running: 15, failed: 2 },
  { id: 'credits-engine', name: 'Credits Engine', role: 'Settlement', type: 'Credits', status: 'ONLINE', total: 891.45, today: 156.23 }
];  
