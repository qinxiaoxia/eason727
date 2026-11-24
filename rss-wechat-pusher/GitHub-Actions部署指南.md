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
| **`LLM_MODELS_JSON`** | **推荐**：分类/摘要等多模型回退，如 `["qwen-plus","qwen-turbo"]` |
| **`LLM_TRANSLATE_MODELS_JSON`** | **标题翻译专用**，推荐 `["qwen-mt-flash"]`（通义翻译模型；勿把 mt 填进上面的 MODELS，分类会坏） |
| `LLM_MODEL` | 单模型时用，如 `qwen-plus`（与 `LLM_MODELS_JSON` 二选一即可；都配时优先 JSON 列表） |
| `WEWE_RSS_URL` | 你的 WeWe RSS 地址，如 `https://eason727.zeabur.app` |
| `FREEBUF_RSS_MIRROR` | 可选。FreeBuf 官方 feed 在 Actions 上 405 时，填镜像 RSS 全文 URL |

### 英文摘要外链（阿里云 OSS，推荐）

GitHub / jsDelivr 国内常打不开，摘要 HTML 上传到 OSS，企微只放链接。

1. 控制台建桶（建议与通义同地域，如华东 1），读写权限选 **公共读**（或私有桶 + 上传时对象 ACL `public-read`，脚本已设置）。
2. 建 RAM 用户，授权 `AliyunOSSFullAccess`（或仅该桶的读写），创建 AccessKey。
3. 仓库 Secrets 增加：

| 名称 | 示例 |
|------|------|
| `OSS_ACCESS_KEY_ID` | LTAI... |
| `OSS_ACCESS_KEY_SECRET` | ... |
| `OSS_BUCKET` | `your-rss-summaries` |
| `OSS_ENDPOINT` | `oss-cn-hangzhou.aliyuncs.com` |
| `OSS_PUBLIC_BASE_URL` | 可选，`https://your-rss-summaries.oss-cn-hangzhou.aliyuncs.com` |

本地验证：`pip install -r requirements.txt && python main.py --test-oss`，用手机打开打印的 URL。

### 知识库 + 每日要点 PDF（依赖同一套 OSS）

每次推送跑完会把 `articles` 归档到桶内：

- 检索页：`https://<OSS_PUBLIC_BASE_URL>/kb/search.html`
- 按日数据：`kb/days/YYYY-MM-DD.json`
- 每日要点：北京 **17:30** 定时档自动生成 `briefs/YYYY-MM-DD.pdf`，企微直接推送 PDF 文件（无文字简述）

手动：

```bash
python main.py --sync-kb
python main.py --daily-brief-only [--date 2026-03-20] [--no-notify]
```

可选 Secret：`OSS_KB_PREFIX`（默认 `kb/`）、`OSS_BRIEF_PREFIX`（默认 `briefs/`）。

---

## 第三步：确认 workflow 已存在

项目包含两个 workflow（**Secrets 共用**），推送后自动生效：

| 文件 | 名称 | 作用 |
|------|------|------|
| `rss-push.yml` | **RSS Push** | 轮巡（北京 **6、8、12、14、18** 整点，跳过 10:00/16:00）→ 实时两类 |
| `rss-push-timed.yml` | **RSS Push Timed** | 北京 **9:30 / 15:30** → 四类汇总；**9:30 档**会先跑 `generate_yijinglab_feed.py`：从 [行业资讯列表](https://www.yijinglab.com/industry/) 按**北京当天日期**选中「网络安全日报」，进详情把每条资讯拆成独立 RSS 条目（来源写 `www.yijinglab.com`，时间为详情「发表于」），再走原有分类逻辑（**非官方**，请自行评估合规） |

> 为何拆成两个？职责分离；**定时触发不依赖 GitHub `schedule`**，由 Zeabur `zeabur-cron-trigger` 按北京时间 `workflow_dispatch` 触发（见第四步）。

- **手动触发**：**Actions** → 选 **RSS Push** 或 **RSS Push Timed** → **Run workflow**

---

## 第四步：用阿里云 FC 做**唯一**调度（推荐；勿再用 Zeabur）

Zeabur [已宣布停运](https://zeabur.com/zh-CN/blogs/migrate-from-zeabur)。请用 **函数计算定时触发器**，见 [`docs/迁移到-阿里云.md`](../docs/迁移到-阿里云.md) 与 [`aliyun-fc-trigger/README.md`](../aliyun-fc-trigger/README.md)。

GitHub 的 `schedule` 易漏跑且非北京时区，**推荐 workflow 只保留 `workflow_dispatch`**。

1. FC 创建 Python 函数，入口 `index.handler`，代码用 `aliyun-fc-trigger/index.py`  
2. 环境变量：`GITHUB_TOKEN`、`GITHUB_REPO`  
3. 配置北京时区定时触发器（轮巡 6/18；定时 9:30/12:00/15:30/17:30）  
4. 测试事件 `{"mode":"timed"}`，确认 Actions 被触发后，停掉旧 Zeabur/Railway 触发器  

**为啥 Actions 里显示「Manually run by 我」？**  
用 PAT 调 `workflow_dispatch` 时界面会像手动运行，属正常。

（备选 Railway：见 [`docs/迁移到-Railway.md`](../docs/迁移到-Railway.md)。）

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
