# Node Credits Settlement Model  
 
Version: 2.1  
Date: 2026-05-09  
 
## Formula  
 
Credits = BaseReward * Difficulty * CapabilityMultiplier * QualityScore * StabilityScore * SpeedBonus  
 
### BaseReward  
- Simple task: 5 credits  
- Medium task: 10 credits  
- Complex task: 25 credits  
- Critical task: 50 credits  
 
### Difficulty  
- 1.0: Basic  
- 1.5: Intermediate  
- 2.0: Advanced  
- 3.0: Expert  
 
### CapabilityMultiplier  
- Basic capability: 1.0x  
- GPU: 1.5x  
- Docker: 1.3x  
- Browser Agent: 1.2x  
 
### QualityScore  
- Excellent: 1.5x  
- Good: 1.2x  
- Acceptable: 1.0x  
- Poor: 0.5x  
 
### StabilityScore  
- Perfect (100%% uptime): 1.0x  
- High (99%% uptime): 0.95x  
- Medium (95%% uptime): 0.85x  
- Low: 0.5x or suspension  
 
### SpeedBonus  
- Faster than expected: +0.2x  
- On time: 0x  
- Late: -0.1x  
 
## Platform Policy  
 
1. Platform Cloud Nodes:  
   - No cash reward  
   - Credits used for internal accounting  
 
2. User Local Boxes:  
   - Earn full credits  
   - Can deduct monthly fees  
   - Can purchase compute power  
 
3. Credits Use Cases:  
   - Deduct subscription fees  
   - Purchase GPU compute  
   - Buy API tokens  
   - Reserved for features  
 
4. No Cash Out:  
   - Credits cannot be cashed out  
   - Platform currency only  
 
## Quality Incentives  
 
- High quality nodes (0.95+ stability): 1.3x multiplier  
- Medium quality: 1.0x multiplier  
- Low quality (below 0.7): 0.7x multiplier or suspended  
