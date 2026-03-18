#!/bin/bash
# 部署到 GitHub eason727 仓库
# 用法：GITHUB_TOKEN=你的token bash rss-wechat-pusher/deploy-to-github.sh
# 或先 export GITHUB_TOKEN=你的token，再 bash rss-wechat-pusher/deploy-to-github.sh

set -e
cd "$(dirname "$0")/.."
REPO="https://github.com/qinxiaoxia/eason727.git"

# 若有 GITHUB_TOKEN，用带 token 的 URL 推送
if [ -n "$GITHUB_TOKEN" ]; then
  PUSH_URL="https://qinxiaoxia:${GITHUB_TOKEN}@github.com/qinxiaoxia/eason727.git"
else
  PUSH_URL="$REPO"
fi

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
echo "正在推送到 eason727 ..."
git push -u "$PUSH_URL" main

echo ""
echo "=== 部署完成 ==="
echo "下一步：到 https://github.com/qinxiaoxia/eason727/settings/secrets/actions 配置 Secrets"
echo "  必填：WECHAT_WEBHOOK, FEEDS_JSON"
echo "  可选：LLM_API_KEY, LLM_BASE_URL, LLM_MODEL"
