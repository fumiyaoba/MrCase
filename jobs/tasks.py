"""
jobs/tasks.py
毎日 0:00 (Asia/Tokyo) に実行されるCeleryタスク
  1. Slackの当日メッセージを取得して ManHourRecord に登録
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

from jobs.models import Case, ManHourRecord
from MRCASE.app.filter import filter_by_first_line
from MRCASE.app.manhour_parser import parse_man_hour_message
from MRCASE.app.slack_ReadChannel import get_channel_messages

logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID", "")


# ------------------------------------------------------------------ #
#  メインタスク
# ------------------------------------------------------------------ #

@shared_task(name="jobs.tasks.nightly_import_and_export")
def nightly_import_and_export():
    """毎日0時に実行: Slack取得 → DB登録 → Excel出力 → Slack送信"""
    logger.info("nightly_import_and_export: start")

    imported = _import_from_slack()
    logger.info("nightly_import_and_export: imported %d records", imported)

    excel_bytes = _build_monthly_excel()
    logger.info("nightly_import_and_export: excel built (%d bytes)", len(excel_bytes))

    _upload_excel_to_slack(excel_bytes)
    logger.info("nightly_import_and_export: done")


# ------------------------------------------------------------------ #
#  手動実行用タスク
# ------------------------------------------------------------------ #

@shared_task(name="jobs.tasks.manual_import")
def manual_import():
    """手動で Slack → DB 取り込みだけ実行"""
    count = _import_from_slack()
    logger.info("manual_import: imported %d records", count)
    return count


@shared_task(name="jobs.tasks.manual_export")
def manual_export():
    """手動で Excel 生成 → Slack 送信だけ実行"""
    excel_bytes = _build_monthly_excel()
    _upload_excel_to_slack(excel_bytes)
    logger.info("manual_export: done")


# ------------------------------------------------------------------ #
#  内部処理
# ------------------------------------------------------------------ #

def _get_slack_username(user_id: str) -> str:
    """Slack の user_id から表示名を取得する"""
    if not user_id or not SLACK_BOT_TOKEN:
        return user_id or "不明"
    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        res = client.users_info(user=user_id)
        profile = res["user"]["profile"]
        # 日本語名 → 表示名 → ユーザー名 の優先順で取得
        return (
            profile.get("real_name_normalized")
            or profile.get("display_name")
            or res["user"].get("name")
            or user_id
        )
    except Exception as exc:
        logger.warning("Failed to get Slack username for %s: %s", user_id, exc)
        return user_id


def _ts_to_date(ts: str) -> date:
    """Slack の ts（UNIXタイムスタンプ文字列）を date に変換する"""
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).date()
    except (ValueError, TypeError):
        return date.today()


def _import_from_slack() -> int:
    """
    Slack チャンネルから工数登録メッセージを取得して ManHourRecord に保存。
    - 日付省略 → メッセージの送信日を使用
    - 担当者省略 → Slack の送信者名を使用
    """
    try:
        messages = get_channel_messages()
    except Exception as exc:
        logger.error("Slack get_channel_messages failed: %s", exc)
        return 0

    from MRCASE import env
    filtered = filter_by_first_line(messages, env.ADD_MAN_HOUR)

    imported = 0
    for msg in filtered:
        ts = msg.ts

        # メッセージの送信日を取得
        message_date = _ts_to_date(ts)

        # 送信者名を取得（担当者省略時に使う）
        sender_name = _get_slack_username(msg.user) if msg.user else "不明"

        entries = parse_man_hour_message(msg.text, message_date=message_date)

        for i, entry in enumerate(entries):
            unique_ts = f"{ts}_{i}"

            if ManHourRecord.objects.filter(source_ts=unique_ts).exists():
                continue

            # 担当者: メッセージに指定があればそちら優先、なければ送信者名
            assignee = entry.assignee or sender_name

            # ユニークキーでCase検索
            case = Case.objects.filter(unique_key=entry.case_key, is_active=True).first()

            ManHourRecord.objects.create(
                case=case,
                project_name=case.name if case else entry.case_key,
                assignee=assignee,
                work_date=entry.work_date,
                hours=entry.hours,
                source_ts=unique_ts,
            )
            imported += 1

    return imported


def _build_monthly_excel() -> bytes:
    """当月分の ManHourRecord を rawシートに書き出して bytes で返す"""
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
        ws.append([
            r.work_date.isoformat(),
            r.project_name,
            r.assignee,
            float(r.hours),
        ])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _upload_excel_to_slack(excel_bytes: bytes) -> None:
    """Excel を Slack チャンネルへ送信"""
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
