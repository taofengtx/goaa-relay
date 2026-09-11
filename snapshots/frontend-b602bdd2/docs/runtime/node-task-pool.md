# Node Task Pool Status  
 
Version: 2.1  
 
## Task Lifecycle States  
 
### 1. Pending  
- Initial state after creation  
- Waiting for coordinator assignment  
- Can be cancelled  
 
### 2. Bidding  
- Coordinator evaluates available nodes  
- Matches task requirements  
- Selects best fit  
 
### 3. Assigned  
- Task allocated to specific node  
- Node acknowledged  
- Deadline set  
 
### 4. Running  
- Node actively executing task  
- Status updates sent periodically  
- Can timeout if exceeds deadline  
 
### 5. Verifying  
- Task complete, result submitted  
- Coordinator verifies output  
- Quality score assigned  
 
### 6. Completed  
- Verification passed  
- Credits calculated and awarded  
- Result archived  
 
### 7. Failed  
- Task execution failed  
- Error logged  
- Moved to retry or discard  
 
### 8. Retrying  
- Task failed, queued for retry  
- Can be reassigned to different node  
- Max 3 retry attempts  
 
### 9. Settled  
- Final state for completed tasks  
- Credits finalized  
- Result permanently recorded  
 
## State Transitions  
 
Pending -{assignment}- Assigned -{start}- Running  
 
Running -{success}- Verifying -{approved}- Completed -{settle}- Settled  
 
Running -{failure}- Failed -{retry}- Retrying -{assignment}- Assigned  
 
Retrying -{max_retries}- Failed -{discard}- Cancelled  
