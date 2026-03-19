#!/usr/bin/env python3
"""
RSS 推送到企业微信机器人
- 6 类：监管机构预警、漏洞信息、重大安全事件、网安新闻资讯、网安赛事资讯、其他资讯
- 1）实时：监管机构预警、重大安全事件→仅推送当天（去重）
- 2）15:30 北京：全部 6 类→仅推送当天
- 3）9:30 北京：全部 6 类→仅推送前一天 15:30 至当天 9:30
- 4）国家网络安全通报中心+重点防范：有 IOC 用特殊格式，无则按 1
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
        WEWE_RSS_URL,
        SCHEDULED_PUSH_TIMES,
        SCHEDULED_WINDOW_MINUTES,
    )
    from classifier import (
        classify,
        REALTIME_CATEGORIES,
        SCHEDULED_CATEGORIES,
    )
except ImportError:
    import json
    import os
    webhook = os.getenv("WECHAT_WEBHOOK")
    feeds_json = os.getenv("FEEDS_JSON")
    if webhook and feeds_json:
        WECHAT_WEBHOOK = webhook
        FEEDS = [(u, t) for u, t in json.loads(feeds_json)]
        WEWE_RSS_URL = os.getenv("WEWE_RSS_URL", "")
        SCHEDULED_PUSH_TIMES = [(9, 30), (15, 30)]
        SCHEDULED_WINDOW_MINUTES = 5
        from classifier import classify, REALTIME_CATEGORIES, SCHEDULED_CATEGORIES
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
    """当前若在定时窗口内，返回 (9,30) 或 (15,30)，否则 None"""
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
    """格式化为 YYYY-MM-DD HH:mm"""
    dt = parse_date(entry)
    if dt:
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


def fetch_feed(url):
    """拉取 RSS"""
    try:
        d = feedparser.parse(
            url,
            request_headers={"User-Agent": "RSS-WeChat-Pusher/2.0"},
        )
        return d.entries if d.entries else []
    except Exception as e:
        print(f"拉取失败 {url}: {e}")
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
    link = item.get("link") or ""
    time_str = item.get("published_str") or ""
    text = _fetch_article_text(link)
    pairs = _extract_iocs(text)
    if not pairs:
        return None  # 无有效 IOC，用基础格式
    lines = [
        "【信息类型】监管机构预警",
        f"【标题】{title}",
        f"【时间】{time_str}",
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


def _translate_to_chinese(title):
    """将纯英文标题翻译为中文，支持多模型自动切换"""
    if not title or title in _translate_cache:
        return _translate_cache.get(title, title)
    from llm_utils import call_llm_with_fallback, get_llm_providers
    if not get_llm_providers():
        return title
    result = call_llm_with_fallback(
        [{"role": "user", "content": f"将以下英文标题翻译成中文，只返回翻译结果，不要其他内容：\n{title}"}],
        max_tokens=100,
    )
    if result:
        _translate_cache[title] = result
        return result
    return title


def _build_single_category_content(category, items):
    """构建单个分类的 Markdown 内容（使用 comment 灰色字体，视觉更紧凑）"""
    try:
        from config import TRANSLATE_ENABLED
    except ImportError:
        TRANSLATE_ENABLED = False
    emoji = CATEGORY_STYLE.get(category, "📌")
    lines = [f"### {emoji} {category}", ""]
    for item in items:
        raw_title = (item["title"] or "")[:80] + ("..." if len(item["title"] or "") > 80 else "")
        translated = False
        if TRANSLATE_ENABLED and raw_title and not _has_chinese(raw_title):
            title = _translate_to_chinese(raw_title) or raw_title
            translated = True
        else:
            title = raw_title
        if translated:
            title = f"{title}（译）"
        link = item["link"] or ""
        time_str = item.get("published_str") or ""
        title_safe = (title or "").replace("]", "］").replace("[", "［")
        lines.append(f"[{title_safe}]({link})")
        lines.append(f"> {time_str}")
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
    all_new = []  # [(link, title, summary, category, author, feed_url, published_str), ...]

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
                    all_new.append((link, title, summary, category, author, feed_url, published_str))
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
    for link, title, summary, category, author, feed_url, published_str in all_new:
        if link in known:
            continue
        conn.execute(
            """INSERT OR IGNORE INTO articles
               (link, title, summary, category, author, source_url, published_str, first_seen_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (link, title, summary, category, author, feed_url, published_str, now_str),
        )
        known.add(link)
        if category in REALTIME_CATEGORIES and link not in pushed:
            dt_bj = _parse_published_to_beijing(published_str)
            if _is_today_beijing(dt_bj):
                new_realtime.append({
                    "title": title, "published_str": published_str, "link": link, "category": category, "author": author or ""
                })

    conn.commit()

    # 2. 实时推送（每个类型一条消息）
    if new_realtime:
        by_cat = {}
        for item in new_realtime:
            by_cat.setdefault(item["category"], []).append(item)
        send_wechat_per_category(WECHAT_WEBHOOK, by_cat)
        for item in new_realtime:
            conn.execute(
                "INSERT OR IGNORE INTO pushed (link, pushed_at, push_type) VALUES (?, ?, ?)",
                (item["link"], datetime.now().isoformat(), "realtime"),
            )
        conn.commit()
        print(f"实时推送 {len(new_realtime)} 条")

    # 3. 定时推送（9:30、15:30 北京，全部 6 类，与实时去重）
    # 轮巡时仅推监管预警+重大事件；定时类(漏洞/新闻/赛事/其他)仅在 slot 内或手动触发时推
    slot = _get_scheduled_slot()
    force_now = "--push-now" in sys.argv or os.getenv("PUSH_SCHEDULED_NOW") == "1"
    if slot is not None or force_now:
        ph = ",".join("?" * len(SCHEDULED_CATEGORIES))
        cur = conn.execute(
            f"""SELECT link, title, published_str, category, author FROM articles
               WHERE category IN ({ph}) AND link NOT IN (SELECT link FROM pushed)""",
            tuple(SCHEDULED_CATEGORIES),
        )
        rows = cur.fetchall()
        if slot == (15, 30):
            rows = [(l, t, ps, c, a) for l, t, ps, c, a in rows if _is_today_beijing(_parse_published_to_beijing(ps))]
        elif slot == (9, 30):
            rows = [(l, t, ps, c, a) for l, t, ps, c, a in rows if _is_in_930_window(_parse_published_to_beijing(ps))]
        elif "--push-now" in sys.argv or os.getenv("PUSH_SCHEDULED_NOW") == "1":
            rows = [(l, t, ps, c, a) for l, t, ps, c, a in rows if _is_today_beijing(_parse_published_to_beijing(ps))]
        if rows:
            by_cat = {}
            for link, title, published_str, category, author in rows:
                by_cat.setdefault(category, []).append({
                    "title": title,
                    "published_str": published_str,
                    "link": link,
                    "author": author or "",
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
        elif "--push-now" in sys.argv:
            print("定时推送: 0 条（无待推送文章，可能已推送过）")
    elif not new_realtime:
        print("提示: 定时类文章仅在 9:30、15:30 左右推送，或使用 python main.py --push-now 立即推送")

    conn.close()
    print("完成")


def test_llm():
    """测试 LLM API 是否可用"""
    try:
        from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
    except ImportError:
        print("无法加载 config，请检查 config.py")
        return
    if not LLM_API_KEY:
        print("LLM_API_KEY 未配置，请在 config.py 中填写")
        return
    print(f"测试 LLM 连接: {LLM_BASE_URL} / {LLM_MODEL}")
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": "回复：测试成功"}],
        "max_tokens": 20,
    }
    try:
        r = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        content = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        print(f"✓ 成功！API 返回: {content[:50]}...")
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
