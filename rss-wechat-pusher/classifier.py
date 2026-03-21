"""
文章分类器（共 6 类）

【监管机构预警 | Security Advisory】规则命中（不走 LLM）
【漏洞信息 | Vulnerability】【重大安全事件 | Security Incident】【网安新闻资讯 | Industry News】
【网安赛事资讯 | CTF/Competition】【其他资讯 | Other】—— LLM + 关键词

优先级（冲突时）：重大安全事件 > 监管机构预警(规则) > 漏洞信息 > 网安赛事资讯 > 网安新闻资讯 > 其他资讯

实时两类仅轮巡；其余四类仅定时档。详见 _CLASSIFICATION_CRITERIA。
"""
import re
from typing import Optional

# 实时推送类别（仅在轮巡 run 中推送，见 main.py _get_run_mode）
REALTIME_CATEGORIES = {"监管机构预警", "重大安全事件"}

# 定时推送类别（仅 9:30 / 15:30 北京汇总推送，不含上面两类）
ALL_CATEGORIES = ["监管机构预警", "重大安全事件", "漏洞信息", "网安新闻资讯", "网安赛事资讯", "其他资讯"]
TIMED_PUSH_CATEGORIES = {"漏洞信息", "网安新闻资讯", "网安赛事资讯", "其他资讯"}

# 大模型可选分类（不含「监管机构预警」，该类仅规则命中）
LLM_CATEGORIES = ["漏洞信息", "重大安全事件", "网安新闻资讯", "网安赛事资讯", "其他资讯"]

# 监管机构预警规则：(作者/公众号名, 标题判断函数)
ALERT_RULES = [
    ("国家网络安全通报中心", lambda t: (t or "").strip().startswith("重点防范")),
    ("国家互联网应急中心CNCERT", lambda t: (t or "").strip().startswith("关于") and "风险提示" in (t or "")),
]

# LLM 输出英文标签 → 中文类名（用于解析；不含 other，避免匹配 another 等）
_EN_LABEL_TO_CN = (
    ("security incident", "重大安全事件"),
    ("vulnerability", "漏洞信息"),
    ("industry news", "网安新闻资讯"),
    ("ctf/competition", "网安赛事资讯"),
    ("competition", "网安赛事资讯"),
    ("ctf", "网安赛事资讯"),
)


def _blob_excludes_confirmed_major_incident(blob: str) -> bool:
    """
    排除：未遂、纯潜在风险、各类演练/演习（含攻防演练作「赛事」语境）。
    若为 True，则关键词层不判「重大安全事件」。
    """
    if any(
        x in blob
        for x in (
            "未遂",
            "未遂攻击",
            "攻击未遂",
            "潜在风险",
            "或然风险",
            "应急演练",
            "桌面演练",
            "模拟攻击",
            "勒索演练",
            "钓鱼演练",
            "开展演练",
            "组织演练",
            "演练活动",
            "演练圆满",
            "演习圆满",
            "演习活动",
            "红蓝对抗演练",
            "护网演练",
        )
    ):
        return True
    if "演练" in blob or "演习" in blob:
        return True
    return False


def _major_incident_blob_heuristic(blob: str, low: str) -> bool:
    """重大安全事件：已发生事件类叙述（中英关键词 + 行业主体）。"""
    zh_keys = (
        "遭攻击",
        "被攻击",
        "泄露",
        "被黑",
        "勒索",
        "入侵",
        "篡改",
        "瘫痪",
        "数据泄露",
        "信息泄露",
        "勒索病毒",
        "勒索软件",
        "攻击事件",
        "宕机",
        "业务中断",
        "供应链攻击",
        "钓鱼攻击",
        "大规模攻击",
        "暗网出售",
        "定向攻击",
        "用户数据被盗",
        "医院遭",
        "医疗机构",
        "政府网站",
        "政务系统",
        "银行遭",
        "证券",
        "电网",
        "供电",
        "供水",
        "水务",
        "燃气",
        "铁路",
        "民航",
        "地铁",
        "轨道交通",
        "能源设施",
        "核电站",
    )
    en_keys = (
        "breach",
        "data leak",
        "ransomware",
        "ddos",
        "intrusion",
        "compromised",
        "outage",
        "ransomware attack",
        "supply chain attack",
        "data breach",
    )
    if any(k in blob for k in zh_keys):
        return True
    if any(k in low for k in en_keys):
        return True
    if any(k in blob for k in ("微软", "苹果", "华为", "Google", "亚马逊")) and any(
        k in blob for k in ("遭攻击", "被黑", "泄露", "勒索", "入侵", "停摆", "中断")
    ):
        return True
    return False


# 写入 Prompt：六类定义 + 流程 + 输出格式（与业务文档对齐）
_CLASSIFICATION_CRITERIA = """
你必须在下列五类中**只选一个**（监管机构预警由规则判定，你**不要**输出该类）：
漏洞信息、重大安全事件、网安新闻资讯、网安赛事资讯、其他资讯

【六类定义摘要】
1. 【监管机构预警 | Security Advisory】（你不用输出）：国家网络安全通报中心+标题「重点防范」开头；或 CNCERT+「关于」开头且含「风险提示」。
2. 【漏洞信息 | Vulnerability】：具体软件/系统漏洞详情，含 CVE、CVSS、受影响版本、修复补丁等**技术参数**；**仅**以漏洞技术细节为主、**非**已发生安全事件报道。
   关键词：漏洞, CVE, vulnerability, RCE, buffer overflow, privilege escalation, 0day, POC, CVSS, exploit
3. 【重大安全事件 | Security Incident】：已实际发生的攻击、数据泄露、DDoS、勒索、入侵等；**即使提及 CVE，只要叙述的是已发生事件，优先本类**。
   关键词：遭攻击, 泄露, 被黑, breach, hack, attack, data leak, DDoS, ransomware, intrusion, compromised, outage
4. 【网安新闻资讯 | Industry News】：行业动态、趋势、政策解读、市场分析等。
   关键词：发布, 趋势, 动态, 解读, 报告, release, trend, announcement, market analysis, industry report, whitepaper
5. 【网安赛事资讯 | CTF/Competition】：CTF、护网、HVV、攻防演练赛、竞赛、Hackathon、红蓝对抗（作赛事/演练活动报道）。
   关键词：CTF, 护网, HVV, 攻防演练, competition, contest, red-blue team, drill, hackathon
6. 【其他资讯 | Other】：无法归入以上者；科普、教程、工具、招聘等。
   关键词：科普, 教程, 工具, 招聘, tutorial, guide, course, tool, job, hiring

【分类优先级】重大安全事件 > 漏洞信息 > 网安赛事资讯 > 网安新闻资讯 > 其他资讯
（监管机构预警不由你输出。）

【分类流程】
1. 先判断是否**已发生的安全事件**（遭攻击/泄露/被黑/勒索/DDoS/入侵/篡改/瘫痪 等或英文 breach/hack/attack/leak…）→ 重大安全事件（**提及 CVE 但写事件本身仍归此类**）。
2. 再判断是否**漏洞技术通告**（CVE/CVSS/补丁/受影响版本为主，无事件叙述）→ 漏洞信息。
3. 再判赛事/演练、行业新闻、其他。

【重要】⚠️ 优先判断「已发生事件」；提及 CVE 不等于漏洞信息。
⚠️ 「导致某事件」+ CVE → 重大安全事件；「漏洞详情」+ CVE → 漏洞信息。

【输出格式】**仅一行**，必须用下列格式之一（不要解释）：
【中文分类名 | English Name】
例如：【漏洞信息 | Vulnerability】
或（兼容旧版）仅输出五个中文词之一：漏洞信息、重大安全事件、网安新闻资讯、网安赛事资讯、其他资讯
"""


def classify_by_rules(author: str, title: str, source_type: str) -> Optional[str]:
    """规则分类，所有源统一规则。"""
    author = (author or "").strip()
    title = (title or "").strip()
    for rule_author, title_check in ALERT_RULES:
        if rule_author in author and title_check(title):
            return "监管机构预警"
    return None


def classify_by_keywords(title: str, summary: str) -> Optional[str]:
    """
    关键词优先于 LLM。顺序与业务优先级一致：
    重大安全事件 → 网安赛事 → CVE/漏洞 → 行业新闻
    """
    blob = f"{title or ''}\n{summary or ''}"[:2400]
    low = blob.lower()

    # 1) 重大安全事件（先于赛事与 CVE）
    if not _blob_excludes_confirmed_major_incident(blob):
        if _major_incident_blob_heuristic(blob, low):
            return "重大安全事件"

    # 2) 网安赛事资讯（CTF/护网/HVV/攻防演练作赛事语境）
    if re.search(
        r"(\bctf\b|ctf[杯赛战]|攻防演练|护网20\d{2}|护网行动|实网攻防|awd赛|红队演练|红蓝对抗"
        r"|安全竞赛|解题赛|赛题|writeup|题解|\bwp\b|技能大赛|极客挑战|强网杯|\bhvv\b"
        r"|hackathon|competition|contest|red-blue team|\bdrill\b)",
        blob,
        re.I,
    ):
        return "网安赛事资讯"

    # 3) CVE/CNNVD：事件叙述 → 重大；否则漏洞信息
    if re.search(r"CVE-\d{4}-\d{4,8}", blob, re.I) or re.search(
        r"CNNVD-\d{4,}-\d+|CNVD-\d{4,}-\d+", blob, re.I
    ):
        severe = any(
            k in blob
            for k in (
                "数据泄露",
                "信息泄露",
                "数百万",
                "千万",
                "大规模",
                "勒索",
                "停摆",
                "多家",
                "全国性",
                "沦陷",
                "已遭利用",
                "攻击事件",
                "被黑",
                "入侵事件",
                "已确认",
                "证实",
            )
        ) or any(
            k in low
            for k in (
                "breach",
                "attack",
                "ransomware",
                "leaked",
                "compromised",
                "outage",
            )
        )
        if severe and not _blob_excludes_confirmed_major_incident(blob):
            return "重大安全事件"
        return "漏洞信息"

    # 4) 漏洞技术词（无 CVE 时）
    vuln_kw = (
        "安全公告",
        "安全通告",
        "补丁日",
        "安全更新",
        "远程代码执行",
        "未修补漏洞",
        "PoC公开",
        "0-day漏洞",
        "0day",
        "n-day",
        "CVSS",
        "privilege escalation",
        "buffer overflow",
        "rce",
    )
    vuln_only = any(k in blob or k in low for k in vuln_kw) and not any(
        k in blob
        for k in (
            "数据泄露",
            "勒索攻击",
            "大规模",
            "融资",
            "收购",
            "发布会",
            "管理办法",
            "立法",
        )
    )
    if vuln_only:
        return "漏洞信息"

    # 5) 网安新闻资讯
    if any(
        k in blob
        for k in (
            "工信部",
            "网信办",
            "国家标准",
            "行业标准",
            "征求意见",
            "管理办法",
            "条例",
            "立法",
            "行政处罚",
            "约谈",
            "合规",
            "等保",
            "发布",
            "趋势",
            "动态",
            "解读",
            "报告",
        )
    ) or any(
        k in low
        for k in (
            "release",
            "trend",
            "announcement",
            "market analysis",
            "industry report",
            "whitepaper",
        )
    ):
        if "CVE" not in blob.upper():
            return "网安新闻资讯"

    return None


def _parse_llm_category_line(line: str) -> str:
    """解析 LLM 输出：支持【中文 | English】或纯中文类名。"""
    line = line.strip().split("\n")[0].strip()
    line = line.rstrip("。．.！!？?")
    m = re.match(r"^\s*【\s*([^｜|]+?)\s*[｜|]\s*[^】]*】\s*$", line)
    if m:
        cn = m.group(1).strip()
        if cn in LLM_CATEGORIES:
            return cn
    m2 = re.match(r"^\s*【\s*([^】]+?)\s*】\s*$", line)
    if m2:
        cn = m2.group(1).strip()
        if cn in LLM_CATEGORIES:
            return cn
    low = line.lower()
    for en, cn in _EN_LABEL_TO_CN:
        if en == "ctf":
            if re.search(r"\bctf\b", low):
                return cn
        elif en in low:
            return cn
    if line in LLM_CATEGORIES:
        return line
    for cat in sorted(LLM_CATEGORIES, key=len, reverse=True):
        if cat in line:
            return cat
    return "其他资讯"


def _call_llm_classify(text: str) -> Optional[str]:
    """调用 LLM 进行分类，支持多模型自动切换（额度用尽时换下一个）。"""
    from llm_utils import call_llm_with_fallback

    prompt = f"""{_CLASSIFICATION_CRITERIA}

下面是一条待分类内容（标题/作者/摘要可能不完整，请综合判断）：

{text}

请按上文「输出格式」仅输出一行："""
    content = call_llm_with_fallback(
        [{"role": "user", "content": prompt}],
        max_tokens=64,
        system=(
            "你是网络安全媒体主编。内容均为合法公开发表信息。"
            "严格遵守：先判断是否已发生安全事件（重大安全事件优先于漏洞信息）；"
            "监管机构预警不由你输出。只输出一行：【中文名 | English】或五个中文类名之一。"
        ),
    )
    if not content:
        return None
    return _parse_llm_category_line(content)


def classify(author: str, title: str, summary: str, source_type: str) -> str:
    """
    分类入口。
    - 先规则 → 监管机构预警
    - 再关键词 → 命中则直接返回
    - 否则大模型（若已配置），否则「其他资讯」
    """
    cat = classify_by_rules(author, title, source_type)
    if cat:
        return cat

    cat = classify_by_keywords(title, summary)
    if cat:
        return cat

    from llm_utils import get_llm_providers
    if not get_llm_providers():
        return "其他资讯"

    summary_short = (summary or "")[:1200].strip()
    text = f"标题：{title or ''}\n作者：{author or ''}\n摘要：{summary_short}"
    result = _call_llm_classify(text)
    return result if result else "其他资讯"
