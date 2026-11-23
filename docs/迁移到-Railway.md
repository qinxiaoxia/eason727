# 从 Zeabur 迁到 Railway（备选）

> **更推荐阿里云**：见 [`迁移到-阿里云.md`](./迁移到-阿里云.md)（FC 定时触发 + 轻量服务器跑情报应用）。

Zeabur [停止运营](https://zeabur.com/zh-CN/blogs/migrate-from-zeabur)后，若仍想用国外 PaaS，可用 **Railway**（同类还有 Render / Fly.io）。

**不用迁、可继续用的：**

- GitHub Actions 推送（`rss-wechat-pusher`）
- 阿里云 OSS（摘要 / 知识库 / PDF）
- 公众号源：你已在用 **SupSub**（`supsub.net/...`），一般**不必**再迁旧的 `*.zeabur.app` WeWe

**必须迁的：**

| 旧 Zeabur 服务 | 新平台服务 | 目录 |
|----------------|------------|------|
| 定时触发器 | Railway 服务 A | `zeabur-cron-trigger/` |
| （新建）情报应用 | Railway 服务 B | `intel-app/` |

---

## 一、Railway：定时触发器（保推送不断）

1. 打开 [railway.app](https://railway.app) ，用 GitHub 登录  
2. **New Project** → **Deploy from GitHub repo** → 选 `eason727`（或你的仓库）  
3. 添加服务后，在 Settings → **Root Directory** 填：`zeabur-cron-trigger`  
4. 变量（与以前 Zeabur 相同）：

| 变量 | 说明 |
|------|------|
| `GITHUB_TOKEN` | 能 `workflow_dispatch` 的 PAT |
| `GITHUB_REPO` | 如 `qinxiaoxia/eason727` |
| `WORKFLOW_POLL` | 默认 `rss-push.yml` |
| `WORKFLOW_TIMED` | 默认 `rss-push-timed.yml` |

5. Deploy 成功后看日志：应出现北京时间下次执行时间  
6. **确认跑通**：到点后 GitHub Actions 有运行；或在触发器服务里看健康检查/日志  

Zeabur 上的旧触发器确认 Railway 正常后即可删除/停用。

---

## 二、Railway：情报应用 `intel-app`

1. 同一 Project 再 **Add Service** → 同一仓库  
2. Root Directory：`intel-app`  
3. 变量：

| 变量 | 说明 |
|------|------|
| `OSS_PUBLIC_BASE_URL` | `https://eason727.oss-cn-beijing.aliyuncs.com` |
| `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET` | 只读即可 |
| `OSS_BUCKET` | `eason727` |
| `OSS_ENDPOINT` | `oss-cn-beijing.aliyuncs.com` |
| `INTEL_WEB_PASSWORD` | Web 口令 |
| `INTEL_API_TOKEN` | API Bearer |
| `INTEL_DATA_DIR` | 建议 `/data`（配合 Volume） |

4. 建议挂一个 Volume 到 `/data`，避免重启丢本地 SQLite（丢了也可从 OSS 再同步）  
5. Settings → Networking → **Generate Domain**，得到 `https://xxx.up.railway.app`  
6. 浏览器打开域名 → 口令登录；API 文档：`/docs`

企微「知识库」入口改成这个域名（不要用 OSS HTML / 旧 Zeabur 域名）。

---

## 三、可选：Render / Fly

- **Render**：Web Service，Root Directory 同上，Build 用 Dockerfile 或 `pip install + uvicorn`  
- **Fly.io**：`fly launch` 在对应子目录，需装 flyctl  

逻辑、环境变量与 Railway 相同。

---

## 四、检查清单

- [ ] Railway 触发器日志里有下次北京时间任务  
- [ ] 手动或等到点后 Actions 被触发  
- [ ] `intel-app` 能登录，列表有数据（或点同步 / 等 15 分钟）  
- [ ] Secrets / 变量未贴到公开聊天  
- [ ] Zeabur 旧服务停用；文档里的 `*.zeabur.app` 链接已改掉  

详情见各目录 README：[`zeabur-cron-trigger/README.md`](../zeabur-cron-trigger/README.md)、[`intel-app/README.md`](../intel-app/README.md)。
