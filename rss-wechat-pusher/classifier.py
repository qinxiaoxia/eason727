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


def _blob_looks_like_industry_news_not_incident(blob: str, low: str) -> bool:
    """
    明显是行业新闻/分析/科普/厂商建议/综述，不宜用关键词判「重大安全事件」。
    （边界案例交给 LLM。）
    """
    if re.search(
        r"(职场观察|观察[：:]|行业观察|趋势分析|市场分析|深度解读|专访|综述|"
        r"安全简报|简报第|国际版\s*\(|译\)|newsletter|briefing|international edition|"
        r"安全动态\s*[｜|]|辟谣|匪夷所思|杰克·伦敦|"
        r"邮件安全网关|企业邮箱防|核心技术|如何防范|科普|教程|指南[：:：]|"
        r"窃密技术预警|新技术预警|防范钓鱼|防钓鱼攻击|"
        r"敦促.{0,6}更新|建议.{0,6}更新|建议用户|尽快更新|"
        r"urges?\s+\w+\s+to\s+update|urge\s+users?\s+to\s+update|"
        r"apple\s+urges|vendor\s+advisory)",
        blob,
        re.I,
    ):
        return True
    # 「新型攻击工具曝光」类威胁情报稿，无明确受害方与规模 → 当新闻
    if re.search(r"(新型|全新).{0,12}(攻击工具|exploit).{0,8}(曝光|现身|emerges?)", blob, re.I):
        if not re.search(r"(入侵|遭攻击|数据泄露|百万|million|breached|ransomware\s+group)", blob, re.I):
            return True
    return False


def _strong_major_incident_evidence(blob: str, low: str) -> bool:
    """
    重大安全事件（关键词层）：须体现「已发生」且通常有规模/关键设施/明确受害方，
    避免仅凭「泄露/勒索/攻击」等高频词误判资讯稿。
    """
    # 中文：规模 + 泄露/影响
    if re.search(
        r"(数百万|千万|百[余]?万|近\s*[\d\.]+\s*万|[\d\.]+\s*万\s*人).{0,48}(数据泄露|信息泄露|影响|用户|记录)",
        blob,
    ):
        return True
    if re.search(
        r"(数据泄露|信息泄露).{0,36}(数百万|千万|近\s*[\d\.]+\s*万|[\d\.]+\s*万|万人)",
        blob,
    ):
        return True
    # 勒索软件组织 + 入侵实锤
    if re.search(r"(勒索软件|勒索病毒).{0,16}(组织)?.{0,12}(入侵|攻陷|瘫痪)", blob):
        return True
    if re.search(r"(市|州|县|政府|地铁|医院|大学).{0,12}遭.{0,8}(入侵|勒索|攻击)", blob):
        return True
    if re.search(r"(已入侵|已遭攻击|证实.{0,6}泄露|确认.{0,6}泄露|证实的.{0,8}攻击)", blob):
        return True
    # 英文：大规模泄露 / 市政遭勒索等
    if re.search(r"data\s+breach.{0,96}(million|records|people|impacts?|individuals)", low):
        return True
    if re.search(r"(ransomware|ransomware\s+group).{0,48}(breach|breached|hit\s+\w+|invad|attack\s+on)", low):
        return True
    if re.search(r"\b(breached|hacked)\b.{0,40}(city|government|metro|million|ransomware)", low):
        return True
    if re.search(r"city\s+of\s+\w+.{0,60}(breach|ransomware|ransomware\s+group)", low):
        return True
    if re.search(r"\b(hit\s+by|struck\s+by)\b.{0,24}ransomware", low):
        return True
    if re.search(r"ransomware\s+group.{0,40}\b(breached|hit)\b", low):
        return True
    # 关键基础设施出大事（保留少量强词，避免单字「勒索」误伤）
    if re.search(
        r"(电网|地铁|政务系统|政府网站).{0,20}(遭攻击|被黑|瘫痪|停摆|大规模)", blob
    ) or re.search(r"(大规模攻击|业务全面中断|全国性.{0,6}停摆)", blob):
        return True
    return False


def _major_incident_blob_heuristic(blob: str, low: str) -> bool:
    """重大安全事件：关键词层仅在有强证据且非「纯新闻稿」时命中。"""
    if _blob_looks_like_industry_news_not_incident(blob, low):
        return False
    return _strong_major_incident_evidence(blob, low)


# 写入 Prompt：六类定义 + 流程 + 输出格式（与业务文档对齐）
_CLASSIFICATION_CRITERIA = """
你必须在下列五类中**只选一个**（监管机构预警由规则判定，你**不要**输出该类）：
漏洞信息、重大安全事件、网安新闻资讯、网安赛事资讯、其他资讯

【六类定义摘要】
1. 【监管机构预警 | Security Advisory】（你不用输出）：国家网络安全通报中心+标题「重点防范」开头；或 CNCERT+「关于」开头且含「风险提示」。
2. 【漏洞信息 | Vulnerability】：具体软件/系统漏洞详情，含 CVE、CVSS、受影响版本、修复补丁等**技术参数**；**仅**以漏洞技术细节为主、**非**已发生安全事件报道。
   关键词：漏洞, CVE, vulnerability, RCE, buffer overflow, privilege escalation, 0day, POC, CVSS, exploit
3. 【重大安全事件 | Security Incident】：**已真实发生**且**影响大**的安全事件：大规模数据泄露（常带用户/记录规模）、关键设施/政府/大型企业遭入侵或勒索实锤、已证实的严重中断等。
   **不要**把下列归入本类：行业趋势/观察/简报/综述、威胁情报「工具曝光」、厂商「敦促/建议更新」、科普与防护指南、政策辟谣、无明确受害规模的一般新闻。
   英文参考：confirmed data breach affecting millions; ransomware group breached city/government; major outage with widespread impact（非单纯 CVE 技术稿）。
4. 【网安新闻资讯 | Industry News】：行业动态、趋势、政策解读、市场分析、威胁综述、工具/漏洞曝光新闻稿等（**未强调单一已发生的大规模实害事件**）。
   关键词：发布, 趋势, 动态, 解读, 报告, release, trend, announcement, market analysis, industry report, whitepaper
5. 【网安赛事资讯 | CTF/Competition】：CTF、护网、HVV、攻防演练赛、竞赛、Hackathon、红蓝对抗（作赛事/演练活动报道）。
   关键词：CTF, 护网, HVV, 攻防演练, competition, contest, red-blue team, drill, hackathon
6. 【其他资讯 | Other】：无法归入以上者；科普、教程、工具、招聘等。
   关键词：科普, 教程, 工具, 招聘, tutorial, guide, course, tool, job, hiring

【分类优先级】重大安全事件 > 漏洞信息 > 网安赛事资讯 > 网安新闻资讯 > 其他资讯
（监管机构预警不由你输出。）

【分类流程】
1. 先判断是否**已发生的、大规模或高影响的实害安全事件**（如大规模用户数据泄露、市政/交通系统遭勒索入侵已证实等）→ 重大安全事件。
2. 若仅为 CVE/补丁/技术参数、或厂商更新建议、或行业新闻/分析 → **不要**标重大安全事件。
3. 再判断是否**漏洞技术通告**（CVE/CVSS/补丁/受影响版本为主）→ 漏洞信息。
4. 再判赛事/演练、行业新闻、其他。

【重要】⚠️ 「重大安全事件」门槛高：须**实害已发生**且通常**规模大或影响严重**；标题含「泄露/勒索/攻击」但实为资讯/分析/预警的 → 归**网安新闻资讯**。
⚠️ 提及 CVE 时：以**技术通告**为主 → 漏洞信息；以**已利用造成大规模事件**为主 → 重大安全事件。

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

    # 3) CVE/CNNVD：重大须「强证据」；行业新闻口吻 → 漏洞信息；其余交给后续关键词或 LLM
    if re.search(r"CVE-\d{4}-\d{4,8}", blob, re.I) or re.search(
        r"CNNVD-\d{4,}-\d+|CNVD-\d{4,}-\d+", blob, re.I
    ):
        if _blob_excludes_confirmed_major_incident(blob):
            return "漏洞信息"
        if _blob_looks_like_industry_news_not_incident(blob, low):
            return "漏洞信息"
        if _strong_major_incident_evidence(blob, low):
            return "重大安全事件"
        # 不默认标「重大」：CVE 稿多为技术通告，由 LLM 或下方漏洞词判定
        return None

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
            "「重大安全事件」仅用于已发生且大规模/高影响的实害事件，不要把行业新闻、观察、厂商敦促更新、工具曝光综述归入此类。"
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
