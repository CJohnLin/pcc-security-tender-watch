"""g0v 政府採購公告 API（pcc-api.openfun.app）的薄包裝。

API 文件：https://pcc-api.openfun.app/skill.md
選用這個第三方 API 而非直接查詢政府電子採購網的理由見
docs/adr/0001-use-g0v-pcc-api.md。
"""

from __future__ import annotations

import time

import requests

from . import config

_SESSION = requests.Session()
if config.PCC_API_TOKEN:
    _SESSION.headers["Authorization"] = f"Bearer {config.PCC_API_TOKEN}"

_MAX_RETRIES = 3
_TIMEOUT_SECONDS = 20


def _get(path: str, **params: str) -> dict:
    url = f"{config.PCC_API_BASE}/{path}"
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        # 節流：沒有 Bearer Token 時，g0v API 有一個沒公開數字的短時間流量限制，
        # 實測每次請求間隔 config.REQUEST_DELAY_SECONDS（預設 2 秒）不會被 429 擋下來。
        # 有 Token 的話這個限制會放寬，但延遲不高，先不特別為有無 Token 分兩套邏輯。
        time.sleep(config.REQUEST_DELAY_SECONDS)
        try:
            response = _SESSION.get(url, params=params, timeout=_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError as exc:
            # 常見於完全沒有公告的日期：這個第三方 API 本身的 bug 會把 PHP 警告文字
            # 混進本來要回傳的 JSON 裡，導致解析失敗。這種失敗不是暫時性的（同一個
            # 日期重打幾次結果都一樣），重試沒有意義，直接放棄、不浪費時間等待。
            last_error = exc
            break
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"呼叫 g0v API 失敗：{url} {params}｜{type(last_error).__name__}: {last_error}") from last_error


def list_by_date(date: str) -> list[dict]:
    """date 為西元 YYYYMMDD。回傳當天所有公告的摘要列表（不分頁，一次回傳全部）。"""
    data = _get("listbydate", date=date)
    return data.get("records", [])


def get_tender_detail(unit_id: str, job_number: str) -> dict | None:
    """回傳某個標案代碼「最新一次」公告的完整欄位（含公告類型），查無資料回傳 None。

    /api/tender 會回傳這個標案代碼底下的歷次公告（原始公告、更正公告…），
    我們只關心最新一次公告的狀態與欄位。
    """
    data = _get("tender", unit_id=unit_id, job_number=job_number)
    records = data.get("records", [])
    if not records:
        return None
    latest = records[-1]
    return {
        "brief_type": latest.get("brief", {}).get("type", ""),
        "detail": latest.get("detail", {}),
    }
