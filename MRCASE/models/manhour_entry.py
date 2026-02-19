from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class ManHourEntry:
    project: str     # 案件名
    assignee: str    # 担当者
    hours: float     # 時間
    work_date: date  # 日付
