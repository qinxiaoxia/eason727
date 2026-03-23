#!/usr/bin/env python3
"""
Zeabur 定时触发器：按【北京时间】cron 调用 GitHub API 触发 workflow_dispatch。

不再依赖 GitHub Actions 的 schedule（易漏跑）。部署本服务后，请在 workflow 里去掉 on.schedule，
只保留 workflow_dispatch。

环境变量：
  GITHUB_TOKEN（必填）
  GITHUB_REPO（默认 qinxiaoxia/eason727）
  WORKFLOW_POLL（默认 rss-push.yml）— 轮巡
  WORKFLOW_TIMED（默认 rss-push-timed.yml）— 9:30/15:30 定时

PAT 需含 repo + workflow（或 classic repo 全权限）。
"""

from __future__ import annotations

import os
import time

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "qinxiaoxia/eason727")
WORKFLOW_POLL = os.getenv("WORKFLOW_POLL", "rss-push.yml")
WORKFLOW_TIMED = os.getenv("WORKFLOW_TIMED", "rss-push-timed.yml")
GITHUB_REF = os.getenv("GITHUB_REF", "main")
# 与 backend / rss-push 轮巡时间一致（北京整点）
TZ = os.getenv("TRIGGER_TIMEZONE", "Asia/Shanghai")


def trigger_workflow(workflow_file: str, label: str) -> None:
    """POST /repos/.../actions/workflows/{file}/dispatches"""
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN 未配置，跳过触发")
        return
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {"ref": GITHUB_REF}
    try:
        r = requests.post(url, json=data, headers=headers, timeout=15)
        if r.status_code == 204:
            print(f"[{time.strftime('%H:%M:%S')}] 已触发 {label} ({workflow_file})", flush=True)
        else:
            print(
                f"[{time.strftime('%H:%M:%S')}] 触发失败 {label}: {r.status_code} {r.text[:300]}",
                flush=True,
            )
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] 触发异常 {label}: {e}", flush=True)


def _poll():
    trigger_workflow(WORKFLOW_POLL, "轮巡 RSS Push")


def _timed():
    trigger_workflow(WORKFLOW_TIMED, "定时 RSS Push Timed")


@app.route("/")
def index():
    return (
        "Zeabur RSS 触发器：北京时间 轮巡 6/8/12/14/18 整点 + 定时 9:30/15:30 → "
        f"GitHub workflow_dispatch（{WORKFLOW_POLL} / {WORKFLOW_TIMED}）"
    )


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("警告: GITHUB_TOKEN 未设置，将不会触发 workflow")

    scheduler = BackgroundScheduler(timezone=TZ)

    # 北京 6、8、12、14、18 整点轮巡（与 rss-push 设计一致）
    scheduler.add_job(
        _poll,
        CronTrigger(hour="6,8,12,14,18", minute="0", timezone=TZ),
        id="poll_beijing",
        name="poll",
    )
    # 北京 9:30、15:30 定时四类
    scheduler.add_job(
        _timed,
        CronTrigger(hour="9,15", minute="30", timezone=TZ),
        id="timed_beijing",
        name="timed",
    )

    scheduler.start()
    print(
        f"[Zeabur trigger] 时区={TZ} | 轮巡 {WORKFLOW_POLL} @ 北京 6,8,12,14,18:00 | "
        f"定时 {WORKFLOW_TIMED} @ 北京 9:30,15:30",
        flush=True,
    )

    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
