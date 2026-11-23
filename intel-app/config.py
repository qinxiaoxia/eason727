"""情报应用配置（与推送线解耦；只读 OSS）。"""
from __future__ import annotations

import os
from pathlib import Path


def env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default or "").strip()


ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(env("INTEL_DATA_DIR") or str(ROOT / "data"))
DB_PATH = DATA_DIR / "intel_app.db"

OSS_ACCESS_KEY_ID = env("OSS_ACCESS_KEY_ID")
OSS_ACCESS_KEY_SECRET = env("OSS_ACCESS_KEY_SECRET")
OSS_BUCKET = env("OSS_BUCKET")
OSS_ENDPOINT = env("OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")
OSS_PUBLIC_BASE_URL = env("OSS_PUBLIC_BASE_URL", "").rstrip("/")
OSS_KB_PREFIX = env("OSS_KB_PREFIX", "kb/")
if OSS_KB_PREFIX and not OSS_KB_PREFIX.endswith("/"):
    OSS_KB_PREFIX += "/"
OSS_BRIEF_PREFIX = env("OSS_BRIEF_PREFIX", "briefs/")
if OSS_BRIEF_PREFIX and not OSS_BRIEF_PREFIX.endswith("/"):
    OSS_BRIEF_PREFIX += "/"

INTEL_WEB_PASSWORD = env("INTEL_WEB_PASSWORD", "changeme")
INTEL_API_TOKEN = env("INTEL_API_TOKEN", "")
INTEL_SYNC_MINUTES = int(env("INTEL_SYNC_MINUTES", "15") or "15")
INTEL_SESSION_SECRET = env("INTEL_SESSION_SECRET") or (INTEL_API_TOKEN or INTEL_WEB_PASSWORD or "dev-secret")
HOST = env("HOST", "0.0.0.0")
PORT = int(env("PORT", "8080") or "8080")


def oss_configured() -> bool:
    return bool(OSS_PUBLIC_BASE_URL or (OSS_ACCESS_KEY_ID and OSS_ACCESS_KEY_SECRET and OSS_BUCKET))


def public_url(object_key: str) -> str:
    key = (object_key or "").lstrip("/")
    if OSS_PUBLIC_BASE_URL:
        return f"{OSS_PUBLIC_BASE_URL}/{key}"
    endpoint = OSS_ENDPOINT.replace("https://", "").replace("http://", "").rstrip("/")
    return f"https://{OSS_BUCKET}.{endpoint}/{key}"
