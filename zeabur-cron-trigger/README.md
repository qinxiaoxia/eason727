# Zeabur RSS Push 定时触发器（主调度）

**不再依赖 GitHub Actions 的 `schedule`**（易漏跑）。本服务在 Zeabur 上常驻，用 **APScheduler + 北京时间（`Asia/Shanghai`）cron** 调用 GitHub API 的 **`workflow_dispatch`**，分别触发：

| 目标 workflow | 北京时间 | 说明 |
|---------------|----------|------|
| `rss-push.yml`（默认） | **6、8、12、14、18** 整点 | 轮巡 + 实时两类 |
| `rss-push-timed.yml`（默认） | **9:30、15:30** | 定时四类 |

仓库里的 `.github/workflows/rss-push*.yml` 应 **只保留 `workflow_dispatch`**（及可选 `repository_dispatch`），**不要**再写 `on.schedule`。

---

## 部署到 Zeabur（推荐：独立仓库）

若从主仓库部署时 Root Directory 报错，可用独立仓库：

1. 在 GitHub 新建空仓库，如 `rss-push-trigger`
2. 把本目录下 `main.py`、`requirements.txt` 放到仓库**根目录**
3. 在 Zeabur 添加服务，选择该仓库，**无需设置 Root Directory**
4. 配置环境变量（见下表）
5. 部署

## 部署到 Zeabur（从主仓库子目录）

1. 在 Zeabur 添加服务，选择你的 GitHub 仓库
2. **Root Directory** 设为 `zeabur-cron-trigger`（无前导斜杠）
3. 配置环境变量
4. 部署

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
| `PORT` | 否 | Flask 监听端口，默认 `8080`（Zeabur 一般会注入） |

**已废弃（旧版 interval 触发）：** `INTERVAL_MINUTES`、`MIN_INTERVAL_MINUTES`、`I_ACCEPT_HOURLY_DUPLICATE_TRIGGER` — 可全部删除，改由上述 cron 调度。

---

## 验证

1. Zeabur 日志应出现：`[Zeabur trigger] 时区=Asia/Shanghai | 轮巡 ... | 定时 ...`
2. 到点后在 GitHub **Actions** 应出现对应 workflow 运行；触发者可能显示为你的账号（PAT 所有者），属正常现象。

---

## 修改推送时间

改 **本目录 `main.py`** 里 `CronTrigger` 的 `hour` / `minute`，推送后 **重新部署 Zeabur**。同时建议与 `rss-wechat-pusher/config.example.py` 里的 `POLL_HOURS_BEIJING` / `SCHEDULED_PUSH_TIMES` 语义保持一致。
