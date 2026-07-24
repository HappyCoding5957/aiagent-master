# DocAgent — Enterprise Multi-Document Intelligence Engine（乾淨重寫版）

這是 Response Intelligence / Supplier Compliance / RFP 問卷自動化產品的核心引擎（Core Engine），**不含任何真實客戶資料**，可以直接開源、放上 Upwork 作品集、或當作給客戶的私有部署（Private Deployment）起點。

## 架構設計（Architecture）

沿用先前討論的 5 層架構，每一層都是獨立模組、透過介面（Interface / Abstract Base Class）串接，方便未來替換成正式的商用元件而不用改動其他層——這是 **策略模式（Strategy Pattern）** 的標準用法。

```
L1 Ingestion（擷取層）
  PDF / Excel / 圖片 / 純文字 → 統一轉成 Chunk
  OCR 可插拔：TesseractOCR（正式）↔ MockOCR（demo/離線降級）
        │
        ▼
L2 Schema Detection（表格結構偵測層）
  用關鍵字啟發式（keyword heuristics）自動找出「題號/問題/答案/備註」對應到哪一欄
  不假設客戶問卷格式固定，同一套引擎可以吃不同客戶、不同語言的問卷
        │
        ▼
L3 Hybrid Retrieval（混合檢索層）
  Fuzzy 字串相似度 + 關鍵字飽和計分（keyword saturation scoring）
  之後要接正式 Embeddings + Reranker，只需新增一個 Retriever 實作
        │
        ▼
L4 Reasoning（推理層）
  可插拔 LLM：正式環境接 Claude/GPT，demo/離線環境用 MockReasoner
  信心分級：≥0.85 自動通過／0.60–0.85 建議覆核／<0.60 強制人工
        │
        ▼
L5 Output（輸出層）
  Excel 回填 + 信心分級上色（綠/黃/紅）
  JSON 稽核報告（Audit Trail）—— 每題附證據來源、頁碼/列號、分數，不是黑盒子
```

## 快速開始（Quick Start）

```bash
pip install -r requirements.txt --break-system-packages
python sample_data/generate_sample.py   # 產生假資料（Acme Manufacturing 範例問卷 + 知識庫）
python run_demo.py                       # 跑一次完整 pipeline，印出自動化率
pytest tests/                            # 煙霧測試
```

啟動 API（n8n 相容，可直接被 n8n HTTP Request node 呼叫）：

```bash
uvicorn api.main:app --reload --port 8420
```

## 為什麼可以公開這份代碼

- 完全用合成資料（Synthetic Data）測試，`sample_data/` 裡是虛構公司「Acme Manufacturing」，沒有任何真實客戶名稱、內網位置、真實供應商資料。
- 每一層都是通用邏輯，沒有寫死任何特定客戶的欄位名稱或業務規則。
- 這是你可以放上 GitHub public repo、Upwork 作品集連結、Demo 影片裡直接展示代碼畫面的版本。

## 下一步可以接的正式元件（對應你 GitHub 上已有的 repo）

| 這裡的 Mock/簡化版 | 換成你已寫過的正式版 |
|---|---|
| `MockOCR` | `PaddleOCR` repo |
| `HybridRetriever`（fuzzy+關鍵字）| `prj_ENGPT_RAG`（Azure RAG，接 embeddings）|
| `MockReasoner` | 接 Claude/GPT API，或 `model-hub` 本地託管的模型 |
| API 層 | `n8n-MCP` repo 的 Connector 邏輯 |
| 私有部署 | `nvidia-container-toolkit-offline`（離線 GPU 環境）|
