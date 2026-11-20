"""阿里云 OSS：英文摘要 HTML 上传与公开 URL。"""
from __future__ import annotations

import os
from pathlib import Path


def _cfg(name: str, default: str = "") -> str:
    env = (os.getenv(name) or "").strip()
    if env:
        return env
    try:
        import config as cfg

        return str(getattr(cfg, name, default) or default).strip()
    except ImportError:
        return (default or "").strip()


def oss_enabled() -> bool:
    return bool(
        _cfg("OSS_ACCESS_KEY_ID")
        and _cfg("OSS_ACCESS_KEY_SECRET")
        and _cfg("OSS_BUCKET")
        and _cfg("OSS_ENDPOINT")
    )


def oss_prefix() -> str:
    p = _cfg("OSS_PREFIX", "rss-summaries/")
    if p and not p.endswith("/"):
        p += "/"
    return p.lstrip("/")


def oss_object_key(day: str, slug: str) -> str:
    return f"{oss_prefix()}{day}/{slug}.html"


def oss_public_url(object_key: str) -> str:
    """公开访问 URL（桶需公共读，或对象 ACL public-read）。"""
    key = (object_key or "").lstrip("/")
    base = _cfg("OSS_PUBLIC_BASE_URL") or _cfg("TRANSLATE_VIEW_BASE_URL")
    if base:
        return f"{base.rstrip('/')}/{key}"
    bucket = _cfg("OSS_BUCKET")
    endpoint = _cfg("OSS_ENDPOINT").replace("https://", "").replace("http://", "").rstrip("/")
    # 虚拟主机：https://bucket.oss-cn-xxx.aliyuncs.com/key
    return f"https://{bucket}.{endpoint}/{key}"


def _bucket():
    import oss2

    ak = _cfg("OSS_ACCESS_KEY_ID")
    sk = _cfg("OSS_ACCESS_KEY_SECRET")
    endpoint = _cfg("OSS_ENDPOINT")
    if not endpoint.startswith("http"):
        endpoint = f"https://{endpoint}"
    auth = oss2.Auth(ak, sk)
    return oss2.Bucket(auth, endpoint, _cfg("OSS_BUCKET"))


def upload_bytes(
    object_key: str,
    data: str | bytes,
    *,
    content_type: str = "application/octet-stream",
    content_disposition: str | None = "inline",
    public_read: bool = True,
) -> str:
    """上传任意字节，返回公开 URL。"""
    if not oss_enabled():
        raise RuntimeError(
            "未配置 OSS：请设置 OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET / "
            "OSS_BUCKET / OSS_ENDPOINT（及可选 OSS_PUBLIC_BASE_URL）"
        )
    raw = data.encode("utf-8") if isinstance(data, str) else data
    headers = {"Content-Type": content_type}
    if content_disposition:
        headers["Content-Disposition"] = content_disposition
    if public_read:
        headers["x-oss-object-acl"] = "public-read"
    key = object_key.lstrip("/")
    _bucket().put_object(key, raw, headers=headers)
    return oss_public_url(key)


def upload_html(object_key: str, html: str | bytes, *, public_read: bool = True) -> str:
    """上传 HTML，返回公开 URL。"""
    return upload_bytes(
        object_key,
        html,
        content_type="text/html; charset=utf-8",
        content_disposition="inline",
        public_read=public_read,
    )


def upload_json(object_key: str, obj, *, public_read: bool = True) -> str:
    import json

    body = json.dumps(obj, ensure_ascii=False, indent=2)
    return upload_bytes(
        object_key,
        body,
        content_type="application/json; charset=utf-8",
        content_disposition="inline",
        public_read=public_read,
    )


def upload_pdf(object_key: str, pdf_bytes: bytes, *, public_read: bool = True) -> str:
    """PDF 允许 attachment（领导下载阅读更自然）。"""
    return upload_bytes(
        object_key,
        pdf_bytes,
        content_type="application/pdf",
        content_disposition='attachment; filename="brief.pdf"',
        public_read=public_read,
    )


def download_bytes(object_key: str) -> bytes | None:
    """下载对象；不存在返回 None。"""
    if not oss_enabled():
        return None
    try:
        import oss2

        key = object_key.lstrip("/")
        r = _bucket().get_object(key)
        return r.read()
    except Exception:
        return None


def upload_file(object_key: str, path: Path, *, public_read: bool = True) -> str:
    return upload_html(object_key, path.read_text(encoding="utf-8"), public_read=public_read)


def kb_prefix() -> str:
    p = _cfg("OSS_KB_PREFIX", "kb/")
    if p and not p.endswith("/"):
        p += "/"
    return p.lstrip("/")


def brief_prefix() -> str:
    p = _cfg("OSS_BRIEF_PREFIX", "briefs/")
    if p and not p.endswith("/"):
        p += "/"
    return p.lstrip("/")


def test_upload_ping() -> str:
    """上传连通性测试页，返回 URL。"""
    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>OSS 摘要通道测试</title></head>
<body style="font-family:sans-serif;padding:24px">
<h1>OSS 摘要通道测试</h1>
<p style="color:#0a7;font-weight:600">若能看到本页，说明阿里云 OSS 公开读正常。</p>
</body></html>
"""
    key = f"{oss_prefix()}ping.html"
    return upload_html(key, html)
