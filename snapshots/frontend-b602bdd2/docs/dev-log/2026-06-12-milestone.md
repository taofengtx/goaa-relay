# GOAA 里程碑檢查表 — 2026-06-12

## 今日完成(開工盤點 + F 線真實定位)
- [x] 開工全線盤點 + 三端對齊驗證(AiKa-1 = DO = `deebcc6`,router/console/telemetry/worker 四服務 active)
- [x] V5.5 真實定位(讀 roadmap 正文):**V5.5 = Provider Workspace + Graph-backed Skills + Marketplace**(排在 V5.4 Workflow Graph + External Agents 之後);B/C/D 為 Dogfooding 地基階段,**非** V5.5 本身 ← 更正先前誤解
- [x] F 線(半自動執行)真實盤點:Router 生產 `api.py` 已內建風險引擎雛形 — `TASK_REVENUE`(risk 1-4)/ `select_model`(高風險走 Claude)/ `auto_dispatcher_loop`(P0/P1 + risk≥4 阻擋待審批),對齊 P3-7 治理四級(LOW/MEDIUM/HIGH/CRITICAL)
- [x] 執行層代碼佈局盤點:`local-console/main.py`、`workers/agent.py`、`services/rag/workers/task_runner.py` 等定位確認
- [x] 結論:**F-lite 非從零造**,係形式化現有風險引擎 + 補審批 UI + 節點白名單(對齊 #27 整合優先)

## 背景(近期,aika-core-01 隔離環境;非生產 / 非 Provider 可調用 / 無真實 USD·credits)
- [x] ComfyUI 本地獨立環境跑通(512 baseline 3.5s;768 LCM 6 步 2.4s,2.1x)
- [x] LatentSync 1.6 lip-sync 跑通(93s,峰值 3.71GB)— ⚠️ 臉糊待修(256→512)
- [x] CosyVoice2-0.5B 聲音克隆引擎裝通 — ⚠️ 克隆音質待修(疑 prompt_text ↔ 參考音訊對齊)

## Dogfooding 路線進度(B → C → D → A → E → F)
- [x] B 盒子看見自己(Node Health 真實心跳)
- [x] C 盒子能對話 + 唯讀工具執行(6/9 閉環,mock=false)
- [ ] D Cloud Binding —(核心鏈路已通:心跳自 6/9 未斷、節點 online、PG nodes 表已註冊 aika-core-01;⚠️ 缺口:Router 實時狀態未持久化 PG,未閉環)
- [ ] A 補 SOON 頁做實(Aika Memory/Logs/Settings)
- [ ] E 產品化($1299 出貨打包 / 安裝流程)
- [ ] F 安全執行層(**本次設計目標**;接 Router 現有風險引擎,安全閘須重設計)

## 🔴 待辦 / P0
- [ ] **主線:起草 F-lite 執行層設計** → `docs/architecture/GOAA_LOCAL_TASK_RUNNER_F_LITE.md`
      接點:Router 風險引擎 + 15 條安全硬禁令 + Console/Worker 解耦
      首版必帶:secret 攔截 + 危險命令攔截(rm -rf / dd / 改 systemd / chmod 777)+ HIGH/CRITICAL 審批接 5188 + 生產節點白名單
- [ ] D 線閉環:Router 實時狀態 PG 持久化 + 文檔補完
- [ ] repo 殘留清理(`_tmp_*` / `apply_*` / `.bak`)— **先 list 確認真垃圾再清**(#11 只增不毀,不盲跑 git clean)
- [ ] 本地試水待修:LatentSync 256→512、CosyVoice prompt_text 對齊
- [ ] (低優先)core01 GitHub key — frontend repo 無法 fetch,不卡主線

## 安全提醒(持續)
- secret / 9119 sudo 密碼一律**不印、不貼對話**;export 後讀 `os.environ`(本週反覆洩漏教訓,#22)

---
*狀態截至本次更新;以三端 git HEAD + repo 為最終事實。*
