"""把篩選後的標案清單組成 HTML email 內容。"""

from __future__ import annotations

import html

_TABLE_STYLE = "border-collapse:collapse;width:100%;font-family:sans-serif;font-size:14px;"
_TH_STYLE = "border:1px solid #ccc;padding:6px 10px;background:#f2f2f2;text-align:left;"
_TD_STYLE = "border:1px solid #ccc;padding:6px 10px;"

_COLUMNS = [
    ("categories", "分類"),
    ("agency", "機關名稱"),
    ("title", "標案名稱"),
    ("announce_date", "公告日"),
    ("deadline", "截止投標"),
    ("open_time", "開標時間"),
    ("budget", "預算金額"),
]


def _cell(value: str) -> str:
    return f'<td style="{_TD_STYLE}">{html.escape(value or "")}</td>'


def build_success_html(tenders: list[dict], run_date: str) -> str:
    if not tenders:
        return f"<p>{run_date} 查詢完成，目前沒有符合「資安」「網路設備」條件、且還在投標期限內的標案。</p>"

    header = "".join(f'<th style="{_TH_STYLE}">{label}</th>' for _, label in _COLUMNS)
    rows = []
    for tender in tenders:
        cells = []
        for key, _ in _COLUMNS:
            value = tender[key]
            if key == "categories":
                value = "、".join(value)
            cells.append(_cell(value))
        rows.append(f"<tr>{''.join(cells)}</tr>")

    return (
        f"<p>{run_date} 查詢完成，共 {len(tenders)} 件符合條件、還在投標期限內的標案：</p>"
        f'<table style="{_TABLE_STYLE}"><thead><tr>{header}</tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def build_failure_html(run_date: str, error_message: str) -> str:
    return (
        f"<p>{run_date} 的標案查詢執行失敗，請自行檢查（GitHub Actions 的執行紀錄會有完整錯誤訊息）。</p>"
        f"<pre>{html.escape(error_message)}</pre>"
    )
