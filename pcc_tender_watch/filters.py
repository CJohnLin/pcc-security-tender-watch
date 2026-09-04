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


def _roc_groups_to_datetime(roc_year: str, month: str, day: str, hour: str, minute: str) -> dt.datetime | None:
    try:
        return dt.datetime(
            int(roc_year) + 1911, int(month), int(day), int(hour or 0), int(minute or 0)
        )
    except ValueError:
        return None


def parse_roc_datetime(value: str) -> dt.datetime | None:
    """把「115/07/21 08:00」這種民國年字串轉成 Gregorian datetime，方便比較大小。

    格式不合法或空字串回傳 None；只有日期沒有時間時，時間視為 00:00。
    """
    if not value:
        return None
    match = _ROC_DATETIME_RE.search(value)
    if not match:
        return None
    return _roc_groups_to_datetime(*match.groups())


def parse_roc_period_end(value: str) -> dt.datetime | None:
    """解析「公開徵求期間」這類「115/09/03 － 115/09/11」的日期區間欄位，回傳結束時間。

    不假設固定的分隔符號（實際觀察到的是全形「－」），直接抓字串裡所有民國年日期，
    取最後一個當結束時間；只有一個日期時，效果等同 parse_roc_datetime。
    """
    if not value:
        return None
    matches = _ROC_DATETIME_RE.findall(value)
    if not matches:
        return None
    return _roc_groups_to_datetime(*matches[-1])


def is_still_open(deadline_text: str, now: dt.datetime) -> bool:
    """判斷某個「期限」字串代表的時間是否還沒到（因此這個公告還在有效期內）。"""
    deadline = parse_roc_period_end(deadline_text)
    if deadline is None:
        return False
    return deadline >= now


def is_security_sensitive(detail: dict) -> bool:
    """官方欄位本身的「國安/資安疑慮」旗標，命中就額外算資安類（見 config.SECURITY_SENSITIVE_FIELD）。"""
    return detail.get(config.SECURITY_SENSITIVE_FIELD, "") == "是"
