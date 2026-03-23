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

注意：若 PaaS 用 gunicorn 多 worker 启动 main:app，必须用文件锁只启一个调度器；
推荐启动命令：python main.py（见 Procfile）。
"""

from __future__ import annotations

import atexit
import os
import sys
import time

try:
    import fcntl
except ImportError:  # Windows 等环境无 fcntl，仅开发机；Zeabur 为 Linux
    fcntl = None  # type: ignore[misc, assignment]

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, jsonify

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "qinxiaoxia/eason727")
WORKFLOW_POLL = os.getenv("WORKFLOW_POLL", "rss-push.yml")
WORKFLOW_TIMED = os.getenv("WORKFLOW_TIMED", "rss-push-timed.yml")
GITHUB_REF = os.getenv("GITHUB_REF", "main")
# 与 backend / rss-push 轮巡时间一致（北京整点）
TZ = os.getenv("TRIGGER_TIMEZONE", "Asia/Shanghai")
# 若容器在整点前后才启动/唤醒，允许在宽限时间内补跑一次（秒）。Zeabur 若长时间休眠则仍会漏跑。
MISFIRE_GRACE_SEC = int(os.getenv("MISFIRE_GRACE_SEC", "7200"))

_LOCK_PATH = os.getenv("SCHEDULER_LOCK_PATH", "/tmp/zeabur_rss_trigger_scheduler.lock")
_scheduler_lock_fp = None


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


@app.route("/status")
def status():
    """排查用：下次执行时间、是否配置了 TOKEN（不泄露内容）。"""
    sched = app.config.get("_scheduler")
    if not sched:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "scheduler not running",
                    "hint": "若用 gunicorn 多 worker，仅持锁进程会启动调度；请设单 worker 或启动命令 python main.py",
                }
            ),
            500,
        )
    jobs = []
    for job in sched.get_jobs():
        jobs.append({"id": job.id, "next_run_time": str(job.next_run_time)})
    return jsonify(
        {
            "ok": True,
            "timezone": TZ,
            "github_repo": GITHUB_REPO,
            "github_token_configured": bool(GITHUB_TOKEN),
            "misfire_grace_sec": MISFIRE_GRACE_SEC,
            "jobs": jobs,
        }
    )


def _release_lock() -> None:
    global _scheduler_lock_fp
    if _scheduler_lock_fp is not None and fcntl is not None:
        try:
            fcntl.flock(_scheduler_lock_fp.fileno(), fcntl.LOCK_UN)
            _scheduler_lock_fp.close()
        except OSError:
            pass
    _scheduler_lock_fp = None


def start_scheduler() -> BackgroundScheduler | None:
    """
    启动 APScheduler。必须在 import main / worker 进程内调用一次。
    gunicorn 多 worker 时仅第一个抢到文件锁的进程会启动调度，避免重复触发。
    """
    if app.config.get("_scheduler"):
        return app.config["_scheduler"]

    if os.getenv("DISABLE_TRIGGER_SCHEDULER") == "1":
        print("[Zeabur trigger] 已设置 DISABLE_TRIGGER_SCHEDULER=1，不启动调度", flush=True)
        return None

    global _scheduler_lock_fp
    if fcntl is not None:
        try:
            _scheduler_lock_fp = open(_LOCK_PATH, "a+")
            fcntl.flock(_scheduler_lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(
                "[Zeabur trigger] 另一进程已持有调度锁（常见于 gunicorn 多 worker），"
                "本进程不启动 APScheduler",
                flush=True,
            )
            return None
        except OSError as e:
            print(f"[Zeabur trigger] 文件锁不可用 ({e})，仍尝试启动调度（单进程环境）", flush=True)

    if not GITHUB_TOKEN:
        print("警告: GITHUB_TOKEN 未设置，将不会触发 workflow", flush=True)

    scheduler = BackgroundScheduler(timezone=TZ)

    scheduler.add_job(
        _poll,
        CronTrigger(hour="6,8,12,14,18", minute="0", timezone=TZ),
        id="poll_beijing",
        name="poll",
        misfire_grace_time=MISFIRE_GRACE_SEC,
        coalesce=True,
    )
    scheduler.add_job(
        _timed,
        CronTrigger(hour="9,15", minute="30", timezone=TZ),
        id="timed_beijing",
        name="timed",
        misfire_grace_time=MISFIRE_GRACE_SEC,
        coalesce=True,
    )

    scheduler.start()
    app.config["_scheduler"] = scheduler
    atexit.register(_release_lock)

    msg = (
        f"[Zeabur trigger] 时区={TZ} | 轮巡 {WORKFLOW_POLL} @ 北京 6,8,12,14,18:00 | "
        f"定时 {WORKFLOW_TIMED} @ 北京 9:30,15:30"
    )
    print(msg, flush=True)
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()
    for job in scheduler.get_jobs():
        line = f"[Zeabur trigger] 任务 {job.id} 下次执行: {job.next_run_time}"
        print(line, flush=True)
        sys.stderr.write(line + "\n")
        sys.stderr.flush()

    return scheduler


# 关键：Zeabur 若用 gunicorn main:app 启动，不会走 __main__，必须在 import 时启动调度器
start_scheduler()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)
