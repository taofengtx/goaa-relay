# 11 — D0：Aika-Box／本地開發機 盤點（唯讀）

- 日期：2026-09-13
- 性質：**唯讀盤點**（未修改／未重啟／未 enable-disable 任何服務；未讀取任何秘密值）
- 命名（本輪起統一）：**D0 = Aika-Box / Local Development**

## 1. 身分

| 項目 | 值 | 證據 |
|---|---|---|
| hostname | `aika-core-01` | `hostname` |
| role | **D0**＝本地開發機（Aika-Box Pro） | 令文命名 |
| Tailscale IP | `100.114.37.90` | `ip -4 -o addr`；`tailscale status` → `aika-core-01-1` linux active |
| LAN | `192.168.1.24/24`（`enp4s0`） | `ip -4 -o addr` |
| Public IP（**只報告，不修改**） | `165.162.8.⟨177⟩` | `curl https://api.ipify.org` |
| OS | Ubuntu **26.04 LTS（resolute）** | `/etc/os-release` |
| kernel | `7.0.0-29-generic`（#29-Ubuntu SMP PREEMPT_DYNAMIC Fri Jul 17 20:52:35 UTC 2026, x86_64） | `uname -a` |
| CPU | `nproc = 12` | `nproc` |
| RAM | **30 GiB**（used 10 / buff-cache 22 / available 20）；swap 8 GiB | `free -h` |
| Disk | `/dev/nvme0n1p2` **937 G，用 188 G（22%）** | `df -h /` |
| git | `2.53.0` | `git --version` |
| node / npm | `v22.22.3` / `10.9.8` | `node -v`、`npm -v` |
| python | `3.12.13` | `python3 -V` |
| docker | **未安裝**（client 與 server 皆無） | `docker ps` → command not found |
| systemd | `259（259.5-0ubuntu3.4）` | `systemctl --version` |

## 2. 監聽埠 × 行程（精確）

| 埠 | 行程 | 對外可達性 |
|---|---|---|
| 22 | sshd | `0.0.0.0` |
| 3389 / 3390 | `gnome-remote-desktop`（pid 3173702） | `*`（**全介面**） |
| 4000 | （未識別） | `0.0.0.0` |
| 3199 / 4100 | next-server | `*`（**全介面**） |
| 3102 | next-server（cwd `work/planning-r1b-20260908/stage-r2`） | 127.0.0.1 |
| 3103 | next-server（cwd `work/planning-r1b-20260908/stage-r3`） | 127.0.0.1 |
| 3200 | next-server（`work/goaa-p5-153/.next/standalone`） | 127.0.0.1 |
| 5188 | uvicorn（`goaa-local-console`, pid 6113） | 127.0.0.1 ＋ **`100.114.37.90`（socat tailnet proxy）** |
| 8088 | qwenpaw（pid 7366） | `100.114.37.90` |
| 8188 | ComfyUI（socat tailnet proxy） | `100.114.37.90` |
| 11434 | ollama | 127.0.0.1 |
| 13102 | **ssh tunnel**（pid 1772631, `-L 13102:127.0.0.1:13102 do-c2`） | `[::1]` |
| 18790 | **`/home/aika/.framer-bridge/server.js`**（pid 3183910） | 127.0.0.1 |
| 7001 / 7002 / 12001 / 12002 / 25002 | NoMachine（`nxnode.bin` / `nxrunner.bin`） | `[::1]` |
| 16789 / 19820 | `qoderwake` daemon | 127.0.0.1 |
| 631 / 53 | cups / systemd-resolved | 本機 |
| 36129 / 53593 | 未識別（127.0.0.1 / tailnet IPv6） | 本機 / tailnet |

## 3. systemd（system）

| unit | 狀態 | 說明 |
|---|---|---|
| `goaa-local-console.service` | **enabled + active** | `/opt/goaa/venv/bin/uvicorn main:app --host 127.0.0.1 --port 5188`；`Restart=always`；MainPID 6113；`EnvironmentFiles=/etc/goaa/console.env` |
| `goaa-local-console-tailscale-proxy.service` | enabled + active | `socat TCP-LISTEN:5188,bind=100.114.37.90 → 127.0.0.1:5188` |
| `goaa-comfyui-tailscale-proxy.service` | enabled + active | `socat TCP-LISTEN:8188,bind=100.114.37.90 → 127.0.0.1:8188` |
| `goaa-telemetry-writer.service` | enabled + active | `telemetry_writer.py`（MainPID 6114） |
| `goaa-worker-agent.service` | enabled + active | `/opt/goaa/venv/bin/python /opt/goaa/workers/agent.py`；`WORKER_ID=aika-core-01`、`ROUTER_URL=http://134.199.227.⟨108⟩:8080`、`TAILSCALE_IP=100.114.37.90`（見 §5 更正） |
| `qwenpaw.service` | enabled + active | QwenPaw AI Agent Console |
| （user `aika`）`framer-bridge.service` | active | 「GOAA Framer Agent Bridge V2.1（main draft safe-write, dry-run lock, no publish/deploy）」→ pid 3183910, 埠 18790 |

## 4. 目錄與 repo

- `/opt/goaa/`：`config/ data/ downloads/ heartbeat.py local-console/ logs/ registration.json repo/ run/ runtime/ task_results/ tasks/ venv/ workers/`。
- `/opt/goaa/workers/`：`agent.py`（5,918 B, sha16 `8b1ce13e532fd8e4`）、`task_runner.py`、`embed_worker.py`、`memory_context_fetch.py`、`rag_context_fetch.py`、`topk_query.py`、`telemetry_writer.py`、`corpus_all.jsonl`（577,030 B）。
- `/home/aika/`：`Projects/`（`goaa-ai-main`、`goaa-evidence-tmp`）、`goaa-collaboration/`（`access-test`、`artifact-worktrees`、`claude-worktrees`、`doc-worktrees`、`gemini-review`、`tasks`）、`goaa-control/`、`goaa-review-packages/`、`qwenpaw/`、`qwenpaw-share/`、`.framer-bridge/`、`.qwenpaw/`。
- git repos（D0）：

| repo | branch | HEAD | dirty |
|---|---|---|---|
| `/home/aika/Projects/goaa-ai-main` | `codex/backend-source-capture-20260902` | `02a17ff` | **8** |
| `/opt/goaa/repo` | `main` | `53f599f` | 0 |
| `…/workspaces/default/work/goaa-agent` | `master` | `ee8f811` | **5** |
| `…/work/goaa-butler-candidate-20260902` | detached | `3c8ef2f` | 3 |
| `…/work/goaa-order`、`…/work/goaa-router` | — | — | **無 `.git`**（純目錄） |

- worktree：`workspaces/default/work/` **56 個項目**；`work` + `goaa-collaboration` 底下 `.git` 標記 **40 個**。

## 5. 🔴 更正（本輪實測推翻前輪結論）

`/opt/goaa/workers/agent.py` 第 9 行：

```
ROUTER_URL = os.getenv("ROUTER_API", "http://134.199.227.⟨108⟩:8080")
```

- D0 的 unit 設的是 **`ROUTER_URL`**，而程式讀的是 **`ROUTER_API`** ⇒ env **名不對**；
- 但因**預設值剛好等於 C1 公網位址**，D0 worker **照常運作**（`/workers/status` 顯示 `aika-core-01` 心跳 `2026-09-13T08:14:39Z`，新鮮）。
- 前輪「D0 worker 不會被派遣／不註冊」的推論**不成立**，此處更正。
- 附帶事實：**D0→C1 的 worker 通道走公網（非 tunnel）**，因此 `8080/tcp` 必須保持開放（對應 D0.3 被 Tao 撤銷）。

## 6. Aika-Box 主控台（:5188）能力清單

- 源碼＝`/home/aika/Projects/goaa-ai-main/local-console`（**drop-in 覆寫**：unit 檔寫 `/opt/goaa/local-console`，實際 WorkingDirectory 由 `/etc/systemd/system/goaa-local-console.service.d/override.conf` 指到 repo 版）。
- 證據：`main.py`（138,956 B, sha16 `7f62dfea43d025f6`）＋ `auth.py`（5,104）＋ `intent_detector.py`（13,234）＋ `task_gateway.py`（30,971）＋ `task_envelope.py`（15,725）＋ `tests/` 7 檔。
- `/opt/goaa/local-console` 是**殘缺舊副本**（`task_gateway.py`／`intent_detector.py`／`task_envelope.py` 缺、`main.py` 指紋不同）⇒ **實際運行版本＝repo 版**。

| 能力 | 端點 | 資料來源 |
|---|---|---|
| Models | `GET /settings/models` | `registry/models.json`（911 B, sha16 `c6e05bdae7660671`；`ollama-nomic-embed-text`（embedding）、`ollama-qwen2.5-3b`（chat）…） |
| Skills | `GET /settings/skills` | `registry/skills.json`（1,865 B, **repo `a4bac01bb9e38f14` ≠ opt `41b6bd6830f301f9`**；`exec_embed_corpus_full`（admin）、`exec_topk_query_verify`…） |
| Agents | `GET /settings/agents` | `registry/agents.json`（1,574 B；`rag_memory_agent`、`provider_assistant_agent`…） |
| Task Pool | `GET /tasks/results`、`/tasks/results/{id}`、`POST /tasks/plan`、`POST /tasks/run` | `task_gateway.py`、`task_envelope.py` |
| RAG（含 Memory） | `GET /rag/stats`、`POST /rag/topk`、`POST /rag/chat` | `ENABLE_RAG_CHAT`、`EMBED_MODEL`、`OLLAMA_URL`、`POSTGRES_*` |
| Logs | `GET /logs/recent` | `/opt/goaa/logs/` |
| Node | `GET /node/health` | 本機 worker |
| 登入 | `GET /login`、`POST /login`、`POST /logout`、`GET /session` | `auth.py`、`CONSOLE_SESSION_KEY` |
| Stepper | — | **程式碼中無 `stepper` 識別字**；最接近者＝`task_gateway` 的階段流＋`intent_detector` |

- 路由總數：**19**（uvicorn 已連跑 **33 天**）。

## 7. 入口／代理

- Cloudflare Tunnel：**無**（D0 未安裝 cloudflared）。
- Tailscale：`socat` 兩個（5188、8188）暴露到 `100.114.37.90`。
- SSH：`-L 13102:127.0.0.1:13102 do-c2`（Sep 10 起常駐）⇒ 本機 `:13102` 看 **C2 候選 UI**。

## 8. 風險（唯讀觀察，未處置）

1. RDP `3389`／`3390` 綁 **全介面**；`3199`／`4100`／`4000` 亦綁全介面 ⇒ 若 NAT 有轉發即對公網可見。
2. `18790`（Framer Agent Bridge）為**可寫 Framer 草稿**的通道（描述自稱 dry-run lock、no publish），建議納入守門清單。
3. D0 同時跑 **5 個 next-server**（3102/3103/3199/3200/4100），來源為多個 worktree ⇒ 資源與版本易混淆。
4. `/etc/goaa/worker_secrets.env`（600 `root:root`）以 `aika` 身分**不可讀**（本輪未嘗試提權，未抄錄）。
