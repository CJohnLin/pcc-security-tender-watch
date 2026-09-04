# 改成手動執行的本機 .exe，不用 GitHub Actions 自動排程

實測發現 GitHub Actions 執行環境呼叫 g0v `pcc-api.openfun.app` 一律收到 `HTTPError: 403 Forbidden`（在本機同一支程式碼、同樣的節流間隔完全正常），推斷是 Cloudflare 對 GitHub Actions 這類資料中心 IP 做了區塊層級的封鎖，跟請求頻率無關，換 Bearer Token 大概率也無法繞過（403 很可能發生在 Cloudflare 邊緣層，根本到不了會檢查 Token 的後端）。找不到其他使用者回報過相同狀況或現成解法。

在「改用自架 GitHub Actions runner（電腦需常駐開機）」「回到 Windows 排程器（電腦需常駐開機）」與「放棄全自動排程、改成手動執行」之間，選擇了手動執行：不需要處理 runner 常駐、也不用再依賴 Email 寄送機制，程式改成產生本機 HTML 檔案並自動開啟瀏覽器查看，執行地點固定在使用者本機（已驗證這個網路環境不會被擋）。代價是失去「電腦沒開也照跑」這個當初選雲端排程的原始動機（見 [ADR-0001](0001-use-g0v-pcc-api.md) 的前置討論），改為每次要查詢時手動執行 `.exe`。
