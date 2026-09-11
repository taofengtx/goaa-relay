# Memory and Context Governance

## Session Memory Architecture

### Short-term Memory (Session)
- **Duration**: Current session only
- **Scope**: In-memory, not persisted
- **Use Cases**: Real-time chat context, request tracking

### Long-term Memory (MEMORY.md)
- **Duration**: Persistent across sessions
- **Scope**: Agent profile, preferences, decisions
- **Structure**:
  ```
  MEMORY.md
  ├── 身份 (Identity)
  ├── 用户资料 (User Profile)
  ├── 工具设置 (Tool Configuration)
  ├── 决策记录 (Decision Log)
  └── 经验教训 (Lessons Learned)
  ```

### Daily Notes (memory/YYYY-MM-DD.md)
- **Duration**: Per-day capture
- **Scope**: Raw event logs, decisions made
- **Retention**: Keep for 30 days, then archive

## Data Governance Policies

### Privacy
- ✅ No sensitive data in public memory
- ✅ Credential separation
- ✅ User data isolation

### Accuracy
- ✅ Verify before recording
- ✅ Update outdated information
- ✅ Mark deprecated entries

### Retention
- ✅ Daily notes: 30 days
- ✅ Long-term memory: 1 year review
- ✅ Backups: Keep 6 months

## Agent Memory Lifecycle

```
Session Start
  ↓
Load MEMORY.md
  ↓
Load Today's Notes
  ↓
Operation
  ↓
Update Memory (if significant)
  ↓
Session End
  ↓
Save Daily Log
```

---

**Version:** 2.0  
**Status:** Active  
**Last Updated:** 2026-05-08
