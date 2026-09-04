"""關鍵字比對、公告類型排除、民國年日期解析與「是否還在投標期限內」判斷。"""

from __future__ import annotations

import datetime as dt
import re

from . import config

_ROC_DATETIME_RE = re.compile(r"(\d{2,3})/(\d{1,2})/(\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?")


def match_keyword_groups(title: str) -> list[str]:
    """回傳標題命中的分類名稱（可能同時命中多個），沒命中則回傳空 list。"""
    return [
        group_name
        for group_name, synonyms in config.KEYWORD_GROUPS.items()
        if any(word in title for word in synonyms)
    ]


def is_excluded_announcement(brief_type: str) -> bool:
    """判斷是不是決標/無法決標/廢標等已經不算「招標中」的公告類型。"""
    return any(keyword in brief_type for keyword in config.EXCLUDED_ANNOUNCEMENT_TYPE_KEYWORDS)


def parse_roc_datetime(value: str) -> dt.datetime | None:
    """把「115/07/21 08:00」這種民國年字串轉成 Gregorian datetime，方便比較大小。

    格式不合法或空字串回傳 None；只有日期沒有時間時，時間視為 00:00。
    """
    if not value:
        return None
    match = _ROC_DATETIME_RE.search(value)
    if not match:
        return None
    roc_year, month, day, hour, minute = match.groups()
    try:
        return dt.datetime(
            int(roc_year) + 1911, int(month), int(day), int(hour or 0), int(minute or 0)
        )
    except ValueError:
        return None


def is_still_open(detail: dict, now: dt.datetime) -> bool:
    """依「截止投標」欄位判斷這個標案是否還在投標期限內（因此必然還沒決標）。"""
    deadline = parse_roc_datetime(detail.get("領投開標:截止投標", ""))
    if deadline is None:
        return False
    return deadline >= now


def is_security_sensitive(detail: dict) -> bool:
    """官方欄位本身的「國安/資安疑慮」旗標，命中就額外算資安類（見 config.SECURITY_SENSITIVE_FIELD）。"""
    return detail.get(config.SECURITY_SENSITIVE_FIELD, "") == "是"
