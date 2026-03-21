#!/usr/bin/env python3
"""
RSS 推送到企业微信机器人
- 静默：北京每天 20:00–次日 6:00 不推送（实时与定时均不推，拉取入库照常）
- 实时两类（监管预警、重大事件）：6:00–20:00 内轮巡（约每 2 小时，可接受延迟）；夜间发布的在次日 6:00 后非静默时段补推
- 定时四类：9:30 档用「昨 15:30～今 9:30」时间窗（覆盖静默造成的缺口）；15:30 档与手动 --push-now 仅「今天」稿（北京日期）
- 去重：已写入 pushed 的链接不再推送
- 全量：`--push-all-now`；临时含昨天：`--push-now --with-yesterday`
"""

import os
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

try:
    from config import (
        WECHAT_WEBHOOK,
        FEEDS,
        SCHEDULED_PUSH_TIMES,
        SCHEDULED_WINDOW_MINUTES,
        POLL_HOURS_BEIJING,
        POLL_WINDOW_MINUTES,
    )
    from classifier import (
        classify,
        REALTIME_CATEGORIES,
        TIMED_PUSH_CATEGORIES,
    )
except ImportError:
    import json
    import os
    webhook = os.getenv("WECHAT_WEBHOOK")
    feeds_json = os.getenv("FEEDS_JSON")
    if webhook and feeds_json:
        WECHAT_WEBHOOK = webhook
        FEEDS = [(u, t) for u, t in json.loads(feeds_json)]
        SCHEDULED_PUSH_TIMES = [(9, 30), (15, 30)]
        SCHEDULED_WINDOW_MINUTES = 5
        POLL_HOURS_BEIJING = (6, 8, 10, 12, 14, 16, 18)
        POLL_WINDOW_MINUTES = 5
        from classifier import classify, REALTIME_CATEGORIES, TIMED_PUSH_CATEGORIES
    else:
        print("请复制 config.example.py 为 config.py 并填写配置")
        sys.exit(1)

# 数据库路径：CI 下用仓库内文件（可持久化），本地用用户目录
if os.getenv("CI") and os.getenv("GITHUB_WORKSPACE"):
    DB_DIR = Path(os.getenv("GITHUB_WORKSPACE")) / "rss-wechat-pusher"
    DB_PATH = DB_DIR / "rss_push.db"
else:
    DB_DIR = Path(os.path.expanduser("~/.rss-wechat-pusher"))
    DB_DIR.mkdir(exist_ok=True)
    DB_PATH = DB_DIR / "rss_push.db"
# 企业微信 markdown 单条上限 4096 字节（中文约 3 字节/字），超长自动分片
MAX_CONTENT_BYTES = int(os.getenv("WECHAT_MAX_BYTES", "3800"))


def init_db(conn):
    """初始化数据库"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
            link TEXT PRIMARY KEY,
            title TEXT,
            summary TEXT,
            category TEXT,
            author TEXT,
            source_url TEXT,
            published_str TEXT,
            first_seen_at TEXT
        );
        CREATE TABLE IF NOT EXISTS pushed (
            link TEXT PRIMARY KEY,
            pushed_at TEXT,
            push_type TEXT
        );
    """)
    conn.commit()


def get_known_links(conn):
    """已入库的文章链接"""
    cur = conn.execute("SELECT link FROM articles")
    return {row[0] for row in cur.fetchall()}


def get_pushed_links(conn):
    """已推送的链接"""
    cur = conn.execute("SELECT link FROM pushed")
    return {row[0] for row in cur.fetchall()}


def _parse_published_to_beijing(published_str):
    """解析 published_str（假定 UTC）为北京时区 datetime"""
    if not published_str or not isinstance(published_str, str):
        return None
    try:
        s = published_str.strip()[:16]
        utc = datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        from zoneinfo import ZoneInfo
        return utc.astimezone(ZoneInfo("Asia/Shanghai"))
    except Exception:
        return None


def _is_today_beijing(dt):
    """是否北京时间的当天"""
    if not dt:
        return False
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        return dt.date() == now.date()
    except ImportError:
        return False


def _is_yesterday_beijing(dt):
    """是否北京时间的昨天（按日历日）"""
    if not dt:
        return False
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        return dt.date() == (now.date() - timedelta(days=1))
    except ImportError:
        return False


def _is_today_or_yesterday_beijing(dt):
    return _is_today_beijing(dt) or _is_yesterday_beijing(dt)


def _now_beijing():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Shanghai"))
    except ImportError:
        return datetime.now()


def _is_quiet_hours_beijing_now():
    """北京 20:00–次日 6:00 为静默时段，不执行任何推送。"""
    now = _now_beijing()
    h = now.hour
    return h >= 20 or h < 6


def _is_publish_time_in_quiet_hours(dt):
    """文章发布时间是否落在 20:00–次日 6:00（北京，不含 6:00 整）。"""
    if not dt:
        return False
    total_m = dt.hour * 60 + dt.minute
    if total_m >= 20 * 60:
        return True
    if total_m < 6 * 60:
        return True
    return False


def _realtime_should_queue_for_push(dt):
    """是否把实时两类加入待推送队列（入库后候选，最终以 eligibility 为准）。"""
    if not dt:
        return False
    if _is_publish_time_in_quiet_hours(dt):
        return True
    if _is_today_beijing(dt):
        return True
    if _is_yesterday_beijing(dt):
        return True
    return False


def _realtime_article_eligible_now(dt, now_bj):
    """
    当前时刻是否允许推送该实时稿（须非静默时段）。
    - 夜间发布：次日 6:00～当日 19:59 之间的非静默轮巡可推
    - 日间 6:00–20:00 发布：仅今天或昨天稿（补昨天白天遗留）
    """
    if not dt:
        return False
    if _is_quiet_hours_beijing_now():
        return False
    if _is_publish_time_in_quiet_hours(dt):
        if now_bj.date() > dt.date():
            return 6 <= now_bj.hour < 20
        if now_bj.date() == dt.date():
            return now_bj.hour >= 6 and now_bj.hour < 20
        return False
    if _is_today_beijing(dt):
        return True
    if _is_yesterday_beijing(dt):
        return True
    return False


def _is_in_930_window(dt):
    """是否在前一天 15:30 至当天 9:30 之间（北京）"""
    if not dt:
        return False
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Shanghai")
        now = datetime.now(tz)
        today_930 = now.replace(hour=9, minute=30, second=0, microsecond=0)
        yesterday_1530 = (now - timedelta(days=1)).replace(hour=15, minute=30, second=0, microsecond=0)
        return yesterday_1530 <= dt <= today_930
    except ImportError:
        return False


def _get_scheduled_slot():
    """当前若在定时窗口内，返回 config 中某一档 (h,m)，否则 None"""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Shanghai")
        now = datetime.now(tz)
    except ImportError:
        now = datetime.now()
    for h, m in SCHEDULED_PUSH_TIMES:
        start = datetime(now.year, now.month, now.day, h, m - SCHEDULED_WINDOW_MINUTES, tzinfo=getattr(now, "tzinfo", None))
        end = datetime(now.year, now.month, now.day, h, m + SCHEDULED_WINDOW_MINUTES, tzinfo=getattr(now, "tzinfo", None))
        if start <= now <= end:
            return (h, m)
    return None


def _is_polling_slot_beijing():
    """当前是否在北京轮巡窗口内（整点 ± POLL_WINDOW_MINUTES，小时见 POLL_HOURS_BEIJING）"""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Shanghai")
        now = datetime.now(tz)
    except ImportError:
        now = datetime.now()
    if now.hour not in POLL_HOURS_BEIJING:
        return False
    return now.minute <= POLL_WINDOW_MINUTES + 1


def _get_run_mode():
    """
    poll: 轮巡，仅推送实时两类
    scheduled: 定时，仅推送其余四类
    None: 不在窗口，仅拉取入库不推送
    环境变量 RSS_PUSH_MODE=poll 强制轮巡；scheduled 与 --push-now 在 main 中单独处理
    """
    ov = os.getenv("RSS_PUSH_MODE", "").strip().lower()
    if ov in ("poll", "polling"):
        return "poll"
    if _get_scheduled_slot():
        return "scheduled"
    if _is_polling_slot_beijing():
        return "poll"
    return None


def _collect_realtime_to_push(conn, new_realtime, include_db_backlog):
    """
    本轮待推送的实时两类。
    include_db_backlog=False：仅本 run 新入库的 new_realtime（与轮巡行为一致）。
    include_db_backlog=True：合并库内当日仍未推送的实时类（用于 --push-all-now）。
    """
    if not include_db_backlog:
        return list(new_realtime)
    by_link = {item["link"]: item for item in new_realtime}
    ph = ",".join("?" * len(REALTIME_CATEGORIES))
    cur = conn.execute(
        f"""SELECT link, title, published_str, category, author, source_url FROM articles
           WHERE category IN ({ph}) AND link NOT IN (SELECT link FROM pushed)""",
        tuple(REALTIME_CATEGORIES),
    )
    for link, title, ps, cat, author, su in cur.fetchall():
        if link in by_link:
            continue
        dt_bj = _parse_published_to_beijing(ps)
        if not _realtime_should_queue_for_push(dt_bj):
            continue
        su = su or ""
        st = _source_type_for_feed_url(su)
        by_link[link] = {
            "title": title,
            "published_str": ps,
            "link": link,
            "category": cat,
            "author": author or "",
            "source_url": su,
            "source_type": st,
        }
    return list(by_link.values())


def parse_date(entry):
    """解析发布日期"""
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    return None


def format_published(entry):
    """格式化为 YYYY-MM-DD HH:mm（北京时间，国外源统一换算）"""
    dt = parse_date(entry)
    if dt:
        try:
            from zoneinfo import ZoneInfo
            dt_bj = dt.astimezone(ZoneInfo("Asia/Shanghai"))
            return dt_bj.strftime("%Y-%m-%d %H:%M")
        except ImportError:
            return dt.strftime("%Y-%m-%d %H:%M")
    return ""


def get_author(entry):
    """从 entry 提取公众号/作者"""
    author = getattr(entry, "author", None)
    if author:
        if isinstance(author, dict):
            return author.get("name", "") or author.get("email", "")
        return str(author)
    source = getattr(entry, "source", None)
    if source and hasattr(source, "title"):
        return getattr(source, "title", "") or ""
    return ""


def _source_type_for_feed_url(feed_url: str) -> str:
    """根据 config.FEEDS 匹配条目所属 feed 类型（wewe_rss / rss），旧库无类型字段时用。"""
    if not feed_url:
        return "rss"
    ff = feed_url.rstrip("/")
    for u, st in FEEDS:
        uu = u.rstrip("/")
        if ff == uu or ff.startswith(uu + "/"):
            return st
    return "rss"


def _hostname_from_feed(feed_url: str) -> str:
    """RSS/Atom 页的域名，用于网站类来源展示。"""
    from urllib.parse import urlparse

    p = urlparse(feed_url or "")
    host = (p.netloc or "").split("@")[-1].lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _source_bracket_label(author: str, source_type: str, feed_url: str) -> str:
    """
    紧挨时间的括号备注：来源：xx公众号 / 来源：xx网站
    - wewe_rss：优先用 RSS 里的作者名作为公众号名
    - rss：用订阅域名 + 「网站」
    """
    st = (source_type or "rss").strip().lower()
    author = (author or "").strip()
    host = _hostname_from_feed(feed_url)
    if st == "wewe_rss":
        if author:
            core = author if author.endswith("公众号") else f"{author}公众号"
        elif host:
            core = f"{host}公众号"
        else:
            core = "未知公众号"
    else:
        core = f"{host}网站" if host else "未知网站"
    return f"来源：{core}"


def fetch_feed(url):
    """
    拉取 RSS：requests 拉正文再 feedparser 解析。
    FreeBuf 等对云主机/脚本常返回 405：使用浏览器级请求头，并对 /feed、/feed/、镜像 URL 依次重试。
    若 GitHub Actions 仍 405，可在 Secrets 设置 FREEBUF_RSS_MIRROR 为自建 RSSHub 等镜像完整地址。
    """
    from urllib.parse import urlparse

    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    def headers_for(target):
        p = urlparse(target)
        referer = f"{p.scheme}://{p.netloc}/" if p.scheme and p.netloc else "https://www.freebuf.com/"
        return {
            "User-Agent": ua,
            "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": referer,
            "Cache-Control": "no-cache",
        }

    candidates = []
    seen = set()

    def add(u):
        if u and u not in seen:
            seen.add(u)
            candidates.append(u)

    low = (url or "").lower()
    mirror = (os.getenv("FREEBUF_RSS_MIRROR") or "").strip()
    if mirror and "freebuf.com" in low:
        add(mirror)

    add(url)

    if "freebuf.com" in low:
        stripped = url.rstrip("/")
        if stripped.endswith("/feed"):
            add(stripped + "/")
        elif not url.endswith("/"):
            add(stripped + "/")

    session = requests.Session()
    last_err = None
    for u in candidates:
        try:
            r = session.get(u, headers=headers_for(u), timeout=25, allow_redirects=True)
            if r.status_code in (403, 405):
                last_err = f"{r.status_code} Client Error for url: {u}"
                continue
            r.raise_for_status()
            r.encoding = r.apparent_encoding or getattr(r, "encoding", None) or "utf-8"
            d = feedparser.parse(r.text)
            return d.entries if d.entries else []
        except requests.HTTPError as e:
            resp = e.response
            if resp is not None and resp.status_code in (403, 405):
                last_err = str(e)
                continue
            last_err = str(e)
            continue
        except Exception as e:
            last_err = str(e)
            continue

    print(f"拉取失败 {url}: {last_err or 'unknown'}")
    return []


# 分类对应的 emoji
CATEGORY_STYLE = {
    "监管机构预警": "🔴",
    "重大安全事件": "🔥",
    "漏洞信息": "🐛",
    "网安新闻资讯": "📰",
    "网安赛事资讯": "🏆",
    "其他资讯": "📋",
}


CATEGORY_ORDER = ["监管机构预警", "重大安全事件", "漏洞信息", "网安新闻资讯", "网安赛事资讯", "其他资讯"]

# 国家网络安全通报中心 + 重点防范 → 需抓取正文提取 IOC
IOC_ALERT_AUTHOR = "国家网络安全通报中心"
IOC_ALERT_TITLE_PREFIX = "重点防范"

# 翻译缓存，避免重复调用
_translate_cache = {}


def _fetch_article_text(url):
    """抓取文章正文（支持微信公众号等）"""
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=15)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        body = soup.find(id="js_content") or soup.find(class_=re.compile("rich_media_content|content"))
        if body:
            return body.get_text(separator="\n", strip=True)
        for tag in ("article", "main", "body"):
            el = soup.find(tag)
            if el:
                return el.get_text(separator="\n", strip=True)
    except Exception:
        pass
    return ""


# 非恶意 IP（本地/保留地址），不计入有效 IOC
_IGNORE_IPS = {"0.0.0.0", "255.255.255.255"}


def _is_meaningful_ip(ip):
    """排除本地、保留地址"""
    if not ip or ip in _IGNORE_IPS:
        return False
    if ip.startswith("127."):  # loopback
        return False
    return True


def _extract_iocs(text):
    """从正文提取域名与 IP，尝试配对为 (恶意地址, 关联IP)，仅保留有效 IOC"""
    if not text:
        return []
    pairs = []
    for m in re.finditer(r"(?:恶意地址|域名)[:：]\s*([^\s，。\n]+)\s*关联IP(?:地址)?[:：]\s*([\d.]+)", text):
        domain, ip = m.group(1).strip(), m.group(2).strip()
        if domain and domain != "-" and ip and ip.count(".") == 3 and _is_meaningful_ip(ip):
            pairs.append((domain, ip))
    if not pairs:
        domains = list(dict.fromkeys(re.findall(r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}", text)))
        ips = list(dict.fromkeys(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)))
        for i in range(max(len(domains), len(ips))):
            d = domains[i] if i < len(domains) else ""
            ip = ips[i] if i < len(ips) else ""
            if d and ip and _is_meaningful_ip(ip):
                pairs.append((d, ip))
    return pairs[:20]


def _build_ioc_push_content(item):
    """构建「重点防范」类文章的特殊格式（含 IOC）。若无有效 IOC 则返回 None，改用基础格式。"""
    title = item.get("title") or ""
    try:
        from config import TRANSLATE_ENABLED
    except ImportError:
        TRANSLATE_ENABLED = True
    if TRANSLATE_ENABLED and title and _should_translate_title(title):
        t2, ok = _translate_to_chinese(title[:200])
        if ok:
            title = f"{t2}（译）"
    link = item.get("link") or ""
    time_str = item.get("published_str") or ""
    text = _fetch_article_text(link)
    pairs = _extract_iocs(text)
    if not pairs:
        return None  # 无有效 IOC，用基础格式
    feed_url = item.get("source_url") or ""
    st = item.get("source_type") or _source_type_for_feed_url(feed_url)
    src = _source_bracket_label(item.get("author") or "", st, feed_url)
    lines = [
        "【信息类型】监管机构预警",
        f"【标题】{title}",
        f"【时间】{time_str}（{src}）",
        f"【链接】{link}",
        "【相关IOC】",
    ]
    cn_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    for i, (domain, ip) in enumerate(pairs):
        num = f"（{cn_nums[i]}）" if i < len(cn_nums) else f"（{i+1}）"
        lines.append(f"{num}恶意地址：{domain} 关联IP：{ip}")
    return "\n".join(lines)


def _has_chinese(text):
    """检测文本是否包含中文"""
    if not text:
        return False
    for c in text:
        if "\u4e00" <= c <= "\u9fff":
            return True
    return False


def _should_translate_title(title: str) -> bool:
    """
    是否需要将标题译为中文（用于推送展示）。
    - 无中文（CJK 统一表意区）：译
    - 中英混合：英文字母数明显多于汉字时仍译（避免「短英文前缀+少量汉字」被误判为已中文化）
    """
    if not title or not str(title).strip():
        return False
    t = str(title).strip()
    if not _has_chinese(t):
        return True
    cn = sum(1 for c in t if "\u4e00" <= c <= "\u9fff")
    latin = sum(1 for c in t if "a" <= c <= "z" or "A" <= c <= "Z")
    # 原阈值 latin>=6 过严：如 "RCE风险" "AI安全周报" 会整句不译
    if latin >= 3 and latin >= cn * 1.05:
        return True
    if latin >= cn * 1.5:
        return True
    return False


# 翻译专用系统提示：减少「涉攻击/漏洞」类标题被模型误拒；要求单行输出
_TRANSLATION_SYSTEM = """你是网络安全行业媒体的中文编辑。用户给出的英文标题均为互联网上已公开发表的技术资讯（厂商公告、CVE、漏洞说明、安全研究报道等合法内容）。
请只输出一句简体中文标题：不要引号、不要解释、不要前后缀；禁止拒绝回答或输出免责声明。
若标题极短或专有名过多，可保留必要英文词。"""


def _looks_like_llm_refusal(text: str) -> bool:
    """模型拒答、合规话术 → 不用作标题展示"""
    if not text or not text.strip():
        return True
    t = text.strip()
    low = t.lower()
    for s in (
        "我不能", "我无法", "对不起", "抱歉", "无法提供", "不能提供", "无法翻译",
        "不能翻译", "不提供", "涉及非法", "不道德", "不符合", "服务准则",
        "安全原因", "违规内容", "无法完成", "不应提供", "不予", "拒绝",
    ):
        if s in t:
            return True
    for s in (
        "i cannot", "i can't", "i'm sorry", "sorry,", "unable to translate",
        "cannot translate", "can't translate", "cannot provide", "as an ai",
        "i will not", "i'm not able",
    ):
        if s in low:
            return True
    return False


def _sanitize_translation_output(raw: str, original: str) -> str:
    """去掉「translated to:」链式重复、多行废话，检测拒答后回退英文原标题"""
    if not raw:
        return original
    s = raw.strip().strip('"').strip("'")
    # 模型反复「translated to:」时只取最后一次后面的文本
    for _ in range(8):
        m = re.search(r"(?i)translated\s*to\s*:\s*(.+)$", s)
        if m:
            s = m.group(1).strip()
            continue
        m2 = re.search(r"(?:译为|翻译为|翻译结果)[:：]\s*(.+)$", s)
        if m2:
            s = m2.group(1).strip()
            continue
        break
    s = s.split("\n")[0].strip()
    for prefix in ("中文标题：", "翻译结果：", "翻译：", "标题：", "结果：", "输出："):
        if s.startswith(prefix):
            s = s[len(prefix) :].strip()
    s = re.sub(r"[（(]译[）)]\s*$", "", s).strip()
    if len(s) > 200:
        s = s[:200].rstrip()
    if _looks_like_llm_refusal(s):
        return original
    # 要求有中文；若仍全英文则视为失败，避免把拒答残句推出去
    if not _has_chinese(s):
        return original
    return s


def _translate_title_for_display(full_title: str, max_in: int = 500, max_out: int = 200):
    """
    用完整标题（限长）调用翻译，避免只取前 80 字导致中英比例失真或截断在词中间。
    返回 (展示用标题, 是否译成功)。失败时退回与原先一致的 80 字截断展示。
    """
    full_title = (full_title or "").strip()
    if not full_title:
        return "", False
    tin = full_title[:max_in]
    t, ok = _translate_to_chinese(tin)
    if ok:
        if len(t) > max_out:
            t = t[: max_out - 1].rstrip() + "…"
        return t, True
    short = full_title[:80] + ("..." if len(full_title) > 80 else "")
    return short, False


def _translate_to_chinese(title):
    """
    将纯英文标题译为中文。
    返回 (展示用标题, 是否采用了中文译名)。失败时第二项为 False，展示仍用原文（不标记「译」）。
    """
    if not title:
        return title, False
    if title in _translate_cache:
        cached = _translate_cache[title]
        if isinstance(cached, tuple) and len(cached) == 2:
            return cached
        # 旧缓存：仅有字符串
        ok = cached != title and _has_chinese(cached or "") and not _looks_like_llm_refusal(cached or "")
        return (cached if ok else title, ok)

    from llm_utils import call_llm_with_fallback, get_llm_providers

    if not get_llm_providers():
        _translate_cache[title] = (title, False)
        return title, False

    raw = call_llm_with_fallback(
        [{"role": "user", "content": f"请翻译为简体中文标题（仅此一行）：\n{title}"}],
        max_tokens=256,
        system=_TRANSLATION_SYSTEM,
    )
    if not raw:
        _translate_cache[title] = (title, False)
        return title, False

    cleaned = _sanitize_translation_output(raw, title)
    ok = cleaned != title and _has_chinese(cleaned) and not _looks_like_llm_refusal(cleaned)
    pair = (cleaned if ok else title, ok)
    _translate_cache[title] = pair
    return pair


def _build_single_category_content(category, items):
    """构建单个分类的 Markdown 内容（使用 comment 灰色字体，视觉更紧凑）"""
    try:
        from config import TRANSLATE_ENABLED
    except ImportError:
        TRANSLATE_ENABLED = True
    emoji = CATEGORY_STYLE.get(category, "📌")
    lines = [f"### {emoji} {category}", ""]
    for item in items:
        full = (item.get("title") or "").strip()
        raw_title = full[:80] + ("..." if len(full) > 80 else "")
        translated = False
        # 用完整标题判断是否该译、并送入模型（避免 80 字截断误判「已有中文」或漏译后半段英文）
        if TRANSLATE_ENABLED and full and _should_translate_title(full):
            title, translated = _translate_title_for_display(full)
        else:
            title = raw_title
        if translated:
            title = f"{title}（译）"
        link = item["link"] or ""
        time_str = item.get("published_str") or ""
        feed_url = item.get("source_url") or ""
        st = item.get("source_type") or _source_type_for_feed_url(feed_url)
        src = _source_bracket_label(item.get("author") or "", st, feed_url)
        title_safe = (title or "").replace("]", "］").replace("[", "［")
        lines.append(f"[{title_safe}]({link})")
        lines.append(f"> {time_str}（{src}）")
        lines.append("")
    return "\n".join(lines).strip()


def _is_ioc_alert_item(item):
    """是否为国家网络安全通报中心 + 重点防范（需抓取正文提取 IOC）"""
    author = (item.get("author") or "").strip()
    title = (item.get("title") or "").strip()
    return IOC_ALERT_AUTHOR in author and title.startswith(IOC_ALERT_TITLE_PREFIX)


def send_wechat_per_category(webhook, items_by_category):
    """按分类分别推送，每个类型一条消息。重点防范类单独抓正文提取 IOC 后按特殊格式推送。"""
    for i, category in enumerate(CATEGORY_ORDER):
        items = items_by_category.get(category, [])
        if not items:
            continue
        if i > 0:
            time.sleep(0.3)
        # 监管机构预警：重点防范类若有有效 IOC 则用特殊格式，否则用基础格式
        if category == "监管机构预警":
            ioc_items = [x for x in items if _is_ioc_alert_item(x)]
            normal_items = [x for x in items if not _is_ioc_alert_item(x)]
            for item in ioc_items:
                time.sleep(0.3)
                content = _build_ioc_push_content(item)
                if content:
                    send_wechat(webhook, content, use_markdown=False)  # 有有效 IOC，特殊格式
                else:
                    normal_items.append(item)  # 无有效 IOC，并入基础格式
            items = normal_items
        if items:
            content = _build_single_category_content(category, items)
            send_wechat(webhook, content)


def _split_by_bytes(content, max_bytes):
    """按字节数分割，避免 UTF-8 中文超限"""
    chunks = []
    enc = "utf-8"
    while content:
        b = content.encode(enc)
        if len(b) <= max_bytes:
            chunks.append(content)
            break
        # 从 max_bytes 往前找换行符，避免截断
        cut = b[:max_bytes].rfind(b"\n")
        if cut <= 0:
            cut = max_bytes
        chunk = b[:cut].decode(enc, errors="ignore")
        chunks.append(chunk)
        content = content[len(chunk):].lstrip()
    return chunks


def send_wechat(webhook, content, use_markdown=True):
    """发送到企业微信（按字节分片，单条间隔 0.3s 防限流）"""
    chunks = _split_by_bytes(content, MAX_CONTENT_BYTES)

    for i, chunk in enumerate(chunks):
        if i > 0:
            time.sleep(0.3)
        if use_markdown:
            payload = {"msgtype": "markdown", "markdown": {"content": chunk}}
        else:
            payload = {"msgtype": "text", "text": {"content": chunk}}
        try:
            r = requests.post(webhook, json=payload, timeout=10)
            r.raise_for_status()
            j = r.json()
            if j.get("errcode") != 0:
                print(f"企业微信返回错误: {j}")
        except Exception as e:
            print(f"发送失败: {e}")
            raise


def is_scheduled_time():
    """当前是否在定时推送时间窗口内（使用北京时区，兼容 GitHub Actions UTC 环境）"""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Shanghai")
        now = datetime.now(tz)
    except ImportError:
        now = datetime.now()
    for h, m in SCHEDULED_PUSH_TIMES:
        start = datetime(now.year, now.month, now.day, h, m - SCHEDULED_WINDOW_MINUTES, tzinfo=getattr(now, "tzinfo", None))
        end = datetime(now.year, now.month, now.day, h, m + SCHEDULED_WINDOW_MINUTES, tzinfo=getattr(now, "tzinfo", None))
        if start <= now <= end:
            return True
    return False


def main():
    # 1. 并行拉取所有源（8 个同时请求，大幅提速）
    # all_new: (link, title, summary, category, author, feed_url, published_str, source_type)
    all_new = []

    def fetch_one(feed_url, source_type):
        entries = fetch_feed(feed_url)
        return [(feed_url, source_type, e) for e in entries]

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_one, url, st): (url, st) for url, st in FEEDS}
        for future in as_completed(futures):
            try:
                items = future.result()
                for feed_url, source_type, entry in items:
                    link = entry.get("link")
                    if not link:
                        continue
                    title = (entry.get("title") or "").strip()
                    summary = (entry.get("summary") or "")
                    author = get_author(entry)
                    published_str = format_published(entry)
                    category = classify(author, title, summary, source_type)
                    all_new.append((link, title, summary, category, author, feed_url, published_str, source_type))
            except Exception as e:
                url, st = futures[future]
                print(f"拉取失败 {url}: {e}")

    # 2. 短时连接数据库，批量读写
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")  # WAL 模式减少锁定
    init_db(conn)
    known = get_known_links(conn)
    pushed = get_pushed_links(conn)

    new_realtime = []
    now_str = datetime.now().isoformat()
    for link, title, summary, category, author, feed_url, published_str, source_type in all_new:
        if link in known:
            continue
        conn.execute(
            """INSERT OR IGNORE INTO articles
               (link, title, summary, category, author, source_url, published_str, first_seen_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (link, title, summary, category, author, feed_url, published_str, now_str),
        )
        known.add(link)
        # 监管预警、重大事件→实时推送（公众号+网站均支持，以分类为准）
        if category in REALTIME_CATEGORIES and link not in pushed:
            dt_bj = _parse_published_to_beijing(published_str)
            if _realtime_should_queue_for_push(dt_bj):
                new_realtime.append({
                    "title": title,
                    "published_str": published_str,
                    "link": link,
                    "category": category,
                    "author": author or "",
                    "source_url": feed_url,
                    "source_type": source_type,
                })

    conn.commit()

    force_push_all = "--push-all-now" in sys.argv or os.getenv("PUSH_ALL_NOW") == "1"
    include_yesterday = "--with-yesterday" in sys.argv or os.getenv("SCHEDULED_INCLUDE_YESTERDAY") == "1"
    force_timed_digest = (
        force_push_all
        or "--push-now" in sys.argv
        or os.getenv("PUSH_SCHEDULED_NOW") == "1"
        or os.getenv("RSS_PUSH_MODE", "").strip().lower() in ("scheduled", "timed")
    )
    if force_timed_digest and not force_push_all:
        mode = "scheduled"
    else:
        mode = _get_run_mode()

    quiet_now = _is_quiet_hours_beijing_now()
    if quiet_now:
        print("提示: 北京静默时段（20:00–次日 6:00），不执行任何推送（拉取与入库已完成）。")

    # 2. 实时两类：轮巡 run，或 --push-all-now 全量（静默时段不推）
    if not quiet_now and (mode == "poll" or force_push_all):
        realtime_items = _collect_realtime_to_push(conn, new_realtime, include_db_backlog=force_push_all)
        now_bj = _now_beijing()
        realtime_items = [
            x
            for x in realtime_items
            if _realtime_article_eligible_now(_parse_published_to_beijing(x.get("published_str")), now_bj)
        ]
        if realtime_items:
            by_cat = {}
            for item in realtime_items:
                by_cat.setdefault(item["category"], []).append(item)
            send_wechat_per_category(WECHAT_WEBHOOK, by_cat)
            for item in realtime_items:
                conn.execute(
                    "INSERT OR IGNORE INTO pushed (link, pushed_at, push_type) VALUES (?, ?, ?)",
                    (item["link"], datetime.now().isoformat(), "realtime"),
                )
            conn.commit()
            tag = "全量实时" if force_push_all else "轮巡实时"
            print(f"{tag}推送 {len(realtime_items)} 条")
    elif new_realtime and mode != "poll" and not force_push_all:
        if quiet_now:
            print(f"提示: 有 {len(new_realtime)} 条实时类文章已入库，当前为静默时段，将在次日 6:00 后轮巡补推。")
        else:
            print(f"提示: 有 {len(new_realtime)} 条实时类文章已入库，当前非轮巡时段，将在 6:00–20:00 每两小时轮巡中推送")

    # 3. 定时四类：9:30（含缺口窗）/ 15:30（仅今天）或强制汇总；静默时段不推
    slot = _get_scheduled_slot()
    if (
        not quiet_now
        and (force_push_all or (mode == "scheduled" and (slot is not None or force_timed_digest)))
    ):
        ph = ",".join("?" * len(TIMED_PUSH_CATEGORIES))
        cur = conn.execute(
            f"""SELECT link, title, published_str, category, author, source_url FROM articles
               WHERE category IN ({ph}) AND link NOT IN (SELECT link FROM pushed)""",
            tuple(TIMED_PUSH_CATEGORIES),
        )
        rows = cur.fetchall()
        # --push-now --with-yesterday：临时把定时四类扩到「今天或昨天」（北京），不沿用 9:30 时间窗
        if force_timed_digest and include_yesterday:
            rows = [
                (l, t, ps, c, a, su)
                for l, t, ps, c, a, su in rows
                if _is_today_or_yesterday_beijing(_parse_published_to_beijing(ps))
            ]
        elif slot == (9, 30):
            rows = [(l, t, ps, c, a, su) for l, t, ps, c, a, su in rows if _is_in_930_window(_parse_published_to_beijing(ps))]
        elif slot == (15, 30):
            rows = [(l, t, ps, c, a, su) for l, t, ps, c, a, su in rows if _is_today_beijing(_parse_published_to_beijing(ps))]
        elif force_timed_digest:
            rows = [(l, t, ps, c, a, su) for l, t, ps, c, a, su in rows if _is_today_beijing(_parse_published_to_beijing(ps))]
        if rows:
            by_cat = {}
            for link, title, published_str, category, author, source_url in rows:
                su = source_url or ""
                st = _source_type_for_feed_url(su)
                by_cat.setdefault(category, []).append({
                    "title": title,
                    "published_str": published_str,
                    "link": link,
                    "author": author or "",
                    "source_url": su,
                    "source_type": st,
                })
            send_wechat_per_category(WECHAT_WEBHOOK, by_cat)
            now = datetime.now().isoformat()
            for link, *_ in rows:
                conn.execute(
                    "INSERT OR IGNORE INTO pushed (link, pushed_at, push_type) VALUES (?, ?, ?)",
                    (link, now, "scheduled"),
                )
            conn.commit()
            print(f"定时推送 {len(rows)} 条")
        elif force_timed_digest:
            hint = "（含昨天）" if include_yesterday else ""
            print(f"定时推送: 0 条{hint}（无待推送文章，可能已推送过）")
    elif mode is None and not new_realtime and not quiet_now:
        print("提示: 当前不在轮巡时段(6:00–20:00 每两小时整点) 或 定时档(9:30/15:30)；实时两类在轮巡；其余四类在定时。使用 python main.py --push-now 仅推四类，或 python main.py --push-all-now 全量推送。")

    conn.close()
    print("完成")


def test_llm():
    """测试 LLM API 是否可用（与分类相同：多模型则按顺序尝试）"""
    try:
        from llm_utils import call_llm_with_fallback, get_llm_providers
    except ImportError:
        print("无法加载 llm_utils")
        return
    providers = get_llm_providers()
    if not providers:
        print("未配置 LLM：需要 LLM_API_KEY + LLM_BASE_URL，以及 LLM_MODEL 或 LLM_MODELS / LLM_MODELS_JSON")
        return
    names = [p[2] for p in providers]
    print(f"测试 LLM 连接（按顺序最多 {len(providers)} 个）: {names}")
    try:
        content = call_llm_with_fallback(
            [{"role": "user", "content": "只回复：测试成功"}],
            max_tokens=20,
        )
        if content:
            print(f"✓ 成功！API 返回: {content[:80]}...")
        else:
            print("✗ 全部模型均未返回内容")
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP 错误: {e}")
        if e.response is not None:
            try:
                err = e.response.json()
                print(f"  详情: {err}")
            except Exception:
                print(f"  响应: {e.response.text[:200]}")
        print("  可能原因：API Key 无效、未充值、模型名错误")
    except Exception as e:
        print(f"✗ 调用失败: {e}")


# --test-ioc 默认用国家网络安全通报中心文章测试（可传自定义 URL）
TEST_IOC_URL = "https://mp.weixin.qq.com/s/8Xg-BO7wswu8u95XAnkCCQ"
TEST_IOC_TITLE = "OpenClaw安全风险预警"


def test_ioc():
    """用历史文章测试 IOC 提取。无有效 IOC 时按基础格式推送。"""
    idx = sys.argv.index("--test-ioc") + 1 if "--test-ioc" in sys.argv else -1
    url = sys.argv[idx] if idx > 0 and idx < len(sys.argv) and not sys.argv[idx].startswith("-") else TEST_IOC_URL
    title = TEST_IOC_TITLE
    item = {"title": title, "link": url, "published_str": "2026-03-13 18:38", "author": IOC_ALERT_AUTHOR}
    print(f"测试 IOC 提取: {url}")
    content = _build_ioc_push_content(item)
    if content:
        print("--- 有有效 IOC，特殊格式 ---")
        print(content)
        send_wechat(WECHAT_WEBHOOK, content, use_markdown=False)
        print("✓ 已推送（特殊格式）")
    else:
        print("--- 无有效 IOC，按基础格式 ---")
        by_cat = {"监管机构预警": [item]}
        send_wechat_per_category(WECHAT_WEBHOOK, by_cat)
        print("✓ 已推送（基础格式）")


if __name__ == "__main__":
    if "--test-llm" in sys.argv:
        test_llm()
    elif "--test-ioc" in sys.argv:
        test_ioc()
    else:
        main()
