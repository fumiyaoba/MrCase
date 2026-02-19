import re
from datetime import datetime, timezone, timedelta

from slack_sdk import WebClient
from openpyxl import load_workbook
import MRCASE.env as env
from typing import List
from MRCASE.models.manhour_entry import ManHourEntry

EXCEL_FILE = "casetest.xlsx"

# 必須3項目だけを「どこにあっても」抜く
RE_PROJECT  = re.compile(r"案件名\s*=\s*([^,\n]+)")
RE_ASSIGNEE = re.compile(r"担当者\s*=\s*([^,\n]+)")
RE_HOURS    = re.compile(r"時間\s*=\s*(\d+(?:\.\d+)?)")

def pick_message_with_text(messages: List[ManHourEntry]) -> dict | None:
    for msg in messages:
        if msg.get("ts") and msg.get("user") and msg.get("text") and msg["text"].strip():
            return msg
    return None

def parse_fields(text: str):
    # 本文全体から検索（改行があってもOK）
    m1 = RE_PROJECT.search(text)
    m2 = RE_ASSIGNEE.search(text)
    m3 = RE_HOURS.search(text)

    if not (m1 and m2 and m3):
        return None

    project = m1.group(1).strip()
    assignee = m2.group(1).strip()
    hours = float(m3.group(1))
    return project, assignee, hours

def main():
    client = WebClient(token=env.SLACK_BOT_TOKEN)
    channel_id = env.SLACK_CHANNEL_ID

    resp = client.conversations_history(channel=channel_id)
    messages = resp.get("messages", [])
    if not messages:
        print("メッセージなし")
        return

    msg = pick_message_with_text(messages)
    if not msg:
        print("textが入っているメッセージが見つかりませんでした")
        return

    slack_ts = msg["ts"]
    user_id = msg.get("user")
    text_raw = msg.get("text", "")

    parsed = parse_fields(text_raw)
    if parsed:
        project, assignee, hours = parsed
    else:
        project = assignee = None
        hours = None

    # ts → JST
    jst = timezone(timedelta(hours=9))
    dt_jst = datetime.fromtimestamp(float(slack_ts), tz=timezone.utc).astimezone(jst)

    wb = load_workbook(EXCEL_FILE)
    ws = wb["raw"]

    ws.append([slack_ts, dt_jst.isoformat(), user_id, project, assignee, hours, text_raw])
    wb.save(EXCEL_FILE)

    print("1行書き込みました")
    print("parsed:", (project, assignee, hours))

if __name__ == "__main__":
    main()
