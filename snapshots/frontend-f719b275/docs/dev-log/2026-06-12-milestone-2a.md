# GOAA F-lite 第二刀 2a 里程碑檢查表

**里程碑日期**: 2026-06-12 PT
**整理日期**: 2026-06-13 PT
**主題**: Approve endpoint 生產驗證完成；Git 納管待辦
**当时 Git 基线**: `5ab8364`

> 本文件區分 Runtime Truth 與 Git Truth。
> 生產 2a 已完成並驗證，但生產修改尚未進入 Git 跟蹤檔案。
> 本里程碑不是部署腳本，也不包含 secret、環境變數或原始敏感輸出。

**历史状态说明（2026-06-14）**:

**当前审查基线**: `1d67bd6`
本文件记录 2026-06-12 至 2026-06-13 当时的 F-lite 2a 状态。
其中"Git 纳管待办"是历史快照，不代表当前仍未完成。
当前状态必须以 GitHub main、DO Runtime 取证及后续 DevLog 为准。


---

## A. Runtime Truth — 已完成

- [x] 生產 Router 真實路徑為 `/opt/goaa/router/api.py`
- [x] `POST /task/approve` 可用
- [x] 任務狀態必須為 `awaiting_approval`
- [x] 狀態可由 `awaiting_approval` 轉為 `approved`
- [x] 寫入 sanitized `audit_log`
- [x] note 經 `f_lite_sanitize()` 脫敏
- [x] PG 類敏感模式脫敏驗證
- [x] SSH 類敏感模式脫敏驗證
- [x] sudo 類敏感模式脫敏驗證
- [x] AST_OK
- [x] IMPORT_OK
- [x] Router health 200
- [x] 回應包含 `resume_behavior: pending_dispatcher_support`

---

## B. 2a 的真實能力邊界

- [x] 2a 只記錄 approve 狀態流轉
- [x] 2a 不自動 resume
- [x] 2a 不自動 requeue
- [x] 2a 不實作 reject
- [x] 2a 不實作 approval persistence
- [x] 2a 不修改 dispatcher 對 `approved` 的處理
- [x] 2a 不代表 5188 Review UI 已完成

---

## C. Git Truth — 尚未完成

- [x] Git 跟蹤 Router 路徑為 `infra/router/api.py`
- [x] 當前 Git 檔案沒有 `/task/approve`
- [x] 當前 Git 檔案沒有 `ApproveReq`
- [x] 當前 Git 檔案沒有 `pending_dispatcher_support`
- [x] `services/rag/f_lite_redact.py` 已在 Git
- [x] commit `5ab8364` 只新增本 milestone 的空白檔案
- [x] 可達 branch / commit 未發現 2a 真實代碼
- [x] 不可達 commit 未發現 2a 真實代碼
- [x] repo 未發現可恢復的 2a patch / diff / Router backup

---

## D. Git 納管待辦

> 以下清单保留为历史记录。部分事项已由后续 commit 完成或取代；
> 未经逐项 Runtime/Git 复核，不在本历史文件中自动改为已完成。

- [ ] Tao 明確批准生產只讀取證
- [ ] 取得 `/opt/goaa/router/api.py` 檔案 hash
- [ ] 取得 Git `infra/router/api.py` 檔案 hash
- [ ] 生成 production vs Git unified diff
- [ ] 對 diff 做 secret pattern 掃描
- [ ] 人工確認 diff 不含其他 production drift
- [ ] 僅提取 2a 已驗證變更
- [ ] 納入 Codex worktree
- [ ] 補本地 mock / unit regression test
- [ ] AST check
- [ ] import check
- [ ] endpoint targeted test
- [ ] audit failure rollback test
- [ ] response no-secret test
- [ ] Tao 審批 commit
- [ ] Tao 另行審批 push
- [ ] Tao 另行審批 deploy
- [ ] 部署後 production verification

---

## E. 建議 Commit 範圍

```text
infra/router/api.py
<2a targeted local regression test>
```

建議 commit message：

```text
fix(router): sync verified F-lite 2a approve endpoint from production
```

不應混入：

- [ ] 2b reject
- [ ] resume / requeue
- [ ] dispatcher 修改
- [ ] approval persistence
- [ ] migration / 新表
- [ ] 5188 Review UI
- [ ] HANDOFF / AGENTS
- [ ] deploy script

---

## F. 風險與回滾

- [ ] 生產與 Git 可能包含 2a 以外的版本漂移，必須分類 diff
- [ ] 不得用重新設計的代碼覆蓋已驗證生產行為
- [ ] 不得把 `5ab8364` 當作 2a 代碼 commit
- [ ] 未取得 sanitized diff 前，不聲稱 Git 已對齊
- [ ] Git 對齊失敗時，只回滾 Codex worktree 的局部變更
- [ ] 未經 Tao 批准，不連線、不部署、不 push

---

## G. 人工簽核

**Runtime 里程碑確認**: ____________________

**Git 納管完成**: __________________________

**Production / Git 一致**: __________________

**簽核日期**: ______________________________

**備註**: __________________________________

## H. 后续状态索引

- GitHub main 当前审查基线：`1d67bd6`
- 后续 F-lite 第三刀、持久化与 systemd 变更见 2026-06-13 DevLog 和 Git history
- 本文件不作为当前 Roadmap
- 本文件不证明 Production / Git 已完全一致
- 当前真实状态应重新依据 Runtime Truth、Git Truth、Documentation Truth 核验
