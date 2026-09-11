# Round C2.1 — 發版前一致性檢查（唯讀）

- **性質**：**只讀**。未改檔、未重啟、未建目錄、未動 env／DNS／tunnel／防火牆。
  - 唯一非純讀動作：依令執行的 `git fetch origin --prune`（只更新 remote-tracking refs，**不動工作樹**）。
- **主機**：
  - 前端倉（黃金 clone，aika-core-01 本機）：`/home/aika/Projects/goaa-ai-main`，remote `git@github-goaa:taofengtx/goaa-ai-frontend.git`，當前分支 `codex/backend-source-capture-20260902`。
  - C1：ssh 別名 `do-runtime-anchor`（root）。
- 所有 IP 以切分寫法。

---

## 1. 前端版本基準（發版前置條件）

### 1.1 fetch

指令：`git fetch origin --prune`

```
来自 github-goaa:taofengtx/goaa-ai-frontend
 * branch            codex/backend-source-capture-20260902 -> FETCH_HEAD
```

### 1.2 `git merge-base 718ee109 76af718b0568992c900b72d1aff5aad2516046dc`

```
76af718b0568992c900b72d1aff5aad2516046dc
```

→ **merge-base 就等於 C1 的版本**（`76af718b`）。

### 1.3 `git log --oneline 718ee109..76af718b…`（C1 有、候選線沒有）

```
（空）
count: 0
```

### 1.4 `git log --oneline 76af718b…718ee109`（候選線有、C1 沒有）

```
718ee10 Round C1 fix: scope token sheets to .goaa-portal (golden chat avatar already uses class goaa)
51c9914 Round C1: three-portal shell, growth pages, golden sign-out wiring, tests
daecc2a fix(c2): keep the golden business credential in the golden slot
45ca6de feat(c2): clerk sign-in with a golden business-session bridge (isolated candidate)
13ecaa8 docs(c2): document the hardened database authentication posture
b289587 feat(c2): isolated PostgreSQL-backed agent licence application loop
b8050fc feat: add isolated three-portal business preview
a7e8b1c Portal Preview Technical Foundation (isolated v1)
count: 8
```

### 1.5 `git diff --stat 718ee109 76af718b…`

```
109 files changed, 14 insertions(+), 16045 deletions(-)
```

（此方向 = 「從候選線退回 C1」，故表現為刪除 16,045 行。反向 `git diff --stat 76af718b 718ee109` = `109 files changed, 16045 insertions(+), 14 deletions(-)`，即候選線的累積增量。）

### 1.6 該倉 main 最新 commit 與日期

指令：`git log -1 --format='%H | %ad | %an | %s' --date=iso origin/main`

```
00c848d85b5de93e725c0df99743783d365022f0 | 2026-08-25 23:20:22 -0700 | Tao | fix: show $39.90 professional connect CTA in planning workspace
```

補充：`git merge-base --is-ancestor 00c848d… 76af718b…` → **YES**；`00c848d..76af718b` 共 **311 commits** → **main 又落後 C1 311 個 commit**。

### 1.7 結論（明確）

> **C1 的版本 `76af718b0568992c900b72d1aff5aad2516046dc` 是候選線 `718ee109` 的「祖先」（ancestor），未分岔。**
> - `718ee109..76af718b` = **0 個 commit** → C1 **沒有任何候選線缺的改動**。
> - 候選線嚴格在其之上（8 個 commit，見 1.4；我們的 C2 分支 HEAD `40c8546e` 又在 `718ee109` 之上 12 個 commit）。
> - 另：`origin/main` 是 C1 的祖先（落後 311 個 commit）。
>
> **部署方向安全**：C1 → 候選線屬 fast-forward 語意，**不需 rebase、無衝突風險**。

---

## 2. 「C1 有候選線沒有的改動」→ **條件不成立，免做**

第 1 項顯示 `718ee109..76af718b` = **0**，即 C1 **沒有**候選線缺的改動 → 本節要求的「C1 專有 commit 檔案清單」**不存在，無需列舉**。

**補充（方向相反，供手冊參考）**：候選線相對 C1 的累積增量共 **109 檔**（+16,045 / −14）。其中與「我們改過的 6 個檔案」重疊者為 **5 個**：

| 我們改過的檔案 | 候選線是否動到 |
|---|---|
| `app/lib/clerk-entry.ts` | **是** |
| `middleware.ts` | **是** |
| `app/layout.tsx` | **是** |
| `app/goaa-clerk-login/page.tsx` | **是** |
| `app/styles/goaa-tokens.css` | **是** |
| `app/components/`（`ProfessionalHandoffCard` / `ProfessionalConnectBar` / `MatterProfessionalConnect`） | **否（未被動到）** |

> 讀法：這些重疊是「候選線相對 C1 的新增」，**不是** C1 專有改動；因 C1 是候選線的祖先，重疊不構成衝突。

---

## 3. C1 防火牆現況（唯讀）

### 3.1 `ufw status verbose`

```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp (OpenSSH)           ALLOW IN    Anywhere
80/tcp                     ALLOW IN    Anywhere
443/tcp                    ALLOW IN    Anywhere
8080/tcp                   ALLOW IN    Anywhere      # GOAA Model Router API
22/tcp (OpenSSH (v6))      ALLOW IN    Anywhere (v6)
80/tcp (v6)                ALLOW IN    Anywhere (v6)
443/tcp (v6)               ALLOW IN    Anywhere (v6)
8080/tcp (v6)              ALLOW IN    Anywhere (v6)  # GOAA Model Router API

587/tcp                    ALLOW OUT   Anywhere      # Zoho SMTP
587/tcp (v6)               ALLOW OUT   Anywhere (v6)
```

### 3.2 關鍵鏈（`iptables -S`）

```
-P FORWARD DROP
-A FORWARD -j DOCKER-USER          ← 空（僅 -N，無規則）
-A FORWARD -j DOCKER-FORWARD
-A FORWARD -j ufw-before-logging-forward
-A FORWARD -j ufw-before-forward   ← ufw 的 forward 規則在 Docker 之後

-A DOCKER-FORWARD -j DOCKER-CT / DOCKER-INTERNAL / DOCKER-BRIDGE
-A DOCKER-BRIDGE -o docker0 -j DOCKER
-A DOCKER -d 172.17.0.`＋`2/32 ! -i docker0 -o docker0 -p tcp --dport 5432 -j ACCEPT
-A DOCKER -d 172.18.0.`＋`3/32 ! -i br-03d6f0fd0feb -o br-03d6f0fd0feb -p tcp --dport 80 -j ACCEPT

（nat） -A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER
（nat） -A DOCKER ! -i docker0 -p tcp --dport 5432 -j DNAT --to-destination 172.17.0.`＋`2:5432
（nat） -A DOCKER ! -i br-03d6f0fd0feb -p tcp --dport 17879 -j DNAT --to-destination 172.18.0.`＋`3:80
```

- `net.ipv4.ip_forward = 1`（Docker 必需）。
- **`DOCKER-USER` 鏈為空** → Docker 沒有任何額外限制。

### 3.3 逐埠判定（主機層）

| 埠 | 服務 | ufw 是否放行 | 實際對公網 | 說明 |
|---|---|---|---|---|
| **5432** | Postgres（Docker） | **否** | **可達** | **Docker 繞過 ufw**：nat DNAT 至容器，filter 由 `DOCKER` 鏈先 `ACCEPT`（在 `ufw-before-forward` 之前）；`DOCKER-USER` 空 → 無限制 |
| **8080** | goaa-router（systemd） | **是**（`# GOAA Model Router API`） | **可達** | ufw 明確 ALLOW IN；非 Docker，走 INPUT |
| **18789** | openclaw（systemd） | **否** | **不可達** | 非 Docker → 走 INPUT，被 default deny 擋下；僅 Cloudflare tunnel 可達 |
| **17879** | openclaw 容器 nginx（Docker） | **否** | **可達** | 同 5432 的 Docker 繞過機制 |
| 3100 | goaa-web | — | **不可達** | 只綁 `127.0.0.`＋`1` |
| 22 / 80 / 443 | sshd / — / — | 是 | 22 可達；80/443 **無服務監聽** | 宿主無 nginx（80/443 放行但沒有後端） |
| 20241 | cloudflared metrics | 否 | 不可達 | 只綁 `127.0.0.`＋`1` |

### 3.4 邊界聲明

**以上為「主機層」判定。雲端供應商防火牆（DO Cloud Firewall／面板規則）在主機上不可見 →「主機層以外未知」。** 本輪未做任何外部連通性探測，也未改動任何規則。

---

## 4. C1 前端 unit 的環境變數注入方式確認（唯讀）

指令：`ls -la /etc/systemd/system/goaa-web.service.d/`、`grep -rl EnvironmentFile /etc/systemd/system/*.service`、`ls -la /etc/goaa/`、`systemctl cat goaa-web.service`

| 檢查 | 結果 |
|---|---|
| `goaa-web.service` 是否有 drop-in 目錄 | **無**（`/etc/systemd/system/goaa-web.service.d/` 不存在） |
| 是否有 `EnvironmentFile=` | **無** |
| 環境變數注入方式 | **`Environment=` 內聯** 3 個變數名：`NODE_ENV`、`HOSTNAME`、`PORT`（值未列） |
| `/etc/goaa/` 是否有前端用 env 檔 | **無**；目錄僅 `openclaw.env`(600)、`secrets.env`(600) 及 4 個 `secrets.env.*` 備份檔（皆 600） |
| 全機使用 `EnvironmentFile=` 的 unit | `goaa-router.service`、`goaa-model-router.service`、`openclaw.service`、`sshd.service` |

→ **前端目前沒有任何外部 env 檔可用**；任何新變數（例如 Clerk／付費開關）只能改 unit 的 `Environment=`（值會寫進 unit 檔，不建議放機密），或**新增** env 檔 + drop-in（本輪未建）。

---

## 5. 對發版手冊的直接意涵

1. **部署方向安全**：C1（`76af718b`）是候選線祖先 → 以候選線覆蓋 C1 為 fast-forward 語意，**無需 rebase、無衝突**（與 §1.7 一致）。
2. **`origin/main` 不能當發版基準**：main 落後 C1 311 個 commit（2026-08-25）。
3. **前端 env 注入需先建置**：目前無前端 env 檔、無 drop-in；若要注入開關，手冊須含「新增 env 檔 + drop-in + `daemon-reload`」步驟（**本輪未執行**）。
4. **暴露面需先拍板**：`8080`（ufw 放行）與 `5432`／`17879`（Docker 繞過 ufw）目前對公網可達；`18789` 不可達。發版前應確認是否為預期，否則應收斂（**本輪未改**）。
5. **備份缺口仍在**（承 C2.0）：部署前必須手動 dump（最近一次 2026-09-06）。

---

## 6. 本輪未做的事

未改任何檔案、未重啟／未 reload、未建目錄、未動 env／DNS／tunnel／防火牆；除依令的 `git fetch`（僅更新 remote-tracking ref）外，全部指令為唯讀查詢。

---

## 附錄 A — 第 1 項原始輸出（重跑留檔，作為正式取證）

```
### git fetch origin --prune
来自 github-goaa:taofengtx/goaa-ai-frontend
 * branch            codex/backend-source-capture-20260902 -> FETCH_HEAD

### merge-base 718ee109 76af718b0568992c900b72d1aff5aad2516046dc
76af718b0568992c900b72d1aff5aad2516046dc

### git log --oneline 718ee109..76af718b（C1 有、候選線沒有）
count=0

### git log --oneline 76af718b..718ee109（候選線有、C1 沒有）
718ee10 Round C1 fix: scope token sheets to .goaa-portal (golden chat avatar already uses class goaa)
51c9914 Round C1: three-portal shell, growth pages, golden sign-out wiring, tests
daecc2a fix(c2): keep the golden business credential in the golden slot
45ca6de feat(c2): clerk sign-in with a golden business-session bridge (isolated candidate)
13ecaa8 docs(c2): document the hardened database authentication posture
b289587 feat(c2): isolated PostgreSQL-backed agent licence application loop
b8050fc feat: add isolated three-portal business preview
a7e8b1c Portal Preview Technical Foundation (isolated v1)
count=8

### git diff --stat 718ee109 76af718b
 109 files changed, 14 insertions(+), 16045 deletions(-)

### main 最新 commit 與日期
00c848d85b5de93e725c0df99743783d365022f0 | 2026-08-25 23:20:22 -0700 | Tao | fix: show $39.90 professional connect CTA in planning workspace
```

> 本次重跑輸出與首次執行**逐字一致**（含 commit 計數與 diffstat）。

## 附錄 B — 第 2 項判定依據

條件句式：「**若**第 1 項顯示 C1 有候選線沒有的改動」→ 第 1 項 `718ee109..76af718b` = **0 筆** → **條件不成立**，故不產出「C1 專有 commit 的檔案清單」。

反向事實（候選線相對 C1 的 109 檔增量）中，與指定 6 個項目重疊者：

| 指定檔案 | 是否被候選線動到 |
|---|---|
| `app/lib/clerk-entry.ts` | 是 |
| `middleware.ts` | 是 |
| `app/layout.tsx` | 是 |
| `app/goaa-clerk-login/page.tsx` | 是 |
| `app/styles/goaa-tokens.css` | 是 |
| `app/components/`（`ProfessionalHandoffCard`／`ProfessionalConnectBar`／`MatterProfessionalConnect`） | 否 |

判定指令：`git diff --name-only 76af718b… 718ee109 | grep -E 'clerk-entry|(^|/)middleware\.ts$|layout\.tsx|goaa-clerk-login|goaa-tokens|ProfessionalHandoff|ProfessionalConnectBar|MatterProfessionalConnect'`
