# DocAgent MVP 功能清單（含優先順序）

排序原則：P0 = 沒有它就不能跟第一個付費客戶收錢；P1 = 有它才能把第一個客戶變成 3–5 個客戶；P2 = 等真實客戶回饋進來再做，現在做是猜測。

## P0 — 現在就要有（首個付費案子的最低門檻）

| 功能 | 現況 | 為什麼是 P0 |
|------|------|-------------|
| L4 接真實 LLM（Claude API）| 目前是 `MockReasoner`，`ClaudeReasoner` 骨架已寫好但沒接金鑰測試 | 客戶不會為規則比對付錢，要能力展示真實語言理解 |
| PDF/圖片真實 OCR（PaddleOCR 或 Tesseract）| 目前 PDF 只抽文字層，圖片是 `MockOCR` 佔位 | 客戶的問卷/證明文件有一半是掃描件或圖片，這塊沒接等於做一半 |
| 上傳介面（不是靠終端機下指令）| 只有 `demo_ui.html` 靜態展示版，沒有真的能上傳檔案跑 pipeline 的網頁 | 客戶不會用你的 `run_demo.py`，需要一個能拖檔案進去的畫面，串接現有 FastAPI `/process` 端點即可 |
| 私有部署一鍵啟動（Docker Compose）| 有 `Dockerfile`，沒有 `docker-compose.yml` 串資料庫/儲存 | 你的核心賣點是「Private Deployment」，客戶要能自己在內網跑起來，不是只能你電腦上跑 |
| 基本存取控制（單一密碼/API Key）| 完全沒有 | 客戶問卷含機密資料，API 完全開放是不能給客戶看的東西 |

## P1 — 讓第一個客戶變成 3–5 個客戶

| 功能 | 說明 |
|------|------|
| 引用來源可回溯到原始 PDF 頁面截圖 | 現在 citation 只有檔名+行號文字，正式版要能點開看到原文件那一頁高亮，這是你在競品矩陣裡強調的差異化賣點 |
| Embeddings + Reranker 可插拔實作 | `Retriever` 介面已經設計成可替換，接下來實作 `EmbeddingRetriever`（本地 embedding 模型或 API）+ Cohere Rerank，提升 auto-approve 率（目前 baseline 只有 10%）|
| n8n 節點/workflow 範本包裝 | 對應你 GitHub 上的 `n8n-MCP` repo，把 `/process` 包成 n8n custom node 或現成 workflow JSON，方便你用 n8n 接案時直接套用 |
| 多語言問卷支援（英文已有，補西班牙文/日文關鍵字）| L2 的 `QUESTION_KEYWORDS` 目前只有中英文，接國際客戶前要擴充 |
| Excel 範本相容性測試 | 目前假設答案欄一定在問題欄右邊一格，正式客戶的問卷格式五花八門，需要更寬鬆的欄位偵測 |

## P2 — 等真實客戶回饋進來再做（現在做就是純猜測）

- 多租戶 SaaS 模式（RBAC/SSO）—— 只有真的要同時服務多個客戶且各自要獨立帳號時才需要
- Dual-LLM 驗證層（第二個模型覆核答案，標記幻覺）—— 等客戶開始質疑答案準確度時再做
- 瀏覽器自動化模組（對應你的 `CUA` repo）—— 讓 AI 直接登入 EcoVadis/客戶入口網站填表，這個很強大但技術風險也高，先確認客戶真的需要「填表」而不只是「產出答案」再投入
- 版本衝突偵測（Knowledge Operations Agent，對應 `SuperMemory` repo）—— 客戶知識庫大到需要治理時才有價值
- 正式的稽核/合規認證（如你自己的產品要做 SOC2）—— 賣方需要，但不是 MVP 該做的事

## 一句話總結

現在手上的乾淨版 MVP 已經證明「架構跑得通、90% 自動化率是真實數字」，離「可以跟客戶收錢」中間只差 P0 那 5 項——其中最花時間的是私有部署（Docker Compose + 存取控制），最快能做完的是接 Claude API（`ClaudeReasoner` 骨架已經寫好，只差測試）。建議下一步直接做 P0，不要先跳去做 P1/P2 的進階功能。
