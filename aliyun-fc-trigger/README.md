# 阿里云函数计算：RSS 推送定时触发器

用 **FC 定时触发器**（按次计费、北京时区）替代 Zeabur / Railway 上常驻的 `zeabur-cron-trigger`。

到点调用 GitHub `workflow_dispatch`，**不常驻进程**。

## 控制台创建（推荐）

1. 打开 [函数计算 FC](https://fcnext.console.aliyun.com/)（选与 OSS 相同或就近地域，如华北2 北京）  
2. **创建函数** → 使用内置运行时 → **Python 3.10/3.12** → 创建方式「单文件」或上传本目录  
3. 入口：`index.handler`  
4. 把 [`index.py`](./index.py) 贴进在线编辑或打包上传  
5. **环境变量**：

| 变量 | 必填 | 说明 |
|------|------|------|
| `GITHUB_TOKEN` | 是 | 能触发 Actions 的 PAT |
| `GITHUB_REPO` | 否 | 默认 `qinxiaoxia/eason727` |
| `WORKFLOW_POLL` | 否 | 默认 `rss-push.yml` |
| `WORKFLOW_TIMED` | 否 | 默认 `rss-push-timed.yml` |
| `GITHUB_REF` | 否 | 默认 `main` |

6. **配置触发器**（同一函数可挂多个「定时触发器」，时区选 **Asia/Shanghai**）：

| 名称建议 | Cron（秒 分 时 日 月 星期） | 触发消息（event） |
|----------|-----------------------------|-------------------|
| poll-6 | `0 0 6 * * *` | `{"mode":"poll"}` |
| poll-18 | `0 0 18 * * *` | `{"mode":"poll"}` |
| timed-930 | `0 30 9 * * *` | `{"mode":"timed"}` |
| timed-1200 | `0 0 12 * * *` | `{"mode":"timed"}` |
| timed-1530 | `0 30 15 * * *` | `{"mode":"timed"}` |
| timed-1730 | `0 30 17 * * *` | `{"mode":"timed"}` |

> 若控制台 Cron 不含「秒」字段，去掉最前面的 `0 `，用 `0 6 * * *` 这种 5 段式，并确认文档与控制台一致。

7. **测试**：在函数页「测试函数」，事件体填 `{"mode":"timed"}`，应返回 `ok: true`，随后 GitHub Actions 出现运行。  
8. （可选）加 **HTTP 触发器**，浏览器访问 `?mode=poll` 可手动补跑。

## 与旧触发器

- Zeabur / Railway 上的 `zeabur-cron-trigger` 在 FC 验证稳定后**关掉**，避免双触发。  
- GitHub workflow 继续只保留 `workflow_dispatch` 即可。

## 费用

定时触发每天 6 次量级，按调用计费，通常远低于常驻 Web 容器。
