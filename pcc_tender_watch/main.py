"""每天執行一次的進入點：

抓政府電子採購網「資安」「網路設備」相關、目前還在投標期限內（尚未決標）的標案，
整理成 HTML 表格 Email 通知。查詢過程中任何一步失敗，改寄一封失敗通知信，並讓程式
以非零結束碼結束，讓 GitHub Actions 那次執行也顯示失敗（雙重提醒，不只靠 email）。
"""

from __future__ import annotations

import datetime as dt

from . import config, filters, mailer, pcc_client, report

TenderKey = tuple[str, str]


def _collect_candidates(now: dt.datetime) -> dict[TenderKey, list[str]]:
    """掃過去 LOOKBACK_DAYS 天的公告列表，回傳 {(unit_id, job_number): 命中的分類} 的候選清單（已去重）。"""
    candidates: dict[TenderKey, list[str]] = {}
    for offset in range(config.LOOKBACK_DAYS):
        date_str = (now - dt.timedelta(days=offset)).strftime("%Y%m%d")
        for record in pcc_client.list_by_date(date_str):
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


def _resolve_open_tenders(candidates: dict[TenderKey, list[str]], now: dt.datetime) -> list[dict]:
    """對每個候選標案抓完整資料，過濾掉已決標/已截止的，回傳依截止投標時間排序好的清單。"""
    tenders = []
    for (unit_id, job_number), categories in candidates.items():
        result = pcc_client.get_tender_detail(unit_id, job_number)
        if result is None or filters.is_excluded_announcement(result["brief_type"]):
            continue

        detail = result["detail"]
        if not filters.is_still_open(detail, now):
            continue

        if filters.is_security_sensitive(detail) and "資安" not in categories:
            categories = [*categories, "資安"]

        tenders.append(
            {
                "categories": categories,
                "agency": detail.get("機關資料:機關名稱", ""),
                "title": detail.get("採購資料:標案名稱", ""),
                "announce_date": detail.get("招標資料:公告日", ""),
                "deadline": detail.get("領投開標:截止投標", ""),
                "open_time": detail.get("領投開標:開標時間", ""),
                "budget": detail.get("採購資料:預算金額", ""),
            }
        )

    tenders.sort(key=lambda t: filters.parse_roc_datetime(t["deadline"]) or dt.datetime.max)
    return tenders


def run(now: dt.datetime | None = None) -> list[dict]:
    now = now or dt.datetime.now()
    candidates = _collect_candidates(now)
    return _resolve_open_tenders(candidates, now)


def main() -> None:
    now = dt.datetime.now()
    run_date = now.strftime("%Y-%m-%d")

    try:
        tenders = run(now)
    except Exception as exc:  # noqa: BLE001 - 故意攔截所有例外，改寄失敗通知信
        mailer.send_email(
            f"[政府標案通知] {run_date} 查詢失敗",
            report.build_failure_html(run_date, str(exc)),
        )
        raise

    mailer.send_email(
        f"[政府標案通知] {run_date} 資安/網路設備標案 {len(tenders)} 件",
        report.build_success_html(tenders, run_date),
    )


if __name__ == "__main__":
    main()
