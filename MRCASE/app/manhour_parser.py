from __future__ import annotations

from datetime import date
from typing import Dict, List

from MRCASE import env
from MRCASE.models.manhour_entry import ManHourEntry  # あなたの実ファイル名に合わせて変更


def _normalize(s: str) -> str:
    """空白除去 + 前後trim"""
    return s.replace(" ", "").strip()


def _parse_kv_line(line: str) -> Dict[str, str]:
    """
    '案件名=..., 担当者=..., 時間=..., 日付=...[, 単位=h]' のような1行を
    {key: value} に変換する（余分なフィールドはそのまま入る）
    """
    parts = [p.strip() for p in line.split(",") if p.strip()]
    kv: Dict[str, str] = {}

    for p in parts:
        if "=" not in p:
            continue
        k, v = p.split("=", 1)
        kv[_normalize(k)] = v.strip()

    return kv


def parse_man_hour_message(text: str) -> List[ManHourEntry]:
    """
    Slackメッセージ text を解析して ManHourEntry の配列に変換する。
    - 先頭行が env.ADD_MAN_HOUR と一致するメッセージのみ対象（空白揺れ吸収）
    - 2行目以降を1行ずつ key=value として解析
    - env.KEY_* で指定した必須キーが揃った行だけ採用
    - それ以外のフィールド（例：単位=h）は無視
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []

    # 先頭行チェック
    if _normalize(lines[0]) != _normalize(env.ADD_MAN_HOUR):
        return []

    required_project = _normalize(env.KEY_PROJECT)
    required_assignee = _normalize(env.KEY_ASSIGNEE)
    required_hours = _normalize(env.KEY_TIME)
    required_date = _normalize(env.KEY_DATE)

    entries: List[ManHourEntry] = []

    for line in lines[1:]:
        kv = _parse_kv_line(line)

        # 必須項目が揃っていない行はスキップ
        if (
            required_project not in kv
            or required_assignee not in kv
            or required_hours not in kv
            or required_date not in kv
        ):
            continue

        try:
            entries.append(
                ManHourEntry(
                    project=kv[required_project].strip(),
                    assignee=kv[required_assignee].strip(),
                    hours=float(kv[required_hours]),
                    work_date=date.fromisoformat(kv[required_date]),
                )
            )
        except (ValueError, TypeError):
            # 数値変換/日付変換に失敗した行はスキップ
            continue

    return entries
