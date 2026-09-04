# pcc-security-tender-watch

每天早上 8 點（台灣時間）自動查詢政府電子採購網，找出跟「資安」「網路設備」相關、目前還在投標期限內（尚未決標）的標案，寄一封 HTML 表格 Email 通知。

設計決策見 [`CONTEXT.md`](CONTEXT.md)（詞彙定義）與 [`docs/adr/`](docs/adr/)（架構決策記錄）。

## 運作方式

1. 用 [g0v 政府採購公告 API](https://pcc-api.openfun.app/skill.md) 掃過去 90 天（可調）的公告列表
2. 用標題比對「資安」「網路設備」關鍵字與同義詞（見 [`pcc_tender_watch/config.py`](pcc_tender_watch/config.py)）
3. 排除決標/無法決標/廢標等公告，只留還在投標期限內的
4. 依截止投標時間排序，整理成 HTML 表格寄出

沒有持久化狀態：每次執行都重新掃描一次，同一個標案只要還在期限內，會每天重複出現在通知裡。

## 部署步驟

### 1. 建立 GitHub repo 並推送

```bash
git init
git add .
git commit -m "Initial commit: pcc-security-tender-watch"
git branch -M main
git remote add origin https://github.com/<你的帳號>/pcc-security-tender-watch.git
git push -u origin main
```

### 2. 申請 g0v API 的 Bearer Token

1. 前往 https://data.openfun.tw/user，用 Google 帳號登入
2. 在 Dashboard 取得長效 API 金鑰

### 3. 申請 Gmail 應用程式密碼

需要先幫 Google 帳號開啟兩步驟驗證，再到 [Google 帳戶安全性設定](https://myaccount.google.com/apppasswords) 產生一組「應用程式密碼」（16 碼），不是你平常登入用的密碼。

### 4. 設定 GitHub repo Secrets

到 repo 的 `Settings → Secrets and variables → Actions`，新增：

| Secret | 說明 |
|---|---|
| `PCC_API_TOKEN` | 步驟 2 拿到的 g0v API Token |
| `GMAIL_ADDRESS` | 用來寄信的 Gmail 地址 |
| `GMAIL_APP_PASSWORD` | 步驟 3 拿到的應用程式密碼 |
| `RECIPIENT_EMAIL` | 收件信箱（選填，沒設就寄回 `GMAIL_ADDRESS`） |

### 5. 排程會自動生效

`.github/workflows/daily-tender-check.yml` 排程是台灣時間每天 08:00。也可以到 repo 的 Actions 頁面手動觸發（`workflow_dispatch`）先測試一次。

## 本機測試

```bash
pip install -r requirements-dev.txt

# PowerShell
$env:PCC_API_TOKEN="..."
$env:GMAIL_ADDRESS="..."
$env:GMAIL_APP_PASSWORD="..."
python -m pcc_tender_watch.main

# bash
PCC_API_TOKEN=... GMAIL_ADDRESS=... GMAIL_APP_PASSWORD=... python -m pcc_tender_watch.main
```

跑單元測試（不需要任何憑證、不會打真的 API）：

```bash
pytest
```

## 已知限制

- 依賴非官方、社群維運的第三方 API（g0v `pcc-api.openfun.app`），該服務中斷或改版時本程式需要跟著調整，見 [ADR-0001](docs/adr/0001-use-g0v-pcc-api.md)。
- 篩選仍以「標案名稱」關鍵字比對為主，名稱裡完全沒出現任何關鍵字/同義詞的資安相關標案會被漏掉；`detail` 裡官方的「國安/資安疑慮」旗標只用來補標分類，沒有用來擴大候選名單（那需要對每天所有公告都呼叫一次 `/api/tender`，成本太高）。
- 該 API 的完整資料授權條款尚未能確認清楚，個人使用應無虞，但不建議直接拿通知內容做商業轉載。
