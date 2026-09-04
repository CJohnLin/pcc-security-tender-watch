"""手動執行的進入點：

抓政府電子採購網「資安」「網路設備」相關、目前還在投標期限內（尚未決標）的標案，
輸出成本機 HTML 檔（見 docs/adr/0002-local-manual-exe-instead-of-cloud-schedule.md），
並自動用預設瀏覽器開啟。結尾會等使用者按 Enter 才結束，這樣打包成 .exe 雙擊執行時，
視窗不會在讀完結果前就自己關掉。
"""

from __future__ import annotations

import datetime as dt
import os
import sys
import webbrowser

from . import config, filters, pcc_client, report

TenderKey = tuple[str, str]


def _fix_windows_console_encoding() -> None:
    """Windows 主控台預設用系統代碼頁（cp950/cp437 等），直接印中文會變亂碼。

    切成 UTF-8 代碼頁並讓 stdout/stderr 改用 UTF-8 輸出，雙擊 .exe 或用 cmd.exe
    執行時中文才會正常顯示。非 Windows、或非終端機（沒有 stdout）時直接跳過。
    """
    if sys.platform != "win32":
        return
    os.system("chcp 65001 >NUL 2>&1")
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _collect_candidates(now: dt.datetime) -> dict[TenderKey, list[str]]:
    """掃過去 LOOKBACK_DAYS 天的公告列表，回傳 {(unit_id, job_number): 命中的分類} 的候選清單（已去重）。

    單一天查詢失敗（例如假日沒有公告時，g0v API 會回傳夾雜 PHP 警告文字的壞掉 JSON）
    不會讓整次執行失敗：印出警告、當作那天沒有資料、繼續掃下一天。
    """
    candidates: dict[TenderKey, list[str]] = {}
    for offset in range(config.LOOKBACK_DAYS):
        if offset > 0 and offset % 10 == 0:
            print(f"查詢進度：{offset}/{config.LOOKBACK_DAYS} 天...")
        date_str = (now - dt.timedelta(days=offset)).strftime("%Y%m%d")
        try:
            records = pcc_client.list_by_date(date_str)
        except RuntimeError as exc:
            print(f"警告：{date_str} 查詢失敗，跳過這一天。原因：{exc}", file=sys.stderr)
            continue
        for record in records:
            brief = record.get("brief", {})
            if filters.is_excluded_announcement(brief.get("type", "")):
                continue
            matched_categories = filters.match_keyword_groups(brief.get("title", ""))
            if not matched_categories:
                continue
            key = (record["unit_id"], record["job_number"])
            existing = candidates.setdefault(key, [])
            for category in matched_categories:
                if category not in existing:
                    existing.append(category)
    return candidates


# 正式招標公告跟「公開徵求廠商提供參考資料公告」（RFI，還沒進入正式招標程序的市場調查）
# 用的是兩套完全不同的欄位命名（前綴分別是「機關資料/採購資料/招標資料/領投開標」跟「標案內容」）。
# 用別名清單依序找，抓到第一個有值的就用；RFI 沒有預算金額、也沒有分開的截止投標/開標時間，
# 這些欄位就會維持空字串，是預期行為、不是漏抓。
_FIELD_ALIASES = {
    "agency": ["機關資料:機關名稱", "標案內容:機關名稱"],
    "case_number": ["採購資料:標案案號", "標案內容:標案案號"],
    "title": ["採購資料:標案名稱", "標案內容:標案名稱"],
    "announce_date": ["招標資料:公告日", "標案內容:公告日期"],
    "budget": ["採購資料:預算金額"],
    "open_time": ["領投開標:開標時間"],
}
# 期限欄位語意不同（截止投標是單一時間點，公開徵求期間是「起－迄」區間），
# 但 filters.is_still_open / parse_roc_period_end 兩種格式都吃得下，所以用同一套別名找法即可。
_DEADLINE_ALIASES = ["領投開標:截止投標", "標案內容:公開徵求期間"]


def _first_present(detail: dict, keys: list[str]) -> str:
    for key in keys:
        value = detail.get(key)
        if value:
            return value
    return ""


def _stage_label(brief_type: str) -> str:
    return "徵求" if "徵求" in brief_type else "招標"


def _resolve_open_tenders(candidates: dict[TenderKey, list[str]], now: dt.datetime) -> list[dict]:
    """對每個候選標案抓完整資料，過濾掉已決標/已過期的，回傳依期限排序好的清單。"""
    tenders = []
    total = len(candidates)
    print(f"找到 {total} 個候選標案，開始查詢詳細資料...")
    for i, ((unit_id, job_number), categories) in enumerate(candidates.items(), start=1):
        if i > 1 and i % 10 == 0:
            print(f"查詢進度：{i}/{total} 筆候選...")
        result = pcc_client.get_tender_detail(unit_id, job_number)
        if result is None or filters.is_excluded_announcement(result["brief_type"]):
            continue

        detail = result["detail"]
        deadline = _first_present(detail, _DEADLINE_ALIASES)
        if not filters.is_still_open(deadline, now):
            continue

        if filters.is_security_sensitive(detail) and "資安" not in categories:
            categories = [*categories, "資安"]

        tenders.append(
            {
                "categories": categories,
                "stage": _stage_label(result["brief_type"]),
                "agency": _first_present(detail, _FIELD_ALIASES["agency"]),
                "case_number": _first_present(detail, _FIELD_ALIASES["case_number"]),
                "title": _first_present(detail, _FIELD_ALIASES["title"]),
                "announce_date": _first_present(detail, _FIELD_ALIASES["announce_date"]),
                "deadline": deadline,
                "open_time": _first_present(detail, _FIELD_ALIASES["open_time"]),
                "budget": _first_present(detail, _FIELD_ALIASES["budget"]),
            }
        )

    tenders.sort(key=lambda t: filters.parse_roc_period_end(t["deadline"]) or dt.datetime.max)
    return tenders


def run(now: dt.datetime | None = None) -> list[dict]:
    now = now or dt.datetime.now()
    candidates = _collect_candidates(now)
    return _resolve_open_tenders(candidates, now)


def _write_html(html_content: str, run_time: dt.datetime) -> str:
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    filename = f"tenders_{run_time.strftime('%Y%m%d_%H%M%S')}.html"
    path = os.path.join(config.OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return os.path.abspath(path)


def _pause() -> None:
    try:
        input("\n按 Enter 鍵結束...")
    except EOFError:
        pass


def main() -> None:
    _fix_windows_console_encoding()

    now = dt.datetime.now()
    run_time_label = now.strftime("%Y-%m-%d %H:%M")
    print(f"開始查詢，結果會存到：{os.path.abspath(config.OUTPUT_DIR)}（往回掃 {config.LOOKBACK_DAYS} 天，可能需要幾分鐘）")

    try:
        tenders = run(now)
    except Exception as exc:  # noqa: BLE001 - 故意攔截所有例外，改輸出失敗頁面
        path = _write_html(report.build_failure_html(run_time_label, str(exc)), now)
        print(f"查詢失敗，錯誤已寫入：{path}", file=sys.stderr)
        webbrowser.open(f"file://{path}")
        _pause()
        raise

    path = _write_html(report.build_report_html(tenders, run_time_label), now)
    print(f"完成，共找到 {len(tenders)} 筆標案，結果已寫入：{path}")
    webbrowser.open(f"file://{path}")
    _pause()


if __name__ == "__main__":
    main()
