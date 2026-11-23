"""本地只读副本库（由 OSS 同步填充）。"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import DATA_DIR, DB_PATH


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: Optional[sqlite3.Connection] = None) -> sqlite3.Connection:
    own = conn is None
    if own:
        conn = connect()
    assert conn is not None
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            link TEXT UNIQUE NOT NULL,
            title TEXT,
            title_zh TEXT,
            summary TEXT,
            summary_zh TEXT,
            summary_url TEXT,
            category TEXT,
            author TEXT,
            published_str TEXT,
            day TEXT,
            incident_priority TEXT,
            tags_json TEXT,
            cves_json TEXT,
            iocs_json TEXT,
            entities_json TEXT,
            updated_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_articles_day ON articles(day);
        CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
        CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_str);

        CREATE TABLE IF NOT EXISTS briefs (
            day TEXT PRIMARY KEY,
            count INTEGER,
            overview TEXT,
            bullets_json TEXT,
            watch_json TEXT,
            pdf_url TEXT,
            json_url TEXT,
            raw_json TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS meta (
            k TEXT PRIMARY KEY,
            v TEXT
        );
        """
    )
    conn.commit()
    if own:
        return conn
    return conn


def _dumps(obj: Any) -> str:
    return json.dumps(obj if obj is not None else [], ensure_ascii=False)


def _loads(raw: Optional[str], default=None):
    if not raw:
        return [] if default is None else default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [] if default is None else default


def article_id_from_link(link: str) -> str:
    import hashlib

    return hashlib.sha1((link or "").encode("utf-8")).hexdigest()[:16]


def upsert_article(conn: sqlite3.Connection, item: Dict[str, Any]) -> None:
    link = (item.get("link") or "").strip()
    if not link:
        return
    aid = item.get("id") or article_id_from_link(link)
    title = item.get("title") or ""
    title_zh = item.get("title_zh") or item.get("display_title") or ""
    if title_zh == title:
        # display_title 可能已是中文
        pass
    tags = item.get("tags") or []
    cves = item.get("cves") or []
    iocs = item.get("iocs") or []
    entities = item.get("entities") or []
    if isinstance(tags, str):
        tags = _loads(tags)
    if isinstance(cves, str):
        cves = _loads(cves)
    if isinstance(iocs, str):
        iocs = _loads(iocs)
    if isinstance(entities, str):
        entities = _loads(entities)
    from datetime import datetime

    now = datetime.utcnow().isoformat() + "Z"
    conn.execute(
        """
        INSERT INTO articles (
            id, link, title, title_zh, summary, summary_zh, summary_url,
            category, author, published_str, day, incident_priority,
            tags_json, cves_json, iocs_json, entities_json, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            link=excluded.link,
            title=excluded.title,
            title_zh=excluded.title_zh,
            summary=excluded.summary,
            summary_zh=excluded.summary_zh,
            summary_url=excluded.summary_url,
            category=excluded.category,
            author=excluded.author,
            published_str=excluded.published_str,
            day=excluded.day,
            incident_priority=excluded.incident_priority,
            tags_json=excluded.tags_json,
            cves_json=excluded.cves_json,
            iocs_json=excluded.iocs_json,
            entities_json=excluded.entities_json,
            updated_at=excluded.updated_at
        """,
        (
            aid,
            link,
            title,
            title_zh or "",
            (item.get("summary") or "")[:4000],
            (item.get("summary_zh") or item.get("display_summary") or "")[:4000],
            item.get("summary_url") or "",
            item.get("category") or "",
            item.get("author") or "",
            item.get("published_str") or "",
            item.get("day") or "",
            item.get("incident_priority") or "",
            _dumps(tags),
            _dumps(cves),
            _dumps(iocs),
            _dumps(entities),
            now,
        ),
    )


def upsert_brief(conn: sqlite3.Connection, day: str, payload: Dict[str, Any], *, pdf_url: str = "", json_url: str = "") -> None:
    from datetime import datetime

    brief = payload.get("brief") if isinstance(payload.get("brief"), dict) else payload
    overview = (brief.get("overview") or "") if isinstance(brief, dict) else ""
    bullets = (brief.get("bullets") or []) if isinstance(brief, dict) else []
    watch = (brief.get("watch") or []) if isinstance(brief, dict) else []
    count = int(payload.get("count") or 0)
    now = datetime.utcnow().isoformat() + "Z"
    conn.execute(
        """
        INSERT INTO briefs (day, count, overview, bullets_json, watch_json, pdf_url, json_url, raw_json, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(day) DO UPDATE SET
            count=excluded.count,
            overview=excluded.overview,
            bullets_json=excluded.bullets_json,
            watch_json=excluded.watch_json,
            pdf_url=excluded.pdf_url,
            json_url=excluded.json_url,
            raw_json=excluded.raw_json,
            updated_at=excluded.updated_at
        """,
        (
            day,
            count,
            overview,
            _dumps(bullets),
            _dumps(watch),
            pdf_url or payload.get("pdf_url") or "",
            json_url or "",
            json.dumps(payload, ensure_ascii=False),
            now,
        ),
    )


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
        (key, value),
    )


def get_meta(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT v FROM meta WHERE k=?", (key,)).fetchone()
    return (row["v"] if row else default) or default


def row_to_article(row: sqlite3.Row) -> Dict[str, Any]:
    title_zh = (row["title_zh"] or "").strip()
    title = (row["title"] or "").strip()
    summary_zh = (row["summary_zh"] or "").strip()
    summary = (row["summary"] or "").strip()
    return {
        "id": row["id"],
        "link": row["link"],
        "title": title,
        "title_zh": title_zh,
        "display_title": title_zh or title,
        "summary": summary,
        "summary_zh": summary_zh,
        "display_summary": summary_zh or summary,
        "summary_url": row["summary_url"] or "",
        "category": row["category"] or "",
        "author": row["author"] or "",
        "published_str": row["published_str"] or "",
        "day": row["day"] or "",
        "incident_priority": row["incident_priority"] or "",
        "tags": _loads(row["tags_json"]),
        "cves": _loads(row["cves_json"]),
        "iocs": _loads(row["iocs_json"]),
        "entities": _loads(row["entities_json"]),
        "updated_at": row["updated_at"] or "",
    }


def list_articles(
    conn: sqlite3.Connection,
    *,
    q: str = "",
    category: str = "",
    cve: str = "",
    tag: str = "",
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Dict[str, Any]], int]:
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    where = ["1=1"]
    args: List[Any] = []
    if category:
        where.append("category = ?")
        args.append(category)
    if q:
        like = f"%{q}%"
        where.append(
            "(title LIKE ? OR title_zh LIKE ? OR summary LIKE ? OR summary_zh LIKE ?"
            " OR tags_json LIKE ? OR cves_json LIKE ? OR iocs_json LIKE ? OR link LIKE ?)"
        )
        args.extend([like] * 8)
    if cve:
        where.append("cves_json LIKE ?")
        args.append(f"%{cve.upper()}%")
    if tag:
        where.append("tags_json LIKE ?")
        args.append(f"%{tag}%")
    clause = " AND ".join(where)
    total = conn.execute(f"SELECT COUNT(*) AS n FROM articles WHERE {clause}", args).fetchone()["n"]
    offset = (page - 1) * page_size
    rows = conn.execute(
        f"""SELECT * FROM articles WHERE {clause}
            ORDER BY published_str DESC, day DESC, updated_at DESC
            LIMIT ? OFFSET ?""",
        args + [page_size, offset],
    ).fetchall()
    return [row_to_article(r) for r in rows], int(total)


def get_article(conn: sqlite3.Connection, article_id: str) -> Optional[Dict[str, Any]]:
    row = conn.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
    return row_to_article(row) if row else None


def list_categories(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute(
        "SELECT DISTINCT category FROM articles WHERE category IS NOT NULL AND category != '' ORDER BY category"
    ).fetchall()
    return [r["category"] for r in rows]


def list_briefs(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        "SELECT day, count, overview, pdf_url, updated_at FROM briefs ORDER BY day DESC"
    ).fetchall()
    return [
        {
            "day": r["day"],
            "count": r["count"],
            "overview": (r["overview"] or "")[:200],
            "pdf_url": r["pdf_url"] or "",
            "updated_at": r["updated_at"] or "",
        }
        for r in rows
    ]


def get_brief(conn: sqlite3.Connection, day: str) -> Optional[Dict[str, Any]]:
    row = conn.execute("SELECT * FROM briefs WHERE day=?", (day,)).fetchone()
    if not row:
        return None
    return {
        "day": row["day"],
        "count": row["count"],
        "overview": row["overview"] or "",
        "bullets": _loads(row["bullets_json"]),
        "watch": _loads(row["watch_json"]),
        "pdf_url": row["pdf_url"] or "",
        "json_url": row["json_url"] or "",
        "updated_at": row["updated_at"] or "",
    }


def article_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) AS n FROM articles").fetchone()["n"])
