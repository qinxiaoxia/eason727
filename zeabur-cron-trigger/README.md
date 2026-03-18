# Zeabur RSS Push 定时触发器

每 5 分钟调用 GitHub API 触发 `repository_dispatch`，启动 RSS Push workflow。

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
