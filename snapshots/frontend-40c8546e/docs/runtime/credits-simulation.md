# Credits Simulation Runtime

**Version:** 2.1  
**Last Updated:** 2026-05-09 11:35 UTC

## Overview

GOAA.AI Credits System: Economic model for distributed worker task allocation and reward.

---

## 1. Base Reward Calculation

```
BaseReward = TaskDifficulty × (1 + TaskComplexityBonus)
```

**Task Difficulty Levels:**
- **Simple:** 5 credits (data processing, log rotation, syntax check)
- **Medium:** 10 credits (API health check, queue rebalancing, doc updates)
- **Complex:** 25 credits (Docker deployment, bootstrap, refactoring)
- **Critical:** 50 credits (infrastructure recovery, security patch)

**Complexity Bonus:** +0.5 to +2.0x for multi-component tasks

---

## 2. Local-Box Rewards (AiKa-1)

**Task Types:**
- Idle task execution: 5 credits/task
- GitHub sync: 10 credits
- Documentation update: 5 credits
- Auto-repair (low-risk): 10 credits
- API health check: 2 credits

**Simulation Example:**
```
Daily Tasks (AiKa-1):
- 8 idle tasks @ 5 credits = 40 credits
- 2 GitHub syncs @ 10 credits = 20 credits
- 5 doc updates @ 5 credits = 25 credits
- 2 auto-repairs @ 10 credits = 20 credits
- 12 health checks @ 2 credits = 24 credits
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Daily: 129 credits
```

---

## 3. Cloud-Node Rewards (AKC-001)

**Task Types:**
- Runtime queue execution: 20-50 credits/task
- OpenClaw API calls: 1-5 credits each
- Database queries: 2-10 credits
- Compute-intensive tasks: 30-100 credits
- 24/7 uptime bonus: 50 credits/day

**Simulation Example:**
```
Daily Tasks (AKC-001):
- 10 queue tasks @ 30 credits avg = 300 credits
- 100 API calls @ 2 credits avg = 200 credits
- 20 database ops @ 5 credits avg = 100 credits
- 24/7 uptime bonus = 50 credits
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Daily: 650 credits
```

---

## 4. Worker-Node Rewards (AiKa-2)

**Bootstrap Phase (No Credits Yet)**
- Bootstrap initialization: 0 credits (setup cost)
- After bootstrap completion: Eligible for task rewards

**Post-Bootstrap Tasks:**
- Worker task execution: 15-40 credits/task
- Watchdog health monitoring: 5 credits/day
- Queue processing: 20-60 credits/task
- Docker container management: 10 credits/action

---

## 5. Idle Penalties & Uptime Bonus

**Idle Penalties:**
- 5 minutes idle: -1 credit
- 30 minutes idle: -5 credits
- 1 hour idle: -10 credits

**Uptime Bonus:**
- 99% uptime (daily): +10 credits
- 99.9% uptime (daily): +25 credits
- 99.99% uptime (daily): +50 credits

---

## 6. Quality Multiplier

**Task Quality Factors:**
- **Excellent** (1.5x): All requirements met, optimized, documented
- **Good** (1.2x): All requirements met, works correctly
- **Acceptable** (1.0x): Minimum requirements met
- **Poor** (0.5x): Partially working, needs fixes

**Example:**
```
Base Task Reward: 20 credits
Quality Score: Excellent (1.5x)
Final Reward: 20 × 1.5 = 30 credits
```

---

## 7. Stability Index

**Factors:**
- Successful completion rate: 0-1.0
- No crashes/timeouts: +0.1
- Fast execution: +0.05 (if < 10% of avg time)

**Example:**
```
Node: AKC-001
- Success rate: 98% = 0.98
- No crashes: +0.1
- Fast execution: +0.05
- Stability Index: 1.03

Task Reward: 30 credits
Final: 30 × 1.03 = 30.9 credits
```

---

## 8. Complete Formula

```
CREDITS = BaseReward 
        × DifficultyMultiplier 
        × QualityMultiplier 
        × StabilityIndex 
        + BonusCredits
```

**Full Example:**
```
Task: Docker deployment on AKC-001

BaseReward: 50 (critical task)
DifficultyMultiplier: 1.2 (complex)
QualityMultiplier: 1.3 (excellent execution)
StabilityIndex: 1.05 (99% success, fast)
UptimeBonus: +25 (99.9% uptime today)

TOTAL = 50 × 1.2 × 1.3 × 1.05 + 25
      = 81.9 + 25
      = 106.9 credits
```

---

## 9. Daily Simulation Results

**Scenario: Continuous Runtime Mode (May 9-10)**

| Node | Base Tasks | Reward | Uptime Bonus | Quality Multi | Total |
|------|-----------|--------|--------------|---------------|-------|
| AiKa-1 | 20 | 120 | 10 | 1.1x | 142 |
| AiKa-2 | 0 | 0 | 0 | N/A | 0 |
| AKC-001 | 15 | 450 | 25 | 1.2x | 565 |
| **TOTAL** | | | | | **707** |

---

## 10. System Benefits

**Why Credits Matter:**
- Incentivizes continuous task execution
- Rewards high-quality, stable performance
- Penalizes idleness
- Fair allocation across nodes
- Encourages optimization

---

## 11. Future Integration

**Planned:**
- Leaderboard (monthly rankings)
- Credit conversion to priority queue slots
- Reward redemption system
- Economic model for node incentives

---

## Status

- **Simulation Ready:** ✅ Yes
- **Live Integration:** ⏳ Phase-3
- **Next Review:** 2026-05-10
