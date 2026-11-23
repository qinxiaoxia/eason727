"""Web 口令 Cookie + API Bearer Token。"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, Request, Response, status

from config import INTEL_API_TOKEN, INTEL_SESSION_SECRET, INTEL_WEB_PASSWORD

COOKIE_NAME = "intel_session"


def _sign(payload: str) -> str:
    return hmac.new(
        INTEL_SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def make_session_token(ttl_seconds: int = 7 * 24 * 3600) -> str:
    exp = int(time.time()) + ttl_seconds
    nonce = secrets.token_hex(8)
    payload = f"{exp}.{nonce}"
    return f"{payload}.{_sign(payload)}"


def verify_session_token(token: Optional[str]) -> bool:
    if not token or token.count(".") != 2:
        return False
    exp_s, nonce, sig = token.split(".", 2)
    payload = f"{exp_s}.{nonce}"
    if not hmac.compare_digest(_sign(payload), sig):
        return False
    try:
        exp = int(exp_s)
    except ValueError:
        return False
    return exp >= int(time.time())


def check_web_password(password: str) -> bool:
    return hmac.compare_digest((password or "").strip(), INTEL_WEB_PASSWORD)


def set_login_cookie(response: Response) -> None:
    response.set_cookie(
        COOKIE_NAME,
        make_session_token(),
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/",
    )


def clear_login_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def require_web_session(
    request: Request,
    intel_session: Optional[str] = Cookie(default=None, alias=COOKIE_NAME),
) -> None:
    # 允许未配置口令时仅开发：仍要求 cookie，避免裸奔
    if verify_session_token(intel_session):
        return
    # API 同源带 Bearer 也可打开 JSON，但 HTML 页必须登录
    raise HTTPException(
        status_code=status.HTTP_303_SEE_OTHER,
        headers={"Location": "/login"},
    )


def require_api_token(
    authorization: Optional[str] = Header(default=None),
) -> None:
    if not INTEL_API_TOKEN:
        # 未配置 token 时拒绝外部 API（强制设 token）
        raise HTTPException(status_code=503, detail="INTEL_API_TOKEN 未配置")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="需要 Authorization: Bearer <token>")
    token = authorization.split(" ", 1)[1].strip()
    if not hmac.compare_digest(token, INTEL_API_TOKEN):
        raise HTTPException(status_code=401, detail="无效 token")


def api_ok(data=None, meta=None):
    body = {"ok": True, "data": data}
    if meta is not None:
        body["meta"] = meta
    return body


def api_err(message: str, status_code: int = 400):
    raise HTTPException(status_code=status_code, detail={"ok": False, "error": message})
