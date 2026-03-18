# 复制此文件为 config.py 并填写你的配置

import json
import os

# 企业微信机器人 Webhook 地址（也可用环境变量 WECHAT_WEBHOOK）
WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK") or "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"

# WeWe RSS 地址（用于识别公众号来源，规则分类仅对公众号生效）
WEWE_RSS_URL = os.getenv("WEWE_RSS_URL") or "https://eason727.zeabur.app/feeds/all.atom"

# RSS 源配置：每项为 (feed_url, source_type)
# source_type: "wewe_rss" = 微信公众号（WeWe RSS），"rss" = 普通 RSS
# 环境变量 FEEDS_JSON 可覆盖，格式：[["url1","wewe_rss"],["url2","rss"]]
_feeds_json = os.getenv("FEEDS_JSON")
FEEDS = (
    [(u, t) for u, t in json.loads(_feeds_json)] if _feeds_json
    else [
        ("https://eason727.zeabur.app/feeds/all.atom", "wewe_rss"),
        ("https://cybersecuritynews.com/feed/", "rss"),
        ("https://www.helpnetsecurity.com/feed/", "rss"),
        ("http://hackernews.cc/feed", "rss"),
        ("https://api.anquanke.com/data/v1/rss", "rss"),
        ("https://www.freebuf.com/feed", "rss"),
    ]
)

# 定时推送时间（小时, 分钟），每天两次
SCHEDULED_PUSH_TIMES = [(9, 30), (15, 30)]

# 推送时间窗口（分钟），即 9:28-9:32 或 15:28-15:32 内运行才视为定时推送（收紧避免误触发）
SCHEDULED_WINDOW_MINUTES = 2

# 大模型分类（Phase 2）：规则未命中时调用 LLM 细分类
# LLM_API_KEY 留空则全部归为「其他资讯」
# 支持 OpenAI 兼容 API：DeepSeek、通义千问、智谱、OpenAI 等
LLM_API_KEY = os.getenv("LLM_API_KEY") or ""
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or "https://api.deepseek.com/v1"
LLM_MODEL = os.getenv("LLM_MODEL") or "deepseek-chat"

# 纯英文标题自动翻译为中文（需配置 LLM）
TRANSLATE_ENABLED = True
