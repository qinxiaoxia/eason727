#!/bin/bash
# 将 zeabur-cron-trigger 推送到独立仓库，便于 Zeabur 部署（无需 Root Directory）
# 用法：先在 GitHub 创建空仓库（如 rss-push-trigger），然后：
#   REPO_URL=https://github.com/qinxiaoxia/rss-push-trigger.git GITHUB_TOKEN=xxx bash deploy-standalone.sh

set -e
cd "$(dirname "$0")"
REPO_URL="${REPO_URL:-https://github.com/qinxiaoxia/rss-push-trigger.git}"

if [ -z "$GITHUB_TOKEN" ]; then
  echo "请设置 GITHUB_TOKEN"
  exit 1
fi

# 带 token 的 URL（从 REPO_URL 提取用户名，或默认 qinxiaoxia）
USER="${GITHUB_USER:-qinxiaoxia}"
PUSH_URL="${REPO_URL/https:\/\//https://${USER}:${GITHUB_TOKEN}@}"

rm -rf /tmp/zeabur-trigger-deploy
mkdir -p /tmp/zeabur-trigger-deploy
cp main.py requirements.txt /tmp/zeabur-trigger-deploy/
cd /tmp/zeabur-trigger-deploy

git init
git add .
git commit -m "zeabur cron trigger"
git branch -M main
git remote add origin "$REPO_URL"
git push -u "$PUSH_URL" main

echo "已推送到 $REPO_URL"
echo "在 Zeabur 添加该仓库，无需 Root Directory"
