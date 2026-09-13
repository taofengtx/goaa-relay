# 04 — GitHub 考古（全分支 / tag / worktree）

- 日期：2026-09-13；方法：`git fetch`（唯讀同步 refs）+ `git for-each-ref` + `git merge-base/rev-list` + `git ls-tree`。
- 未 merge / 未 rebase / 未 delete / 未 force-push / 未改任何 ref。

## 1. 唯一的生產 repo

- **`github.com:taofengtx/goaa-ai-frontend.git`**（私有）。
- 主 clone：`/home/aika/Projects/goaa-ai-main`（branch `codex/backend-source-capture-20260902` @ `02a17ff`）。
- **這是 monorepo**：Next 前端 + `local-console/`（Aika-Box 主控台）+ `services/rag/workers/authorization_kernel/` + `docs/runtime|nodes|roadmap/` + `aika-deploy/`。

### 1.1 🔴 fetch refspec 原本是「窄的」

`origin` 原本只抓 `+refs/heads/main:refs/remotes/origin/main`，因此 `git fetch --all` **看不到其他分支**。
本輪以 `git fetch origin '+refs/heads/*:refs/remotes/origin/*' --prune`（唯讀）補齊，fetch rc=0。

## 2. 規模

| 項目 | 數量 |
|---|---|
| local branches | **56** |
| remote branches（`origin/*`，不含 HEAD） | **58** |
| tags | **3** |
| worktrees | **40** |
| commits（`--all`） | **700** |
| `origin/main` tracked files | **400** |
| 生產前端 `40c8546` tracked files | **638** |
| 生產後端 `dc64591` tracked files | **585** |
| `origin` 上**最新**的 ref | **2026-09-07**（`origin/codex/login-legal-links-20260906` @ `76af718`） |

tags：`golden/phase4-start-20260827`(`316dfaa`)、`portal-preview-technical-foundation-v1`(`a7e8b1c`)、`v5.2b-golden-r1`(`a10ce1e`)。

## 3. 🔴 核心發現：**生產 commit 不在 GitHub 任何 ref 上**

| 生產物 | commit | 在 GitHub？ |
|---|---|---|
| C1 前端 release（`current`） | `40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` | **否**（`git branch -r --contains` 空、`git tag --contains` 空） |
| C1 後端 3103 | `dc64591ba7485aa973f373d5340842297f28b630` | **否** |

⇒ **GitHub 不是 C1 現行生產的唯一真實來源**。真正的事實來源是：`C1 release 目錄` + `本機 worktree` + `relay 報告`。

## 4. 血緣（相對共同祖先）

**`76af718`（`origin/codex/login-legal-links-20260906`，2026-09-07）是整個九月生產線的共同祖先**：

| ref | merge-base(76af718) | ahead | behind |
|---|---|---|---|
| `40c8546`（生產前端） | `76af718b` | **+20** | 0 |
| `dc64591`（生產後端） | `76af718b` | **+5** | 0 |
| `a7e8b1c`（three-portals-isolated） | `76af718b` | +1 | 0 |
| `b8050fc`（portal-preview / agent-application-loop） | `76af718b` | +2 | 0 |
| `c542977`（backup-p44b，8/30） | `9348541c` | +1 | **203** |
| `a532a66`（stripe-return-urls，9/4） | `87e0165a` | +2 | **24** |

⇒ 生產線＝**GitHub 上的祖先 `76af718` ＋ 25 個 local-only commit**（前端 20、後端 5，部分重疊）。

## 5. local-only 分支（無 `origin/<name>`）

> 數到 **22** 個；其中包含 C1 現行生產前後端。代表者：

`feat/c2-clerk-unified-login-v1`(`40c8546`)、`feat/c2-pg-agent-loop-v1`(`dc64591`)、`feat/agent-application-loop-v1`(`b8050fc`)、`feat/c2-agent-application-ui-v1`(`13ecaa8`)、`feat/portal-preview-business-loop-v1`、`feat/three-portals-isolated-v1`(`a7e8b1c`)、`feat/three-portals-v1`、`codex/stripe-return-urls-20260904`(`a532a66`)、`backup-p44b-*`(`c542977`)、`evidence/*` 等。

**`76af718`（回滾/golden 基線）在 GitHub 上** ✓（`origin/codex/login-legal-links-20260906`）。

## 6. 六月 runtime / worker 血緣（多已上 GitHub）

`feature/runtime-orchestrator-core-v1`、`feature/controlled-shell-executor-v1`、`feature/runtime-evidence-store-v1`（皆 `52694be`）、`feat/dispatch-protocol-v01-20260621`、`feat/multi-node-registry-v01-20260621`、`feat/readonly-dry-run-protocol-v01-20260621`、`feat/ai-workspace-conversation-task-flow-v01-20260622`(`c82a821`)、`docs/goaa-12-baton-standard-v1.1-20260619`。
worktrees 分佈：`~/.qwenpaw/workspaces/default/work/*`（~36）與 `/home/aika/goaa-collaboration/{claude-worktrees,doc-worktrees,…}`（~7）。

## 7. 其他 repo / 目錄（非此 GitHub repo）

| 路徑 | 性質 | 血緣 |
|---|---|---|
| `/opt/goaa/repo`（C1） | **同一個 repo 的部署 clone** @ `53f599f`（2026-06） | remote = `goaa-ai-frontend` ✓ |
| `work/goaa-agent` | **獨立 git repo，`master`，`remote` = 0 個** | Agent Console V1 後端（`ee8f811`，8/26）**只存在本機** |
| `work/goaa-order` | 純目錄（非 git） | 與 `goaa-agent` 同批檔（8/27 快照） |
| `work/goaa-router` | 純目錄（非 git） | 模型路由/規劃引擎舊碼（8/25） |
| `/opt/goaa/router`（C1） | git repo @ `1d67bd6` | **現行 `api.goaa.ai` 服務來源**；僅 1093+449 行 |
| `/opt/goaa/local-console` | 純目錄 | 主控台舊拷貝 |

## 8. 逐 ref 矩陣（素材）

- `/tmp/gh-matrix.py` → `/tmp/gh/matrix.txt`、`matrix.json`（116 行）：每個 ref 記 sha／日期／subject／tree／與 `origin/main` 的 merge-base／ahead-behind／diff 檔數／tracked 檔數／能力指紋。
- 能力指紋（本輪新增）：`/tmp/gh-caps.py` → `/tmp/gh/caps.txt`、`caps.json`（17 ref × 26 樣式）。
- ref 清單：`/tmp/gh/refs_local.txt`、`/tmp/gh/refs_remote.txt`；`/tmp/gh-a1.sh|a2.sh|a3.sh` 與其 `.out`。
