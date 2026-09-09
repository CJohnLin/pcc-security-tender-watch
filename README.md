# pcc-security-tender-watch

查詢政府電子採購網，找出跟「資安」「網路設備」相關、目前還在投標期限內（尚未決標）的標案。有兩種執行模式：

- **互動模式**：手動雙擊執行，輸出成本機 HTML 檔並自動用瀏覽器打開
- **無人值守模式**：Windows 工作排程器每天 8:00 自動執行，完成後在 Gmail 建立一封**草稿**（不會寄出），HTML 報表以附件夾帶，收件人 peggy.wu@rehfeldt.org、副本 supportlf@rehfeldt.org

設計決策見 [`CONTEXT.md`](CONTEXT.md)（詞彙定義）與 [`docs/adr/`](docs/adr/)（架構決策記錄）。

## 運作方式

1. 用 [g0v 政府採購公告 API](https://pcc-api.openfun.app/skill.md) 掃過去 90 天（可調）的公告列表
2. 用標題比對「資安」「網路設備」關鍵字與同義詞（見 [`pcc_tender_watch/config.py`](pcc_tender_watch/config.py)）
3. 排除決標/無法決標/廢標等公告，只留還在投標期限內的
4. 依截止投標時間排序，輸出成 `output/tenders_<時間戳記>.html`
5. 無人值守模式：呼叫 Gmail API 建立草稿信，HTML 檔案當附件

沒有持久化狀態：每次執行都重新掃描一次，同一個標案只要還在期限內，每次執行都會重複出現。

## 架構決策摘要

- **為什麼不是雲端排程（GitHub Actions）**：實測發現雲端機房 IP 會被 g0v API 的 Cloudflare 防護直接 403 擋掉，只能在本機（住宅/公司網路）執行，見 [ADR-0002](docs/adr/0002-local-manual-exe-instead-of-cloud-schedule.md)。
- **為什麼是 Windows 工作排程器 + 獨立 Gmail API，不是 Claude 排程任務**：Claude 本機排程任務需要應用程式開著才會準時觸發、也無法應付電腦睡眠；Windows 工作排程器可以設定「喚醒電腦來執行」且不依賴任何應用程式，代價是要另外申請一組獨立的 Gmail OAuth 憑證（見下方設定），不能直接用 Claude 裡已設定好的 Gmail 連接器（連接器只有 Claude session 主動執行時才能呼叫），見 [ADR-0003](docs/adr/0003-unattended-mode-and-gmail-draft.md)。

## 使用方式

### 直接跑 Python（開發/除錯用）

```bash
pip install -r requirements-dev.txt
python run.py
```

### 打包成 .exe（互動模式用，不需要對方電腦裝 Python）

```bash
pip install -r requirements-dev.txt
pyinstaller --onefile --console --name pcc-tender-watch run.py
```

打包完的檔案在 `dist\pcc-tender-watch.exe`，雙擊執行即可：跑完會自動開瀏覽器顯示結果，並在主控台印出「按 Enter 鍵結束」等你確認才關閉視窗。

### 跑單元測試（不需要任何憑證、不會打真的 API）

```bash
pytest
```

## 設定無人值守模式（每天自動建草稿）

### 1. 申請 Gmail API OAuth 憑證

1. [Google Cloud Console](https://console.cloud.google.com/) 建立一個專案
2. 「API 和服務」→「程式庫」搜尋「Gmail API」，按「**啟用**」（這步漏掉會拿到 403 錯誤）
3. 「API 和服務」→「OAuth 同意畫面」：使用者類型選「**內部**」（如果 Google Cloud 專案是建在公司 Google Workspace 組織下才會有這個選項）——選「內部」授權不會有「外部＋測試」狀態下 Refresh Token 只有 7 天效期的問題，也不需要 Google 審核；如果沒有 Internal 選項（例如用個人 Gmail 帳號建的專案），才選「外部」，並注意 token 每 7 天要重新互動登入一次
4. 「API 和服務」→「憑證」→「建立憑證」→「OAuth 用戶端 ID」，應用程式類型選「桌面應用程式」，下載 JSON
5. 把下載的 JSON 存成專案根目錄下的 `credentials.json`（`.gitignore` 已排除，不會進版控）

### 2. 第一次互動式登入

```bash
$env:UNATTENDED="1"
python run.py
```

會跳出瀏覽器要你登入、同意權限，成功後會在專案根目錄產生 `token.json`（一樣已 gitignore）。之後排程執行會靜默用它刷新，不會再跳瀏覽器——但如果 `token.json` 失效或被刪除，下次執行一樣會需要互動登入，排程跑的時候沒人在會直接卡住/失敗，需要留意。

### 3. 設定 Windows 工作排程器

「工作排程器」→「建立工作」：

- **一般**：勾選「不論使用者登入與否均執行」
- **觸發程序**：每天 08:00
- **設定**：勾選「喚醒電腦來執行此工作」
- **動作**：
  - 程式：`C:\Users\john.lin\AppData\Local\Programs\Python\Python312\python.exe`
  - 引數：`run.py`
  - 開始位置：`C:\Users\john.lin\Desktop\Claude`
- 環境變數 `UNATTENDED=1` 沒有地方在工作排程器 UI 直接設，改用一個小批次檔包一層（見下方）

建議寫一個 `run_unattended.bat`（不進版控，自己在本機建立）：

```bat
@echo off
set UNATTENDED=1
cd /d C:\Users\john.lin\Desktop\Claude
C:\Users\john.lin\AppData\Local\Programs\Python\Python312\python.exe run.py
```

工作排程器的「動作」直接指向這個 `.bat` 檔即可。

## 設定（都選填，預設值就能直接跑）

用環境變數覆寫，例如 PowerShell：`$env:LOOKBACK_DAYS="30"`。

| 環境變數 | 預設值 | 說明 |
|---|---|---|
| `LOOKBACK_DAYS` | `90` | 往回掃幾天的公告 |
| `REQUEST_DELAY_SECONDS` | `2` | 每次 API 呼叫的間隔秒數，避開未公開的流量限制 |
| `OUTPUT_DIR` | `output` | 結果 HTML 存放的資料夾 |
| `PCC_API_TOKEN` | 無 | g0v API Token（目前需要邀請名單才能申請，見下方限制） |
| `UNATTENDED` | 無 | 設 `1` 時不開瀏覽器、不等按鍵，改成建立 Gmail 草稿 |
| `GOOGLE_CREDENTIALS_PATH` | `credentials.json` | Gmail OAuth 用戶端憑證檔案路徑 |
| `GOOGLE_TOKEN_PATH` | `token.json` | Gmail OAuth 授權快取檔案路徑 |

草稿的收件人（`DRAFT_TO`）、副本（`DRAFT_CC`）、主旨格式、內文都寫在 [`pcc_tender_watch/config.py`](pcc_tender_watch/config.py)，要改的話直接編輯那個檔案。

## 已知限制

- 依賴非官方、社群維運的第三方 API（g0v `pcc-api.openfun.app`），該服務中斷或改版時本程式需要跟著調整，見 [ADR-0001](docs/adr/0001-use-g0v-pcc-api.md)。
- g0v API 只能在本機（非資料中心 IP）執行，見 [ADR-0002](docs/adr/0002-local-manual-exe-instead-of-cloud-schedule.md)；Windows 工作排程器仍是跑在你的電腦上，只是電腦可以睡眠/沒登入，不是真正的雲端執行。
- API 的 Bearer Token 目前需要邀請才能申請，一般使用者拿不到；程式改用請求節流因應，實測穩定，但代表沒有官方保證的流量額度，短時間內密集執行多次可能還是會被限流（429），正常一天執行一次不會有問題。
- `listbydate` 在完全沒有公告的日期（例如假日）會回傳夾雜 PHP 警告文字的壞掉 JSON（第三方 API 本身的 bug），程式會把那一天當作沒有資料、印警告後跳過，不會讓整次執行失敗。
- 篩選仍以「標案名稱」關鍵字比對為主，名稱裡完全沒出現任何關鍵字/同義詞的資安相關標案會被漏掉；`detail` 裡官方的「國安/資安疑慮」旗標只用來補標分類，沒有用來擴大候選名單（那需要對每天所有公告都呼叫一次 `/api/tender`，成本太高）。
- 因為節流限速，90 天回溯視窗完整跑一次大約需要 10～15 分鐘（實測 10 天約 3 分鐘）。
- 該 API 的完整資料授權條款尚未能確認清楚，個人使用應無虞，但不建議直接拿通知內容做商業轉載。
- `token.json` 失效（例如被撤銷，或 OAuth 同意畫面是「外部＋測試」狀態、超過 7 天效期）時，無人值守模式會直接執行失敗（無法互動登入），需要人工重新跑一次互動登入。這個專案目前用「內部」使用者類型，沒有 7 天過期問題。
