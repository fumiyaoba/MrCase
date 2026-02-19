from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Any
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from MRCASE import env
from MRCASE.models.manhour_entry import ManHourEntry

def open_sheet(excel_filepath: str | Path, excel_sheet_name: str) -> Worksheet:
    workbook = load_workbook(excel_filepath)
    worksheet = workbook[excel_sheet_name] if excel_sheet_name else workbook[env.EXCEL_SHEET_RAW] if env.EXCEL_SHEET_RAW else workbook.active
    return worksheet

def _row_has_value(ws: Worksheet, row: int, cols: Iterable[int]) -> bool:
    """指定行に、指定列のどれか1つでも値があるか"""
    return any(ws.cell(row=row, column=c).value not in (None, "") for c in cols)


def _find_next_row(
    worksheet: Worksheet,
    *,
    header_row: int,
    cols_to_check: list[int],
) -> int:
    """
    実データが入っている最終行 + 1 を返す。
    max_row は書式だけの行を拾うことがあるため、値の有無で判定する。
    """
    for r in range(worksheet.max_row, header_row, -1):
        if _row_has_value(worksheet, r, cols_to_check):
            return r + 1
    return header_row + 1


def _format_value(entry: ManHourEntry, attr: str) -> Any:
    """ManHourEntry の値を Excel 用に整形"""
    value = getattr(entry, attr)

    if attr == "work_date" and env.EXCEL_DATE_FORMAT == "iso":
        return value.isoformat()

    return value


def append_entries_to_excel(entries: Iterable[ManHourEntry], filepath: str | Path) -> Path:
    """
    既存の Excel ファイルに ManHourEntry を追記する。
    追記位置・列構成は env.py で制御。
    """
    path = Path(filepath)

    sheet_name = sheet_name if sheet_name is not None else env.EXCEL_SHEET_NAME
    header_row = header_row if header_row is not None else env.EXCEL_HEADER_ROW
    column_map = column_map if column_map is not None else env.EXCEL_COLUMN_MAP

    wb = load_workbook(path)
    ws = wb[sheet_name] if sheet_name else wb.active

    cols = sorted(column_map.keys())
    row = _find_next_row(ws, header_row=header_row, cols_to_check=cols)

    for entry in entries:
        for col, attr in column_map.items():
            ws.cell(row=row, column=col, value=_format_value(entry, attr))
        row += 1

    wb.save(path)
    return path
