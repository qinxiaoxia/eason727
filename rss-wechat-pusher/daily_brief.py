"""
每日要点：汇总北京「当天」已入库资讯 → LLM 提炼要点 → 生成 PDF → 上传 OSS → 可选企微通知。

用法：
  python daily_brief.py              # 今天
  python daily_brief.py --date 2026-03-20
  python main.py --daily-brief       # 由 main 收尾调用
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 保证同目录可 import
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _now_beijing_date() -> str:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    except Exception:
        return datetime.utcnow().strftime("%Y-%m-%d")


def _db_path() -> Path:
    try:
        from main import DB_PATH

        return Path(DB_PATH)
    except Exception:
        return _ROOT / "rss_push.db"


def _articles_for_day(conn: sqlite3.Connection, day: str) -> List[Dict[str, Any]]:
    # published_str 前 10 位或 first_seen_at 日期；兼容情报库扩展列
    cur = conn.execute("PRAGMA table_info(articles)")
    cols = {row[1] for row in cur.fetchall()}
    has_intel = "title_zh" in cols and "summary_url" in cols
    if has_intel:
        sql = """SELECT link, title, summary, category, incident_priority, author, published_str,
                        title_zh, summary_zh, summary_url
                 FROM articles
                 WHERE substr(COALESCE(published_str,''),1,10)=?
                    OR substr(COALESCE(first_seen_at,''),1,10)=?
                 ORDER BY
                   CASE category
                     WHEN '监管机构预警' THEN 0
                     WHEN '重大安全事件' THEN 1
                     WHEN '漏洞信息' THEN 2
                     WHEN '网安新闻资讯' THEN 3
                     WHEN '网安赛事资讯' THEN 4
                     WHEN 'AI与信息安全技术' THEN 5
                     WHEN 'AI行业资讯' THEN 6
                     ELSE 9
                   END,
                   published_str DESC"""
    else:
        sql = """SELECT link, title, summary, category, incident_priority, author, published_str
                 FROM articles
                 WHERE substr(COALESCE(published_str,''),1,10)=?
                    OR substr(COALESCE(first_seen_at,''),1,10)=?
                 ORDER BY published_str DESC"""
    cur = conn.execute(sql, (day, day))
    rows = []
    for row in cur.fetchall():
        if has_intel:
            link, title, summary, category, pri, author, published_str, title_zh, summary_zh, summary_url = row
        else:
            link, title, summary, category, pri, author, published_str = row
            title_zh = summary_zh = summary_url = ""
        display = (title_zh or "").strip() or (title or "")
        rows.append(
            {
                "link": link or "",
                "title": display,
                "title_orig": title or "",
                "summary": ((summary_zh or summary or ""))[:600],
                "category": category or "其他资讯",
                "incident_priority": pri or "",
                "author": author or "",
                "published_str": published_str or "",
                "summary_url": (summary_url or "").strip(),
                "is_english": False,
            }
        )
    return rows


# 明显中文媒体域名：这些一般不需要「中文摘要」外链
_CN_HOST_HINTS = (
    "weixin.qq.com",
    "mp.weixin",
    "4hou.com",
    "anquanke.com",
    "freebuf.com",
    "secrss.com",
    "cnvd.org.cn",
    "cac.gov.cn",
    "miit.gov.cn",
    "cert.org.cn",
    "yijinglab",
    "aqniu.com",
    "ithome.com",
    "zhihu.com",
)


def _host_looks_chinese(link: str) -> bool:
    from urllib.parse import urlparse

    host = (urlparse(link or "").netloc or "").lower()
    if not host:
        return False
    if host.endswith(".cn") or host.endswith(".com.cn"):
        return True
    return any(h in host for h in _CN_HOST_HINTS)


def _lookup_existing_summary_url(link: str, published_str: str, extra_days: Optional[List[str]] = None) -> str:
    """若推送时已上传过中文摘要 HTML，直接复用 OSS 链接（多日期兜底）。"""
    try:
        from main import _summary_day_slug
        from oss_utils import object_exists, oss_enabled, oss_object_key, oss_public_url
    except Exception:
        return ""
    if not oss_enabled() or not link:
        return ""
    day0, slug = _summary_day_slug(link, published_str or "")
    days = [day0]
    for d in extra_days or []:
        if d and d not in days:
            days.append(d)
    for day in days:
        key = oss_object_key(day, slug)
        if object_exists(key):
            return oss_public_url(key)
    return ""


def _batch_translate_titles(titles: List[str]) -> Dict[str, str]:
    """批量译标题，返回 {原文: 中文}。Qwen-MT 逐条译；其它模型一次 JSON。"""
    from llm_utils import call_llm_with_fallback, get_llm_providers, is_mt_model

    titles = [t.strip() for t in titles if (t or "").strip()]
    providers = get_llm_providers("translate")
    if not titles or not providers:
        return {}
    titles = titles[:40]
    use_mt = any(is_mt_model(m) for _, _, m in providers)

    if use_mt:
        out: Dict[str, str] = {}
        for src in titles:
            raw = call_llm_with_fallback(
                [{"role": "user", "content": src}],
                max_tokens=256,
                purpose="translate",
            )
            zh = (raw or "").strip()
            if zh and re.search(r"[\u4e00-\u9fff]", zh):
                out[src] = zh
        print(f"[每日要点] 批量译标题成功 {len(out)}/{len(titles)} (mt)", flush=True)
        return out

    numbered = "\n".join(f"{i}. {t}" for i, t in enumerate(titles, 1))
    system = (
        "你是网安资讯标题翻译。用户给出编号的英文标题列表。"
        "只输出 JSON 对象：{\"1\":\"中文标题\",\"2\":\"中文标题\"}，键为编号字符串。"
        "每条译成简洁通顺的简体中文；专有名词可保留英文；不要解释。"
    )
    raw = call_llm_with_fallback(
        [{"role": "user", "content": numbered}],
        max_tokens=min(80 * len(titles) + 200, 2500),
        system=system,
        purpose="translate",
    )
    if not raw:
        print("[每日要点] 批量译标题失败（LLM 无返回，可能额度不足）", flush=True)
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
        print("[每日要点] 批量译标题 JSON 解析失败", flush=True)
        return {}
    out = {}
    for i, src in enumerate(titles, 1):
        zh = (data.get(str(i)) or data.get(i) or "").strip()
        if zh and re.search(r"[\u4e00-\u9fff]", zh):
            out[src] = zh
    print(f"[每日要点] 批量译标题成功 {len(out)}/{len(titles)}", flush=True)
    return out


def _enrich_articles_for_brief(
    articles: List[Dict[str, Any]],
    *,
    brief_day: str = "",
    ensure_missing_summary: bool = True,
    ensure_limit: int = 8,
) -> List[Dict[str, Any]]:
    """
    英文标题译成中文；英文稿附「原文 + 中文摘要」链接（优先复用 OSS，缺失时少量补生成）。
    """
    try:
        from main import (
            _ensure_chinese_body_summary,
            _should_translate_title,
        )
    except Exception as e:
        print(f"[每日要点] 无法加载翻译能力: {e}", flush=True)
        return articles

    need_zh_idxs = []
    for i, a in enumerate(articles):
        orig = (a.get("title") or "").strip()
        a["title_orig"] = orig
        need_title_zh = _should_translate_title(orig)
        foreign = need_title_zh or (bool(a.get("link")) and not _host_looks_chinese(a["link"]))
        a["is_english"] = bool(foreign)
        a["_need_title_zh"] = need_title_zh
        if need_title_zh:
            need_zh_idxs.append(i)

    translated = _batch_translate_titles(
        [articles[i]["title_orig"] for i in need_zh_idxs]
    )
    for i in need_zh_idxs:
        src = articles[i]["title_orig"]
        if src in translated:
            articles[i]["title"] = translated[src]

    attempts = 0
    for a in articles:
        if not a.get("is_english"):
            continue
        extra = [brief_day] if brief_day else []
        url = _lookup_existing_summary_url(
            a.get("link") or "", a.get("published_str") or "", extra_days=extra
        )
        if (
            not url
            and ensure_missing_summary
            and attempts < ensure_limit
            and a.get("_need_title_zh")
        ):
            attempts += 1
            item = {
                "title": a.get("title_orig") or a.get("title") or "",
                "link": a.get("link") or "",
                "summary": a.get("summary") or "",
                "published_str": a.get("published_str") or "",
                "author": a.get("author") or "",
                "source_url": "",
            }
            try:
                url = _ensure_chinese_body_summary(item, a.get("title") or item["title"]) or ""
            except Exception as e:
                print(f"[每日要点] 补摘要失败: {e}", flush=True)
                url = ""
        a["summary_url"] = url or ""
        a.pop("_need_title_zh", None)

    return articles


_BRIEF_SYSTEM = (
    "你是面向单位领导的网络安全值班编辑。根据当日资讯列表，输出 JSON（不要 markdown 围栏）："
    '{"overview":"80-150字中文总览","bullets":["中文要点1","中文要点2"],"watch":["需关注1"]}'
    "bullets 5到8条，突出实害、金融相关、监管通报、高危漏洞；watch 0到3条。"
    "overview、bullets、watch 必须全部使用中文撰写；专有名词、CVE、产品名可保留英文，但句子主体必须是中文。"
    "不要编造列表中没有的事实；不要整句照抄英文标题。"
)


def _parse_brief_json(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
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
        return None
    if not isinstance(data, dict):
        return None
    overview = (data.get("overview") or "").strip()
    bullets = [str(x).strip() for x in (data.get("bullets") or []) if str(x).strip()][:8]
    watch = [str(x).strip() for x in (data.get("watch") or []) if str(x).strip()][:3]
    if not overview and not bullets:
        return None
    return {"overview": overview, "bullets": bullets, "watch": watch}


def _llm_daily_brief(day: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    from llm_utils import call_llm_with_fallback, get_llm_providers

    if not get_llm_providers() or not articles:
        # 无 LLM：用分类计数做极简总览
        from collections import Counter

        c = Counter(a["category"] for a in articles)
        parts = [f"{k}{v}条" for k, v in c.most_common()]
        return {
            "overview": f"{day} 共收录 {len(articles)} 条（{'、'.join(parts[:6])}）。",
            "bullets": [f"[{a['category']}] {a['title']}" for a in articles[:8]],
            "watch": [],
        }

    # 控制入模长度，优先前 50 条（库查询已按类别优先级排好）
    lines = []
    for i, a in enumerate(articles[:50], 1):
        # 入模用中文标题；摘要截短，避免挤掉要点生成
        sum_bit = (a.get("summary") or "").replace("\n", " ").strip()[:80]
        lines.append(
            f"{i}. [{a['category']}] {a['title']}"
            + (f" | {sum_bit}" if sum_bit else "")
        )
    user = (
        f"日期：{day}\n共 {len(articles)} 条（下列为优先摘录 {min(50, len(articles))} 条）：\n"
        + "\n".join(lines)
        + "\n\n请用中文输出 overview / bullets / watch。"
    )
    raw = call_llm_with_fallback(
        [{"role": "user", "content": user}],
        max_tokens=1200,
        system=_BRIEF_SYSTEM,
    )
    parsed = _parse_brief_json(raw or "")
    if parsed:
        return parsed
    print("[每日要点] 要点 LLM 失败，使用中文条目兜底", flush=True)
    return {
        "overview": f"{day} 共收录 {len(articles)} 条资讯。",
        "bullets": [f"[{a['category']}] {a['title']}" for a in articles[:8]],
        "watch": [],
    }


def _find_cjk_font() -> Tuple[str, int]:
    """
    返回 (字体路径, ttc_subfontIndex)。
    优先仓库内 TTF（简体），避免 Helvetica 导致中文乱码；
    NotoSansCJK.ttc 的 index 0 常为日文，简体一般用 2。
    """
    home = Path.home()
    candidates: List[Tuple[str, int]] = [
        # 仓库自带（Actions/本地一致）
        (str(_ROOT / "fonts" / "AlibabaPuHuiTi-Regular.ttf"), 0),
        (str(_ROOT / "fonts" / "NotoSansSC-Regular.otf"), 0),
        (str(_ROOT / "fonts" / "NotoSansSC-Regular.ttf"), 0),
        # 本机常见
        (str(home / "Library/Fonts/Alibaba-PuHuiTi-Regular.ttf"), 0),
        ("/Library/Fonts/Arial Unicode.ttf", 0),
        # Ubuntu fonts-noto-cjk：简体通常为 subfontIndex=2
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 2),
        ("/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf", 0),
        ("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc", 2),
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 2),
        # macOS 黑体（多 face）
        ("/System/Library/Fonts/STHeiti Light.ttc", 1),
        ("/System/Library/Fonts/STHeiti Light.ttc", 0),
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
    ]
    for path, idx in candidates:
        if Path(path).is_file():
            return path, idx
    raise RuntimeError(
        "未找到可用中文字体。请将 AlibabaPuHuiTi-Regular.ttf 放到 rss-wechat-pusher/fonts/，"
        "或在 CI 安装 fonts-noto-cjk。"
    )


def _register_cjk_font() -> str:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if "CJK" in pdfmetrics.getRegisteredFontNames():
        return "CJK"
    font_path, sub = _find_cjk_font()
    last_err = None
    # TTC 多试几个 index，防止简体落在别的 face
    indices = [sub] + [i for i in (0, 1, 2, 3) if i != sub]
    if not font_path.lower().endswith(".ttc"):
        indices = [0]
    for idx in indices:
        try:
            if font_path.lower().endswith(".ttc"):
                pdfmetrics.registerFont(TTFont("CJK", font_path, subfontIndex=idx))
            else:
                pdfmetrics.registerFont(TTFont("CJK", font_path))
            # 冒烟：确保能取到常用汉字宽度
            from reportlab.pdfbase.pdfmetrics import stringWidth

            w = stringWidth("网安银行", "CJK", 10)
            if w <= 0:
                raise RuntimeError("stringWidth=0")
            print(f"[每日要点] 使用字体: {font_path} (ttcIndex={idx})", flush=True)
            return "CJK"
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"中文字体注册失败: {font_path} ({last_err})")


def build_pdf_bytes(day: str, brief: Dict[str, Any], articles: List[Dict[str, Any]]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    font_name = _register_cjk_font()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"网安情报每日要点 {day}",
    )
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle(
        "T",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=16,
        leading=22,
        spaceAfter=8,
    )
    h_s = ParagraphStyle(
        "H",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=12,
        leading=18,
        spaceBefore=10,
        spaceAfter=6,
    )
    body_s = ParagraphStyle(
        "B",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=15,
        spaceAfter=4,
    )
    small_s = ParagraphStyle(
        "S",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        leading=13,
        textColor="#444444",
        spaceAfter=3,
    )

    def p(text: str, style=body_s):
        t = (
            (text or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )
        return Paragraph(t, style)

    story = [
        p(f"网安情报每日要点（{day}）", title_s),
        p(f"共收录 {len(articles)} 条 · 自动生成，仅供内部快速浏览", small_s),
        Spacer(1, 4),
        p("一、要点总览", h_s),
        p(brief.get("overview") or "（无）", body_s),
        p("二、今日要点", h_s),
    ]
    for i, b in enumerate(brief.get("bullets") or [], 1):
        story.append(p(f"{i}. {b}", body_s))
    if brief.get("watch"):
        story.append(p("三、需持续关注", h_s))
        for i, w in enumerate(brief["watch"], 1):
            story.append(p(f"{i}. {w}", body_s))

    story.append(p("四、当日条目一览", h_s))
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for a in articles:
        by_cat.setdefault(a["category"], []).append(a)
    for cat, rows in by_cat.items():
        story.append(p(f"【{cat}】{len(rows)} 条", h_s))
        for a in rows[:40]:
            story.append(p(f"· {a['title']}", body_s))
            if a.get("link"):
                # 英文稿：原文 + 中文摘要；中文稿：只给原文链接
                if a.get("is_english") or a.get("summary_url"):
                    story.append(p(f"原文：{a['link']}", small_s))
                    if a.get("summary_url"):
                        story.append(p(f"中文摘要：{a['summary_url']}", small_s))
                else:
                    story.append(p(a["link"], small_s))

    story.append(Spacer(1, 8))
    story.append(p("— 由 RSS 推送机器人自动生成 —", small_s))
    doc.build(story)
    return buf.getvalue()


def generate_daily_brief(
    day: Optional[str] = None,
    *,
    conn: Optional[sqlite3.Connection] = None,
    notify_wechat: bool = True,
) -> Dict[str, Any]:
    """生成并上传 PDF；返回 {day, count, pdf_url, json_url}。"""
    from oss_utils import brief_prefix, oss_enabled, upload_json, upload_pdf

    day = day or _now_beijing_date()
    own_conn = conn is None
    if own_conn:
        path = _db_path()
        if not path.is_file():
            print(f"[每日要点] 无数据库: {path}", flush=True)
            return {}
        conn = sqlite3.connect(str(path))

    try:
        articles = _articles_for_day(conn, day)
        if not articles:
            print(f"[每日要点] {day} 无文章，跳过", flush=True)
            return {"day": day, "count": 0}

        articles = _enrich_articles_for_brief(articles, brief_day=day)
        brief = _llm_daily_brief(day, articles)
        pdf_bytes = build_pdf_bytes(day, brief, articles)

        result = {"day": day, "count": len(articles), "brief": brief}
        if oss_enabled():
            prefix = brief_prefix()
            pdf_url = upload_pdf(f"{prefix}{day}.pdf", pdf_bytes)
            json_url = upload_json(
                f"{prefix}{day}.json",
                {"day": day, "count": len(articles), "brief": brief, "articles": articles},
            )
            result["pdf_url"] = pdf_url
            result["json_url"] = json_url
            print(f"[每日要点] 已上传 PDF: {pdf_url}", flush=True)
        else:
            out = _ROOT / "briefs"
            out.mkdir(exist_ok=True)
            local = out / f"{day}.pdf"
            local.write_bytes(pdf_bytes)
            result["pdf_url"] = str(local)
            print(f"[每日要点] 未配置 OSS，已写本地 {local}", flush=True)

        if notify_wechat:
            _notify_wechat_pdf(day, pdf_bytes)

        return result
    finally:
        if own_conn and conn is not None:
            conn.close()


def _webhook_key(webhook: str) -> str:
    from urllib.parse import parse_qs, urlparse

    return (parse_qs(urlparse(webhook or "").query).get("key") or [""])[0].strip()


def _send_wechat_file(webhook: str, filename: str, data: bytes) -> None:
    """企微群机器人：上传并发送文件消息（直接推 PDF，无文字简述）。"""
    import requests

    key = _webhook_key(webhook)
    if not key:
        raise RuntimeError("webhook 缺少 key")
    # 企微文件上限约 20MB
    if len(data) > 19 * 1024 * 1024:
        raise RuntimeError(f"PDF 过大: {len(data)} bytes")
    upload_url = (
        f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={key}&type=file"
    )
    files = {"media": (filename, data, "application/pdf")}
    r = requests.post(upload_url, files=files, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("errcode", 0) != 0 or not j.get("media_id"):
        raise RuntimeError(f"上传媒体失败: {j}")
    media_id = j["media_id"]
    r2 = requests.post(
        webhook,
        json={"msgtype": "file", "file": {"media_id": media_id}},
        timeout=30,
    )
    r2.raise_for_status()
    j2 = r2.json()
    if j2.get("errcode", 0) != 0:
        raise RuntimeError(f"发送文件失败: {j2}")


def _notify_wechat_pdf(day: str, pdf_bytes: bytes) -> None:
    """只推送 PDF 文件，不发文字概述。"""
    try:
        from main import WECHAT_WEBHOOK, _collector_webhook_url
    except Exception as e:
        print(f"[每日要点] 无法加载企微配置: {e}", flush=True)
        return
    filename = f"网安情报每日要点-{day}.pdf"
    hooks = []
    if WECHAT_WEBHOOK:
        hooks.append(("主群", WECHAT_WEBHOOK))
    try:
        collector = _collector_webhook_url()
    except Exception:
        collector = ""
    if collector and collector.rstrip("/") != (WECHAT_WEBHOOK or "").rstrip("/"):
        hooks.append(("采集群", collector))
    if not hooks:
        print("[每日要点] 未配置 WECHAT_WEBHOOK，跳过推送", flush=True)
        return
    for name, hook in hooks:
        try:
            _send_wechat_file(hook, filename, pdf_bytes)
            print(f"[每日要点] 已向{name}推送 PDF 文件", flush=True)
        except Exception as e:
            print(f"[每日要点] {name} PDF 推送失败: {e}", flush=True)


def maybe_run_end_of_day_brief(slot, conn: sqlite3.Connection) -> None:
    """定时档 17:30 结束后自动出 PDF；可用环境变量强制。"""
    force = (os.getenv("GENERATE_DAILY_BRIEF") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if not force and slot != (17, 30):
        return
    if (os.getenv("DAILY_BRIEF_ENABLED", "1") or "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        return
    try:
        generate_daily_brief(conn=conn, notify_wechat=True)
    except Exception as e:
        print(f"[每日要点] 生成失败: {e}", flush=True)


if __name__ == "__main__":
    day = None
    if "--date" in sys.argv:
        i = sys.argv.index("--date")
        if i + 1 < len(sys.argv):
            day = sys.argv[i + 1]
    notify = "--no-notify" not in sys.argv
    r = generate_daily_brief(day, notify_wechat=notify)
    print(json.dumps({k: v for k, v in r.items() if k != "brief"}, ensure_ascii=False, indent=2))
