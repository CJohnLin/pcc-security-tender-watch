import datetime as dt

from pcc_tender_watch import filters


def test_match_keyword_groups_matches_multiple_categories():
    assert set(filters.match_keyword_groups("XX機關防火牆設備汰換案")) == {"資安", "網路設備"}


def test_match_keyword_groups_no_match():
    assert filters.match_keyword_groups("辦公室桌椅採購案") == []


def test_is_excluded_announcement_true_for_award_notice():
    assert filters.is_excluded_announcement("公開招標決標公告") is True


def test_is_excluded_announcement_false_for_tender_notice():
    assert filters.is_excluded_announcement("公開招標公告") is False


def test_parse_roc_datetime_with_time():
    assert filters.parse_roc_datetime("115/07/21 08:30") == dt.datetime(2026, 7, 21, 8, 30)


def test_parse_roc_datetime_without_time():
    assert filters.parse_roc_datetime("115/07/21") == dt.datetime(2026, 7, 21, 0, 0)


def test_parse_roc_datetime_invalid_returns_none():
    assert filters.parse_roc_datetime("") is None
    assert filters.parse_roc_datetime("not a date") is None


def test_is_still_open_true_when_deadline_in_future():
    now = dt.datetime(2026, 9, 4, 9, 0)
    assert filters.is_still_open("115/09/15 09:00", now) is True


def test_is_still_open_false_when_deadline_passed():
    now = dt.datetime(2026, 9, 4, 9, 0)
    assert filters.is_still_open("115/08/01 09:00", now) is False


def test_is_still_open_false_when_no_deadline():
    now = dt.datetime(2026, 9, 4, 9, 0)
    assert filters.is_still_open("", now) is False


def test_parse_roc_period_end_single_date_matches_datetime():
    assert filters.parse_roc_period_end("115/09/15 09:00") == dt.datetime(2026, 9, 15, 9, 0)


def test_parse_roc_period_end_range_takes_last_date():
    # RFI（公開徵求廠商提供參考資料公告）用的「起－迄」區間格式
    assert filters.parse_roc_period_end("115/09/03 － 115/09/11") == dt.datetime(2026, 9, 11, 0, 0)


def test_parse_roc_period_end_invalid_returns_none():
    assert filters.parse_roc_period_end("") is None
    assert filters.parse_roc_period_end("not a date") is None


def test_is_still_open_true_for_rfi_period_not_yet_ended():
    now = dt.datetime(2026, 9, 4, 9, 0)
    assert filters.is_still_open("115/09/03 － 115/09/11", now) is True


def test_is_still_open_false_for_rfi_period_already_ended():
    now = dt.datetime(2026, 9, 20, 9, 0)
    assert filters.is_still_open("115/09/03 － 115/09/11", now) is False


def test_is_security_sensitive():
    field = "採購資料:本採購是否屬「具敏感性或國安(含資安)疑慮之業務範圍」採購"
    assert filters.is_security_sensitive({field: "是"}) is True
    assert filters.is_security_sensitive({field: "否"}) is False
    assert filters.is_security_sensitive({}) is False
