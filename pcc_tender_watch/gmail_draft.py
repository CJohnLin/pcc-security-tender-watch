"""Gmail API 整合：建立一封草稿信（不會寄出），把 HTML 報表以附件形式夾帶。

用獨立的 OAuth 應用程式（Google Cloud Console 申請），不透過 Claude 的連接器，
因為連接器只有 Claude session 主動執行時才能呼叫，Windows 工作排程器觸發的
獨立執行檔沒有 Claude session，接不到連接器（見 docs/adr/0003）。

第一次執行需要互動式登入（跳出瀏覽器要求同意權限），之後的授權會存在 token.json，
排程執行時靜默用它刷新，不會再跳瀏覽器。
"""

from __future__ import annotations

import base64
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from . import config

_SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
_DRAFTS_URL = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"


def _get_credentials() -> Credentials:
    creds: Credentials | None = None
    if os.path.exists(config.GOOGLE_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(config.GOOGLE_TOKEN_PATH, _SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not os.path.exists(config.GOOGLE_CREDENTIALS_PATH):
            raise RuntimeError(
                f"找不到 Gmail OAuth 憑證檔案：{config.GOOGLE_CREDENTIALS_PATH}。"
                "需要先從 Google Cloud Console 下載 OAuth 用戶端 ID 的 JSON，"
                "放在這個路徑（或用 GOOGLE_CREDENTIALS_PATH 環境變數指定）。"
            )
        flow = InstalledAppFlow.from_client_secrets_file(config.GOOGLE_CREDENTIALS_PATH, _SCOPES)
        creds = flow.run_local_server(port=0)

    with open(config.GOOGLE_TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    return creds


def _build_raw_message(
    to: list[str], cc: list[str], subject: str, body_text: str, attachment_path: str
) -> str:
    msg = MIMEMultipart()
    msg["To"] = ", ".join(to)
    msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    with open(attachment_path, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="html")
    part.add_header(
        "Content-Disposition", "attachment", filename=os.path.basename(attachment_path)
    )
    msg.attach(part)

    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def create_draft(
    to: list[str], cc: list[str], subject: str, body_text: str, attachment_path: str
) -> str:
    """建立一封 Gmail 草稿（絕對不會寄出），HTML 檔案以附件形式夾帶。回傳草稿 ID。"""
    creds = _get_credentials()
    raw = _build_raw_message(to, cc, subject, body_text, attachment_path)
    response = requests.post(
        _DRAFTS_URL,
        headers={"Authorization": f"Bearer {creds.token}"},
        json={"message": {"raw": raw}},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["id"]
