from typing import List
from datetime import datetime

import openpyxl

import yaml_


def init_sheet() -> None:
    global wb, ws

    wb = openpyxl.Workbook(write_only=True)

    ws = wb.create_sheet()
    ws.title = "크롤링 데이터"
    ws.append(yaml_.sheet_headers)


def append_to_sheet(row: List) -> None:
    ws.append(row)


def save_sheet() -> None:
    wb.save(f"크롤링 - {datetime.now()}.xlsx")
