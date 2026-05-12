"""
文章分类器（共 8 类）

【监管机构预警 | Security Advisory】规则命中（不走 LLM）
【漏洞信息 | Vulnerability】【重大安全事件 | Security Incident】【网安新闻资讯 | Industry News】
【网安赛事资讯 | CTF/Competition】【AI行业资讯】【AI与信息安全技术】【其他资讯 | Other】
—— **默认全部由 LLM 分类**；仅当未配置 LLM 或调用失败时，用关键词兜底。

优先级（冲突时）：重大安全事件 > 监管机构预警(规则) > 漏洞信息 > 网安赛事资讯 > AI与信息安全技术 > AI行业资讯 > 网安新闻资讯 > 其他资讯

实时两类仅轮巡；定时档含原四类 + AI 两类。详见 _CLASSIFICATION_CRITERIA。
classify() 返回 (类别, incident_priority)；incident_priority 仅「重大安全事件」为 high/medium/low，其余为 None。
"""
import re
from typing import Optional, Tuple

# 实时推送类别（仅在轮巡 run 中推送，见 main.py _get_run_mode）
REALTIME_CATEGORIES = {"监管机构预警", "重大安全事件"}

# 定时推送类别（仅 9:30 / 15:30 北京汇总推送，不含实时两类）
ALL_CATEGORIES = [
    "监管机构预警",
    "重大安全事件",
    "漏洞信息",
    "网安新闻资讯",
    "网安赛事资讯",
    "AI行业资讯",
    "AI与信息安全技术",
    "其他资讯",
]
TIMED_PUSH_CATEGORIES = {
    "漏洞信息",
    "网安新闻资讯",
    "网安赛事资讯",
    "其他资讯",
    "AI行业资讯",
    "AI与信息安全技术",
}

# 大模型可选分类（不含「监管机构预警」，该类仅规则命中）；长名优先用于解析
LLM_CATEGORIES = [
    "重大安全事件",
    "漏洞信息",
    "网安赛事资讯",
    "AI与信息安全技术",
    "AI行业资讯",
    "网安新闻资讯",
    "其他资讯",
]

# 监管机构预警规则：(作者/公众号名, 标题判断函数)
ALERT_RULES = [
    ("国家网络安全通报中心", lambda t: (t or "").strip().startswith("重点防范")),
    ("国家互联网应急中心CNCERT", lambda t: (t or "").strip().startswith("关于") and "风险提示" in (t or "")),
]

# LLM 输出英文标签 → 中文类名（用于解析；不含 other，避免匹配 another 等）
_EN_LABEL_TO_CN = (
    ("security incident", "重大安全事件"),
    ("ai & information security", "AI与信息安全技术"),
    ("ai and information security", "AI与信息安全技术"),
    ("ai infosec", "AI与信息安全技术"),
    ("ai industry news", "AI行业资讯"),
    ("ai industry", "AI行业资讯"),
    ("vulnerability", "漏洞信息"),
    ("industry news", "网安新闻资讯"),
    ("ctf/competition", "网安赛事资讯"),
    ("competition", "网安赛事资讯"),
    ("ctf", "网安赛事资讯"),
)


# ---------- AI 两类：关键词兜底（无 LLM 时）----------

_AI_INDUSTRY_TIER1 = re.compile(
    r"(发布|上线|开源|公测|商用|突破|SOTA|超越|替代|暂停|下线|封禁|"
    r"监管|立法|合规|禁令|指南|行政令|白宫|国会|网信办|发改委|欧盟|"
    r"\blaunch\b|\brelease\b|open[\s-]?source|general\s+availability|\bGA\b|"
    r"breakthrough|benchmark|\bSOTA\b|deprecate|\bban\b|"
    r"regulation|legislation|compliance|executive\s+order|white\s+house|\bEU\b|\bFTC\b)",
    re.I,
)

_AI_INDUSTRY_TIER2 = re.compile(
    r"(GPT-?5|GPT-?4|Claude|Gemini|Llama|多模态|大模型|基座模型|Scaling\s*Law|AGI|"
    r"Agent|智能体|Copilot|\bRAG\b|具身智能|自动驾驶|AIGC|文生图|视频生成|"
    r"算力|芯片|英伟达|\bH100\b|ASIC|数据中心|液冷|云计算)",
    re.I,
)

_AI_INDUSTRY_INTERFERE = re.compile(
    r"(赋能|重塑|颠覆|机遇|挑战|沙龙|峰会|圆满落幕|干货满满|诚邀|报名|白皮书下载|"
    r"入门|教程|十分钟看懂|小白必看|是什么|有哪些|(?<!年度)盘点|"
    r"回顾|总结|展望|"
    r"融资|IPO|上市|并购|收购|独角兽|投资|估值|财报|营收|亏损|裁员|重组|"
    r"\bfunding\b|\bIPO\b|\bM&A\b|\bacquisition\b|\bunicorn\b|\bvaluation\b|\brevenue\b|\blayoff\b)",
    re.I,
)

_AI_AUTHORITY = re.compile(
    r"(人民日报|新华社|新华网|央视新闻|人民网|澎湃新闻|财新|第一财经|经济观察报|"
    r"36氪|钛媒体|品玩|机器之心|量子位|InfoQ|华尔街见闻|中国新闻网|光明日报|"
    r"经济参考报|中国日报|欧盟委员会|白宫|美国国会|"
    r"TechCrunch|Reuters|Bloomberg|The\s+Verge|Ars\s+Technica|MIT\s+Technology\s+Review|"
    r"Wall\s+Street\s+Journal|\bWSJ\b|Financial\s+Times|\bFT\b|"
    r"The\s+Information|Wired|Nature|Science\b)",
    re.I,
)


def _ai_industry_interfere_dominant(blob: str) -> bool:
    """干扰词密集且缺少一级触发 → 不作为 AI 行业资讯兜底。"""
    if _AI_INDUSTRY_TIER1.search(blob):
        return False
    hits = len(_AI_INDUSTRY_INTERFERE.findall(blob))
    return hits >= 3


def _classify_ai_industry_keywords(author: str, blob: str) -> bool:
    """
    【AI行业资讯】兜底：须至少一级触发词 + 权威媒体/机构来源线索；
    若全文主要由干扰词构成且无一级触发，不命中。
    """
    if _ai_industry_interfere_dominant(blob):
        return False
    if not _AI_INDUSTRY_TIER1.search(blob):
        return False
    head = f"{author or ''}\n{blob}"[:2400]
    if not _AI_AUTHORITY.search(head):
        return False
    return True


_AI_TECH_MARK = re.compile(
    r"(GPT|Claude|Gemini|Llama|\bLLM\b|大模型|多模态|生成式|AIGC|Agent|智能体|"
    r"\bRAG\b|Copilot|基座模型|Scaling|AGI|文生图|视频生成|Sora|OpenAI|Anthropic|"
    r"DeepSeek|通义|文心|豆包|向量数据库|embedding|Transformers|"
    r"提示词|Prompt\s*Injection|Jailbreak|越狱|对抗样本|Deepfake|深伪|"
    r"语音克隆|人脸伪造|数据投毒|Model\s*Stealing|Model\s*Extraction|"
    r"Membership\s*Inference|后门攻击|RLHF|幻觉|对齐|宪法AI|Guardrails|水印|"
    r"OWASP.*LLM|CVE-\d{4}-\d{4,8}.*\b(LLM|GPT|model|AI)\b)",
    re.I,
)

_SEC_MARK = re.compile(
    r"(安全|信息安全|网络安全|攻击|漏洞|威胁|恶意|勒索|钓鱼|入侵|渗透|红队|"
    r"后门|泄露|隐私|合规|GDPR|CCPA|病毒|木马|杀毒|攻防|"
    r"malware|ransomware|phishing|breach|vulnerability|exploit|"
    r"Threat\s*Detection|Anomaly\s*Detection|SOAR|\bSOC\b|\bXDR\b|"
    r"Fuzzing|供应链安全|态势感知|代码审计)",
    re.I,
)

_AI_SEC_ANCHOR = re.compile(
    r"(生成恶意代码|编写病毒|绕过杀毒|制作钓鱼邮件|深伪|Deepfake|语音克隆|人脸伪造|验证码破解|"
    r"提示词注入|Prompt\s*Injection|越狱攻击|\bJailbreak\b|数据投毒|Data\s*Poisoning|"
    r"对抗样本|Adversarial|模型窃取|Model\s*Stealing|Model\s*Extraction|成员推断|Membership\s*Inference|"
    r"后门攻击|威胁检测|异常行为分析|\bSOAR\b|自动化响应|\bSOC\b|\bXDR\b|态势感知|"
    r"AI辅助代码审计|漏洞挖掘|模糊测试|供应链安全扫描|"
    r"红队|Red\s*Teaming|渗透测试|幻觉.*利用|RLHF攻击|梯度泄露|模型反演|Model\s*Inversion|"
    r"对齐|RLHF|宪法AI|Constitutional\s*AI|水印|Watermarking|护栏|Guardrails|RAG安全|向量数据库泄露|"
    r"隐私计算|联邦学习安全|差分隐私|数据脱敏|"
    r"DEFCON\s+AI|AI\s+Village|Black\s+Hat|RSA\s+Conference|OWASP\s+Top\s*10\s+for\s+LLM|"
    r"WormGPT|FraudGPT|Palo\s+Alto|CrowdStrike|Mandiant)",
    re.I,
)

_AI_SEC_EXCLUDE = re.compile(
    r"(SQL注入|XSS(跨站)?|跨站脚本|\bDDoS\b|防火墙配置|VPN漏洞)(?!.{0,80}(GPT|LLM|大模型|生成式|AI|模型|智能体))",
    re.I,
)

_AI_ENTERTAIN = re.compile(
    r"(AI画画|AI绘画|AI写小说|换脸娱乐|AI换脸(?!.{0,40}(隐私|泄露|诈骗|安全)))",
    re.I,
)


def _classify_ai_security_keywords(blob: str, low: str) -> bool:
    """【AI与信息安全技术】：须 AI 与安全的直接交集，排除纯传统安全或纯娱乐。"""
    if _AI_ENTERTAIN.search(blob) and not _SEC_MARK.search(blob):
        return False
    if _AI_SEC_EXCLUDE.search(blob) and not _AI_TECH_MARK.search(blob):
        return False
    if _AI_SEC_ANCHOR.search(blob):
        return True
    if _AI_TECH_MARK.search(blob) and _SEC_MARK.search(blob):
        return True
    return False


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


# 写入 Prompt：八类定义 + 流程 + 输出格式
_CLASSIFICATION_CRITERIA = """
你必须在下列七类中**只选一个**（监管机构预警由规则判定，你**不要**输出该类；以你本行输出为准）：
漏洞信息、重大安全事件、网安新闻资讯、网安赛事资讯、AI行业资讯、AI与信息安全技术、其他资讯

【八类定义摘要】
1. 【监管机构预警 | Security Advisory】（你不用输出）：国家网络安全通报中心+标题「重点防范」开头；或 CNCERT+「关于」开头且含「风险提示」。
2. 【重大安全事件 | Security Incident】（门槛高）：**已发生且已确认**的实害 + **可验证的实质影响**（泄露、入侵、中断、勒索得逞等）；排除未遂/演练/仅预警/传闻/纯理论。
3. 【AI与信息安全技术 | AI & InfoSec】：**仅当**不能优先归入「漏洞信息」或「网安赛事资讯」时选用。须为 **AI 技术与网络安全/信息安全的直接交集**（二者缺一不归本类）。典型：
   - 利用 AI 发起的新型攻击（LLM 写勒索软件、Deepfake/语音克隆诈骗等）。
   - AI 系统被攻击或风险叙事（提示词注入、越狱、数据投毒、对抗样本、模型窃取等）**且非**以 CVE/CVSS/补丁通告为主体。
   - 利用 AI 提升安全能力的方法论/架构（非单一 CVE 列表）。
   **硬规则**：凡**可归入**漏洞信息（含 LLM/Agent/RAG 相关 **CVE、安全公告、CVSS、受影响版本、补丁** 为主）或可归入网安赛事资讯（**CTF/HVV/竞赛/护网赛/黑客松**等赛事语境）的，**必须**归入那两类，**禁止**归入本类。
   **排除**：仅传统漏洞且无 AI；纯 AI 娱乐无安全风险叙述。
4. 【漏洞信息 | Vulnerability】：**凡**以 CVE/CVSS/补丁/受影响版本/厂商安全通告**技术细节为主**的稿件（**包括**大模型、Agent、RAG、插件供应链等相关漏洞），**一律**归本类，**不归** AI与信息安全技术。已证实大规模实害且非单纯通告 → 重大安全事件。
5. 【网安赛事资讯 | CTF/Competition】：**凡**以 CTF、护网、HVV、竞赛、Hackathon、解题赛、赛题、writeup、作**赛事/演练活动报道**的红蓝对抗为主线的，**一律**归本类（**含**「AI 安全」主题的赛），**不归** AI与信息安全技术。
6. 【AI行业资讯 | AI Industry News】：**仅当**不能归入漏洞信息、网安赛事、重大安全事件时选用。须同时满足：
   - **至少一个一级触发词**（技术与产品：发布/上线/开源/公测/商用/突破/SOTA/超越/替代/暂停/下线/封禁及英译 Launch/Release/Open-source/GA/Breakthrough/Benchmark/SOTA/Deprecate/Ban 等；政策与宏观：监管/立法/合规/禁令/指南/白宫/国会/网信办/发改委/欧盟/行政令及 Regulation/Legislation/Compliance/Executive Order/FTC 等）。
   - **来源为权威媒体或主流科技/财经媒体**（作者、署名、转载来源；如新华社、澎湃、财新、36氪、机器之心、量子位、TechCrunch、Reuters、Bloomberg、The Verge、MIT Technology Review 等）。
   - **二级触发词**为加分项（GPT/Claude、大模型、Agent、RAG、算力、英伟达等）。
   **硬规则**：若内容**可归入**漏洞信息或网安赛事资讯，**必须**归入该两类，**不归**本类。
   **排除/降权**：营销软文腔、低质科普、**仅**资本动态无一一级触发词、简单转载无新增信息。
7. 【网安新闻资讯 | Industry News】：其余网安动态、趋势、政策解读、威胁综述等。
8. 【其他资讯 | Other】：无法归入以上者。

【分类优先级】（冲突时从高到低；监管机构不由你输出）
重大安全事件 > 漏洞信息 > 网安赛事资讯 > AI与信息安全技术 > AI行业资讯 > 网安新闻资讯 > 其他资讯
若**既有**重大实害**又**涉及 AI，**优先**重大安全事件。凡能匹配漏洞信息或网安赛事资讯定义者，**即使**全文涉及 AI，也**不得**标为 AI与信息安全技术或 AI行业资讯。

【分类流程】
1. 是否已证实的大规模/高影响实害安全事件 → 重大安全事件。
2. 是否**以漏洞技术通告为主**（含 LLM/模型相关 CVE/公告/CVSS/补丁）→ **漏洞信息**。
3. 是否**赛事/HVV/CTF/竞赛/黑客松**等语境（含 AI 安全赛）→ **网安赛事资讯**。
4. 在上述均不适用时，是否 **AI 技术与信息安全的交集**（非通告体、非赛事项）→ AI与信息安全技术。
5. 是否 **一级触发词 + 权威来源** 的 AI 产业重磅（且非 2/3/4）→ AI行业资讯。
6. 其余 → 网安新闻资讯；再不行 → 其他资讯。

【重要】⚠️ 标题含「泄露/勒索/攻击」但实为资讯、预警、传闻、未遂、演练 → **勿**标重大安全事件。
⚠️ **CVE/安全公告体** → **漏洞信息**；**已利用且大规模确认实害** → 重大安全事件；**非通告、非赛事**的 AI∩安全叙事/防护架构 → AI与信息安全技术。

【输出格式】**仅一行**，不要解释、不要加前后缀：
- 若 **不是** 重大安全事件：【中文分类名 | English Name】
  例如：【AI行业资讯 | AI Industry News】、【AI与信息安全技术 | AI & InfoSec】、【漏洞信息 | Vulnerability】
- 若 **是** 重大安全事件：**必须**第三段优先级：
  【重大安全事件 | Security Incident | 高优先级】
- 兼容旧版：仅输出中文类名（不含优先级）时，重大安全事件会再追问优先级。
"""


def classify_by_rules(author: str, title: str, source_type: str) -> Optional[str]:
    """规则分类，所有源统一规则。"""
    author = (author or "").strip()
    title = (title or "").strip()
    for rule_author, title_check in ALERT_RULES:
        if rule_author in author and title_check(title):
            return "监管机构预警"
    return None


def classify_by_keywords(author: str, title: str, summary: str) -> Optional[str]:
    """
    关键词兜底（仅无 LLM 或 LLM 分类失败时使用）。顺序与业务优先级一致：
    重大安全事件 → 网安赛事 → CVE/漏洞 → AI与信息安全技术 → AI行业资讯 → 网安新闻
    （漏洞信息、网安赛事资讯 优先于两个 AI 类。）
    """
    blob = f"{title or ''}\n{summary or ''}"[:2400]
    low = blob.lower()

    # 1) 重大安全事件
    if not _blob_excludes_confirmed_major_incident(blob):
        if _major_incident_blob_heuristic(blob, low):
            return "重大安全事件"

    # 2) 网安赛事资讯（优先于 AI∩安全、AI 行业）
    if re.search(
        r"(\bctf\b|ctf[杯赛战]|攻防演练|护网20\d{2}|护网行动|实网攻防|awd赛|红队演练|红蓝对抗"
        r"|安全竞赛|解题赛|赛题|writeup|题解|\bwp\b|技能大赛|极客挑战|强网杯|\bhvv\b"
        r"|hackathon|competition|contest|red-blue team|\bdrill\b)",
        blob,
        re.I,
    ):
        return "网安赛事资讯"

    # 3) CVE/CNNVD → 漏洞信息或重大（不落入 AI∩安全，与 LLM 规则一致）
    if re.search(r"CVE-\d{4}-\d{4,8}", blob, re.I) or re.search(
        r"CNNVD-\d{4,}-\d+|CNVD-\d{4,}-\d+", blob, re.I
    ):
        if _blob_excludes_confirmed_major_incident(blob):
            return "漏洞信息"
        if _blob_looks_like_industry_news_not_incident(blob, low):
            return "漏洞信息"
        if _strong_major_incident_evidence(blob, low):
            return "重大安全事件"
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

    # 5) AI 与信息安全（非通告体、非赛事项）
    if _classify_ai_security_keywords(blob, low):
        return "AI与信息安全技术"

    # 6) AI 行业资讯
    if _classify_ai_industry_keywords(author, blob):
        return "AI行业资讯"

    # 7) 网安新闻资讯
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
        max_tokens=120,
        system=(
            "你是网络安全与人工智能交叉领域媒体主编。内容均为合法公开发表信息。"
            "「重大安全事件」须已确认实害；若归入须带第三段优先级。"
            "**凡可归入「漏洞信息」（含 LLM/模型相关 CVE、安全公告、CVSS、补丁）或「网安赛事资讯」（CTF/HVV/竞赛/黑客松等，含 AI 安全赛）的，必须归入这两类，不得归入「AI与信息安全技术」或「AI行业资讯」。**"
            "「AI与信息安全技术」仅用于**非通告体、非赛事项**的 AI 与安全交集叙事或防护架构讨论。"
            "「AI行业资讯」须一级触发词 + 可信媒体来源，且不能是漏洞通告或赛事稿。"
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

    cat = classify_by_keywords(author, title, summary)
    if cat:
        if cat == "重大安全事件":
            pri = _call_llm_incident_priority_only(text) if get_llm_providers() else None
            if not pri:
                pri = major_incident_priority(title, summary)
            return cat, pri
        return cat, None
    return "其他资讯", None
