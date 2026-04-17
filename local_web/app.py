from __future__ import annotations

import asyncio
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from conf import BASE_DIR
from sau_cli import (
    DOUYIN_PUBLISH_STRATEGY_IMMEDIATE,
    DOUYIN_PUBLISH_STRATEGY_SCHEDULED,
    KUAISHOU_PUBLISH_STRATEGY_IMMEDIATE,
    KUAISHOU_PUBLISH_STRATEGY_SCHEDULED,
    XIAOHONGSHU_PUBLISH_STRATEGY_IMMEDIATE,
    XIAOHONGSHU_PUBLISH_STRATEGY_SCHEDULED,
    BilibiliVideoUploadRequest,
    DouyinNoteUploadRequest,
    DouyinVideoUploadRequest,
    KuaishouNoteUploadRequest,
    KuaishouVideoUploadRequest,
    XiaohongshuNoteUploadRequest,
    XiaohongshuVideoUploadRequest,
    check_bilibili_account,
    check_douyin_account,
    check_kuaishou_account,
    check_xiaohongshu_account,
    login_bilibili_account,
    login_douyin_account,
    login_kuaishou_account,
    login_xiaohongshu_account,
    parse_schedule,
    parse_tags,
    upload_bilibili_video,
    upload_kuaishou_note,
    upload_kuaishou_video,
    upload_note,
    upload_video,
    upload_xiaohongshu_note,
    upload_xiaohongshu_video,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
UPLOAD_ROOT = Path(BASE_DIR) / "web_uploads"

_INVALID_ACCOUNT_CHARS = re.compile(r'[<>:"/\\|?*\x00]')


def _run(coro):
    return asyncio.run(coro)


def _sanitize_account(name: str) -> str | None:
    name = (name or "").strip()
    if not name or len(name) > 128:
        return None
    if _INVALID_ACCOUNT_CHARS.search(name):
        return None
    return name


def _bool_field(form, key: str, default: bool) -> bool:
    raw = form.get(key)
    if raw is None:
        return default
    if isinstance(raw, str):
        return raw.strip().lower() in ("1", "true", "yes", "on")
    return bool(raw)


def _save_upload(fs, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    name = secure_filename(fs.filename or "file")
    path = dest / f"{uuid.uuid4().hex}_{name}"
    fs.save(path)
    return path


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/assets")
    app.config["MAX_CONTENT_LENGTH"] = 1600 * 1024 * 1024

    @app.get("/")
    def index():
        return send_from_directory(STATIC_DIR, "index.html")

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    @app.post("/api/login")
    def api_login():
        data = request.get_json(silent=True) or {}
        platform = (data.get("platform") or "").strip().lower()
        account = _sanitize_account(data.get("account") or "")
        if not account:
            return jsonify({"ok": False, "error": "账号别名无效（1–128 字，不能含路径或非法文件名字符）"}), 400

        headed = bool(data.get("headed", True))
        headless = not headed

        try:
            if platform == "douyin":
                result = _run(login_douyin_account(account, headless=headless))
            elif platform == "kuaishou":
                result = _run(login_kuaishou_account(account, headless=headless))
            elif platform == "xiaohongshu":
                result = _run(login_xiaohongshu_account(account, headless=headless))
            elif platform == "bilibili":
                result = _run(login_bilibili_account(account))
            else:
                return jsonify({"ok": False, "error": "未知平台"}), 400
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500

        if not result.get("success"):
            return jsonify(
                {
                    "ok": False,
                    "error": result.get("message") or "登录失败",
                    "account_file": result.get("account_file"),
                }
            ), 400

        return jsonify(
            {
                "ok": True,
                "message": result.get("message") or "登录完成",
                "account_file": result.get("account_file"),
            }
        )

    @app.post("/api/check")
    def api_check():
        data = request.get_json(silent=True) or {}
        platform = (data.get("platform") or "").strip().lower()
        account = _sanitize_account(data.get("account") or "")
        if not account:
            return jsonify({"ok": False, "error": "账号别名无效"}), 400

        try:
            if platform == "douyin":
                valid = _run(check_douyin_account(account))
            elif platform == "kuaishou":
                valid = _run(check_kuaishou_account(account))
            elif platform == "xiaohongshu":
                valid = _run(check_xiaohongshu_account(account))
            elif platform == "bilibili":
                valid = _run(check_bilibili_account(account))
            else:
                return jsonify({"ok": False, "error": "未知平台"}), 400
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500

        return jsonify({"ok": True, "valid": bool(valid)})

    @app.post("/api/upload/video")
    def api_upload_video():
        form = request.form
        platform = (form.get("platform") or "").strip().lower()
        account = _sanitize_account(form.get("account") or "")
        if not account:
            return jsonify({"ok": False, "error": "账号别名无效"}), 400

        fvideo = request.files.get("video")
        if not fvideo or not fvideo.filename:
            return jsonify({"ok": False, "error": "请选择视频文件"}), 400

        title = (form.get("title") or "").strip()
        if not title:
            return jsonify({"ok": False, "error": "请填写标题"}), 400

        desc = (form.get("desc") or "").strip()
        tags = parse_tags(form.get("tags") or "")
        schedule_raw = (form.get("schedule") or "").strip()
        publish_date: datetime | int = 0
        if schedule_raw:
            try:
                publish_date = parse_schedule(schedule_raw)
            except ValueError:
                return jsonify({"ok": False, "error": "定时格式应为 YYYY-MM-DD HH:MM"}), 400

        headless = _bool_field(form, "headless", True)
        debug = _bool_field(form, "debug", False)

        job_dir = UPLOAD_ROOT / uuid.uuid4().hex
        try:
            video_path = _save_upload(fvideo, job_dir)
            thumb_path = None
            fthumb = request.files.get("thumbnail")
            if fthumb and fthumb.filename:
                thumb_path = _save_upload(fthumb, job_dir)

            if platform == "douyin":
                strat = DOUYIN_PUBLISH_STRATEGY_SCHEDULED if schedule_raw else DOUYIN_PUBLISH_STRATEGY_IMMEDIATE
                req = DouyinVideoUploadRequest(
                    account_name=account,
                    video_file=video_path,
                    title=title,
                    description=desc,
                    tags=tags,
                    publish_date=publish_date,
                    thumbnail_file=thumb_path,
                    product_link=(form.get("product_link") or "").strip(),
                    product_title=(form.get("product_title") or "").strip(),
                    publish_strategy=strat,
                    debug=debug,
                    headless=headless,
                )
                _run(upload_video(req))
            elif platform == "kuaishou":
                strat = KUAISHOU_PUBLISH_STRATEGY_SCHEDULED if schedule_raw else KUAISHOU_PUBLISH_STRATEGY_IMMEDIATE
                req = KuaishouVideoUploadRequest(
                    account_name=account,
                    video_file=video_path,
                    title=title,
                    description=desc,
                    tags=tags,
                    publish_date=publish_date,
                    thumbnail_file=thumb_path,
                    publish_strategy=strat,
                    debug=debug,
                    headless=headless,
                )
                _run(upload_kuaishou_video(req))
            elif platform == "xiaohongshu":
                strat = XIAOHONGSHU_PUBLISH_STRATEGY_SCHEDULED if schedule_raw else XIAOHONGSHU_PUBLISH_STRATEGY_IMMEDIATE
                req = XiaohongshuVideoUploadRequest(
                    account_name=account,
                    video_file=video_path,
                    title=title,
                    description=desc,
                    tags=tags,
                    publish_date=publish_date,
                    thumbnail_file=thumb_path,
                    publish_strategy=strat,
                    debug=debug,
                    headless=headless,
                )
                _run(upload_xiaohongshu_video(req))
            elif platform == "bilibili":
                tid_raw = (form.get("tid") or "").strip()
                if not tid_raw.isdigit():
                    return jsonify({"ok": False, "error": "B 站上传需要填写分区 tid（数字）"}), 400
                tid = int(tid_raw)
                req = BilibiliVideoUploadRequest(
                    account_name=account,
                    video_file=video_path,
                    title=title,
                    description=desc or title,
                    tid=tid,
                    tags=tags,
                    publish_date=publish_date,
                )
                _run(upload_bilibili_video(req))
            else:
                return jsonify({"ok": False, "error": "未知平台"}), 400
        except RuntimeError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500
        finally:
            shutil.rmtree(job_dir, ignore_errors=True)

        return jsonify({"ok": True, "message": "上传任务已执行完成（若页面有延迟，以平台后台为准）"})

    @app.post("/api/upload/note")
    def api_upload_note():
        form = request.form
        platform = (form.get("platform") or "").strip().lower()
        account = _sanitize_account(form.get("account") or "")
        if not account:
            return jsonify({"ok": False, "error": "账号别名无效"}), 400

        files = request.files.getlist("images")
        files = [f for f in files if f and f.filename]
        if not files:
            return jsonify({"ok": False, "error": "请至少选择一张图片"}), 400

        title = (form.get("title") or "").strip()
        if not title:
            return jsonify({"ok": False, "error": "请填写标题"}), 400

        note = (form.get("note") or "").strip()
        tags = parse_tags(form.get("tags") or "")
        schedule_raw = (form.get("schedule") or "").strip()
        publish_date: datetime | int = 0
        if schedule_raw:
            try:
                publish_date = parse_schedule(schedule_raw)
            except ValueError:
                return jsonify({"ok": False, "error": "定时格式应为 YYYY-MM-DD HH:MM"}), 400

        headless = _bool_field(form, "headless", True)
        debug = _bool_field(form, "debug", False)

        job_dir = UPLOAD_ROOT / uuid.uuid4().hex
        try:
            paths: list[Path] = []
            for fs in files:
                paths.append(_save_upload(fs, job_dir))

            if platform == "douyin":
                strat = DOUYIN_PUBLISH_STRATEGY_SCHEDULED if schedule_raw else DOUYIN_PUBLISH_STRATEGY_IMMEDIATE
                req = DouyinNoteUploadRequest(
                    account_name=account,
                    image_files=paths,
                    title=title,
                    note=note,
                    tags=tags,
                    publish_date=publish_date,
                    publish_strategy=strat,
                    debug=debug,
                    headless=headless,
                )
                _run(upload_note(req))
            elif platform == "kuaishou":
                strat = KUAISHOU_PUBLISH_STRATEGY_SCHEDULED if schedule_raw else KUAISHOU_PUBLISH_STRATEGY_IMMEDIATE
                req = KuaishouNoteUploadRequest(
                    account_name=account,
                    image_files=paths,
                    title=title,
                    note=note,
                    tags=tags,
                    publish_date=publish_date,
                    publish_strategy=strat,
                    debug=debug,
                    headless=headless,
                )
                _run(upload_kuaishou_note(req))
            elif platform == "xiaohongshu":
                strat = XIAOHONGSHU_PUBLISH_STRATEGY_SCHEDULED if schedule_raw else XIAOHONGSHU_PUBLISH_STRATEGY_IMMEDIATE
                req = XiaohongshuNoteUploadRequest(
                    account_name=account,
                    image_files=paths,
                    title=title,
                    note=note,
                    tags=tags,
                    publish_date=publish_date,
                    publish_strategy=strat,
                    debug=debug,
                    headless=headless,
                )
                _run(upload_xiaohongshu_note(req))
            else:
                return jsonify({"ok": False, "error": "图文上传仅支持 抖音 / 快手 / 小红书"}), 400
        except RuntimeError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500
        finally:
            shutil.rmtree(job_dir, ignore_errors=True)

        return jsonify({"ok": True, "message": "图文发布流程已执行完成"})

    return app
