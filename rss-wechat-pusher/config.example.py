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
# 蚁景网安「网络安全日报」：由 generate_yijinglab_feed.py 在定时 workflow 内生成 generated_feeds/yijinglab.xml
# （列表页按北京「今日」选日报，详情拆条；main.py 若发现该文件会自动追加为订阅源）。
_feeds_json = os.getenv("FEEDS_JSON")
FEEDS = (
    [(u, t) for u, t in json.loads(_feeds_json)] if _feeds_json
    else [
        ("https://eason727.zeabur.app/feeds/all.atom", "wewe_rss"),
        ("https://cybersecuritynews.com/feed/", "rss"),
        ("https://www.helpnetsecurity.com/feed/", "rss"),
        ("http://hackernews.cc/feed", "rss"),
        ("https://api.anquanke.com/data/v1/rss", "rss"),
        ("https://www.4hou.com/feed", "rss"),
        ("http://securityaffairs.co/wordpress/feed", "rss"),
    ]
)

# 定时推送（北京时间，仅「其余四类」）：每天 9:30、15:30 各一次（须与 workflow 中定时 cron 一致）
SCHEDULED_PUSH_TIMES = [(9, 30), (15, 30)]

# 定时档时间窗口（± 分钟）
SCHEDULED_WINDOW_MINUTES = 2

# 轮巡（仅「实时两类」）：北京 6、8、12、14、18 整点（跳过 10:00/16:00 与 9:30/15:30 定时错峰；20:00–次日 6:00 静默不推），须与 workflow 轮巡 cron 一致
POLL_HOURS_BEIJING = (6, 8, 12, 14, 18)
# 整点后若干分钟内视为本轮轮巡（容错 GitHub Actions 延迟）
POLL_WINDOW_MINUTES = 5

# 大模型分类 / 翻译：规则未命中时调用 LLM；LLM_API_KEY 留空则全部归为「其他资讯」
# 支持 OpenAI 兼容 API：DashScope、DeepSeek、智谱等
LLM_API_KEY = os.getenv("LLM_API_KEY") or ""
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or "https://api.deepseek.com/v1"
# 单模型（当下方 LLM_MODELS 为空且未设置 LLM_MODELS_JSON 时使用）
LLM_MODEL = os.getenv("LLM_MODEL") or "deepseek-chat"

# 多模型回退：同一 KEY + BASE_URL 下按顺序尝试，前一个失败/无内容则换下一个
# GitHub Actions：Secret「LLM_MODELS_JSON」填一行 JSON 数组，例如（勿换行或压缩为一行）：
# ["qwen-plus-2025-07-28","qwen-plus-0112","qwen-plus-2025-12-01","qwen-plus-character","qwen-plus-1220","qwen-plus-latest","qwen-plus-2025-09-11","qwen-plus-2025-01-25","qwen-plus-2025-04-28","qwen-plus-2025-07-14"]
_llm_models_json = os.getenv("LLM_MODELS_JSON")
try:
    LLM_MODELS = json.loads(_llm_models_json) if _llm_models_json else []
except json.JSONDecodeError:
    LLM_MODELS = []
if not LLM_MODELS:
    # 本地默认：与 DashScope compatible-mode 搭配；可按控制台可用模型增删顺序
    LLM_MODELS = [
        "qwen-plus-2025-07-28",
        "qwen-plus-0112",
        "qwen-plus-2025-12-01",
        "qwen-plus-character",
        "qwen-plus-1220",
        "qwen-plus-latest",
        "qwen-plus-2025-09-11",
        "qwen-plus-2025-01-25",
        "qwen-plus-2025-04-28",
        "qwen-plus-2025-07-14",
    ]

# 纯英文标题自动翻译为中文（需配置 LLM）
# 勿使用「数学专用」等不适配 NLP 的模型名做翻译，易拒答或重复输出
TRANSLATE_ENABLED = True
