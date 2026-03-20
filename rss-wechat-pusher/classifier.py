"""
文章分类器（共 6 类）

【监管机构预警】—— 仅由规则命中（不走 LLM）
  - 国家网络安全通报中心 + 标题以「重点防范」开头
  - 国家互联网应急中心 CNCERT + 标题以「关于」开头且含「风险提示」
  → 属于监管侧正式风险通报，实时推送。

【重大安全事件】—— LLM
  - 已发生或正在造成较大影响的**安全事件**本身：大规模数据泄露、勒索席卷、关键基础设施故障/被黑、
    重大供应链事故、影响面广的 APT 活动通报、百万级用户受影响等**结果导向**报道。
  - 与「漏洞信息」边界：若重点是**CVE/补丁/单个产品漏洞说明**且无强调已造成大规模事件 → 漏洞信息；
    若强调**已爆发、已勒索、已大规模泄露** → 重大安全事件。

【漏洞信息】—— LLM
  - CVE/CNNVD/厂商**安全公告**、安全更新、补丁说明、0-day/n-day **披露**、PoC/修复建议、
    CVSS、组件/框架漏洞技术分析（未升格为全社会级事故报道时）。
  - 与「重大安全事件」边界：以**技术披露、修复**为主 → 漏洞信息；以**事件后果、影响面**为主 → 重大安全事件。

【网安新闻资讯】—— LLM
  - **行业动态**：政策/立法/标准、监管约谈与合规、调研报告、投融资并购、人事、产品发布（非单一 CVE 通告）、
    市场观点、技术解读/科普、安全大会**泛资讯**（非以 CTF/演练为主角）、数据安全/隐私合规新闻等。

【网安赛事资讯】—— LLM
  - **CTF**、AWD、解题赛、**攻防演练**（红队/护网/演习）、安全**竞赛**报名/赛况/成绩、战报、writeup、
    人才赛、SRC **活动**若以比赛/打榜为主。

【其他资讯】—— LLM
  - 泛 IT、弱安全关联、边界模糊软文、无法稳定归入以上任一类的内容。

说明：LLM 只从「漏洞信息、重大安全事件、网安新闻资讯、网安赛事资讯、其他资讯」五选一输出；
     「监管机构预警」仅由本文件内规则函数命中。

【实时推送】与 main.py 一致：`REALTIME_CATEGORIES = {监管机构预警, 重大安全事件}`。
即：**重大安全事件** 与 **监管机构预警** 一样，在**首次入库**且**发布日=北京时间当天**、且未推送过时，会**立即推送到企业微信**（不按 9:30/15:30）。
仅改库中旧数据的分类不会自动补发「实时」，需依赖之后定时汇总或手动 `--push-now`。
"""
import re
from typing import Optional

# 实时推送类别（每 5 分钟检测到立即推送）
REALTIME_CATEGORIES = {"监管机构预警", "重大安全事件"}

# 定时推送类别（9:30、15:30 汇总推送，含全部 6 类，与实时去重）
ALL_CATEGORIES = ["监管机构预警", "重大安全事件", "漏洞信息", "网安新闻资讯", "网安赛事资讯", "其他资讯"]
SCHEDULED_CATEGORIES = set(ALL_CATEGORIES)

# 大模型可选分类（不含「监管机构预警」，该类仅规则命中）
LLM_CATEGORIES = ["漏洞信息", "重大安全事件", "网安新闻资讯", "网安赛事资讯", "其他资讯"]

# 监管机构预警规则：(作者/公众号名, 标题判断函数)
ALERT_RULES = [
    ("国家网络安全通报中心", lambda t: (t or "").strip().startswith("重点防范")),
    ("国家互联网应急中心CNCERT", lambda t: (t or "").strip().startswith("关于") and "风险提示" in (t or "")),
]

# 写入 Prompt 的精简版「六类划分」（与文件头 docstring 一致，供模型对齐）
_CLASSIFICATION_CRITERIA = """
你必须从下列五个分类中**严格只选一个**输出中文全称（不要标点、不要解释、不要换行）：
漏洞信息、重大安全事件、网安新闻资讯、网安赛事资讯、其他资讯

【划分标准】
1. 漏洞信息：CVE/CNNVD、厂商安全通告、补丁/安全更新、0-day·n-day 披露、PoC、组件/框架漏洞分析；
   核心是「有编号或具体缺陷 + 修复/缓解」，**尚未强调已酿成大规模社会性事件**时优先本类。

2. 重大安全事件：已发生或影响面广的**事故**报道——大规模泄露、勒索爆发、关键基础设施被攻击、
   重大供应链事故、APT 行动造成实质危害、大面积业务中断等；**后果与影响面**是判断重点。
   若同一新闻以「某勒索卷土重来」为主角而非单条 CVE，倾向本类。

3. 网安新闻资讯：政策/监管/立法、合规动态、行业报告、投融资并购、产品动态（非单纯漏洞通告）、
   观点评论、技术科普、安全会议/峰会**综合资讯**（主角不是某一场 CTF 或演练本身）。

4. 网安赛事资讯：CTF、AWD、解题赛、攻防演练/护网/演习、安全竞赛、writeup、赛题/战报、以竞赛或演练为主线。

5. 其他资讯：与网络安全弱相关、无法可靠归入以上任一类。

【易混示例】（仅帮助理解）
- 「微软发布本月补丁修复远程代码执行」→ 漏洞信息
- 「某国医疗系统遭勒索，多家医院停摆」→ 重大安全事件
- 「工信部印发××安全管理办法」→ 网安新闻资讯
- 「×× CTF 决赛收官 / 某市网络攻防演练启动」→ 网安赛事资讯

【冲突时优先级】赛事/演练关键词明显 → 网安赛事资讯；已描述大规模实害 → 重大安全事件优先于漏洞信息；
标题或摘要中含 CVE/CNNVD/CNVD 编号且无大面积受害描述 → 倾向漏洞信息；
其余卡边情况 → 其他资讯。
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
    关键词/模式优先于 LLM（减少飘类）。未命中则返回 None 再走大模型。
    顺序：赛事 > CVE/编号漏洞 > 重大事件用语 > 政策/行业新闻
    """
    blob = f"{title or ''}\n{summary or ''}"[:2400]
    low = blob.lower()

    # 1) 赛事/演练（避免 CTF、护网被模型收成「重大事件」）
    if re.search(
        r"(\bctf\b|ctf[杯赛战]|攻防演练|护网20\d{2}|护网行动|实网攻防|awd赛|红队演练"
        r"|安全竞赛|解题赛|赛题|writeup|题解|\bwp\b|技能大赛|极客挑战|强网杯)",
        blob,
        re.I,
    ):
        return "网安赛事资讯"

    # 2) 明确 CVE/CNNVD：一般是漏洞通告；若同时强调已酿成大面积事故 → 重大事件
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
            )
        )
        if severe:
            return "重大安全事件"
        return "漏洞信息"

    # 3) 典型漏洞通告用语（无 CVE 时）
    vuln_only = any(
        k in blob
        for k in (
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
        )
    ) and not any(
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

    # 4) 重大安全事件（结果/影响导向，且无更优先的 CVE+仅技术味）
    if any(
        k in blob
        for k in (
            "数据泄露",
            "信息泄露",
            "勒索软件",
            "勒索攻击",
            "勒索病毒",
            "大规模攻击",
            "供应链攻击",
            "关键基础设施",
            "医院遭",
            "政府网站",
            "银行遭",
            "用户数据被盗",
            "暗网出售",
            "定向攻击",
            "钓鱼攻击",
            "宕机",
            "业务中断",
        )
    ):
        return "重大安全事件"

    # 5) 偏政策/行业动态（避免吃进「漏洞」类）
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
        )
    ) and "CVE" not in blob.upper():
        return "网安新闻资讯"

    return None


def _call_llm_classify(text: str) -> Optional[str]:
    """调用 LLM 进行分类，支持多模型自动切换（额度用尽时换下一个）。"""
    from llm_utils import call_llm_with_fallback

    prompt = f"""{_CLASSIFICATION_CRITERIA}

下面是一条待分类内容（标题/作者/摘要可能不完整，请综合判断）：

{text}

你的输出（仅五个词之一）："""
    content = call_llm_with_fallback(
        [{"role": "user", "content": prompt}],
        max_tokens=32,
        system=(
            "你是网络安全媒体的主编，负责把公开渠道的技术资讯归入固定栏目。"
            "内容均为合法公开发表信息。请严格遵守用户给出的五个分类名之一，"
            "只输出分类名这五个汉字词组之一，不要任何其他字符。"
        ),
    )
    if not content:
        return None
    # 取第一行，去掉可能的括号说明
    line = content.strip().split("\n")[0].strip()
    line = line.rstrip("。．.！!？?")
    # 优先完全相等，减少「非漏洞信息」类误命中
    if line in LLM_CATEGORIES:
        return line
    for cat in sorted(LLM_CATEGORIES, key=len, reverse=True):
        if cat in line:
            return cat
    return "其他资讯"


def classify(author: str, title: str, summary: str, source_type: str) -> str:
    """
    分类入口。
    - 先规则 → 监管机构预警
    - 再关键词/模式（赛事、CVE、事件、政策等）→ 命中则直接返回
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
