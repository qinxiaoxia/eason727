"""
把 OSS 默认域名上的 HTML（会被强制下载）换成 Workbuddy 等可读快照链接。

同事接口约定：
  POST {base}/api/create?sharecode=xxx
  body: {"urls":["https://....aliyuncs.com/...html"]}
  返回: {"code":0,"items":[{"ok":true,"readable":"https://.../view?..."}]}
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests

_cache: Dict[str, str] = {}


def _cfg(name: str, default: str = "") -> str:
    env = (os.getenv(name) or "").strip()
    if env:
        return env
    try:
        import config as cfg

        return str(getattr(cfg, name, default) or default).strip()
    except ImportError:
        return (default or "").strip()


def preview_proxy_enabled() -> bool:
    flag = _cfg("SUMMARY_PREVIEW_ENABLED", "1").lower()
    if flag in ("0", "false", "no", "off"):
        return False
    return bool(_cfg("SUMMARY_PREVIEW_BASE_URL") and _cfg("SUMMARY_PREVIEW_SHARECODE"))


def _create_endpoint() -> str:
    base = _cfg("SUMMARY_PREVIEW_BASE_URL").rstrip("/") + "/"
    share = _cfg("SUMMARY_PREVIEW_SHARECODE")
    return urljoin(base, f"api/create?sharecode={share}")


def to_readable_urls(oss_urls: List[str]) -> Dict[str, str]:
    """
    批量：{oss_url: readable_url}。失败的条目不会出现在返回里。
    """
    urls = []
    out: Dict[str, str] = {}
    for u in oss_urls:
        u = (u or "").strip()
        if not u:
            continue
        if u in _cache:
            out[u] = _cache[u]
        else:
            urls.append(u)
    if not urls:
        return out
    if not preview_proxy_enabled():
        return out
    try:
        r = requests.post(
            _create_endpoint(),
            json={"urls": urls[:20]},
            headers={"Content-Type": "application/json"},
            timeout=45,
        )
        if r.status_code >= 400:
            print(f"[摘要预览] HTTP {r.status_code}: {(r.text or '')[:160]}", flush=True)
            return out
        data = r.json()
        if not isinstance(data, dict):
            return out
        for item in data.get("items") or []:
            if not isinstance(item, dict) or not item.get("ok"):
                continue
            src = (item.get("source") or "").strip()
            readable = (item.get("readable") or "").strip()
            if src and readable:
                _cache[src] = readable
                out[src] = readable
    except Exception as e:
        print(f"[摘要预览] 调用失败: {e}", flush=True)
    return out


def to_readable_url(oss_url: str) -> str:
    """单条：成功返回快照链接，失败回退原 OSS URL。"""
    oss_url = (oss_url or "").strip()
    if not oss_url:
        return ""
    if not preview_proxy_enabled():
        return oss_url
    mapped = to_readable_urls([oss_url])
    readable = mapped.get(oss_url) or ""
    if readable:
        print(f"[摘要预览] 已换成可读链接", flush=True)
        return readable
    print("[摘要预览] 未拿到可读链接，仍用 OSS 原链", flush=True)
    return oss_url
