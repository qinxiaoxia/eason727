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
    # published_str 前 10 位或 first_seen_at 日期
    cur = conn.execute(
        """SELECT link, title, summary, category, incident_priority, author, published_str
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
             published_str DESC""",
        (day, day),
    )
    rows = []
    for link, title, summary, category, pri, author, published_str in cur.fetchall():
        rows.append(
            {
                "link": link or "",
                "title": title or "",
                "summary": (summary or "")[:600],
                "category": category or "其他资讯",
                "incident_priority": pri or "",
                "author": author or "",
                "published_str": published_str or "",
            }
        )
    return rows


_BRIEF_SYSTEM = (
    "你是面向单位领导的网络安全值班编辑。根据当日资讯列表，输出 JSON（不要 markdown 围栏）："
    '{"overview":"80-150字总览","bullets":["要点1","要点2"],"watch":["需关注1"]}'
    "bullets 5到8条，突出实害、金融相关、监管通报、高危漏洞；watch 0到3条。"
    "不要编造列表中没有的事实；专有名词可保留英文。"
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

    lines = []
    for i, a in enumerate(articles[:80], 1):
        lines.append(
            f"{i}. [{a['category']}] {a['title']}"
            + (f" | {a['summary'][:120]}" if a.get("summary") else "")
        )
    user = f"日期：{day}\n共 {len(articles)} 条：\n" + "\n".join(lines)
    raw = call_llm_with_fallback(
        [{"role": "user", "content": user}],
        max_tokens=1200,
        system=_BRIEF_SYSTEM,
    )
    parsed = _parse_brief_json(raw or "")
    if parsed:
        return parsed
    return {
        "overview": f"{day} 共收录 {len(articles)} 条资讯。",
        "bullets": [a["title"] for a in articles[:6]],
        "watch": [],
    }


def _find_cjk_font() -> Tuple[Optional[str], int]:
    candidates = [
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
        ("/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf", 0),
        ("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc", 0),
        ("/System/Library/Fonts/PingFang.ttc", 0),
        ("/System/Library/Fonts/STHeiti Light.ttc", 0),
        ("/Library/Fonts/Arial Unicode.ttf", 0),
        (str(_ROOT / "fonts" / "NotoSansSC-Regular.otf"), 0),
    ]
    for path, idx in candidates:
        if Path(path).is_file():
            return path, idx
    return None, 0


def build_pdf_bytes(day: str, brief: Dict[str, Any], articles: List[Dict[str, Any]]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    font_path, sub = _find_cjk_font()
    font_name = "Helvetica"
    if font_path:
        try:
            if font_path.lower().endswith(".ttc"):
                pdfmetrics.registerFont(TTFont("CJK", font_path, subfontIndex=sub))
            else:
                pdfmetrics.registerFont(TTFont("CJK", font_path))
            font_name = "CJK"
        except Exception as e:
            print(f"[每日要点] 注册字体失败，回退 Helvetica: {e}", flush=True)

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

        if notify_wechat and result.get("pdf_url"):
            _notify_wechat(day, result)

        return result
    finally:
        if own_conn and conn is not None:
            conn.close()


def _notify_wechat(day: str, result: Dict[str, Any]) -> None:
    try:
        from main import WECHAT_WEBHOOK, send_wechat
    except Exception as e:
        print(f"[每日要点] 无法加载企微发送: {e}", flush=True)
        return
    if not WECHAT_WEBHOOK:
        return
    url = result.get("pdf_url") or ""
    n = result.get("count") or 0
    overview = ((result.get("brief") or {}).get("overview") or "")[:120]
    content = (
        f"### 📋 网安情报每日要点（{day}）\n\n"
        f"> 共 {n} 条\n\n"
        f"{overview}\n\n"
        f"[下载 PDF]({url})"
    )
    try:
        send_wechat(WECHAT_WEBHOOK, content)
        print("[每日要点] 已推送企微通知", flush=True)
    except Exception as e:
        print(f"[每日要点] 企微推送失败: {e}", flush=True)


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
