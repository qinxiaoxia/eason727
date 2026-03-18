# Zeabur RSS Push 定时触发器

每 5 分钟调用 GitHub API 触发 `repository_dispatch`，启动 RSS Push workflow。

## 部署到 Zeabur

1. 在 Zeabur 创建新项目，从 GitHub 导入 `qinxiaoxia/eason727` 仓库
2. 添加服务时选择该仓库，**Root Directory** 设为 `zeabur-cron-trigger`
3. 配置环境变量：
   - `GITHUB_TOKEN`：GitHub PAT，需 `repo` 权限
   - `GITHUB_REPO`：（可选）默认 `qinxiaoxia/eason727`
4. 部署后服务会常驻，每 5 分钟自动触发一次

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| GITHUB_TOKEN | 是 | GitHub Personal Access Token，需 repo 权限 |
| GITHUB_REPO | 否 | 仓库，默认 qinxiaoxia/eason727 |
