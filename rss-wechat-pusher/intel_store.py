"""
情报库字段：CVE/标签/实体抽取，以及 articles 表回写。
与推送主流程共用同一 SQLite，不另建系统。
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)

# 规则标签：命中关键词即打标（可叠加）
_TAG_RULES: Sequence[tuple[str, Sequence[str]]] = (
    ("钓鱼", ("phish", "钓鱼", "spear-phish", "credential harvest")),
    ("勒索", ("ransom", "勒索", "lockbit", "blackcat", "alphv")),
    ("供应链", ("supply chain", "供应链", "typosquat", "dependency confusion")),
    ("漏洞利用", ("exploit", "rce", "0-day", "zero-day", "in the wild", "被利用")),
    ("APT", (" apt", "apt ", "nation-state", "国家背景", "高级持续")),
    ("数据泄露", ("data breach", "泄露", "leak", "exposed", "dump")),
    ("物联网", ("iot", "路由器", "router", "摄像头", "dvr")),
    ("云安全", ("aws", "azure", "gcp", "cloud", "kubernetes", "k8s")),
    ("AI安全", (" llm", "chatgpt", "claude", "ai agent", "prompt injection", "模型")),
    ("监管通报", ("cisa", "cnvd", "cnnvd", "cert", "通报", "预警")),
)

_VENDOR_RE = re.compile(
    r"\b(Microsoft|Google|Apple|Amazon|AWS|Azure|Cisco|Fortinet|Palo Alto|CrowdStrike|"
    r"Okta|VMware|Citrix|Oracle|SAP|NVIDIA|Intel|AMD|Samsung|TP-Link|Signal|"
    r"WhatsApp|Telegram|OpenAI|Anthropic|Meta|IBM|Dell|HP|Lenovo|Huawei|阿里|腾讯|华为)\b",
    re.I,
)
_ACTOR_RE = re.compile(
    r"\b(Lazarus|APT\d{1,2}|LockBit|BlackCat|ALPHV|Scattered Spider|Lapsus\$?|"
    r"Sandworm|Fancy Bear|Cozy Bear|Volt Typhoon|红门神|Red Menshen)\b",
    re.I,
)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def extract_cves(*texts: str) -> List[str]:
    found: List[str] = []
    seen = set()
    for t in texts:
        for m in _CVE_RE.findall(t or ""):
            cve = m.upper()
            if cve not in seen:
                seen.add(cve)
                found.append(cve)
    return found[:30]


def extract_tags_rule(title: str, summary: str, category: str = "") -> List[str]:
    blob = f"{title or ''}\n{summary or ''}\n{category or ''}".lower()
    tags: List[str] = []
    for tag, keys in _TAG_RULES:
        if any(k.lower() in blob for k in keys):
            tags.append(tag)
    if category and category not in tags:
        # 不把全部分类塞进标签，仅高价值类
        if category in ("监管机构预警", "重大安全事件", "漏洞信息"):
            tags.append(category)
    # 去重保序
    out: List[str] = []
    for t in tags:
        if t not in out:
            out.append(t)
    return out[:12]


def extract_entities_rule(title: str, summary: str) -> List[Dict[str, str]]:
    blob = f"{title or ''}\n{summary or ''}"
    ents: List[Dict[str, str]] = []
    seen = set()
    for m in _VENDOR_RE.finditer(blob):
        name = m.group(1)
        key = ("vendor", name.lower())
        if key not in seen:
            seen.add(key)
            ents.append({"type": "vendor", "name": name})
    for m in _ACTOR_RE.finditer(blob):
        name = m.group(1)
        key = ("actor", name.lower())
        if key not in seen:
            seen.add(key)
            ents.append({"type": "actor", "name": name})
    return ents[:20]


def enrich_from_text(
    title: str,
    summary: str = "",
    category: str = "",
    summary_zh: str = "",
    *,
    use_llm: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    返回可直接写入的字段 dict（含 json 字符串）。
    CVE 以正则为准；标签/实体规则优先，可选 LLM 补全。
    """
    text_for_cve = "\n".join([title or "", summary or "", summary_zh or ""])
    cves = extract_cves(text_for_cve)
    tags = extract_tags_rule(title, summary or summary_zh, category)
    entities = extract_entities_rule(title, summary or summary_zh)

    if use_llm is None:
        use_llm = (os.getenv("INTEL_LLM_ENRICH", "0") or "0").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
    if use_llm:
        extra = _llm_enrich_tags_entities(title, summary_zh or summary, category)
        for t in extra.get("tags") or []:
            if t and t not in tags:
                tags.append(str(t))
        for e in extra.get("entities") or []:
            if not isinstance(e, dict):
                continue
            name = (e.get("name") or "").strip()
            et = (e.get("type") or "product").strip() or "product"
            if not name:
                continue
            key = (et.lower(), name.lower())
            if not any(
                (x.get("type") or "").lower() == key[0]
                and (x.get("name") or "").lower() == key[1]
                for x in entities
            ):
                entities.append({"type": et, "name": name})
        for c in extra.get("cves") or []:
            c2 = str(c).upper().strip()
            if _CVE_RE.fullmatch(c2) and c2 not in cves:
                cves.append(c2)

    return {
        "tags_json": _dumps(tags[:12]),
        "cves_json": _dumps(cves[:30]),
        "entities_json": _dumps(entities[:20]),
        "tags": tags[:12],
        "cves": cves[:30],
        "entities": entities[:20],
    }


def _llm_enrich_tags_entities(title: str, summary: str, category: str) -> Dict[str, Any]:
    try:
        from llm_utils import call_llm_with_fallback, get_llm_providers
    except Exception:
        return {}
    if not get_llm_providers():
        return {}
    system = (
        "你是网安情报标注助手。根据标题与摘要输出 JSON（不要 markdown）："
        '{"tags":["中文标签"],"cves":["CVE-...."],"entities":[{"type":"vendor|actor|product","name":"..."}]}'
        "tags 最多 5 个；不要编造 CVE；实体仅保留正文明确出现的。"
    )
    user = f"分类：{category}\n标题：{title}\n摘要：{(summary or '')[:1200]}"
    raw = call_llm_with_fallback(
        [{"role": "user", "content": user}],
        max_tokens=400,
        system=system,
    )
    if not raw:
        return {}
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        m = re.search(r"(\{.*\})", text, re.DOTALL)
        if m:
            text = m.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def iocs_from_pairs(pairs: Sequence[tuple]) -> str:
    """监管 IOC (address, ip) 列表 → iocs_json。"""
    rows: List[Dict[str, str]] = []
    for pair in pairs or []:
        if not pair:
            continue
        address = (pair[0] or "").strip() if len(pair) > 0 else ""
        ip = (pair[1] or "").strip() if len(pair) > 1 else ""
        if address:
            typ = "ip" if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", address) else "domain"
            rows.append({"type": typ, "value": address})
        if ip and ip != address:
            rows.append({"type": "ip", "value": ip})
    # 去重
    out: List[Dict[str, str]] = []
    seen = set()
    for r in rows:
        key = (r["type"], r["value"].lower())
        if key not in seen:
            seen.add(key)
            out.append(r)
    return _dumps(out[:100])


_ALLOWED_COLS = {
    "title_zh",
    "summary_zh",
    "summary_url",
    "tags_json",
    "cves_json",
    "iocs_json",
    "entities_json",
}


def update_article_intel(conn: sqlite3.Connection, link: str, **fields: Any) -> bool:
    """按 link 更新情报字段；忽略未知列。返回是否执行了 UPDATE。"""
    if not link or not fields:
        return False
    sets = []
    vals: List[Any] = []
    for k, v in fields.items():
        if k not in _ALLOWED_COLS:
            continue
        if v is None:
            continue
        sets.append(f"{k}=?")
        vals.append(v)
    if not sets:
        return False
    vals.append(link)
    cur = conn.execute(
        f"UPDATE articles SET {', '.join(sets)} WHERE link=?",
        vals,
    )
    conn.commit()
    return cur.rowcount > 0


def _db_path() -> Path:
    try:
        from main import DB_PATH

        return Path(DB_PATH)
    except Exception:
        return Path.home() / ".rss-wechat-pusher" / "rss_push.db"


def persist_article_enrichment(
    link: str,
    *,
    title: str = "",
    summary: str = "",
    category: str = "",
    title_zh: str = "",
    summary_zh: str = "",
    summary_url: str = "",
    iocs_json: str = "",
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """打开库（或用传入 conn）回写摘要与抽取字段。"""
    if not link:
        return
    own = conn is None
    if own:
        path = _db_path()
        if not path.is_file():
            return
        conn = sqlite3.connect(str(path), timeout=30)
        try:
            from main import init_db

            init_db(conn)
        except Exception:
            pass
    assert conn is not None
    try:
        enriched = enrich_from_text(
            title_zh or title,
            summary,
            category,
            summary_zh=summary_zh,
        )
        fields: Dict[str, Any] = {
            "tags_json": enriched["tags_json"],
            "cves_json": enriched["cves_json"],
            "entities_json": enriched["entities_json"],
        }
        if title_zh:
            fields["title_zh"] = title_zh
        if summary_zh:
            fields["summary_zh"] = summary_zh
        if summary_url:
            fields["summary_url"] = summary_url
        if iocs_json:
            fields["iocs_json"] = iocs_json
        update_article_intel(conn, link, **fields)
    finally:
        if own:
            conn.close()
