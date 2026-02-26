"""
jobs/tasks.py
毎日 0:00 (Asia/Tokyo) に実行されるCeleryタスク
  1. Slackの前回取得以降のメッセージを取得して ManHourRecord に登録
  2. 当月分の工数を Excel (rawシート) に出力
  3. 出力した Excel を Slack にアップロード
"""

from __future__ import annotations

import io
import logging
import os
from datetime import date, datetime, timezone

from celery import shared_task
from openpyxl import Workbook
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from jobs.models import Case, ManHourRecord, SlackImportState
from MRCASE.app.filter import filter_by_first_line
from MRCASE.app.manhour_parser import parse_man_hour_message

logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID", "")


# ------------------------------------------------------------------ #
#  メインタスク
# ------------------------------------------------------------------ #

@shared_task(name="jobs.tasks.nightly_import_and_export")
def nightly_import_and_export():
    logger.info("nightly_import_and_export: start")
    imported = _import_from_slack()
    logger.info("nightly_import_and_export: imported %d records", imported)
    excel_bytes = _build_monthly_excel()
    _upload_excel_to_slack(excel_bytes)
    logger.info("nightly_import_and_export: done")


# ------------------------------------------------------------------ #
#  手動実行用タスク
# ------------------------------------------------------------------ #

@shared_task(name="jobs.tasks.manual_import")
def manual_import():
    count = _import_from_slack()
    logger.info("manual_import: imported %d records", count)
    return count


@shared_task(name="jobs.tasks.manual_export")
def manual_export():
    excel_bytes = _build_monthly_excel()
    _upload_excel_to_slack(excel_bytes)
    logger.info("manual_export: done")


# ------------------------------------------------------------------ #
#  内部処理
# ------------------------------------------------------------------ #

_user_cache: dict = {}

def _get_slack_username(user_id: str) -> str:
    """Slack の user_id から表示名を取得する（キャッシュあり）"""
    if user_id in _user_cache:
        return _user_cache[user_id]

    if not user_id or not SLACK_BOT_TOKEN:
        return user_id or "不明"
    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        res = client.users_info(user=user_id)
        profile = res["user"]["profile"]
        name = (
            profile.get("real_name_normalized")
            or profile.get("display_name")
            or res["user"].get("name")
            or user_id
        )
        # ゼロ幅スペースなど不可視文字を除去
        name = "".join(c for c in name if c.isprintable() and ord(c) != 0x200b)
        _user_cache[user_id] = name
        return name
    except Exception as exc:
        logger.warning("Failed to get Slack username for %s: %s", user_id, exc)
        return user_id


def _ts_to_date(ts: str) -> date:
    """Slack の ts を date に変換する"""
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).date()
    except (ValueError, TypeError):
        return date.today()


def _get_messages_since_last(oldest: str | None) -> list:
    """前回取得以降のメッセージを取得する"""
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        logger.error("Slack token or channel ID is not configured.")
        return []

    client = WebClient(token=SLACK_BOT_TOKEN)
    kwargs = {"channel": SLACK_CHANNEL_ID, "limit": 200}
    if oldest:
        kwargs["oldest"] = oldest

    try:
        response = client.conversations_history(**kwargs)
        return response.get("messages", [])
    except SlackApiError as exc:
        logger.error("Slack conversations_history failed: %s", exc.response["error"])
        return []


def _import_from_slack() -> int:
    """
    前回取得以降の工数登録メッセージをDBに保存。
    取得後に最新の ts を SlackImportState に記録。
    """
    from MRCASE import env

    # 前回の最終tsを取得
    state = SlackImportState.objects.first()
    oldest = state.last_ts if state else None

    raw_messages = _get_messages_since_last(oldest)
    if not raw_messages:
        return 0

    # SlackMessage に変換
    from MRCASE.models.slack_message import SlackMessage
    messages = [
        SlackMessage(
            text=m.get("text", ""),
            user=m.get("user"),
            ts=m["ts"],
            thread_ts=m.get("thread_ts"),
            raw=m,
        )
        for m in raw_messages
        if "ts" in m
    ]

    # 最新のtsを保存（messagesは新しい順で返ってくる）
    latest_ts = raw_messages[0]["ts"]

    filtered = filter_by_first_line(messages, env.ADD_MAN_HOUR)

    imported = 0
    for msg in filtered:
        ts = msg.ts
        message_date = _ts_to_date(ts)
        sender_name = _get_slack_username(msg.user) if msg.user else "不明"

        entries = parse_man_hour_message(msg.text, message_date=message_date)

        for i, entry in enumerate(entries):
            unique_ts = f"{ts}_{i}"

            if ManHourRecord.objects.filter(source_ts=unique_ts).exists():
                continue

            assignee = entry.assignee or sender_name
            case = Case.objects.filter(unique_key=entry.case_key, is_active=True).first()

            # 担当者名からDjangoユーザーを検索
            from django.contrib.auth.models import User
            user = (
                User.objects.filter(last_name=assignee).first()
                or User.objects.filter(username=assignee).first()
            )

            ManHourRecord.objects.create(
                case=case,
                user=user,
                project_name=case.name if case else entry.case_key,
                assignee=assignee,
                work_date=entry.work_date,
                hours=entry.hours,
                source_ts=unique_ts,
            )
            imported += 1

    # 最終tsを更新
    if state:
        state.last_ts = latest_ts
        state.save()
    else:
        SlackImportState.objects.create(last_ts=latest_ts)

    return imported


def _build_monthly_excel() -> bytes:
    today = date.today()
    records = ManHourRecord.objects.filter(
        work_date__year=today.year,
        work_date__month=today.month,
    ).order_by("work_date", "assignee")

    wb = Workbook()
    ws = wb.active
    ws.title = "raw"

    ws.append(["日付", "案件名", "担当者", "時間(h)"])
    for r in records:
        ws.append([r.work_date.isoformat(), r.project_name, r.assignee, float(r.hours)])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _upload_excel_to_slack(excel_bytes: bytes) -> None:
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        logger.error("Slack token or channel ID is not configured.")
        return

    today = date.today()
    filename = f"manhour_{today.year}{today.month:02d}.xlsx"

    client = WebClient(token=SLACK_BOT_TOKEN)
    try:
        client.files_upload_v2(
            channel=SLACK_CHANNEL_ID,
            filename=filename,
            content=excel_bytes,
            initial_comment=f"{today.year}年{today.month}月 工数レポートです。",
        )
    except SlackApiError as exc:
        logger.error("Slack file upload failed: %s", exc.response["error"])
        raise
