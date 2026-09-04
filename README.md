# pcc-security-tender-watch

手動執行，查詢政府電子採購網，找出跟「資安」「網路設備」相關、目前還在投標期限內（尚未決標）的標案，輸出成一個本機 HTML 檔並自動用瀏覽器打開。

設計決策見 [`CONTEXT.md`](CONTEXT.md)（詞彙定義）與 [`docs/adr/`](docs/adr/)（架構決策記錄，包含「為什麼是手動執行、不是每天自動排程」的完整原因）。

## 運作方式

1. 用 [g0v 政府採購公告 API](https://pcc-api.openfun.app/skill.md) 掃過去 90 天（可調）的公告列表
2. 用標題比對「資安」「網路設備」關鍵字與同義詞（見 [`pcc_tender_watch/config.py`](pcc_tender_watch/config.py)）
3. 排除決標/無法決標/廢標等公告，只留還在投標期限內的
4. 依截止投標時間排序，輸出成 `output/tenders_<時間戳記>.html`，自動開瀏覽器顯示

沒有持久化狀態：每次執行都重新掃描一次，同一個標案只要還在期限內，每次執行都會重複出現。

## 為什麼是手動執行

原本設計是 GitHub Actions 每天自動排程 + Email 通知，但實測發現 GitHub Actions 的雲端機房 IP 會被 g0v API 的 Cloudflare 防護直接 403 擋掉（跟請求快慢無關），改成在本機（住宅/公司網路，已驗證不會被擋）手動執行，詳見 [ADR-0002](docs/adr/0002-local-manual-exe-instead-of-cloud-schedule.md)。

## 使用方式

### 直接跑 Python（開發/除錯用）

```bash
pip install -r requirements-dev.txt
python run.py
```

### 打包成 .exe（不需要對方電腦裝 Python）

```bash
pip install -r requirements-dev.txt
pyinstaller --onefile --console --name pcc-tender-watch run.py
```

打包完的檔案在 `dist\pcc-tender-watch.exe`，雙擊執行即可：跑完會自動開瀏覽器顯示結果，並在主控台印出「按 Enter 鍵結束」等你確認才關閉視窗。

### 跑單元測試（不需要任何憑證、不會打真的 API）

```bash
pytest
```

## 設定（都選填，預設值就能直接跑）

用環境變數覆寫，例如 PowerShell：`$env:LOOKBACK_DAYS="30"`。

| 環境變數 | 預設值 | 說明 |
|---|---|---|
| `LOOKBACK_DAYS` | `90` | 往回掃幾天的公告 |
| `REQUEST_DELAY_SECONDS` | `2` | 每次 API 呼叫的間隔秒數，避開未公開的流量限制 |
| `OUTPUT_DIR` | `output` | 結果 HTML 存放的資料夾 |
| `PCC_API_TOKEN` | 無 | g0v API Token（目前需要邀請名單才能申請，見下方限制） |

## 已知限制

- 依賴非官方、社群維運的第三方 API（g0v `pcc-api.openfun.app`），該服務中斷或改版時本程式需要跟著調整，見 [ADR-0001](docs/adr/0001-use-g0v-pcc-api.md)。
- 只能在本機（非資料中心 IP）執行，見上方「為什麼是手動執行」與 [ADR-0002](docs/adr/0002-local-manual-exe-instead-of-cloud-schedule.md)。
- API 的 Bearer Token 目前需要邀請才能申請，一般使用者拿不到；程式改用請求節流因應，實測穩定，但代表沒有官方保證的流量額度，短時間內密集執行多次可能還是會被限流（429），正常一天執行一次不會有問題。
- `listbydate` 在完全沒有公告的日期（例如假日）會回傳夾雜 PHP 警告文字的壞掉 JSON（第三方 API 本身的 bug），程式會把那一天當作沒有資料、印警告後跳過，不會讓整次執行失敗。
- 篩選仍以「標案名稱」關鍵字比對為主，名稱裡完全沒出現任何關鍵字/同義詞的資安相關標案會被漏掉；`detail` 裡官方的「國安/資安疑慮」旗標只用來補標分類，沒有用來擴大候選名單（那需要對每天所有公告都呼叫一次 `/api/tender`，成本太高）。
- 因為節流限速，90 天回溯視窗完整跑一次大約需要 10～15 分鐘（實測 10 天約 3 分鐘）。
- 該 API 的完整資料授權條款尚未能確認清楚，個人使用應無虞，但不建議直接拿通知內容做商業轉載。
