"""這支程式的設定值。實際憑證一律從環境變數讀入，不寫死在程式碼裡。"""

import os

PCC_API_BASE = "https://pcc-api.openfun.app/api"
PCC_API_TOKEN = os.environ.get("PCC_API_TOKEN", "")

# 每次執行往回掃幾天的公告，見 docs/adr/0001-use-g0v-pcc-api.md 的抓取策略說明。
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "90"))

# 寄信用的憑證刻意用 .get()、不在 import 時就要求存在：這樣純邏輯（filters/report）
# 才能在沒有設定任何寄信憑證的環境（例如本機跑單元測試）下被 import 與測試。
# 真的要寄信時（mailer.send_email）才會檢查這幾個值存不存在。
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL") or GMAIL_ADDRESS

# 標案「名稱」關鍵字同義詞。對應 CONTEXT.md 的「資安類」「網路設備類」定義。
# 同一個標案可以同時命中多個分類。
KEYWORD_GROUPS: dict[str, list[str]] = {
    "資安": [
        "資安",
        "資通安全",
        "資安服務",
        "資安防護",
        "資安監控",
        "防火牆",
        "入侵偵測",
        "SOC",
    ],
    "網路設備": [
        "網路設備",
        "網通設備",
        "交換器",
        "路由器",
        "無線基地台",
        "防火牆設備",
    ],
}

# 標題比對之外，detail 欄位裡還有一個官方就有的「國安/資安疑慮」旗標，
# 命中候選名單後會額外用這個欄位補標「資安」分類（見 pcc_client.get_tender_detail 的呼叫端）。
SECURITY_SENSITIVE_FIELD = "採購資料:本採購是否屬「具敏感性或國安(含資安)疑慮之業務範圍」採購"

# 公告類型只要含有以下任一關鍵字，就視為「已經不是招標中」的公告（決標、無法決標、廢標等），直接跳過。
EXCLUDED_ANNOUNCEMENT_TYPE_KEYWORDS = ["決標", "無法決標", "廢標", "取消招標", "終止契約", "撤銷"]
