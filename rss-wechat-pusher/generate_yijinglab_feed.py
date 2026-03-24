#!/usr/bin/env python3
"""
抓取 https://www.yijinglab.com/industry/ 列表，按列表上的日期判断「今日」网络安全日报；
进入日报详情，把每条「序号、标题 + 外链 + 摘要」拆成独立 RSS item，供 main.py 走原有分类/推送逻辑。

规则（与产品一致）：
  - 列表图1：用行内日期（或标题里的年月日）判断是否为北京「今天」的日报；非今日则跳过（FORCE 时改为取列表第一条日报）。
  - 详情图2：用「发表于: YYYY-MM-DD HH:MM」作为每条 item 的统一 pubDate。
  - 网站来源固定为 www.yijinglab.com；item.link 仍为外链原文（便于点击）；RSS 标题去掉「1、2、」类序号，仅保留标题正文。

环境变量：
  YIJINGLAB_FEED_DISABLE=1
  YIJINGLAB_FEED_FORCE=1   — 不校验「今日」、不校验 9:30 窗口（调试用）
  YIJINGLAB_LIST_URL       — 默认 https://www.yijinglab.com/industry/
  YIJINGLAB_MAX_ITEMS      — 最多条目数，0 表示不截断
"""

from __future__ import annotations

import html
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

LIST_URL = (os.getenv("YIJINGLAB_LIST_URL") or "https://www.yijinglab.com/industry/").strip()
SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / "generated_feeds"
OUT_FILE = OUT_DIR / "yijinglab.xml"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
SOURCE_LABEL = "www.yijinglab.com"


def _db_path() -> Path:
    if os.getenv("CI") and os.getenv("GITHUB_WORKSPACE"):
        return Path(os.getenv("GITHUB_WORKSPACE")) / "rss-wechat-pusher" / "rss_push.db"
    p = Path(os.path.expanduser("~/.rss-wechat-pusher"))
    p.mkdir(parents=True, exist_ok=True)
    return p / "rss_push.db"


def _headers(url: str) -> dict:
    p = urlparse(url)
    ref = f"{p.scheme}://{p.netloc}/" if p.scheme and p.netloc else "https://www.yijinglab.com/"
    return {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
        "Referer": ref,
        "Cache-Control": "no-cache",
    }


def _beijing_now():
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("Asia/Shanghai"))


def _should_fetch(conn: sqlite3.Connection, now: datetime) -> tuple[bool, str]:
    if os.getenv("YIJINGLAB_FEED_DISABLE") == "1":
        return False, "YIJINGLAB_FEED_DISABLE=1"
    if os.getenv("YIJINGLAB_FEED_FORCE") == "1":
        return True, "force"

    if now.hour >= 15:
        return False, "下午档（15:30 定时）不抓取蚁景日报"
    if now.hour < 9 or (now.hour == 9 and now.minute < 30):
        return False, "早于北京 9:30，不抓取"

    conn.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
    today = now.strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT v FROM meta WHERE k = ?", ("yijinglab_feed_date",)
    ).fetchone()
    if row and row[0] == today:
        return False, f"今日已抓取过 ({today})"
    return True, "ok"


def _date_from_title_chinese(text: str) -> str | None:
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def _row_date_yyyy_mm_dd(a_tag) -> str | None:
    """从列表行/父级文本中取 YYYY-MM-DD（图1 右侧时间）。"""
    p = a_tag
    for _ in range(14):
        if p is None:
            break
        blob = p.get_text(" ", strip=True)
        m = re.search(r"(\d{4}-\d{2}-\d{2})\s+\d{1,2}:\d{2}", blob)
        if m:
            return m.group(1)
        p = p.parent
    return None


def _find_daily_for_today(
    html_bytes: bytes, base: str, today_str: str, force: bool
) -> tuple[str | None, str | None, str | None]:
    """
    返回 (detail_url, list_link_text, reason)。
    reason: 'today' | 'force_first' | None
    """
    soup = BeautifulSoup(html_bytes, "html.parser")
    first_url: str | None = None
    first_text: str | None = None
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        text = (a.get_text() or "").strip()
        if "网络安全日报" not in text:
            continue
        if not re.search(r"/industry/\d{10,}", href):
            continue
        full = urljoin(base, href)
        if first_url is None:
            first_url, first_text = full, text
        d = _row_date_yyyy_mm_dd(a) or _date_from_title_chinese(text)
        if d == today_str:
            return full, text, "today"
    if force and first_url:
        return first_url, first_text, "force_first"
    return None, None, None


def _article_main_soup(html_bytes: bytes) -> BeautifulSoup:
    soup = BeautifulSoup(html_bytes, "html.parser")
    for t in soup(["script", "style", "nav", "header", "footer", "aside"]):
        t.decompose()
    for sel in ("article", ".article-content", ".content", "main", "[class*='detail']"):
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 80:
            return el
    return soup


def _clean_url(u: str) -> str:
    u = (u or "").strip()
    while u and u[-1] in ").,，。；;】」』\"'":
        u = u[:-1]
    return u


def _parse_digest_items(text: str) -> list[dict]:
    items: list[dict] = []
    pat = re.compile(r"(?m)^(\d+)、([^\n]+?)\s*\n\s*(https?://\S+)")
    for m in pat.finditer(text):
        order, title_rest, raw_url = m.group(1), m.group(2).strip(), m.group(3)
        url = _clean_url(raw_url)
        if "yijinglab.com" in url:
            continue
        # 标题不要「1、2、」序号，RSS title 只用正文标题（页面若自带序号由源站决定，此处不重复加）
        title_clean = re.sub(r"^\d+[、,]\s*", "", title_rest).strip() or title_rest.strip()
        tail = text[m.end() :]
        nxt = re.search(r"(?m)^\d+、", tail)
        summary = (tail[: nxt.start()] if nxt else tail).strip()
        summary = re.sub(r"\n{3,}", "\n\n", summary)[:4000]
        items.append({"title": title_clean, "url": url, "order": order, "summary": summary})
    return items


def _parse_published_detail(html_bytes: bytes) -> datetime | None:
    """图2「发表于: 2026-03-24 09:04」→ 北京时区 datetime。"""
    soup = BeautifulSoup(html_bytes, "html.parser")
    text = soup.get_text()
    m = re.search(
        r"发表于\s*[：:]\s*(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})",
        text,
    )
    if not m:
        return None
    from zoneinfo import ZoneInfo

    s = f"{m.group(1)} {m.group(2)}"
    dt = datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    return dt


def _pub_rfc_from_detail_or_url(detail_dt: datetime | None, article_url: str) -> str:
    if detail_dt is not None:
        return format_datetime(detail_dt)
    m = re.search(r"/industry/(\d+)", article_url)
    if not m or len(m.group(1)) < 14:
        return format_datetime(datetime.now(timezone.utc))
    aid = m.group(1)
    y, mo, d = int(aid[:4]), int(aid[4:6]), int(aid[6:8])
    h, mi, s = int(aid[8:10]), int(aid[10:12]), int(aid[12:14])
    from zoneinfo import ZoneInfo

    dt = datetime(y, mo, d, h, mi, s, tzinfo=ZoneInfo("Asia/Shanghai"))
    return format_datetime(dt)


def _fix_cdata(s: str) -> str:
    return s.replace("]]>", "]]]]><![CDATA[>")


def _build_rss_multi(
    daily_page_url: str,
    items: list[dict],
    fallback_pub_rfc: str,
) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        "<channel>",
        "<title>蚁景网安行业资讯 - 网络安全日报</title>",
        "<link>https://www.yijinglab.com/industry/</link>",
        "<description>蚁景日报拆条；网站来源统一为 www.yijinglab.com；条目 link 为原文外链</description>",
        "<language>zh-cn</language>",
        f"<!-- 日报页: {html.escape(daily_page_url)} -->",
    ]
    for it in items:
        t = html.escape(it["title"])
        link = html.escape(it["link"])
        guid = html.escape(it["guid"])
        pub = it.get("pub_rfc") or fallback_pub_rfc
        desc = _fix_cdata(it["description"])
        parts.extend(
            [
                "<item>",
                f"<title>{t}</title>",
                f"<link>{link}</link>",
                f'<guid isPermaLink="false">{guid}</guid>',
                f"<pubDate>{pub}</pubDate>",
                f"<description><![CDATA[{desc}]]></description>",
                "</item>",
            ]
        )
    parts.extend(["</channel>", "</rss>"])
    return "\n".join(parts) + "\n"


def _build_rss_single(title: str, link: str, description: str, pub_rfc: str) -> str:
    title_x = html.escape(title)
    link_x = html.escape(link)
    desc = _fix_cdata(description)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>蚁景网安行业资讯 - 网络安全日报</title>
<link>https://www.yijinglab.com/industry/</link>
<description>蚁景日报</description>
<language>zh-cn</language>
<item>
<title>{title_x}</title>
<link>{link_x}</link>
<guid isPermaLink="true">{link_x}</guid>
<pubDate>{pub_rfc}</pubDate>
<description><![CDATA[{desc}]]></description>
</item>
</channel>
</rss>
"""


def main() -> int:
    now = _beijing_now()
    today_str = now.strftime("%Y-%m-%d")
    force = os.getenv("YIJINGLAB_FEED_FORCE") == "1"
    dbp = _db_path()
    dbp.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(dbp))

    try:
        ok, reason = _should_fetch(conn, now)
        if not ok:
            print(f"[yijinglab] 跳过: {reason}", flush=True)
            return 0

        session = requests.Session()
        list_url = LIST_URL.rstrip("/") + "/" if not LIST_URL.endswith("/") else LIST_URL
        r = session.get(list_url, headers=_headers(list_url), timeout=25)
        r.raise_for_status()

        article_url, list_title, pick_reason = _find_daily_for_today(
            r.content or b"", list_url, today_str, force
        )
        if not article_url:
            print(
                f"[yijinglab] 今日（{today_str}）列表中未找到「网络安全日报」条目，跳过",
                flush=True,
            )
            return 0
        if pick_reason == "force_first":
            print("[yijinglab] FORCE：使用列表首条日报（非今日校验）", flush=True)
        else:
            print(f"[yijinglab] 已匹配今日日报: {article_url}", flush=True)

        r2 = session.get(article_url, headers=_headers(article_url), timeout=25)
        r2.raise_for_status()
        detail_dt = _parse_published_detail(r2.content or b"")
        main_el = _article_main_soup(r2.content or b"")
        body_text = main_el.get_text("\n", strip=False)
        digest_items = _parse_digest_items(body_text)

        max_items = int(os.getenv("YIJINGLAB_MAX_ITEMS", "0"))
        if max_items > 0 and len(digest_items) > max_items:
            digest_items = digest_items[:max_items]
            print(f"[yijinglab] 已按 YIJINGLAB_MAX_ITEMS={max_items} 截断", flush=True)

        fallback_pub = _pub_rfc_from_detail_or_url(detail_dt, article_url)
        pub_rfc_all = fallback_pub

        if digest_items:
            rss_items: list[dict] = []
            for row in digest_items:
                guid = f"{article_url}#item{row['order']}"
                desc = (
                    f"网站来源：{SOURCE_LABEL}\n"
                    f"（详情页发表于：{detail_dt.strftime('%Y-%m-%d %H:%M') if detail_dt else '见 pubDate'}）\n\n"
                    f"{row['summary']}"
                )
                rss_items.append(
                    {
                        "title": row["title"],
                        "link": row["url"],
                        "guid": guid,
                        "pub_rfc": pub_rfc_all,
                        "description": desc,
                    }
                )
                print(f"[yijinglab] 条目 {row['order']}: {row['title'][:48]}...", flush=True)
            xml = _build_rss_multi(article_url, rss_items, fallback_pub)
        else:
            body = body_text.strip() or "(正文解析为空)"
            xml = _build_rss_single(
                list_title or "网络安全日报", article_url, body, fallback_pub
            )
            print("[yijinglab] 未解析到序号+外链结构，回退单条全文", flush=True)

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text(xml, encoding="utf-8")
        print(
            f"[yijinglab] 已生成 {OUT_FILE.name}，共 {len(digest_items) if digest_items else 1} 条",
            flush=True,
        )

        conn.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
        conn.execute(
            "INSERT OR REPLACE INTO meta (k, v) VALUES (?, ?)",
            ("yijinglab_feed_date", now.strftime("%Y-%m-%d")),
        )
        conn.commit()
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
