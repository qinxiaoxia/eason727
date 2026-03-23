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
  ["https://www.4hou.com/feed", "rss"],
  ["http://securityaffairs.co/wordpress/feed", "rss"]
]
```

复制时去掉换行，压缩成一行，例如：
```
[["https://eason727.zeabur.app/feeds/all.atom","wewe_rss"],["https://cybersecuritynews.com/feed/","rss"],["https://www.helpnetsecurity.com/feed/","rss"],["http://hackernews.cc/feed","rss"],["https://api.anquanke.com/data/v1/rss","rss"],["https://www.4hou.com/feed","rss"],["http://securityaffairs.co/wordpress/feed","rss"]]
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
| **`LLM_MODELS_JSON`** | **推荐**：多模型回退，一行 JSON 数组（与 `config.example.py` 中默认列表一致，如多个 `qwen-plus-*` 快照 + `qwen-plus-latest` 等；额度用尽或失败时自动换下一个） |
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

> 为何拆成两个？职责分离；**定时触发不依赖 GitHub `schedule`**，由 Zeabur `zeabur-cron-trigger` 按北京时间 `workflow_dispatch` 触发（见第四步）。

- **手动触发**：**Actions** → 选 **RSS Push** 或 **RSS Push Timed** → **Run workflow**

---

## 第四步：用 Zeabur 做**唯一**调度（推荐）

GitHub 的 `schedule` 易漏跑，**推荐 workflow 里不写 `on.schedule`**，只保留 `workflow_dispatch`，由 **`zeabur-cron-trigger`** 在 Zeabur 上按 **北京时间 cron** 调用 API 触发（轮巡 6/8/12/14/18 整点 + 定时 9:30/15:30）。详见仓库内 `zeabur-cron-trigger/README.md`。

1. 打开 [Zeabur](https://zeabur.com)，创建项目，从 GitHub 导入你的仓库
2. 添加服务，**Root Directory** 设为 `zeabur-cron-trigger`
3. 环境变量：`GITHUB_TOKEN` = PAT（需能触发 Actions，见该 README 表）；`GITHUB_REPO` = `你的用户名/仓库名`
4. 部署后看 Zeabur 日志应打印调度说明；到点后 GitHub Actions 会出现对应运行

**为啥 Actions 里显示「Manually run by 我」？**  
**Zeabur 用 PAT 调 `workflow_dispatch`**，界面会像手动运行，属正常。

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
A：若使用 Zeabur 调度：改 **`zeabur-cron-trigger/main.py`** 里两处 `CronTrigger` 的 `hour`/`minute`，并 **重新部署 Zeabur**。同时保持 `config.example.py` 中 `POLL_HOURS_BEIJING` / `SCHEDULED_PUSH_TIMES` 与之一致。

**Q：本机能跑、GitHub Actions 失败（如 FreeBuf `405`）**  
A：Actions 出口 IP 常被目标站拦截，本机宽带 IP 不一定。可换 `FEEDS_JSON` 里 FreeBuf 为 `https://www.freebuf.com/feed/`、拉最新代码；仍失败请配置 Secret **`FREEBUF_RSS_MIRROR`**（自建 RSSHub 等），或在 SupSub 订阅 FreeBuf 后去掉单独 FreeBuf 源。

**Q：翻译结果像拒答、「translated to」重复一串**  
A：通义等模型勿用 **`qwen-math-turbo`**（数学场景模型），请在 Secrets 将 **`LLM_MODEL`** 改为 **`qwen-turbo`** 或 **`qwen-plus`**。脚本已增加技术资讯场景的翻译提示与拒答/重复过滤，失败时会只用英文原标题且不标「译」。

**Q：GitHub schedule 不触发？**  
A：可完全不用 `on.schedule`，改用第四步 Zeabur 触发器；或检查 fork/60 天无活动是否禁用了 schedule。

**Q：数据库会持久化吗？**  
A：会。`rss_push.db` 随 workflow 提交回仓库，避免重复推送（见 `Commit pushed state` 步骤）。
