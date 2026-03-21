#!/usr/bin/env python3
"""
Zeabur 定时触发器：按间隔调用 GitHub API 触发 RSS Push workflow
环境变量：GITHUB_TOKEN（必填）、GITHUB_REPO（默认 qinxiaoxia/eason727）
INTERVAL_MINUTES（默认 180）。使用你的 PAT 触发时，Actions 上会显示「Manually run by 你的用户名」。

注意：不要在仓库已配置 schedule 的情况下把间隔设成 60 分钟，否则会和 GitHub 定时叠加，
且两台 job 同时 push rss_push.db 容易冲突。默认识别为至少 180 分钟。
"""

import os
import time

import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "qinxiaoxia/eason727")
WORKFLOW_FILE = "rss-push.yml"

# 硬下限 180 分钟：之前若同时设 INTERVAL_MINUTES=60 + MIN_INTERVAL_MINUTES=60，max(60,60)=60 会恢复「每小时」。
# 仅当显式设置 I_ACCEPT_HOURLY_DUPLICATE_TRIGGER=1 时才允许低于 180（仍不推荐）。
_raw = int(os.getenv("INTERVAL_MINUTES", "180"))
_ALLOW_SUB_3H = os.getenv("I_ACCEPT_HOURLY_DUPLICATE_TRIGGER", "").strip().lower() in ("1", "true", "yes")
if _ALLOW_SUB_3H:
    _min_floor = int(os.getenv("MIN_INTERVAL_MINUTES", "60"))
    INTERVAL_MINUTES = max(_raw, max(1, _min_floor))
else:
    INTERVAL_MINUTES = max(_raw, 180)
if INTERVAL_MINUTES != _raw:
    print(
        f"[Zeabur trigger] INTERVAL_MINUTES={_raw} → 实际 {INTERVAL_MINUTES} 分钟（与 GitHub schedule 并行时建议≥180）",
        flush=True,
    )


def trigger_workflow():
    """调用 GitHub repository_dispatch 触发 RSS Push"""
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN 未配置，跳过触发")
        return
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {"ref": "main"}
    try:
        r = requests.post(url, json=data, headers=headers, timeout=10)
        if r.status_code == 204:
            print(f"[{time.strftime('%H:%M:%S')}] 已触发 RSS Push")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 触发失败: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] 触发异常: {e}")


@app.route("/")
def index():
    return f"Zeabur RSS Push 触发器运行中，每 {INTERVAL_MINUTES} 分钟触发一次 GitHub Actions"


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("警告: GITHUB_TOKEN 未设置，将不会触发 workflow")

    scheduler = BackgroundScheduler()
    scheduler.add_job(trigger_workflow, "interval", minutes=max(1, INTERVAL_MINUTES))
    scheduler.start()
    # 启动后立即触发一次
    trigger_workflow()

    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
