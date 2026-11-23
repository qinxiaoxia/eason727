# -*- coding: utf-8 -*-
"""
阿里云函数计算：定时触发 GitHub Actions workflow_dispatch。

替代 Zeabur/Railway 上常驻的 zeabur-cron-trigger。
在 FC 控制台为同一函数配置多个「定时触发器」，通过 event 区分轮巡/定时：

  event 示例（定时触发器「触发消息」）:
    {"mode": "poll"}   → rss-push.yml
    {"mode": "timed"}  → rss-push-timed.yml

环境变量：
  GITHUB_TOKEN（必填）
  GITHUB_REPO（默认 qinxiaoxia/eason727）
  WORKFLOW_POLL（默认 rss-push.yml）
  WORKFLOW_TIMED（默认 rss-push-timed.yml）
  GITHUB_REF（默认 main）
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default or "").strip()


def _parse_event(event) -> Dict[str, Any]:
    if event is None:
        return {}
    if isinstance(event, dict):
        return event
    if isinstance(event, (bytes, bytearray)):
        event = event.decode("utf-8", errors="replace")
    if isinstance(event, str):
        text = event.strip()
        if not text:
            return {}
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else {"mode": str(data)}
        except json.JSONDecodeError:
            return {"mode": text}
    return {}


def trigger_workflow(workflow_file: str, label: str) -> Tuple[bool, str]:
    token = _env("GITHUB_TOKEN")
    repo = _env("GITHUB_REPO", "qinxiaoxia/eason727")
    ref = _env("GITHUB_REF", "main")
    if not token:
        return False, "GITHUB_TOKEN 未配置"
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
    body = json.dumps({"ref": ref}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "aliyun-fc-rss-trigger",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            if code == 204:
                msg = f"已触发 {label} ({workflow_file})"
                print(msg, flush=True)
                return True, msg
            raw = resp.read().decode("utf-8", errors="replace")[:300]
            return False, f"HTTP {code}: {raw}"
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")[:300]
        msg = f"触发失败 {label}: {e.code} {raw}"
        print(msg, flush=True)
        return False, msg
    except Exception as e:
        msg = f"触发异常 {label}: {e}"
        print(msg, flush=True)
        return False, msg


def handler(event, context):
    """
    FC 入口。支持：
    - 定时触发器 payload: {"mode":"poll"|"timed"}
    - HTTP 触发器手动测: ?mode=poll 或 body JSON
    """
    data = _parse_event(event)
    # HTTP 触发时 FC 可能包一层
    if "body" in data and not data.get("mode"):
        body = data.get("body")
        if isinstance(body, str):
            try:
                data = {**data, **json.loads(body or "{}")}
            except json.JSONDecodeError:
                pass
        elif isinstance(body, dict):
            data = {**data, **body}
    qs = data.get("queryParameters") or data.get("queries") or {}
    if isinstance(qs, dict) and qs.get("mode") and not data.get("mode"):
        data["mode"] = qs.get("mode")

    mode = (data.get("mode") or data.get("type") or "timed").strip().lower()
    if mode in ("poll", "rss-push", "realtime"):
        ok, msg = trigger_workflow(_env("WORKFLOW_POLL", "rss-push.yml"), "轮巡")
    else:
        ok, msg = trigger_workflow(_env("WORKFLOW_TIMED", "rss-push-timed.yml"), "定时")

    result = {"ok": ok, "mode": mode, "message": msg}
    # HTTP 触发器友好返回
    if data.get("requestContext") or data.get("httpMethod") or "headers" in data:
        return {
            "statusCode": 200 if ok else 500,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps(result, ensure_ascii=False),
        }
    return result
