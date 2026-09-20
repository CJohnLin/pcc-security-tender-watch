# 改在 Synology NAS 上跑排程，Windows 排程器只當備援

Windows 工作排程器在這台網域管理的筆電上不可靠（ADR-0002/0004）：固定時間觸發會因為電腦登出/睡眠整天不跑，「不論登入與否均執行」需要 IT 才能開的「以批次工作登入」權限，改成「登入/解鎖時觸發」又依賴使用者作息。GitHub Actions 等雲端環境則被 g0v API 的 Cloudflare 以 403 擋掉。

使用者有一台全年開機的 Synology NAS（DS425+，DSM 7.4.1）。實測從 NAS 出去的網路可以正常呼叫 g0v API（HTTP 200，沒有被擋）、Gmail API 與假日日曆資料來源，NAS 時區是台灣時間，所以固定每天 08:00 的 DSM「工作排程器」就能解決「電腦沒登入就漏跑」的問題，不再需要靠登入/解鎖事件推測時機。

做法：
- NAS 只有 Python 3.8，沒有 pip；用內建的 `venv` + `ensurepip` 在 `~/pcc/venv` 建虛擬環境、安裝 `requirements.txt`。程式碼為此改成 3.8 相容（模組層級的 `tuple[str, str]` 改用 `typing.Tuple`，`config.py` 補 `from __future__ import annotations`）。
- NAS 沒有 SFTP 子系統，`scp` 要加 `-O` 用舊式協定；沒有 `crontab`，排程用 DSM「工作排程器」的「使用者定義的指令碼」，指向 `run_nas.sh`（設 `UNATTENDED=1`、log 寫到 `logs/`、只留 30 天）。
- Gmail 授權（`credentials.json`、`token.json`）用 scp 複製到 NAS，權限 `600`。OAuth 用戶端是 Google Workspace「內部」類型，不會有 7 天過期問題，多一份授權存在 NAS 上是這個做法的代價。
- 「今天已執行過」標記檔與假日/時間判斷（ADR-0004）在 NAS 上照常運作，NAS 與筆電各自有獨立的標記檔，所以兩邊同時啟用會各建一封草稿；NAS 驗證穩定後要停用筆電上的排程（不刪除，NAS 故障時可重新啟用）。

已知取捨：Python 3.8 已停止維護，google-auth 與 cryptography 會印出 EOL 警告；venv 內版本已固定不會自動更新，短期內不影響運作，之後如果 Synology 提供 Python 3.9+ 套件可以換。
