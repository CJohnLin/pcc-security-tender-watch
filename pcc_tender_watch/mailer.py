"""用 Gmail SMTP + App Password 寄送通知信。"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

from . import config

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


def send_email(subject: str, html_body: str) -> None:
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "缺少寄信憑證：請設定環境變數 GMAIL_ADDRESS 與 GMAIL_APP_PASSWORD"
            "（GitHub Actions 執行時來自 repo Secrets）。"
        )

    message = MIMEText(html_body, "html", "utf-8")
    message["Subject"] = subject
    message["From"] = config.GMAIL_ADDRESS
    message["To"] = config.RECIPIENT_EMAIL

    with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
        server.starttls()
        server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
        server.send_message(message)
