# 10 — Skills / AI Agent / RAG 血緣

- 日期：2026-09-13；唯讀。

## 1. 三個同名但不同的「agent / skill」

| 名稱 | 位置 | 性質 |
|---|---|---|
| **產品側 Agent Console V1** | `work/goaa-agent/`（**獨立 git repo、`master`、remote 數 = 0**） | `agent_api.py`、`agent_db.py`、`agent_embed.py`、`agent_knowledge.py`、`agent_preview.py`、`agent_skills.py`、`main.py`、`planning_engine.py`(63,601 B)；最後 commit `ee8f811`（2026-08-26） |
| **產品側 Agent Loop（改版後）** | C1 生產樹 `dc64591` 的 `services/c2_agent_loop/`（37 檔） | FastAPI 3103；`agent/panel`、application/licence、`user_roles` 權限 |
| **Aika 自己的 skills** | `~/.qwenpaw/workspaces/default/skills/`（19 個 skill 目錄） | 這是**助手技能**（docx/pdf/xlsx、cron、browser…），不是產品功能 |

⚠️ `work/goaa-agent` **沒有任何 remote** ⇒ 它是**第三個 local-only 風險點**（與 05 報告的 25 個 commit 同類）。`work/goaa-order`、`work/goaa-router` 連 `.git` 都沒有。

## 2. 產品側 Skills / Knowledge 的資料層（C1 `goaa` 庫）

| 表 | 列數 | 說明 |
|---|---|---|
| `goaa_agent_skills` | **2** | 技能註冊（幾乎空） |
| `goaa_agent_knowledge_docs` | **2** | 知識文件 |
| `goaa_agent_knowledge_chunks` | **105** | 切片（RAG 用） |
| `goaa_agent_profiles` / `_leads` / `_preferences` / `_tokens` | — | 代理側資料 |
| `agents` | **0** | Agent Console V1 的主表未使用 |
| `goaa_planning_sessions` | 117 | 規劃會話（黃金流程主體） |
| `tool_invocations` / `tasks` | 21 / 21 | 工具與任務 |

⇒ **RAG/Skills 的資料層已建但幾乎未填**；實際內容仍在原型階段（`SQLite / mock / dev-only` 性質的 `local-console/local_user.db`，12,288 B）。

## 3. 代碼能力指紋（`git grep -l` 檔數）

| ref | skill registry | rag | clerk | agent_loop_api |
|---|---|---|---|---|
| `origin/main` | 34 | 53 | 0 | 0 |
| `76af718`（golden） | 40 | 54 | 0 | 0 |
| `40c8546`（**C1 生產前端**） | **56** | 54 | **53** | **9** |
| `dc64591`（**C1 生產後端**） | 48 | 54 | 14 | 6 |

## 4. 判讀

1. **Skills / RAG 血緣主要在 GitHub 上（`origin/main`）**；但**「Clerk 身分 + agent-loop 權限 + Skills 市集」這一整層只存在於生產樹（local-only）**。
2. Agent 側產品的兩個實作來源（`work/goaa-agent` 與 `services/c2_agent_loop`）**彼此沒有 git 關聯**，且前者無遠端備份。
3. 若要接真實業務，**建議以生產樹 `dc64591` 的 `services/c2_agent_loop/` 為唯一 agent 後端**（它已接上 `goaa_platform`、`user_roles`、Clerk），並把 `work/goaa-agent` 標為「歷史原型、非來源」。
