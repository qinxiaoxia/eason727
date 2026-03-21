# Zeabur RSS Push 定时触发器

默认每 **3 小时**（`INTERVAL_MINUTES=180`）调用 GitHub API 触发 **workflow_dispatch**，启动 RSS Push workflow。

## 部署到 Zeabur（推荐：独立仓库）

若从 eason727 部署时 Root Directory 报错，可用独立仓库：

1. 在 GitHub 新建空仓库，如 `rss-push-trigger`
2. 把本目录下 `main.py`、`requirements.txt` 放到仓库**根目录**
3. 在 Zeabur 添加服务，选择该仓库，**无需设置 Root Directory**
4. 配置环境变量 `GITHUB_TOKEN`（GitHub PAT，需 repo 权限）
5. 部署

## 部署到 Zeabur（从 eason727）

1. 在 Zeabur 添加服务，选择 `qinxiaoxia/eason727` 仓库
2. **Root Directory** 设为 `zeabur-cron-trigger`（无前导斜杠）
3. 配置环境变量 `GITHUB_TOKEN`
4. 部署

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| GITHUB_TOKEN | 是 | GitHub Personal Access Token，需 repo 权限 |
| GITHUB_REPO | 否 | 仓库，默认 qinxiaoxia/eason727 |
| INTERVAL_MINUTES | 否 | 期望间隔（分钟），默认 **180** |
| `I_ACCEPT_HOURLY_DUPLICATE_TRIGGER` | 否 | 设为 `1` 才允许低于 180 分钟；**不要**与 `INTERVAL_MINUTES=60` + `MIN_INTERVAL_MINUTES=60` 同时用，否则会 **每小时** 触发 |

**若仍为「约 1 小时一次」：** 到 Zeabur 环境变量里 **删掉** `INTERVAL_MINUTES`、`MIN_INTERVAL_MINUTES`（或都改为 `180`），**保存后重新部署**。旧版若两变量都是 `60`，程序会按 60 跑。

**若 GitHub Actions 里几乎全是「Manually run by 你」：** 是 **本服务** 在触发，不是 `schedule`。可 **暂停本服务** 只留 GitHub 定时。
