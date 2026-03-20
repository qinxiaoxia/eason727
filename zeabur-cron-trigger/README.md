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
| MIN_INTERVAL_MINUTES | 否 | **下限**（分钟），默认 **180**。若你在 Zeabur 里误设了 `INTERVAL_MINUTES=60`，代码仍会按最少 180 执行，避免 Actions 里出现「每小时 Manually run」 |

**若 GitHub Actions 列表里几乎全是「Manually run by 你本人」且约每小时一次：**  
那是 **本服务在用你的 PAT 调 `workflow_dispatch`**，不是仓库里的 `schedule`。  
处理方式二选一：① **暂停/删除 Zeabur 上该服务**（只依赖 GitHub 定时即可）；② **重新部署** 本目录最新代码，让最短间隔生效为 180 分钟。
