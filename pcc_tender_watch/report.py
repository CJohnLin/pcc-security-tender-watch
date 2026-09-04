"""把篩選後的標案清單組成一個可以直接雙擊開啟的獨立 HTML 檔案。"""

from __future__ import annotations

import html

_PAGE_STYLE = """
body{font-family:-apple-system,"Segoe UI",sans-serif;font-size:14px;margin:24px;color:#222;}
h1{font-size:18px;}
table{border-collapse:collapse;width:100%;margin-top:12px;}
th,td{border:1px solid #ccc;padding:6px 10px;text-align:left;vertical-align:top;}
th{background:#f2f2f2;}
tr:nth-child(even){background:#fafafa;}
pre{white-space:pre-wrap;background:#fff3f3;border:1px solid #e0a0a0;padding:12px;}
"""

_COLUMNS = [
    ("categories", "分類"),
    ("stage", "階段"),
    ("agency", "機關名稱"),
    ("case_number", "標案案號"),
    ("title", "標案名稱"),
    ("announce_date", "公告日"),
    ("deadline", "截止投標/徵求期限"),
    ("open_time", "開標時間"),
    ("budget", "預算金額"),
]


def _cell(value: str) -> str:
    return f"<td>{html.escape(value or '')}</td>"


def _page(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang=zh-Hant><head><meta charset=utf-8>"
        f"<title>{html.escape(title)}</title><style>{_PAGE_STYLE}</style></head>"
        f"<body><h1>{html.escape(title)}</h1>{body}</body></html>"
    )


def build_report_html(tenders: list[dict], run_time: str) -> str:
    title = f"政府標案通知 - {run_time}"

    if not tenders:
        body = f"<p>{run_time} 查詢完成，目前沒有符合「資安」「網路設備」條件、且還在投標期限內的標案。</p>"
        return _page(title, body)

    header = "".join(f"<th>{label}</th>" for _, label in _COLUMNS)
    rows = []
    for tender in tenders:
        cells = []
        for key, _ in _COLUMNS:
            value = tender[key]
            if key == "categories":
                value = "、".join(value)
            cells.append(_cell(value))
        rows.append(f"<tr>{''.join(cells)}</tr>")

    body = (
        f"<p>{run_time} 查詢完成，共 {len(tenders)} 件符合條件、還在投標期限內的標案：</p>"
        f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )
    return _page(title, body)


def build_failure_html(run_time: str, error_message: str) -> str:
    title = f"政府標案通知 - {run_time}（查詢失敗）"
    body = (
        f"<p>{run_time} 的標案查詢執行失敗：</p>"
        f"<pre>{html.escape(error_message)}</pre>"
    )
    return _page(title, body)
