"""从 OSS 拉取 kb/briefs 归档到本地 SQLite（与推送线解耦）。"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import (
    OSS_ACCESS_KEY_ID,
    OSS_ACCESS_KEY_SECRET,
    OSS_BRIEF_PREFIX,
    OSS_BUCKET,
    OSS_ENDPOINT,
    OSS_KB_PREFIX,
    oss_configured,
    public_url,
)
from db import init_db, set_meta, upsert_article, upsert_brief


def _http_get_json(url: str, timeout: int = 45) -> Any:
    req = Request(
        url,
        headers={
            "User-Agent": "intel-app/1.0",
            "Accept": "application/json,*/*",
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def _oss_bucket():
    if not (OSS_ACCESS_KEY_ID and OSS_ACCESS_KEY_SECRET and OSS_BUCKET):
        return None
    import oss2

    endpoint = OSS_ENDPOINT
    if not endpoint.startswith("http"):
        endpoint = f"https://{endpoint}"
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, endpoint, OSS_BUCKET)


def _get_json_object(key: str) -> Optional[Any]:
    """优先公共 URL；失败再用 AK/SK。"""
    url = public_url(key)
    try:
        return _http_get_json(url)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError):
        pass
    bucket = _oss_bucket()
    if not bucket:
        return None
    try:
        result = bucket.get_object(key.lstrip("/"))
        return json.loads(result.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def _list_brief_days(bucket) -> List[str]:
    days: List[str] = []
    prefix = OSS_BRIEF_PREFIX.lstrip("/")
    for obj in oss2_ObjectIterator(bucket, prefix=prefix):
        name = obj.key[len(prefix) :] if obj.key.startswith(prefix) else obj.key
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\.json$", name)
        if m:
            days.append(m.group(1))
    return sorted(set(days), reverse=True)


def oss2_ObjectIterator(bucket, prefix: str = ""):
    import oss2

    return oss2.ObjectIterator(bucket, prefix=prefix)


def sync_from_oss(conn=None) -> Dict[str, Any]:
    """
    同步 catalog + days/index + briefs。
    返回 {ok, articles, briefs, error?}。
    """
    from db import connect

    if not oss_configured():
        return {"ok": False, "articles": 0, "briefs": 0, "error": "OSS 未配置"}

    own = conn is None
    if own:
        conn = connect()
        init_db(conn)
    assert conn is not None

    articles_n = 0
    briefs_n = 0
    errors: List[str] = []

    # 1) catalog
    catalog_key = f"{OSS_KB_PREFIX}catalog.json".lstrip("/")
    catalog = _get_json_object(catalog_key)
    if isinstance(catalog, list):
        for it in catalog:
            if isinstance(it, dict):
                upsert_article(conn, it)
                articles_n += 1
    else:
        errors.append("catalog.json 不可用，尝试按日归档")

    # 2) days/index + 各日（补全 catalog 没有的字段）
    index_key = f"{OSS_KB_PREFIX}days/index.json".lstrip("/")
    index = _get_json_object(index_key)
    days = []
    if isinstance(index, dict):
        days = [d for d in (index.get("days") or []) if isinstance(d, str)]
    for day in days[:60]:
        day_key = f"{OSS_KB_PREFIX}days/{day}.json".lstrip("/")
        payload = _get_json_object(day_key)
        if not isinstance(payload, dict):
            continue
        for it in payload.get("items") or []:
            if isinstance(it, dict):
                upsert_article(conn, it)
                articles_n += 1

    # 3) briefs
    bucket = _oss_bucket()
    brief_days: List[str] = []
    if bucket:
        try:
            brief_days = _list_brief_days(bucket)[:90]
        except Exception as e:
            errors.append(f"list briefs: {e}")
    # 无 AK 时用 days 交集猜近期 brief（近 30 天常见）
    if not brief_days:
        for d in days[:30]:
            brief_days.append(d)

    for day in brief_days:
        jkey = f"{OSS_BRIEF_PREFIX}{day}.json".lstrip("/")
        payload = _get_json_object(jkey)
        if not isinstance(payload, dict):
            continue
        pdf_url = public_url(f"{OSS_BRIEF_PREFIX}{day}.pdf".lstrip("/"))
        json_url = public_url(jkey)
        upsert_brief(conn, day, payload, pdf_url=pdf_url, json_url=json_url)
        briefs_n += 1

    now = datetime.utcnow().isoformat() + "Z"
    set_meta(conn, "last_sync_at", now)
    set_meta(conn, "last_sync_error", "; ".join(errors) if errors else "")
    conn.commit()
    if own:
        conn.close()

    return {
        "ok": True,
        "articles_upserts": articles_n,
        "briefs_upserts": briefs_n,
        "synced_at": now,
        "warnings": errors,
    }
