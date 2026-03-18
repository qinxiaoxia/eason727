#!/bin/bash
# 部署到 GitHub eason727 仓库
# 用法：cd /Users/hehe/Desktop/备份勿动/vue-admin && bash rss-wechat-pusher/deploy-to-github.sh

set -e
cd "$(dirname "$0")/.."
REPO="https://github.com/qinxiaoxia/eason727.git"

echo "=== 1. 修改远程地址为 eason727 ==="
git remote set-url origin "$REPO" 2>/dev/null || git remote add origin "$REPO"
git remote -v

echo ""
echo "=== 2. 提交并推送 ==="
git add .
git status --short
if git diff --staged --quiet 2>/dev/null; then
  echo "无新变更，跳过 commit"
else
  git commit -m "rss-wechat-pusher"
fi
git branch -M main
echo "正在推送到 $REPO ..."
git push -u origin main

echo ""
echo "=== 部署完成 ==="
echo "下一步：到 https://github.com/qinxiaoxia/eason727/settings/secrets/actions 配置 Secrets"
echo "  必填：WECHAT_WEBHOOK, FEEDS_JSON"
echo "  可选：LLM_API_KEY, LLM_BASE_URL, LLM_MODEL"
