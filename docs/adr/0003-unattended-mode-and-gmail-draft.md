# 無人值守模式改用 Windows 工作排程器 + 獨立 Gmail API，不用 Claude 連接器

需求從「手動執行」（見 ADR-0002）改成「每天 8:00 自動執行，完成後建立一封 Gmail 草稿（不寄出），HTML 報表以附件夾帶」。

排程機制選擇上，Claude 本機排程任務（`create_scheduled_task`）原本是最省事的選項，能直接呼叫使用者已設定好的 Gmail 連接器建草稿，不用另外申請 OAuth；但它有兩個限制：一是任務要 Claude 應用程式開著才會準時觸發，程式沒開只會在下次啟動時補跑；二是連 Claude 排程任務本身都沒辦法應付「電腦睡眠」的狀況。使用者要求即使電腦睡眠、應用程式沒開也要能執行，Windows 工作排程器可以設定「喚醒電腦來執行工作」且不依賴任何應用程式保持開啟，穩定性更高，因此改選它。

代價是 Claude 的 Gmail 連接器工具（`create_draft` 等）只有 Claude session 主動執行時才能呼叫，Windows 工作排程器觸發的獨立執行檔沒有 Claude session，接不到連接器。因此另外在 Google Cloud Console 申請了一組獨立的 OAuth 用戶端（`credentials.json`），用 `gmail.compose` 這個最小權限範圍（只能建立/管理草稿與寄信，不能讀取其他郵件），寫在 `pcc_tender_watch/gmail_draft.py`。第一次執行需要互動式登入取得 `token.json`，之後排程執行靠這個快取的授權靜默刷新，不會再跳瀏覽器。`credentials.json`、`token.json` 都含機密內容，已加進 `.gitignore`。

程式新增 `UNATTENDED` 模式（環境變數 `UNATTENDED=1`）：互動模式（手動雙擊 .exe）維持 ADR-0002 的行為，開瀏覽器、等按 Enter；無人值守模式改成不開瀏覽器、不等輸入，查詢完直接呼叫 Gmail API 建草稿。兩種模式共用同一套查詢/篩選邏輯。
