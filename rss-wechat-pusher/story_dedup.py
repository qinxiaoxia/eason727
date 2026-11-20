"""
跨源同一事件去重：不同网站转载/改写同一新闻时，只保留一条推送。
基于标题归一化 + 相似度（SequenceMatcher / 公共子串）。
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Iterable, List, Sequence, Tuple


# 标题噪音：来源括注、译标、常见前缀
_STRIP_PREFIX = re.compile(
    r"^(?:【[^】]{0,40}】|\[[^\]]{0,40}\]|（[^）]{0,20}）|\([^)]{0,20}\))\s*"
)
_STRIP_MARKERS = re.compile(
    r"（译）|【译】|\(译\)|独家|快讯|详讯|最新|突发|重磅|原创|"
    r"报道称|消息称|据报道|外媒称|外电称"
)
_STRIP_PUNCT = re.compile(
    r"[\s\u3000\-—_·•|｜,，.。!！?？:：;；、\"\'“”‘’（）()\[\]【】<>《》]+"
)
# 常见媒体/站点名（出现在标题中时弱化）
_STRIP_SOURCES = re.compile(
    r"(?i)("
    r"freebuf|安全客|嘶吼|secrss|爱加密|安恒|奇安信|腾讯安全|阿里云|"
    r"cybersecurity\s*news|helpnetsecurity|hacker\s*news|thehackernews|"
    r"bleepingcomputer|securityweek|darkreading|zdnet|theregister|"
    r"securityaffairs|anquanke|4hou|solidot"
    r")"
)

# 相似度阈值：略宽松，抓住「同事件不同写法」
_SIM_RATIO = 0.72
_MIN_CORE_LEN = 8
_LONG_SUBSTR = 14  # 归一化后公共子串长度


def normalize_title(title: str) -> str:
    t = (title or "").strip()
    if not t:
        return ""
    for _ in range(3):
        nt = _STRIP_PREFIX.sub("", t)
        if nt == t:
            break
        t = nt
    t = _STRIP_MARKERS.sub("", t)
    t = _STRIP_SOURCES.sub("", t)
    t = _STRIP_PUNCT.sub("", t)
    return t.lower()


def _char_ngrams(s: str, n: int = 2) -> set:
    if len(s) < n:
        return {s} if s else set()
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def title_similarity(a: str, b: str) -> float:
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    # 一方包含另一方核心
    if len(na) >= _MIN_CORE_LEN and len(nb) >= _MIN_CORE_LEN:
        if na in nb or nb in na:
            return 0.92
    ratio = SequenceMatcher(None, na, nb).ratio()
    ga, gb = _char_ngrams(na), _char_ngrams(nb)
    if ga and gb:
        jacc = len(ga & gb) / len(ga | gb)
        ratio = max(ratio, jacc)
    # 最长公共子串（粗略）
    if len(na) >= _LONG_SUBSTR and len(nb) >= _LONG_SUBSTR:
        shorter, longer = (na, nb) if len(na) <= len(nb) else (nb, na)
        for i in range(len(shorter) - _LONG_SUBSTR + 1):
            if shorter[i : i + _LONG_SUBSTR] in longer:
                ratio = max(ratio, 0.85)
                break
    return ratio


def is_same_story(title_a: str, title_b: str, threshold: float = _SIM_RATIO) -> bool:
    return title_similarity(title_a, title_b) >= threshold


def find_duplicate_against(
    title: str, candidates: Sequence[Tuple[str, str]], threshold: float = _SIM_RATIO
) -> Tuple[str, str] | None:
    """
    candidates: [(title, link), ...]
    命中则返回 (matched_title, matched_link)。
    """
    for other_title, other_link in candidates:
        if is_same_story(title, other_title, threshold):
            return other_title, other_link
    return None


def dedupe_items_keep_first(
    items: List[dict],
    prior_titles: Iterable[Tuple[str, str]] | None = None,
    threshold: float = _SIM_RATIO,
) -> Tuple[List[dict], List[dict]]:
    """
    批次内 + 相对已推送标题去重。保留先出现的。
    返回 (kept, dropped)；dropped 项带 dedup_of_link / dedup_of_title。
    """
    prior = list(prior_titles or [])
    kept: List[dict] = []
    dropped: List[dict] = []
    seen_local: List[Tuple[str, str]] = []

    for item in items:
        title = item.get("title") or ""
        link = item.get("link") or ""
        hit = find_duplicate_against(title, prior + seen_local, threshold)
        if hit:
            mt, ml = hit
            dup = dict(item)
            dup["dedup_of_title"] = mt
            dup["dedup_of_link"] = ml
            dropped.append(dup)
            continue
        kept.append(item)
        if title and link:
            seen_local.append((title, link))
    return kept, dropped
