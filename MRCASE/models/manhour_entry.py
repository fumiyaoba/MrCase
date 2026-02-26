from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass(frozen=True)
class ManHourEntry:
    case_key: str          # ユニークキー（8桁）
    hours: float           # 時間
    work_date: date        # 日付（省略時は送信日）
    assignee: Optional[str] = None  # 担当者（省略時はSlackユーザーから取得）
