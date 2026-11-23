"""
情报应用：独立 FastAPI（API + Web），与企微推送线解耦。
数据从 OSS kb/briefs 同步到本地 SQLite。
"""
from __future__ import annotations

import asyncio
import threading
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import (
    COOKIE_NAME,
    api_ok,
    check_web_password,
    clear_login_cookie,
    require_api_token,
    set_login_cookie,
    verify_session_token,
)
from config import HOST, INTEL_SYNC_MINUTES, PORT, ROOT
from db import (
    article_count,
    connect,
    get_article,
    get_brief,
    get_meta,
    init_db,
    list_articles,
    list_briefs,
    list_categories,
)
from sync_oss import sync_from_oss

templates = Jinja2Templates(directory=str(ROOT / "templates"))

_db_lock = threading.Lock()
_conn = None


def get_conn():
    global _conn
    if _conn is None:
        _conn = connect()
        init_db(_conn)
    return _conn


def _sync_safe() -> dict:
    with _db_lock:
        return sync_from_oss(get_conn())


async def _sync_loop():
    # 启动稍等再同步，避免阻塞就绪
    await asyncio.sleep(2)
    while True:
        try:
            await asyncio.to_thread(_sync_safe)
        except Exception as e:
            print(f"[intel-app] sync error: {e}", flush=True)
        await asyncio.sleep(max(60, INTEL_SYNC_MINUTES * 60))


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_conn()
    task = asyncio.create_task(_sync_loop())
    # 首次同步
    try:
        await asyncio.to_thread(_sync_safe)
    except Exception as e:
        print(f"[intel-app] initial sync: {e}", flush=True)
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="网安情报 API",
    description="与企微推送解耦的只读情报接口；Web 与其它应用共用 /api/v1。",
    version="1.0.0",
    lifespan=lifespan,
)
def _web_logged_in(request: Request) -> bool:
    return verify_session_token(request.cookies.get(COOKIE_NAME))


def _require_web(request: Request):
    if not _web_logged_in(request):
        return RedirectResponse("/login", status_code=303)
    return None


# ---------- API v1 ----------


@app.get("/api/v1/health")
def api_health():
    conn = get_conn()
    return api_ok(
        {
            "service": "intel-app",
            "articles": article_count(conn),
            "last_sync_at": get_meta(conn, "last_sync_at"),
            "last_sync_error": get_meta(conn, "last_sync_error"),
        }
    )


@app.get("/api/v1/articles", dependencies=[Depends(require_api_token)])
def api_articles(
    q: str = Query(""),
    category: str = Query(""),
    cve: str = Query(""),
    tag: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = list_articles(
        get_conn(),
        q=q.strip(),
        category=category.strip(),
        cve=cve.strip(),
        tag=tag.strip(),
        page=page,
        page_size=page_size,
    )
    return api_ok(
        items,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
            "categories": list_categories(get_conn()),
        },
    )


@app.get("/api/v1/articles/{article_id}", dependencies=[Depends(require_api_token)])
def api_article_detail(article_id: str):
    item = get_article(get_conn(), article_id)
    if not item:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    return api_ok(item)


@app.get("/api/v1/briefs", dependencies=[Depends(require_api_token)])
def api_briefs():
    return api_ok(list_briefs(get_conn()))


@app.get("/api/v1/briefs/{day}", dependencies=[Depends(require_api_token)])
def api_brief_detail(day: str):
    item = get_brief(get_conn(), day)
    if not item:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    return api_ok(item)


@app.post("/api/v1/admin/sync", dependencies=[Depends(require_api_token)])
def api_admin_sync():
    result = _sync_safe()
    return api_ok(result)


# ---------- Web ----------


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if _web_logged_in(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": ""},
    )


@app.post("/login")
def login_submit(request: Request, password: str = Form("")):
    if not check_web_password(password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "口令错误"},
            status_code=401,
        )
    resp = RedirectResponse("/", status_code=303)
    set_login_cookie(resp)
    return resp


@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    clear_login_cookie(resp)
    return resp


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    q: str = "",
    category: str = "",
    cve: str = "",
    page: int = 1,
):
    redir = _require_web(request)
    if redir:
        return redir
    items, total = list_articles(
        get_conn(),
        q=q.strip(),
        category=category.strip(),
        cve=cve.strip(),
        page=page,
        page_size=20,
    )
    cats = list_categories(get_conn())
    pages = max(1, (total + 19) // 20)
    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "items": items,
            "total": total,
            "q": q,
            "category": category,
            "cve": cve,
            "page": page,
            "pages": pages,
            "categories": cats,
            "last_sync": get_meta(get_conn(), "last_sync_at"),
        },
    )


@app.get("/a/{article_id}", response_class=HTMLResponse)
def article_page(request: Request, article_id: str):
    redir = _require_web(request)
    if redir:
        return redir
    item = get_article(get_conn(), article_id)
    if not item:
        return HTMLResponse("未找到该情报", status_code=404)
    return templates.TemplateResponse(
        "detail.html",
        {"request": request, "item": item},
    )


@app.get("/briefs", response_class=HTMLResponse)
def briefs_page(request: Request):
    redir = _require_web(request)
    if redir:
        return redir
    return templates.TemplateResponse(
        "briefs.html",
        {"request": request, "items": list_briefs(get_conn())},
    )


@app.get("/briefs/{day}", response_class=HTMLResponse)
def brief_detail_page(request: Request, day: str):
    redir = _require_web(request)
    if redir:
        return redir
    item = get_brief(get_conn(), day)
    if not item:
        return HTMLResponse("未找到该日要点", status_code=404)
    return templates.TemplateResponse(
        "brief_detail.html",
        {"request": request, "item": item},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
