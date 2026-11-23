# RSS Push 定时触发器（主调度）

> **托管平台**：请用 **Railway**（或 Render / Fly）。**不要再新建 Zeabur 服务**（[Zeabur 停运](https://zeabur.com/zh-CN/blogs/migrate-from-zeabur)）。迁移步骤见 [`docs/迁移到-Railway.md`](../docs/迁移到-Railway.md)。

**不再依赖 GitHub Actions 的 `schedule`**（易漏跑、且非北京时区）。本服务常驻，用 **APScheduler + 北京时间（`Asia/Shanghai`）cron** 调用 GitHub API 的 **`workflow_dispatch`**，分别触发：

| 目标 workflow | 北京时间 | 说明 |
|---------------|----------|------|
| `rss-push.yml`（默认） | **6、18** 整点 | 轮巡 + 实时两类（12:00 改由定时档覆盖） |
| `rss-push-timed.yml`（默认） | **9:30、12:00、15:30、17:30** | 定时六类（+ 实时两类同跑） |

仓库里的 `.github/workflows/rss-push*.yml` 应 **只保留 `workflow_dispatch`**（及可选 `repository_dispatch`），**不要**再写 `on.schedule`。

---

## 部署到 Railway（推荐）

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub → 选本仓库  
2. **Root Directory** = `zeabur-cron-trigger`  
3. 配置环境变量（见下表）  
4. Deploy；看日志是否打印北京时间下次执行  

也可用本目录 `Dockerfile` 部署到 Render / Fly.io。

## 备选：独立小仓库

若平台对 monorepo Root Directory 不友好：

1. 新建空仓库，把本目录 `main.py`、`requirements.txt`、`Dockerfile` 放到根目录  
2. 整库部署，无需 Root Directory  
3. 配置同样环境变量

---

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `GITHUB_TOKEN` | **是** | GitHub PAT：需能触发 Actions。**Classic**：`repo`。**Fine-grained**：仓库 **Actions: Read and write** + **Contents: Read**（或按需） |
| `GITHUB_REPO` | 否 | `owner/repo`，默认 `qinxiaoxia/eason727`（请改成你的仓库） |
| `WORKFLOW_POLL` | 否 | 轮巡 workflow 文件名，默认 `rss-push.yml` |
| `WORKFLOW_TIMED` | 否 | 定时 workflow 文件名，默认 `rss-push-timed.yml` |
| `TRIGGER_TIMEZONE` | 否 | IANA 时区，默认 `Asia/Shanghai` |
| `GITHUB_REF` | 否 | 触发 workflow 的分支，默认 `main` |
| `PORT` | 否 | Flask 监听端口，默认 `8080`（Railway 一般会注入） |

**已废弃（旧版 interval 触发）：** `INTERVAL_MINUTES`、`MIN_INTERVAL_MINUTES`、`I_ACCEPT_HOURLY_DUPLICATE_TRIGGER` — 可全部删除，改由上述 cron 调度。

---

## 验证

1. Zeabur 日志应出现：`[Zeabur trigger] 时区=Asia/Shanghai | 轮巡 ... | 定时 ...`，以及 **`任务 poll_beijing 下次执行: ...`**
2. 浏览器打开 **`https://你的服务域名/status`**，应看到 `ok: true`、`jobs` 里有两条 `next_run_time`（北京时间）
3. 若 `/status` 报 `scheduler not running`：多半是平台用 **`gunicorn main:app` 且未 import 调度**；本仓库已改为 **import 时即启动调度**，并带 **文件锁**（多 worker 时仅一处触发）。仍建议 **启动命令** 使用 **`python main.py`**（见根目录 `Procfile`）
4. **整点不跑**：部分套餐容器会**休眠**，进程停了就不会触发；需升级常驻实例或用外部 uptime 保活（见下）
5. 到点后在 GitHub **Actions** 应出现对应 workflow；触发者可能显示为你的账号（PAT），属正常

### 若仍漏跑（平台休眠）

Zeabur 若对**无流量**容器缩容/休眠，APScheduler 也会停。可：

- 换**常驻**规格，或  
- 用 [cron-job.org](https://cron-job.org) 等 **每 5 分钟 GET 一次** `https://你的域名/health` 保活（仅缓解，非 100%），或  
- 改用「定时请求 GitHub API」类外部 cron（需自己接 `workflow_dispatch`）

---

## 修改推送时间

改 **本目录 `main.py`** 里 `CronTrigger` 的 `hour` / `minute`，推送后 **重新部署 Zeabur**。同时建议与 `rss-wechat-pusher/config.example.py` 里的 `POLL_HOURS_BEIJING` / `SCHEDULED_PUSH_TIMES` 语义保持一致。
