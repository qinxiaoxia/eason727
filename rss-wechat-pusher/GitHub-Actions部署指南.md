# GitHub Actions 部署指南

按以下步骤将 RSS 推送部署到 GitHub Actions，无需电脑常开。

---

## 第一步：推送代码到 GitHub

### 1.1 在 GitHub 创建新仓库

1. 打开 https://github.com ，点击右上角 **+**（绿色按钮）→ **New repository**
2. **Repository name**：填仓库名，如 `vue-admin` 或 `rss-pusher`
3. **Description**：可留空
4. 选择 **Public**
5. **不要**勾选 "Add a README file"、"Add .gitignore"、"Choose a license"
6. 点击绿色按钮 **Create repository**

### 1.2 在本地推送代码

创建完成后，GitHub 会显示命令。在终端执行（把 `你的用户名` 和 `仓库名` 换成你的）：

```bash
cd /Users/hehe/Desktop/备份勿动/vue-admin

# 若已有 git，检查是否已关联远程
git remote -v

# 若没有 origin，添加远程（替换成你的仓库地址）
git remote add origin https://github.com/你的用户名/仓库名.git

# 提交并推送
git add .
git commit -m "add rss-wechat-pusher"
git branch -M main
git push -u origin main
```

**若仓库已存在**：若 `vue-admin` 已有 GitHub 仓库，直接执行 `git push origin main` 即可。

> 注意：推送前请确认 `config.py` 未被提交（应在 .gitignore 中），避免泄露 Webhook 和 API Key。

---

## 第二步：配置 GitHub Secrets

1. 打开仓库页面，点击 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**，逐个添加以下密钥：

### 必填

| 名称 | 值 |
|------|-----|
| `WECHAT_WEBHOOK` | 你的企业微信群机器人 Webhook 完整地址，如 `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx` |
| `FEEDS_JSON` | RSS 源 JSON，见下方格式 |

### FEEDS_JSON 格式

```json
[
  ["https://eason727.zeabur.app/feeds/all.atom", "wewe_rss"],
  ["https://cybersecuritynews.com/feed/", "rss"],
  ["https://www.helpnetsecurity.com/feed/", "rss"],
  ["http://hackernews.cc/feed", "rss"],
  ["https://api.anquanke.com/data/v1/rss", "rss"],
  ["https://www.freebuf.com/feed", "rss"]
]
```

复制时去掉换行，压缩成一行，例如：
```
[["https://eason727.zeabur.app/feeds/all.atom","wewe_rss"],["https://cybersecuritynews.com/feed/","rss"],["https://www.helpnetsecurity.com/feed/","rss"],["http://hackernews.cc/feed","rss"],["https://api.anquanke.com/data/v1/rss","rss"],["https://www.freebuf.com/feed","rss"]]
```

### 可选（启用大模型分类 + 翻译）

| 名称 | 值 |
|------|-----|
| `LLM_API_KEY` | 通义千问 / DeepSeek 等 API Key |
| `LLM_BASE_URL` | 如 `https://dashscope.aliyuncs.com/compatible-mode/v1`（通义） |
| `LLM_MODEL` | 如 `qwen-turbo` |
| `WEWE_RSS_URL` | 你的 WeWe RSS 地址，如 `https://eason727.zeabur.app` |

---

## 第三步：确认 workflow 已存在

项目已包含 `.github/workflows/rss-push.yml`，推送后会自动生效。

- **定时执行**：每 5 分钟运行一次（监管机构预警、重大安全事件→立即推送；9:30、15:30 北京→定时推送）
- **手动触发**：仓库 → **Actions** → **RSS Push** → **Run workflow**

---

## 第四步：若 schedule 不生效，用 Zeabur 兜底

GitHub 的 schedule 有时不触发（fork 默认禁用、60 天无活动等）。可部署 `zeabur-cron-trigger` 到 Zeabur，每 5 分钟自动触发：

1. 打开 [Zeabur](https://zeabur.com)，创建项目，从 GitHub 导入 `qinxiaoxia/eason727` 仓库
2. 添加服务，选择该仓库，**Root Directory** 设为 `zeabur-cron-trigger`
3. 配置环境变量：`GITHUB_TOKEN` = 你的 GitHub PAT（需 `repo` 权限）
4. 部署后服务常驻，每 5 分钟触发一次 RSS Push

---

## 第五步：验证

1. 打开仓库页面，点击 **Actions**
2. 选择 **RSS Push** workflow
3. 点击 **Run workflow** 手动触发一次
4. 查看运行日志，确认无报错
5. 检查企业微信群是否收到推送

---

## 常见问题

**Q：运行报错「FEEDS_JSON」相关**  
A：检查 FEEDS_JSON 是否为合法 JSON，且为字符串形式（用双引号包裹）。

**Q：企业微信没收到消息**  
A：检查 WECHAT_WEBHOOK 是否完整、是否复制错；检查企业微信机器人是否被移除。

**Q：如何修改推送时间？**  
A：编辑 `.github/workflows/rss-push.yml`，修改 `cron` 表达式。当前为每 5 分钟。

**Q：schedule 不触发、只有手动运行？**  
A：可能是 fork 或 60 天无活动导致 schedule 被禁用。用第四步的 Zeabur 触发器兜底，或到 Actions → RSS Push 检查是否有「Enable workflow」。

**Q：数据库会持久化吗？**  
A：会。使用 GitHub Actions Cache 缓存 `~/.rss-wechat-pusher` 目录，避免重复推送。
