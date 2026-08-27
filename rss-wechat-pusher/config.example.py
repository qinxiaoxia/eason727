# 复制此文件为 config.py 并填写你的配置

import json
import os

# 企业微信机器人 Webhook 地址（也可用环境变量 WECHAT_WEBHOOK）
WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK") or "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"

# 采集群机器人（可选）：与主群推送内容、格式完全一致；未配置则只发主群
# GitHub Secrets 任选其一：
#   WECHAT_WEBHOOK_COLLECTOR — 完整 webhook URL
#   WECHAT_COLLECTOR_BOT_ID  — 仅 key，自动拼成 .../webhook/send?key=
# WECHAT_COLLECTOR_BOT_SECRET 标准群 webhook 发送不用；留作对接/备注，勿提交仓库
WECHAT_WEBHOOK_COLLECTOR = (os.getenv("WECHAT_WEBHOOK_COLLECTOR") or "").strip()
_collector_bot_id = (os.getenv("WECHAT_COLLECTOR_BOT_ID") or "").strip()
if not WECHAT_WEBHOOK_COLLECTOR and _collector_bot_id:
    WECHAT_WEBHOOK_COLLECTOR = (
        f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={_collector_bot_id}"
    )
WECHAT_COLLECTOR_BOT_SECRET = (os.getenv("WECHAT_COLLECTOR_BOT_SECRET") or "").strip()

# 监管机构预警推送时 @ 的成员 userid（群机器人 text 的 mentioned_list）
# GitHub Secret「WECHAT_REGULATORY_MENTION_USERIDS」：["wangxuyang","qinxiaoxia"] 或逗号分隔
def _parse_str_list_env(name: str, default=None):
    raw = (os.getenv(name) or "").strip()
    if raw:
        try:
            v = json.loads(raw)
            if isinstance(v, list):
                return [str(x).strip() for x in v if str(x).strip()]
        except json.JSONDecodeError:
            pass
        return [x.strip() for x in raw.split(",") if x.strip()]
    return list(default or [])


WECHAT_REGULATORY_MENTION_USERIDS = _parse_str_list_env(
    "WECHAT_REGULATORY_MENTION_USERIDS",
    ["wangxuyang", "qinxiaoxia"],
)

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
        ("https://www.helpnetsecurity.com/feed/", "rss"),
        ("http://hackernews.cc/feed", "rss"),
        ("https://api.anquanke.com/data/v1/rss", "rss"),
        ("https://www.4hou.com/feed", "rss"),
        ("http://securityaffairs.co/wordpress/feed", "rss"),
    ]
)

# 定时推送（北京时间，定时档六类）：9:30 / 12:00 / 15:30 / 17:30（须与 zeabur-cron-trigger 一致）
# 9:30 用「昨 15:30～今 9:30」窗口；其余三档推「今天」未推稿
SCHEDULED_PUSH_TIMES = [(9, 30), (12, 0), (15, 30), (17, 30)]

# 定时档时间窗口（± 分钟）
SCHEDULED_WINDOW_MINUTES = 2

# 轮巡（仅「实时两类」）：北京 6、18 整点（12:00 改由定时档同跑实时+六类，避免双跑）
POLL_HOURS_BEIJING = (6, 18)
# 整点后若干分钟内视为本轮轮巡（容错 GitHub Actions 延迟）
POLL_WINDOW_MINUTES = 5

# 大模型分类 / 翻译（快模型）；IOC 提取见 LLM_IOC_MODELS
LLM_API_KEY = os.getenv("LLM_API_KEY") or ""
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_MODEL = os.getenv("LLM_MODEL") or "qwen-turbo"
# GitHub Secret「LLM_MODELS_JSON」示例：["qwen-turbo"]
_llm_models_json = os.getenv("LLM_MODELS_JSON")
try:
    LLM_MODELS = json.loads(_llm_models_json) if _llm_models_json else []
except json.JSONDecodeError:
    LLM_MODELS = []
if not LLM_MODELS:
    LLM_MODELS = ["qwen-turbo"]

# 监管机构 IOC 提取（慢/强模型）；GitHub Secret「LLM_IOC_MODELS_JSON」示例：["qwen3.7-plus"]
_llm_ioc_models_json = os.getenv("LLM_IOC_MODELS_JSON")
try:
    LLM_IOC_MODELS = json.loads(_llm_ioc_models_json) if _llm_ioc_models_json else []
except json.JSONDecodeError:
    LLM_IOC_MODELS = []
if not LLM_IOC_MODELS:
    LLM_IOC_MODELS = ["qwen3.7-plus"]

# 纯英文标题自动翻译为中文（需配置 LLM）
# 勿使用「数学专用」等不适配 NLP 的模型名做翻译，易拒答或重复输出
TRANSLATE_ENABLED = True

# 公众号噪声：规则未命中时用 turbo 复核是否属网安/AI 情报（见 classifier.exclusion_reason）
# 环境变量 NOISE_LLM_REVIEW=0 关闭；=all 时对全部 RSS 源复核
NOISE_LLM_REVIEW = os.getenv("NOISE_LLM_REVIEW", "").strip().lower() not in ("0", "false", "no", "off")
