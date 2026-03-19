"""
文章分类器
- 监管机构预警：规则判断（所有源统一规则）
  - 国家网络安全通报中心 + 标题以「重点防范」开头
  - 国家互联网应急中心CNCERT + 标题以「关于」开头且包含「风险提示」
  → 立即推送
- 其余：大模型细分类 → 漏洞信息、重大安全事件、网安新闻资讯、网安赛事资讯、其他资讯
"""
from typing import Optional

# 实时推送类别（每 5 分钟检测到立即推送）
REALTIME_CATEGORIES = {"监管机构预警", "重大安全事件"}

# 定时推送类别（9:30、15:30 汇总推送，含全部 6 类，与实时去重）
ALL_CATEGORIES = ["监管机构预警", "重大安全事件", "漏洞信息", "网安新闻资讯", "网安赛事资讯", "其他资讯"]
SCHEDULED_CATEGORIES = set(ALL_CATEGORIES)

# 大模型可选分类
LLM_CATEGORIES = ["漏洞信息", "重大安全事件", "网安新闻资讯", "网安赛事资讯", "其他资讯"]

# 监管机构预警规则：(作者/公众号名, 标题判断函数)
ALERT_RULES = [
    ("国家网络安全通报中心", lambda t: (t or "").strip().startswith("重点防范")),
    ("国家互联网应急中心CNCERT", lambda t: (t or "").strip().startswith("关于") and "风险提示" in (t or "")),
]


def classify_by_rules(author: str, title: str, source_type: str) -> Optional[str]:
    """规则分类，所有源统一规则。"""
    author = (author or "").strip()
    title = (title or "").strip()
    for rule_author, title_check in ALERT_RULES:
        if rule_author in author and title_check(title):
            return "监管机构预警"
    return None


def _call_llm_classify(text: str) -> Optional[str]:
    """调用 LLM 进行分类，支持多模型自动切换（额度用尽时换下一个）。"""
    from llm_utils import call_llm_with_fallback

    prompt = f"""将以下网络安全相关文章分类，只返回一个分类名，不要其他内容。

分类选项：漏洞信息、重大安全事件、网安新闻资讯、网安赛事资讯、其他资讯

- 漏洞信息：CVE、漏洞披露、补丁发布、安全更新
- 重大安全事件：大规模攻击、数据泄露、勒索软件、APT、重大安全事故
- 网安新闻资讯：行业动态、政策法规、企业动态、技术解读
- 网安赛事资讯：CTF、攻防演练、安全竞赛
- 其他资讯：无法归入以上类别

文章内容：
{text}

分类："""
    content = call_llm_with_fallback([{"role": "user", "content": prompt}], max_tokens=20)
    if not content:
        return None
    for cat in LLM_CATEGORIES:
        if cat in content:
            return cat
    return "其他资讯"


def classify(author: str, title: str, summary: str, source_type: str) -> str:
    """
    分类入口。
    - 先走规则，命中则返回「监管机构预警」
    - 否则调用大模型（若已配置，支持多模型自动切换），否则返回「其他资讯」
    """
    cat = classify_by_rules(author, title, source_type)
    if cat:
        return cat

    from llm_utils import get_llm_providers
    if not get_llm_providers():
        return "其他资讯"

    summary_short = (summary or "")[:800].strip()
    text = f"标题：{title or ''}\n作者：{author or ''}\n摘要：{summary_short}"
    result = _call_llm_classify(text)
    return result if result else "其他资讯"
