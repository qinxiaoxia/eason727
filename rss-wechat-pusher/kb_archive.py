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
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from oss_utils import (
    download_bytes,
    kb_prefix,
    oss_enabled,
    oss_public_url,
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


def _row_to_item(row) -> Dict[str, Any]:
    link, title, summary, category, incident_priority, author, source_url, published_str, first_seen_at = row
    day = _beijing_day_from_published(published_str or "", (first_seen_at or "")[:10])
    return {
        "link": link or "",
        "title": title or "",
        "summary": (summary or "")[:2000],
        "category": category or "",
        "incident_priority": incident_priority or "",
        "author": author or "",
        "source_url": source_url or "",
        "published_str": published_str or "",
        "first_seen_at": first_seen_at or "",
        "day": day,
    }


def load_articles_from_db(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    cur = conn.execute(
        """SELECT link, title, summary, category, incident_priority, author,
                  source_url, published_str, first_seen_at
           FROM articles ORDER BY published_str DESC, first_seen_at DESC"""
    )
    return [_row_to_item(r) for r in cur.fetchall()]


def _group_by_day(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        by.setdefault(it["day"] or "unknown", []).append(it)
    return by


def _build_search_html(catalog: List[Dict[str, Any]]) -> str:
    """
    把目录内嵌进页面，避免手机企微再 fetch catalog.json（OSS 常强制 attachment，请求会挂死，
    且原先搜索按钮要等加载成功才绑定，所以一直转圈、点搜索也没反应）。
    """
    # </script> 拆开，防止标题摘要里出现该串打断脚本
    payload = json.dumps(catalog, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")
    payload = payload.replace("</script>", "<\\/script>")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>网安情报知识库</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;
margin:0;padding:20px;background:#f6f7f9;color:#1a1a1a;max-width:920px;margin-inline:auto}}
h1{{font-size:1.35rem;margin:0 0 8px}}
.sub{{color:#666;font-size:.9rem;margin-bottom:16px}}
input,select,button{{font:inherit;padding:8px 10px;border:1px solid #ccc;border-radius:6px}}
input{{width:min(420px,100%);box-sizing:border-box}}
.row{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;align-items:center}}
#stats{{color:#555;font-size:.85rem;margin-bottom:10px}}
.card{{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:12px 14px;margin:0 0 10px}}
.card h3{{font-size:1rem;margin:0 0 6px;line-height:1.4}}
.meta{{font-size:.8rem;color:#666}}
.cat{{display:inline-block;background:#eef5fb;color:#1a6fb5;padding:1px 6px;border-radius:4px;margin-right:6px}}
a{{color:#06c;word-break:break-all}}
.empty{{color:#888;padding:24px 0}}
</style>
</head>
<body>
<h1>网安情报知识库</h1>
<p class="sub">检索已归档资讯。关键词匹配标题 / 摘要 / 分类 / 来源。</p>
<div class="row">
  <input id="q" type="search" placeholder="输入关键词，如：银行 勒索 CVE" autofocus/>
  <select id="cat"><option value="">全部分类</option></select>
  <button id="go" type="button">搜索</button>
</div>
<div id="stats"></div>
<div id="list" class="empty">正在准备…</div>
<script>
window.__KB_CATALOG__ = {payload};
(function(){{
  const items = Array.isArray(window.__KB_CATALOG__) ? window.__KB_CATALOG__ : [];
  const listEl = document.getElementById('list');
  const statsEl = document.getElementById('stats');
  const catEl = document.getElementById('cat');
  function esc(s){{return String(s||'').replace(/[&<>"']/g,c=>({{ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }}[c]));}}
  function render(rows){{
    statsEl.textContent = '共 ' + items.length + ' 条，当前显示 ' + rows.length + ' 条';
    if(!rows.length){{ listEl.innerHTML = '<div class="empty">无匹配结果</div>'; return; }}
    listEl.innerHTML = rows.slice(0,200).map(it => `
      <div class="card">
        <h3><span class="cat">${{esc(it.category||'未分类')}}</span>${{esc(it.title)}}</h3>
        <div class="meta">${{esc(it.day||'')}} · ${{esc(it.author||'')}} · ${{esc((it.published_str||'').slice(0,16))}}</div>
        <p style="font-size:.9rem;margin:8px 0 6px;white-space:pre-wrap">${{esc((it.summary||'').slice(0,220))}}</p>
        <a href="${{esc(it.link)}}" target="_blank" rel="noopener">原文链接</a>
      </div>`).join('');
  }}
  function search(){{
    const q = (document.getElementById('q').value||'').trim().toLowerCase();
    const cat = catEl.value;
    let rows = items;
    if(cat) rows = rows.filter(it => (it.category||'') === cat);
    if(q){{
      const parts = q.split(/\\s+/).filter(Boolean);
      rows = rows.filter(it => {{
        const blob = ((it.title||'')+' '+(it.summary||'')+' '+(it.category||'')+' '+(it.author||'')).toLowerCase();
        return parts.every(p => blob.includes(p));
      }});
    }}
    render(rows);
  }}
  const cats = [...new Set(items.map(i=>i.category).filter(Boolean))].sort();
  cats.forEach(c=>{{ const o=document.createElement('option'); o.value=c; o.textContent=c; catEl.appendChild(o); }});
  document.getElementById('go').onclick = search;
  document.getElementById('q').addEventListener('keydown', e=>{{ if(e.key==='Enter') search(); }});
  catEl.onchange = search;
  search();
}})();
</script>
</body>
</html>
"""


def ensure_search_page(catalog: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    if not oss_enabled():
        return None
    key = f"{kb_prefix()}search.html"
    return upload_html(key, _build_search_html(catalog or []))


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

    # catalog：按时间新到旧截断，字段精简便于搜索页加载
    catalog = []
    for it in items[:_CATALOG_LIMIT]:
        catalog.append(
            {
                "title": it["title"],
                "summary": (it["summary"] or "")[:400],
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
