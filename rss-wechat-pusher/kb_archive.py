"""
把 SQLite 中的历史文章归档到阿里云 OSS，形成可检索「知识库」。

结构：
  kb/days/YYYY-MM-DD.json   — 当日全部条目
  kb/days/index.json        — 已有日期列表
  kb/catalog.json           — 轻量目录（近 N 条，供搜索页）
  kb/search.html            — 浏览器内关键词检索
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from oss_utils import (
    kb_prefix,
    oss_enabled,
    upload_html,
    upload_json,
)

_CATALOG_LIMIT = int(os.getenv("KB_CATALOG_LIMIT", "3000"))


def _beijing_day_from_published(published_str: str, fallback: str = "") -> str:
    s = (published_str or "").strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        # published_str 多为 UTC；按日期字符串前 10 位近似归档（与现网一致）
        return s[:10]
    return fallback or datetime.utcnow().strftime("%Y-%m-%d")


def _parse_json_list(raw: str) -> List[Any]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _row_to_item(row) -> Dict[str, Any]:
    (
        link,
        title,
        summary,
        category,
        incident_priority,
        author,
        source_url,
        published_str,
        first_seen_at,
        title_zh,
        summary_zh,
        summary_url,
        tags_json,
        cves_json,
        iocs_json,
        entities_json,
    ) = row
    day = _beijing_day_from_published(published_str or "", (first_seen_at or "")[:10])
    tags = [str(x) for x in _parse_json_list(tags_json or "") if str(x).strip()]
    cves = [str(x).upper() for x in _parse_json_list(cves_json or "") if str(x).strip()]
    display_title = (title_zh or "").strip() or (title or "")
    display_summary = (summary_zh or "").strip() or (summary or "")
    return {
        "link": link or "",
        "title": title or "",
        "title_zh": (title_zh or "").strip(),
        "display_title": display_title,
        "summary": (summary or "")[:2000],
        "summary_zh": (summary_zh or "")[:4000],
        "display_summary": display_summary[:2000],
        "summary_url": (summary_url or "").strip(),
        "tags": tags,
        "cves": cves,
        "iocs": _parse_json_list(iocs_json or ""),
        "entities": _parse_json_list(entities_json or ""),
        "category": category or "",
        "incident_priority": incident_priority or "",
        "author": author or "",
        "source_url": source_url or "",
        "published_str": published_str or "",
        "first_seen_at": first_seen_at or "",
        "day": day,
    }


def load_articles_from_db(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    # 兼容尚未迁移的旧库
    cur = conn.execute("PRAGMA table_info(articles)")
    cols = {row[1] for row in cur.fetchall()}
    extra = [
        "title_zh",
        "summary_zh",
        "summary_url",
        "tags_json",
        "cves_json",
        "iocs_json",
        "entities_json",
    ]
    select_extra = ", ".join(
        (c if c in cols else f"NULL AS {c}") for c in extra
    )
    cur = conn.execute(
        f"""SELECT link, title, summary, category, incident_priority, author,
                  source_url, published_str, first_seen_at, {select_extra}
           FROM articles ORDER BY published_str DESC, first_seen_at DESC"""
    )
    return [_row_to_item(r) for r in cur.fetchall()]


def _group_by_day(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        by.setdefault(it["day"] or "unknown", []).append(it)
    return by


def _html_esc(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "")


_CAT_SLUGS = {
    "监管机构预警": "regulatory",
    "重大安全事件": "incident",
    "漏洞信息": "vuln",
    "网安新闻资讯": "news",
    "网安赛事资讯": "contest",
    "AI行业资讯": "ai-industry",
    "AI与信息安全技术": "ai-security",
    "其他资讯": "other",
    "未分类": "uncat",
}


def _cat_file_slug(cat: str) -> str:
    """分类页文件名：仅 ASCII，避免 OSS 中文路径 403。"""
    import hashlib

    raw = (cat or "未分类").strip() or "未分类"
    if raw in _CAT_SLUGS:
        return _CAT_SLUGS[raw]
    return "c-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def _catalog_to_light(catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """统一成卡片用轻量字段（含标签/CVE/双链接，便于网页内查找）。"""
    light: List[Dict[str, Any]] = []
    for it in catalog:
        title = (it.get("display_title") or it.get("title_zh") or it.get("title") or "")[:200]
        summary = _strip_tags(
            it.get("display_summary") or it.get("summary_zh") or it.get("summary") or ""
        )[:220]
        tags = it.get("tags") or []
        if isinstance(tags, str):
            tags = _parse_json_list(tags)
        cves = it.get("cves") or []
        if isinstance(cves, str):
            cves = _parse_json_list(cves)
        tags = [str(x) for x in tags if str(x).strip()][:8]
        cves = [str(x).upper() for x in cves if str(x).strip()][:8]
        light.append(
            {
                "t": title,
                "s": summary,
                "c": (it.get("category") or "").strip() or "未分类",
                "a": (it.get("author") or "")[:40],
                "l": it.get("link") or "",
                "su": (it.get("summary_url") or "").strip(),
                "d": it.get("day") or "",
                "p": (it.get("published_str") or "")[:16],
                "tags": tags,
                "cves": cves,
                # 供浏览器「在网页中查找」命中
                "kw": " ".join([title, summary] + tags + cves),
            }
        )
    return light


def _render_cards(items: List[Dict[str, Any]], limit: int = 500) -> str:
    cards = []
    for it in items[:limit]:
        cat = it["c"] or "未分类"
        tag_html = "".join(
            f'<span class="tag">{_html_esc(t)}</span>' for t in (it.get("tags") or [])
        )
        cve_html = "".join(
            f'<span class="cve">{_html_esc(c)}</span>' for c in (it.get("cves") or [])
        )
        badges = ""
        if tag_html or cve_html:
            badges = f'<div class="tags">{tag_html}{cve_html}</div>'
        links = (
            f'<a class="link" href="{_html_esc(it["l"])}" target="_blank" rel="noopener">原文链接</a>'
        )
        if it.get("su"):
            links += (
                f'<a class="link" href="{_html_esc(it["su"])}" target="_blank" rel="noopener">中文摘要</a>'
            )
        cards.append(
            f'<div class="card" data-cat="{_html_esc(cat)}">'
            f'<h3><span class="cat">{_html_esc(cat)}</span>{_html_esc(it["t"])}</h3>'
            f'<div class="meta">{_html_esc(it["d"])} · {_html_esc(it["a"])} · {_html_esc(it["p"])}</div>'
            f"{badges}"
            f'<p class="sum">{_html_esc(it["s"])}</p>'
            f'<div class="links">{links}</div>'
            f'<span style="display:none">{_html_esc(it.get("kw") or "")}</span>'
            f"</div>"
        )
    return "\n".join(cards) or '<div class="empty">暂无归档</div>'


def _page_shell(
    title: str,
    sub: str,
    nav_html: str,
    body_html: str,
    *,
    filter_css: str = "",
    filter_controls: str = "",
) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_html_esc(title)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;
margin:0;padding:20px;background:#f6f7f9;color:#1a1a1a;max-width:920px;margin-inline:auto}}
h1{{font-size:1.35rem;margin:0 0 8px}}
.sub{{color:#666;font-size:.9rem;margin-bottom:12px;line-height:1.5}}
.nav{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}}
.nav a,.nav label{{display:inline-block;padding:8px 12px;border-radius:6px;background:#fff;
border:1px solid #ddd;color:#1a1a1a;text-decoration:none;font-size:.92rem}}
.nav a.on,.nav label.on{{background:#1a6fb5;color:#fff;border-color:#1a6fb5}}
/* 纯 CSS 分类筛选：radio + 兄弟选择器，不依赖 JS（适配企微） */
input[name=f]{{position:absolute;opacity:0;width:0;height:0}}
.filters{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}}
.filters label{{display:inline-block;padding:8px 12px;border-radius:6px;background:#fff;
border:1px solid #ddd;font-size:.92rem;cursor:pointer;-webkit-tap-highlight-color:transparent}}
{filter_css}
.card{{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:12px 14px;margin:0 0 10px}}
.card h3{{font-size:1rem;margin:0 0 6px;line-height:1.4}}
.meta{{font-size:.8rem;color:#666}}
.sum{{font-size:.9rem;margin:8px 0 6px;white-space:pre-wrap;color:#333}}
.cat{{display:inline-block;background:#eef5fb;color:#1a6fb5;padding:1px 6px;border-radius:4px;margin-right:6px}}
.tags{{margin:6px 0 4px;line-height:1.6}}
.tag,.cve{{display:inline-block;font-size:.75rem;padding:1px 6px;border-radius:4px;margin:0 4px 4px 0}}
.tag{{background:#f0f0f0;color:#444}}
.cve{{background:#fff4e5;color:#a15c00}}
.links{{margin-top:6px}}
a.link{{color:#06c;word-break:break-all;margin-right:12px}}
.empty{{color:#888;padding:24px 0}}
.tip{{font-size:.85rem;color:#888;margin:0 0 14px;line-height:1.45}}
.searchbox{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px;align-items:center}}
.searchbox input{{flex:1;min-width:160px;font:inherit;padding:8px 10px;border:1px solid #ccc;border-radius:6px}}
.searchbox button{{font:inherit;padding:8px 12px;border:1px solid #1a6fb5;background:#1a6fb5;color:#fff;border-radius:6px}}
</style>
</head>
<body>
<h1>{_html_esc(title)}</h1>
<p class="sub">{sub}</p>
{nav_html}
{filter_controls}
{body_html}
</body>
</html>
"""


def _build_search_html(catalog: List[Dict[str, Any]]) -> str:
    """
    主检索页：列表服务端渲染；分类用「链接跳转分类页」+「纯 CSS radio 筛选」，
    不依赖企微执行 JS。关键词用浏览器原生查找（并提供可选 JS 增强）。
    """
    light = _catalog_to_light(catalog)

    cats = sorted({x["c"] for x in light})
    # 纯 CSS radio：点分类即隐藏其它卡片（企微无 JS 也能用）
    radio_inputs = ['<input type="radio" name="f" id="f-all" checked>']
    labels = ['<label for="f-all">全部</label>']
    css_parts = [
        "#f-all:checked ~ .filters label[for=f-all]{background:#1a6fb5;color:#fff;border-color:#1a6fb5}"
    ]
    for i, c in enumerate(cats):
        fid = f"f-{i}"
        radio_inputs.append(f'<input type="radio" name="f" id="{fid}">')
        labels.append(f'<label for="{fid}">{_html_esc(c)}</label>')
        css_parts.append(
            f"#{fid}:checked ~ .filters label[for={fid}]{{background:#1a6fb5;color:#fff;border-color:#1a6fb5}}"
        )
        css_parts.append(
            f'#{fid}:checked ~ #list .card:not([data-cat="{_html_esc(c)}"]){{display:none!important}}'
        )
    filter_css = "\n".join(css_parts)

    # 顶栏：整页跳转分类专页（比 radio 更稳）
    nav_links = ['<a class="on" href="search.html">全部</a>']
    for c in cats:
        nav_links.append(f'<a href="c/{_cat_file_slug(c)}.html">{_html_esc(c)}</a>')
    nav_html = '<div class="nav">' + "".join(nav_links) + "</div>"

    filter_controls = (
        "".join(radio_inputs)
        + '<div class="filters">'
        + "".join(labels)
        + "</div>"
        + '<p class="tip">推荐：点上方蓝色链接进入「分类专页」。'
        + "本页下方标签也可即时筛选。"
        + "搜关键词/CVE：用系统「在网页中查找」（标题、摘要、标签、CVE 均可命中）。</p>"
    )

    body = f'<div id="list">\n{_render_cards(light, 500)}\n</div>'
    return _page_shell(
        "网安情报知识库",
        f"已归档 {len(light)} 条。分类请点链接或标签（不依赖脚本）。",
        nav_html,
        body,
        filter_css=filter_css,
        filter_controls=filter_controls,
    )


def _build_category_html(cat: str, items: List[Dict[str, Any]], all_cats: List[str]) -> str:
    nav_links = ['<a href="../search.html">全部</a>']
    for c in all_cats:
        slug = _cat_file_slug(c)
        cls = ' class="on"' if c == cat else ""
        nav_links.append(f'<a{cls} href="{slug}.html">{_html_esc(c)}</a>')
    nav_html = '<div class="nav">' + "".join(nav_links) + "</div>"
    body = f'<p class="tip">当前分类：{_html_esc(cat)}（{len(items)} 条）</p><div id="list">{_render_cards(items, 800)}</div>'
    return _page_shell(
        f"{cat} · 网安情报知识库",
        f"分类专页，共 {len(items)} 条。点「全部」返回。",
        nav_html,
        body,
    )


def ensure_search_page(catalog: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    if not oss_enabled():
        return None
    catalog = catalog or []
    light = _catalog_to_light(catalog)
    prefix = kb_prefix()
    # 主页
    url = upload_html(f"{prefix}search.html", _build_search_html(catalog))
    # 分类专页（点分类即整页跳转，最稳）
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for it in light:
        by_cat.setdefault(it["c"], []).append(it)
    cats = sorted(by_cat.keys())
    for c, rows in by_cat.items():
        slug = _cat_file_slug(c)
        upload_html(f"{prefix}c/{slug}.html", _build_category_html(c, rows, cats))
    return url


def sync_knowledge_base(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    全量按日写 OSS，并刷新 catalog / 日期索引 / 搜索页。
    返回 {days, catalog_url, search_url, count}；未配置 OSS 则空 dict。
    """
    if not oss_enabled():
        print("[知识库] 未配置 OSS，跳过归档", flush=True)
        return {}

    items = load_articles_from_db(conn)
    if not items:
        print("[知识库] articles 为空，跳过", flush=True)
        return {}

    prefix = kb_prefix()
    by_day = _group_by_day(items)
    days_sorted = sorted(by_day.keys(), reverse=True)

    for day, rows in by_day.items():
        upload_json(
            f"{prefix}days/{day}.json",
            {"day": day, "count": len(rows), "items": rows},
        )

    upload_json(f"{prefix}days/index.json", {"days": days_sorted, "updated_at": datetime.utcnow().isoformat() + "Z"})

    # catalog：按时间新到旧截断；含中文摘要/标签/CVE/双链接
    catalog = []
    for it in items[:_CATALOG_LIMIT]:
        catalog.append(
            {
                "title": it["title"],
                "title_zh": it.get("title_zh") or "",
                "display_title": it.get("display_title") or it["title"],
                "summary": (it["summary"] or "")[:400],
                "summary_zh": (it.get("summary_zh") or "")[:800],
                "display_summary": (it.get("display_summary") or it["summary"] or "")[:400],
                "summary_url": it.get("summary_url") or "",
                "tags": it.get("tags") or [],
                "cves": it.get("cves") or [],
                "category": it["category"],
                "author": it["author"],
                "link": it["link"],
                "day": it["day"],
                "published_str": it["published_str"],
                "incident_priority": it.get("incident_priority") or "",
            }
        )
    catalog_url = upload_json(f"{prefix}catalog.json", catalog)
    # 搜索页内嵌 catalog，手机端无需再请求 json
    search_url = ensure_search_page(catalog)

    print(
        f"[知识库] 已归档 {len(items)} 条 / {len(days_sorted)} 天 → {search_url or catalog_url}",
        flush=True,
    )
    return {
        "count": len(items),
        "days": len(days_sorted),
        "catalog_url": catalog_url,
        "search_url": search_url,
    }


def sync_knowledge_base_if_enabled(conn: sqlite3.Connection) -> Dict[str, Any]:
    flag = (os.getenv("KB_ARCHIVE_ENABLED", "1") or "1").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return {}
    try:
        return sync_knowledge_base(conn)
    except Exception as e:
        print(f"[知识库] 归档失败: {e}", flush=True)
        return {}
