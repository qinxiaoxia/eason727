# 网安情报应用（独立 API + Web）

与 **企微推送线完全解耦**：本服务不抓 RSS、不写企微、不读写推送用的 `rss_push.db`。  
只从阿里云 OSS 已归档的 `kb/`、`briefs/` **只读同步**到本地库，对外提供固定 REST，并提供手机可直接打开的 Web（不再依赖 OSS HTML 附件下载）。

```
推送线: GitHub Actions → SQLite/OSS/企微
应用线: OSS → intel-app 同步 → /api/v1 + Web
```

## 部署（Railway 推荐；Zeabur 已停运勿再用）

完整步骤见仓库 [`docs/迁移到-Railway.md`](../docs/迁移到-Railway.md)。

1. [Railway](https://railway.app) → Deploy from GitHub → 本仓库  
2. **Root Directory** = `intel-app`  
3. 配置环境变量（见下）；建议 Volume 挂载 `/data`，并设 `INTEL_DATA_DIR=/data`  
4. Generate Domain 后打开 `https://xxx.up.railway.app/`，用口令登录  

也可用本目录 `Dockerfile` 部署到 Render / Fly.io。

启动命令（`Procfile` / Docker）：

```bash
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `OSS_PUBLIC_BASE_URL` | 推荐 | 如 `https://eason727.oss-cn-beijing.aliyuncs.com`（公共读即可同步 catalog） |
| `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET` / `OSS_BUCKET` / `OSS_ENDPOINT` | 建议 | 用于列举 `briefs/*.json`；仅公共 URL 时也能同步 catalog |
| `OSS_KB_PREFIX` | 否 | 默认 `kb/` |
| `OSS_BRIEF_PREFIX` | 否 | 默认 `briefs/` |
| `INTEL_WEB_PASSWORD` | **是** | Web 登录口令 |
| `INTEL_API_TOKEN` | **是** | 其它应用调用 API 的 Bearer Token |
| `INTEL_SESSION_SECRET` | 否 | Cookie 签名密钥，默认回落 token/口令 |
| `INTEL_SYNC_MINUTES` | 否 | 定时同步间隔，默认 `15` |
| `INTEL_DATA_DIR` | 否 | SQLite 目录，默认 `./data` |
| `PORT` | 否 | 默认 `8080` |

## 固定 API（v1）

鉴权：`Authorization: Bearer <INTEL_API_TOKEN>`（`/api/v1/health` 除外）。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 探活与同步状态 |
| GET | `/api/v1/articles` | 查询：`q` `category` `cve` `tag` `page` `page_size` |
| GET | `/api/v1/articles/{id}` | 详情 |
| GET | `/api/v1/briefs` | 每日要点列表 |
| GET | `/api/v1/briefs/{day}` | 某日要点 |
| POST | `/api/v1/admin/sync` | 立即从 OSS 同步 |

统一响应：`{ "ok": true, "data": ..., "meta": { ... } }`。  
交互文档：部署后打开 `/docs`（Swagger）。

示例：

```bash
curl -s -H "Authorization: Bearer $INTEL_API_TOKEN" \
  "https://<host>/api/v1/articles?q=CVE&page=1"
```

## Web

- `/login` 口令登录  
- `/` 情报列表（关键词 / 分类 / CVE）  
- `/a/{id}` 详情（摘要、CVE、IOC、原文）  
- `/briefs`、`/briefs/{day}` 每日要点  

企微里请发 **本应用域名链接**，不要发 OSS `kb/search.html`（易被当成附件下载）。

## 本地运行

```bash
cd intel-app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OSS_PUBLIC_BASE_URL=https://eason727.oss-cn-beijing.aliyuncs.com
export INTEL_WEB_PASSWORD=test
export INTEL_API_TOKEN=dev-token
python main.py
```

浏览器打开 `http://127.0.0.1:8080`。

## 与推送的关系

- **不要**改推送 workflow 来依赖本服务；推送失败不影响情报查阅，本服务挂了也不影响推送。  
- 推送线继续写 OSS；本服务定时拉取。需要立刻刷新时调用 `POST /api/v1/admin/sync`。
