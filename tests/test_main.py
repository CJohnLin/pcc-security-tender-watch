import datetime as dt
from unittest.mock import patch

from pcc_tender_watch import main


def test_skip_reason_none_when_time_and_day_ok(tmp_path):
    marker = str(tmp_path / "last_success_date.txt")
    now = dt.datetime(2026, 9, 17, 9, 0)  # 週四，早上 9 點
    with patch("pcc_tender_watch.main.filters.is_non_working_day", return_value=False):
        assert main._unattended_skip_reason(now, marker) is None


def test_skip_reason_before_earliest_hour(tmp_path):
    marker = str(tmp_path / "last_success_date.txt")
    now = dt.datetime(2026, 9, 17, 7, 30)  # 還沒到 8 點
    with patch("pcc_tender_watch.main.filters.is_non_working_day", return_value=False):
        reason = main._unattended_skip_reason(now, marker)
    assert reason is not None
    assert "8:00" in reason


def test_skip_reason_already_ran_today(tmp_path):
    marker = str(tmp_path / "last_success_date.txt")
    now = dt.datetime(2026, 9, 17, 9, 0)
    main._write_last_success_date(marker, now.date())
    with patch("pcc_tender_watch.main.filters.is_non_working_day", return_value=False):
        reason = main._unattended_skip_reason(now, marker)
    assert reason is not None
    assert "已經成功執行過" in reason


def test_skip_reason_different_day_runs_again(tmp_path):
    marker = str(tmp_path / "last_success_date.txt")
    main._write_last_success_date(marker, dt.date(2026, 9, 16))
    now = dt.datetime(2026, 9, 17, 9, 0)
    with patch("pcc_tender_watch.main.filters.is_non_working_day", return_value=False):
        assert main._unattended_skip_reason(now, marker) is None


def test_skip_reason_holiday(tmp_path):
    marker = str(tmp_path / "last_success_date.txt")
    now = dt.datetime(2026, 9, 19, 9, 0)  # 週六
    with patch("pcc_tender_watch.main.filters.is_non_working_day", return_value=True):
        reason = main._unattended_skip_reason(now, marker)
    assert reason is not None
    assert "假日" in reason
