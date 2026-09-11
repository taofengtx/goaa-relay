# GOAA.AI Runtime Monitor Dashboard  
 
Version: 2.1  
 
## Page: /dashboard/runtime  
 
Title: GOAA.AI Runtime Monitor  
Subtitle: Real-time AI Worker OS Control Center  
 
## 8 Runtime Cards  
 
1. AiKa-1 - Control Tower  
2. AiKa-2 - Linux Worker  
3. AKC-001 - Cloud Worker  
4. OpenClaw - API Gateway  
5. QwenPaw - Agent Runtime  
6. GitHub Sync - Auto Commit  
7. Task Queue - Queue Manager  
8. Credits Engine - Settlement  
 
## UI Style  
 
Background: Dark (#0f1419)  
Cards: Deep Dark (#1a1f2e)  
Borders: Status-colored glowing borders  
Status colors: Green=ONLINE, Blue=BUSY, Gray=IDLE, Yellow=DEGRADED, Red=ERROR  
Typography: White headings, Gray text  
 
## Card Click Detail  
 
Modal shows:  
- Current Tasks  
- Task History  
- Heartbeat Logs  
- Runtime Logs  
- Error Logs  
- Approval Requests  
- Credits Summary  
- Health Check Result  
 
## Implementation Path  
 
Frontend: app/dashboard/runtime/page.tsx  
Components: RuntimeCard.tsx, DetailPanel.tsx  
Data: Mock JSON in runtimeMock.ts  
Build: npm run build  
Deploy: Vercel auto-redeploy  
