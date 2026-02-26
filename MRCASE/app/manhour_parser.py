from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from MRCASE import env
from MRCASE.models.manhour_entry import ManHourEntry


def _normalize(s: str) -> str:
    """空白除去 + 前後trim"""
    return s.replace(" ", "").replace("　", "").strip()


def _parse_kv_line(line: str) -> Dict[str, str]:
    """
    '案件=XXXX, 時間=2[, 日付=2026/02/17][, 担当者=大場]' のような1行を
    {key: value} に変換する
    """
    parts = [p.strip() for p in line.split(",") if p.strip()]
    kv: Dict[str, str] = {}

    for p in parts:
        if "=" not in p:
            continue
        k, v = p.split("=", 1)
        kv[_normalize(k)] = v.strip()

    return kv


def parse_man_hour_message(
    text: str,
    message_date: Optional[date] = None,
) -> List[ManHourEntry]:
    """
    Slackメッセージ text を解析して ManHourEntry の配列に変換する。

    - 先頭行が env.ADD_MAN_HOUR と一致するメッセージのみ対象
    - 2行目以降を1行ずつ key=value として解析
    - 案件・時間は必須、日付・担当者は省略可能
      - 日付省略時 → message_date（Slackの送信日）を使用
      - 担当者省略時 → None を返す（tasks.py 側でSlackユーザーから補完）
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []

    if _normalize(lines[0]) != _normalize(env.ADD_MAN_HOUR):
        return []

    today = message_date or date.today()

    required_case_key = _normalize(env.KEY_CASE)
    required_hours    = _normalize(env.KEY_TIME)
    optional_date     = _normalize(env.KEY_DATE)
    optional_assignee = _normalize(env.KEY_ASSIGNEE)

    entries: List[ManHourEntry] = []

    for line in lines[1:]:
        kv = _parse_kv_line(line)

        # 案件・時間は必須
        if required_case_key not in kv or required_hours not in kv:
            continue

        try:
            # 日付: 省略時はメッセージの送信日
            if optional_date in kv:
                work_date = date.fromisoformat(kv[optional_date])
            else:
                work_date = today

            # 担当者: 省略時はNone（tasks.pyでSlackから補完）
            assignee = kv.get(optional_assignee) or None

            entries.append(
                ManHourEntry(
                    case_key=kv[required_case_key].strip().upper(),
                    hours=float(kv[required_hours]),
                    work_date=work_date,
                    assignee=assignee,
                )
            )
        except (ValueError, TypeError):
            continue

    return entries
