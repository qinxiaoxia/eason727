"""
文章分类器（共 6 类）

【监管机构预警 | Security Advisory】规则命中（不走 LLM）
【漏洞信息 | Vulnerability】【重大安全事件 | Security Incident】【网安新闻资讯 | Industry News】
【网安赛事资讯 | CTF/Competition】【其他资讯 | Other】—— **默认全部由 LLM 分类**；仅当未配置 LLM 或调用失败时，用关键词兜底。

优先级（冲突时）：重大安全事件 > 监管机构预警(规则) > 漏洞信息 > 网安赛事资讯 > 网安新闻资讯 > 其他资讯

实时两类仅轮巡；其余四类仅定时档。详见 _CLASSIFICATION_CRITERIA。
classify() 返回 (类别, incident_priority)；incident_priority 仅「重大安全事件」为 high/medium/low，其余为 None。
"""
import re
from typing import Optional, Tuple

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
    排除：未遂、纯潜在风险、各类演练/演习、仅预警/理论分析、未证实传闻等。
    与「已发生且已确认 + 实质影响」标准对齐；若为 True，则关键词层不判「重大安全事件」。
    """
    if any(
        x in blob
        for x in (
            "未遂",
            "未遂攻击",
            "攻击未遂",
            "潜在风险",
            "或然风险",
            "理论分析",
            "理论漏洞",
            "漏洞理论",
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
            "仅预警",
            "发布预警",
            "安全预警",
            "风险预警",
        )
    ):
        return True
    if "演练" in blob or "演习" in blob:
        return True
    return False


def _blob_suggests_unconfirmed_or_rumor(blob: str) -> bool:
    """未证实、网传口径 → 关键词层不抬升到「重大安全事件」（交给 LLM 或归资讯）。"""
    low = blob.lower()
    if re.search(
        r"(未经证实|尚无法证实|有待核实|待证实|网传|传闻|传言|rumou?r|unconfirmed|alleged(ly)?\s+)",
        blob,
        re.I,
    ):
        return True
    if re.search(r"声称.{0,12}(入侵|泄露|攻击).{0,16}(未|尚|待)", blob):
        return True
    if "claimed responsibility" in low and "unconfirmed" in low:
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
    重大安全事件（关键词层）：须体现「已发生/已确认」类实害，且通常有规模、
    关键设施/政府/大型组织受害，或符合「数百万级」泄露等强信号；
    与《安全事件分级》中高/中优先级中**已确认的实害**情形对齐（关键词仅覆盖明显稿）。
    """
    # 规模：≥约百万量级（条/人/用户/记录）与泄露/影响
    if re.search(
        r"(100\s*万|百万|数百万|千万|百[余]?万|[\d\.]+\s*万\s*(条|人|用户|账户|记录|条记录))",
        blob,
    ) and re.search(r"(泄露|外泄|被盗|脱库|数据泄露|信息泄露|breach)", blob, re.I):
        return True
    if re.search(
        r"(数据泄露|信息泄露|数据外泄).{0,48}(100\s*万|百万|数百万|千万|万\s*条|万\s*人|records|million)",
        blob,
        re.I,
    ):
        return True
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
    if re.search(
        r"(已入侵|已遭攻击|证实.{0,8}泄露|确认.{0,8}泄露|官方确认|已证实|证实的.{0,8}攻击)",
        blob,
    ):
        return True
    # 国内龙头/关键主体遭实害（简体常见报道用语）
    if re.search(
        r"(华为|腾讯|阿里|字节|百度|京东|美团|工商银行|建设银行|国家电网|中国石油|中石化)"
        r".{0,24}(遭攻击|被入侵|数据泄露|确认泄露|瘫痪|赎金)",
        blob,
    ):
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
    # 关键基础设施 / 大中断
    if re.search(
        r"(电网|供水|轨道交通|地铁|政务系统|政府网站|关键信息基础设施|通信运营商).{0,24}"
        r"(遭攻击|被黑|瘫痪|停摆|大规模|中断)",
        blob,
    ) or re.search(
        r"(大规模攻击|业务全面中断|全国性.{0,6}停摆|服务中断.{0,12}(小时|万用户))",
        blob,
    ):
        return True
    return False


def _major_incident_blob_heuristic(blob: str, low: str) -> bool:
    """重大安全事件：关键词层仅在有强证据且非「纯新闻稿 / 未经证实传闻」时命中。"""
    if _blob_looks_like_industry_news_not_incident(blob, low):
        return False
    if _blob_suggests_unconfirmed_or_rumor(blob):
        return False
    return _strong_major_incident_evidence(blob, low)


def _major_incident_priority_high(blob: str, low: str) -> bool:
    """对齐分级标准中的「高优先级」：关键主体或大规模/高影响已确认实害。"""
    if re.search(
        r"(100\s*万|1[0-9]{2}\s*万|[2-9]\d{2}\s*万|一百万|两百万|三百万|数百万|千万|"
        r"百万\s*(余|多|级)?|million)",
        blob,
        re.I,
    ) and re.search(r"(泄露|外泄|被盗|脱库|数据泄露|信息泄露|breach|records|impacts?)", blob, re.I):
        return True
    if re.search(
        r"(电网|供水|轨道交通|地铁|关键信息基础设施|通信运营商|国家电网)"
        r".{0,24}(遭攻击|被黑|瘫痪|停摆|大规模|中断|入侵|勒索)",
        blob,
    ):
        return True
    if re.search(
        r"(华为|腾讯|阿里|字节|百度|京东|美团|工商银行|建设银行|国家电网|中国石油|中石化)"
        r".{0,24}(遭攻击|被入侵|数据泄露|确认泄露|瘫痪|赎金|勒索)",
        blob,
    ):
        return True
    if re.search(r"(市政府|省政府|国务院|政务系统).{0,20}(瘫痪|全面中断|大规模|停摆|核心系统)", blob):
        return True
    if re.search(r"data\s+breach.{0,96}(million|records|people|individuals)", low):
        return True
    if re.search(
        r"(ransomware|勒索).{0,40}(city|government|市政|省政府|市政府|州政府|department)",
        blob,
        re.I,
    ) or re.search(
        r"(市政府|市政|省政府|city\s+of).{0,50}(ransomware|勒索病毒)",
        blob,
        re.I,
    ):
        return True
    if re.search(r"(大规模攻击|业务全面中断|全国性.{0,6}停摆|服务中断.{0,12}(小时|[\d\.]+\s*万\s*用户))", blob):
        return True
    if re.search(
        r"(市|州|县|政府|地铁).{0,12}遭.{0,8}(入侵|勒索|攻击).{0,40}"
        r"(数百?万|千万|million|全面瘫痪|核心)",
        blob,
        re.I,
    ):
        return True
    if re.search(r"(勒索软件|勒索病毒).{0,16}(组织)?.{0,12}(入侵|攻陷|瘫痪)", blob) and re.search(
        r"(政府|市政|医院|大学|交通|能源|金融|银行)", blob
    ):
        return True
    return False


def _major_incident_priority_medium(blob: str, low: str) -> bool:
    """对齐「中优先级」：一定规模或次级关键主体，但未达到高优先级门槛。"""
    if re.search(r"(?:10|[12]\d|[3-9]\d)\s*万", blob) and re.search(
        r"(泄露|外泄|条|记录|用户|影响|账户|信息)",
        blob,
    ):
        return True
    if re.search(r"(十万余|数十万|近\s*99\s*万|[\d\.]+\s*万\s*余\s*条)", blob) and re.search(
        r"(泄露|外泄|用户|记录)",
        blob,
    ):
        return True
    if re.search(r"(大学|高校|学院).{0,16}(遭攻击|勒索|入侵|泄露|停摆)", blob):
        return True
    if re.search(r"(医院|卫生院|三甲医院).{0,14}(遭勒索|被勒索|勒索病毒|入侵|泄露|系统瘫痪)", blob):
        return True
    if re.search(
        r"(地级市|区县政府|县政府|区政府|县委|市局|县公安局)"
        r".{0,22}(入侵|勒索|攻击|泄露|系统|网站|被黑|攻陷)",
        blob,
    ):
        return True
    if re.search(r"(中小企业|民营企业).{0,20}(勒索|入侵|泄露|遭攻击)", blob):
        return True
    if re.search(r"\b(100,000|200,000|300,000|400,000|500,000|600,000|700,000|800,000|900,000)\b", low) and re.search(
        r"breach|leak|stolen|ransomware",
        low,
    ):
        return True
    return False


def major_incident_priority(title: str, summary: Optional[str] = None) -> str:
    """
    已归类为「重大安全事件」的条目，用于推送展示：🔴高 / 🟡中 / 🟢低。
    基于标题+摘要的启发式，与业务分级文档大致对齐；边界情况可能偏保守为「低」。
    """
    blob = f"{title or ''}\n{summary or ''}"[:2400]
    low = blob.lower()
    if _major_incident_priority_high(blob, low):
        return "high"
    if _major_incident_priority_medium(blob, low):
        return "medium"
    return "low"


# 写入 Prompt：六类定义 + 流程 + 输出格式（与业务文档对齐）
_CLASSIFICATION_CRITERIA = """
你必须在下列五类中**只选一个**（监管机构预警由规则判定，你**不要**输出该类；除此五类外**没有**关键词预审，以你本行输出为准）：
漏洞信息、重大安全事件、网安新闻资讯、网安赛事资讯、其他资讯

【六类定义摘要】
1. 【监管机构预警 | Security Advisory】（你不用输出）：国家网络安全通报中心+标题「重点防范」开头；或 CNCERT+「关于」开头且含「风险提示」。
2. 【漏洞信息 | Vulnerability】：具体软件/系统漏洞详情，含 CVE、CVSS、受影响版本、修复补丁等**技术参数**；**仅**以漏洞技术细节为主、**非**已发生安全事件报道。
   关键词：漏洞, CVE, vulnerability, RCE, buffer overflow, privilege escalation, 0day, POC, CVSS, exploit
3. 【重大安全事件 | Security Incident】（门槛高，对齐「分级判断」中的**已发生且已确认**的实害事件）：
   **必须同时满足**：（a）**已发生且已确认**的实质性攻击或泄露（非未遂、非安全演练/演习、非仅预警、非纯理论分析、非未经证实的传闻）；（b）有**可验证的实质影响**（数据泄露、系统入侵、服务中断、勒索得逞等）。
   **优先关注**对中国企事业单位、在华业务或国内关键基础设施有直接影响的实害事件。
   **典型归入本类**：大规模数据泄露（常带百万级用户/条记录规模或敏感数据）、关键设施/政府/大型组织核心系统被入侵或勒索**已证实**、已证实的长时间大范围服务中断等。
   **不要**归入：潜在风险、未遂、演练、仅发预警无实害、工具/漏洞新闻综述、厂商敦促更新、科普指南、行业趋势稿、「声称/网传/未经证实」为主的消息。
   英文参考：confirmed data breach at scale; verified ransomware hitting city/government/major org; widespread confirmed outage（非单纯 CVE 通告）。
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

【重要】⚠️ 「重大安全事件」= 高优先级实害事件的子集：须**已发生+已确认**，有**实质影响**；中低优先级或「仅建议关注」的有限影响事件，若不符合「已确认大规模/关键设施实害」，应归**网安新闻资讯**或**其他资讯**。
⚠️ 标题含「泄露/勒索/攻击」但实为资讯、预警、传闻、未遂、演练 → **网安新闻资讯**等，勿标重大安全事件。
⚠️ CVE：以技术通告为主 → **漏洞信息**；以**已利用且造成大规模确认事件**为主 → 重大安全事件。

【输出格式】**仅一行**，不要解释、不要加前后缀：
- 若 **不是** 重大安全事件：【中文分类名 | English Name】
  例如：【漏洞信息 | Vulnerability】
- 若 **是** 重大安全事件：**必须**带上第三段优先级（三选一：高优先级、中优先级、低优先级，对齐前述分级标准）：
  【重大安全事件 | Security Incident | 高优先级】
- 兼容旧版：仅输出五个中文词之一（不含优先级）时，系统会再向模型追问优先级。
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
    关键词兜底（仅无 LLM 或 LLM 分类失败时使用）。顺序与业务优先级一致：
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


_incident_priority_prompt = """以下资讯已归类为「重大安全事件」。请根据标题与摘要，按单位内部报送惯例在下列三级中**只选一**（高≈关键设施/龙头/国家安全或经济重大影响或百万级等实害；中≈地市政府/高校/医院/中小企业或十万级等有限影响；低≈影响面较小或与我国关联弱）：

只输出一个词组，不要解释：高优先级、中优先级、低优先级"""


def _normalize_incident_priority(fragment: str) -> Optional[str]:
    """将模型输出的片段规范为 high | medium | low；无法识别则 None。"""
    if not fragment:
        return None
    t = fragment.strip()
    t = re.sub(r"^(输出|答案|结果|回复)[:：]\s*", "", t).strip()
    t = t.strip("`\"'“”")
    low = t.lower()
    if re.search(r"(低优先级|^\s*低\s*$|\blow\s+priority\b|\blow\b|\bp3\b)", low):
        return "low"
    if re.search(r"(中优先级|^\s*中\s*$|\bmedium\s+priority\b|\bmedium\b|\bmid\b|\bp2\b)", low):
        return "medium"
    if re.search(r"(高优先级|^\s*高\s*$|\bhigh\s+priority\b|\bhigh\b|\bp1\b)", low):
        return "high"
    return None


def _extract_triplet_priority(first_line: str) -> Optional[str]:
    """从 【类 | EN | 优先级】 第三段取出优先级。"""
    m = re.match(
        r"^\s*【\s*[^】]+?\s*[｜|]\s*[^】]+?\s*[｜|]\s*([^】]+?)\s*】\s*$",
        first_line,
    )
    if m:
        return _normalize_incident_priority(m.group(1))
    return None


def _parse_llm_classify_response(content: str) -> Tuple[str, Optional[str]]:
    """解析分类 LLM 输出：(类名, 重大事件优先级或 None)。"""
    raw = (content or "").strip()
    if not raw:
        return "其他资讯", None
    first = raw.split("\n")[0].strip().rstrip("。．.！!？?")
    cat = _parse_llm_category_line(raw)
    pri = _extract_triplet_priority(first)
    return cat, pri


def _call_llm_incident_priority_only(text: str) -> Optional[str]:
    """重大安全事件专用：模型只输出优先级。"""
    from llm_utils import call_llm_with_fallback

    content = call_llm_with_fallback(
        [{"role": "user", "content": f"{_incident_priority_prompt}\n\n{text}"}],
        max_tokens=32,
        system="你是网络安全值班编辑，只做优先级三选一标注，禁止解释与发散。",
    )
    if not content:
        return None
    line = content.strip().split("\n")[0].strip()
    return _normalize_incident_priority(line)


def _parse_llm_category_line(line: str) -> str:
    """解析 LLM 输出：支持【中文 | English】或纯中文类名（第三段优先级不影响本函数）。"""
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


def _call_llm_classify(text: str) -> Optional[Tuple[str, Optional[str]]]:
    """调用 LLM 进行分类，支持多模型自动切换（额度用尽时换下一个）。"""
    from llm_utils import call_llm_with_fallback

    prompt = f"""{_CLASSIFICATION_CRITERIA}

下面是一条待分类内容（标题/作者/摘要可能不完整，请综合判断）：

{text}

请按上文「输出格式」仅输出一行："""
    content = call_llm_with_fallback(
        [{"role": "user", "content": prompt}],
        max_tokens=96,
        system=(
            "你是网络安全媒体主编。内容均为合法公开发表信息。"
            "「重大安全事件」仅用于已发生且已确认、有实质影响的实害事件（非未遂/演练/仅预警/理论分析/未经证实传闻）；"
            "须通常具备相当规模或涉及关键设施/政府/大型组织，或明确百万级泄露等；与中国受众关联弱的小事件可归网安新闻资讯。"
            "若归入重大安全事件，**必须**在一行内输出第三段优先级（高优先级/中优先级/低优先级），格式："
            "【重大安全事件 | Security Incident | 高优先级】。"
            "不要把行业新闻、观察、厂商敦促更新、工具曝光综述、网传未经证实消息归入重大安全事件。"
            "监管机构预警不由你输出。非重大类输出：【中文名 | English】。"
        ),
    )
    if not content:
        return None
    cat, pri = _parse_llm_classify_response(content)
    if cat == "重大安全事件" and not pri:
        pri = _call_llm_incident_priority_only(text)
    return cat, pri


def classify(author: str, title: str, summary: str, source_type: str) -> Tuple[str, Optional[str]]:
    """
    分类入口。返回 (类别, 事件优先级)。
    - 监管机构预警：仅规则命中。
    - 其余类：**优先 LLM**；未配置 LLM 或调用失败时，才用关键词 classify_by_keywords 兜底。
    - incident_priority 仅「重大安全事件」为 high / medium / low；其余为 None。
    """
    cat = classify_by_rules(author, title, source_type)
    if cat:
        return cat, None

    from llm_utils import get_llm_providers

    summary_short = (summary or "")[:1200].strip()
    text = f"标题：{title or ''}\n作者：{author or ''}\n摘要：{summary_short}"

    if get_llm_providers():
        result = _call_llm_classify(text)
        if result:
            cat, pri = result
            if cat == "重大安全事件" and not pri:
                pri = major_incident_priority(title, summary)
            return cat, pri

    cat = classify_by_keywords(title, summary)
    if cat:
        if cat == "重大安全事件":
            pri = _call_llm_incident_priority_only(text) if get_llm_providers() else None
            if not pri:
                pri = major_incident_priority(title, summary)
            return cat, pri
        return cat, None
    return "其他资讯", None
