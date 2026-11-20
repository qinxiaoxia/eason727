# 英文资讯 · 中文摘要

摘要生成 HTML 后上传 **阿里云 OSS**，企微消息里只留「中文摘要」外链（不把长文塞进群）。

对象路径示例：`rss-summaries/YYYY-MM-DD/<sha1前12位>.html`

本地 `translated/` 仅作备份；领导打开的是 OSS 地址。

## 配置（GitHub Secrets）

| Secret | 说明 |
|--------|------|
| `OSS_ACCESS_KEY_ID` | RAM 用户 AccessKey |
| `OSS_ACCESS_KEY_SECRET` | AccessKey Secret |
| `OSS_BUCKET` | 桶名 |
| `OSS_ENDPOINT` | 如 `oss-cn-hangzhou.aliyuncs.com` |
| `OSS_PUBLIC_BASE_URL` | 可选。如 `https://桶名.oss-cn-hangzhou.aliyuncs.com` 或自定义域名 |
| `OSS_PREFIX` | 可选，默认 `rss-summaries/` |

桶或对象需 **公共读**。本地自测：`python main.py --test-oss`
