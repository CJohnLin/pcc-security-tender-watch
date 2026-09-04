"""這支程式的設定值。沒有任何一項是必填，預設值就能直接跑（見 docs/adr/0002）。"""

import os

PCC_API_BASE = "https://pcc-api.openfun.app/api"
# 選填：g0v API 目前需要邀請名單才能申請 Token，沒有也能跑（見 REQUEST_DELAY_SECONDS 節流）。
PCC_API_TOKEN = os.environ.get("PCC_API_TOKEN", "")

# 每次 API 請求之間的間隔秒數。實測沒有 Token 時，間隔 2 秒不會觸發 g0v API 未公開的流量限制；
# 間隔太短（例如完全不等）會很快被 429 擋下來。這是本機執行才有效的數字，見 ADR-0002：
# GitHub Actions 這類資料中心 IP 直接被 403 擋掉，跟間隔無關。
REQUEST_DELAY_SECONDS = float(os.environ.get("REQUEST_DELAY_SECONDS", "2"))

# 每次執行往回掃幾天的公告，見 docs/adr/0001-use-g0v-pcc-api.md 的抓取策略說明。
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "90"))

# 結果 HTML 檔案要存去哪個資料夾（相對於執行時的工作目錄）。
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")

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
        "路由器",
        "無線基地台",
        "防火牆設備",
        # 「交換器」單獨用太廣，會誤中「熱交換器」這種工業設備（實測發現的真實案例），
        # 改列出具體的網路交換器複合詞，兼顧命中率與精確度。
        "網路交換器",
        "核心交換器",
        "骨幹交換器",
        "乙太網路交換器",
        "光纖交換器",
        "無線交換器",
        "管理型交換器",
        "PoE交換器",
    ],
}

# 標題比對之外，detail 欄位裡還有一個官方就有的「國安/資安疑慮」旗標，
# 命中候選名單後會額外用這個欄位補標「資安」分類（見 pcc_client.get_tender_detail 的呼叫端）。
SECURITY_SENSITIVE_FIELD = "採購資料:本採購是否屬「具敏感性或國安(含資安)疑慮之業務範圍」採購"

# 公告類型只要含有以下任一關鍵字，就視為「已經不是招標中」的公告（決標、無法決標、廢標等），直接跳過。
EXCLUDED_ANNOUNCEMENT_TYPE_KEYWORDS = ["決標", "無法決標", "廢標", "取消招標", "終止契約", "撤銷"]
