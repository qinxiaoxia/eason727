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
  ["https://www.freebuf.com/feed/", "rss"]
]
```

复制时去掉换行，压缩成一行，例如：
```
[["https://eason727.zeabur.app/feeds/all.atom","wewe_rss"],["https://cybersecuritynews.com/feed/","rss"],["https://www.helpnetsecurity.com/feed/","rss"],["http://hackernews.cc/feed","rss"],["https://api.anquanke.com/data/v1/rss","rss"],["https://www.freebuf.com/feed/","rss"]]
```

### FreeBuf 在 GitHub Actions 上报 405

FreeBuf 会对部分**云主机出口 IP**返回 `405 Not Allowed`。脚本已加强浏览器请求头，并对 `.../feed` / `.../feed/` 自动重试。

若仍失败，可任选其一：

1. **Repository secret** `FREEBUF_RSS_MIRROR`：填自建 [RSSHub](https://docs.rsshub.app) 等镜像的完整订阅地址（例如路由 `/freebuf/articles/web`）。
2. **去掉直链 FreeBuf**：在 SupSub 里订阅 FreeBuf，只保留 SupSub 聚合 RSS，不再单独写 FreeBuf 的 URL。

### 可选（启用大模型分类 + 翻译）

| 名称 | 值 |
|------|-----|
| `LLM_API_KEY` | 通义千问 / DeepSeek 等 API Key |
| `LLM_BASE_URL` | 如 `https://dashscope.aliyuncs.com/compatible-mode/v1`（通义） |
| **`LLM_MODELS_JSON`** | **推荐**：多模型回退，一行 JSON 数组，如 `["qwen-plus","qwen1.5-110b-chat","deepseek-r1-distill-qwen-7b","qwen3-32b"]`（与前缀、额度用尽时自动换下一个） |
| `LLM_MODEL` | 单模型时用，如 `qwen-plus`（与 `LLM_MODELS_JSON` 二选一即可；都配时优先 JSON 列表） |
| `WEWE_RSS_URL` | 你的 WeWe RSS 地址，如 `https://eason727.zeabur.app` |
| `FREEBUF_RSS_MIRROR` | 可选。FreeBuf 官方 feed 在 Actions 上 405 时，填镜像 RSS 全文 URL |

---

## 第三步：确认 workflow 已存在

项目包含两个 workflow（**Secrets 共用**），推送后自动生效：

| 文件 | 名称 | 作用 |
|------|------|------|
| `rss-push.yml` | **RSS Push** | 轮巡（北京 **6、8、12、14、18** 整点，跳过 10:00/16:00）→ 实时两类 |
| `rss-push-timed.yml` | **RSS Push Timed** | 北京 **9:30 / 15:30** → 四类汇总 |

> 为何拆成两个？GitHub 对**同一 workflow 里多条 `schedule`** 偶发漏跑；拆成独立文件后更稳定。

- **手动触发**：**Actions** → 选 **RSS Push** 或 **RSS Push Timed** → **Run workflow**

---

## 第四步：若 schedule 不生效，用 Zeabur 兜底

GitHub 的 schedule 有时不触发（fork 默认禁用、60 天无活动等）。可部署 `zeabur-cron-trigger` 到 Zeabur，**默认每 3 小时**触发（可用环境变量 `INTERVAL_MINUTES` 调整）：

1. 打开 [Zeabur](https://zeabur.com)，创建项目，从 GitHub 导入 `qinxiaoxia/eason727` 仓库
2. 添加服务，选择该仓库，**Root Directory** 设为 `zeabur-cron-trigger`
3. 配置环境变量：`GITHUB_TOKEN` = 你的 GitHub PAT（需 `repo` 权限）
4. 部署后服务按 **最少每 180 分钟** 触发一次（与 GitHub `schedule` 叠加时请考虑 **关掉 Zeabur 或只留其一**）。

**为啥 Actions 里全是「Manually run by 我」还约 1 小时一次？**  
多为 **Zeabur 在用你的 PAT** 调 API，在界面上会像「你点的手动运行」。请 **暂停该 Zeabur 服务** 或 **Redeploy** 拉取最新 `zeabur-cron-trigger`（已限制最短间隔 180 分钟）。

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
A：轮巡改 `.github/workflows/rss-push.yml` 的 `cron`（当前 **`0 22,0,4,6,10 * * *`** → 北京 **6、8、12、14、18**，不含 10:00/16:00）；定时改 **`rss-push-timed.yml`** 的 **`30 1,7 * * *`**（UTC）→ 北京 **9:30/15:30**。同时保持 `config.example.py` 中 `POLL_HOURS_BEIJING` / `SCHEDULED_PUSH_TIMES` 一致。

**Q：本机能跑、GitHub Actions 失败（如 FreeBuf `405`）**  
A：Actions 出口 IP 常被目标站拦截，本机宽带 IP 不一定。可换 `FEEDS_JSON` 里 FreeBuf 为 `https://www.freebuf.com/feed/`、拉最新代码；仍失败请配置 Secret **`FREEBUF_RSS_MIRROR`**（自建 RSSHub 等），或在 SupSub 订阅 FreeBuf 后去掉单独 FreeBuf 源。

**Q：翻译结果像拒答、「translated to」重复一串**  
A：通义等模型勿用 **`qwen-math-turbo`**（数学场景模型），请在 Secrets 将 **`LLM_MODEL`** 改为 **`qwen-turbo`** 或 **`qwen-plus`**。脚本已增加技术资讯场景的翻译提示与拒答/重复过滤，失败时会只用英文原标题且不标「译」。

**Q：schedule 不触发、只有手动运行？**  
A：可能是 fork 或 60 天无活动导致 schedule 被禁用。用第四步的 Zeabur 触发器兜底，或到 Actions → RSS Push 检查是否有「Enable workflow」。

**Q：数据库会持久化吗？**  
A：会。`rss_push.db` 随 workflow 提交回仓库，避免重复推送（见 `Commit pushed state` 步骤）。
