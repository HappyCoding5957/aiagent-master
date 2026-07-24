# 🏗️ 系統架構說明

## 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows 電腦 / 瀏覽器                     │
│                 http://10.100.40.5:4200                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ HTTP Request
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Nginx (Frontend Container)                     │
│                    Port 4200 → 80                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │          Angular 17 前端應用                        │    │
│  │  - 檔案上傳介面                                     │    │
│  │  - 狀態查詢顯示                                     │    │
│  │  - 進度條展示                                       │    │
│  │  - 刪除操作確認                                     │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ API Calls
                      │ http://10.100.40.5:8000/api/*
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            FastAPI (Backend Container)                      │
│                     Port 8000                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │              API 端點                               │    │
│  │  - GET  /api/status    (查詢狀態)                  │    │
│  │  - POST /api/upload    (上傳檔案)                  │    │
│  │  - DELETE /api/delete  (刪除知識庫)                │    │
│  │  - GET  /api/progress  (查詢進度)                  │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────┐     │    │
│  │  │        業務邏輯處理                       │     │    │
│  │  │  1. Excel 檔案解析                       │     │    │
│  │  │  2. 資料結構化處理                        │     │    │
│  │  │  3. Embedding 向量生成                   │     │    │
│  │  │  4. 資料庫操作 (CRUD)                    │     │    │
│  │  └──────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────┘    │
└─────┬──────────────────────┬────────────────────────────────┘
      │                      │
      │                      │ HTTP Post
      │ Database             │ http://10.100.40.5:8004/api/embed
      │ Connection           │
      ▼                      ▼
┌───────────────┐    ┌────────────────────┐
│  PostgreSQL   │    │  Embedding API     │
│  10.100.40.5  │    │  10.100.40.5:8004  │
│  Port: 8002   │    │                    │
│               │    │  - 文字向量化      │
│  Tables:      │    │  - 支援批次處理    │
│  - PdfFile    │    │  - 返回 1024 維    │
│  - PdfChunk   │    │    向量            │
└───────────────┘    └────────────────────┘
```

## 技術棧

### 前端 (Frontend)
- **框架**: Angular 17
- **UI 設計**: 自訂 CSS（參考 n8n workflow UIUX）
- **HTTP 客戶端**: HttpClient (RxJS)
- **容器化**: Nginx Alpine
- **建置工具**: Angular CLI + npm

### 後端 (Backend)
- **框架**: FastAPI (Python 3.11)
- **ORM**: SQLModel
- **資料庫驅動**: psycopg2-binary
- **向量擴展**: pgvector
- **Excel 處理**: openpyxl
- **HTTP 客戶端**: requests
- **ASGI 伺服器**: Uvicorn

### 資料庫 (Database)
- **類型**: PostgreSQL with pgvector
- **主機**: 10.100.40.5:8002
- **資料表**:
  - `pdffile`: 儲存檔案元資料
  - `pdfchunk`: 儲存文字區塊和向量

### 容器化 (Containerization)
- **工具**: Docker + Docker Compose v2
- **網路**: Bridge 網路模式
- **卷掛載**: /tmp 進度檔案共享

## 資料流程

### 1. 上傳流程
```
使用者選擇檔案
    ↓
前端上傳檔案 (multipart/form-data)
    ↓
後端接收 UploadFile
    ↓
儲存為暫存檔案 (/tmp/*.xlsx)
    ↓
openpyxl 讀取 Excel
    ↓
解析每一列 (A-G 欄)
    ↓
組成結構化文字
    ↓
分批呼叫 Embedding API (50 筆/批)
    ↓
取得向量 (1024 維)
    ↓
檢查並刪除舊資料 (如果存在)
    ↓
建立新的 PdfFile 記錄
    ↓
批次插入 PdfChunk 記錄
    ↓
提交資料庫事務
    ↓
返回成功結果 (含 pdf_id)
    ↓
前端顯示成功訊息
```

### 2. 查詢狀態流程
```
前端發起 GET /api/status
    ↓
後端查詢 PdfFile 表
    ↓
根據 name 和 unit 篩選
    ↓
統計 PdfChunk 數量
    ↓
返回 JSON 結果
    ↓
前端更新 UI 顯示
```

### 3. 進度輪詢流程
```
上傳開始時，前端啟動定時器 (1秒/次)
    ↓
定時呼叫 GET /api/progress
    ↓
後端讀取 /tmp/attachment3_upload_progress.json
    ↓
返回進度資訊 (stage, percent, message)
    ↓
前端更新進度條
    ↓
當 stage = 'complete' 或 'error' 時停止輪詢
```

### 4. 刪除流程
```
使用者點擊刪除按鈕
    ↓
前端確認對話框
    ↓
發起 DELETE /api/delete
    ↓
後端查詢目標 PdfFile
    ↓
刪除所有相關 PdfChunk
    ↓
刪除 PdfFile 記錄
    ↓
提交事務
    ↓
返回刪除統計
    ↓
前端顯示成功訊息
```

## 目錄結構

```
attachment3-manager/
├── backend/                      # 後端服務
│   ├── main.py                  # FastAPI 應用主檔案
│   ├── models.py                # SQLModel 資料庫模型
│   ├── requirements.txt         # Python 依賴
│   ├── Dockerfile               # 後端容器配置
│   └── .dockerignore           # Docker 忽略檔案
│
├── frontend/                     # 前端服務
│   ├── src/                     # 源代碼
│   │   ├── app/                # Angular 組件
│   │   │   ├── app.component.ts
│   │   │   ├── app.component.html
│   │   │   ├── app.component.css
│   │   │   └── app.module.ts
│   │   ├── environments/       # 環境配置
│   │   │   └── environment.ts
│   │   ├── index.html          # 首頁
│   │   └── main.ts             # 應用入口
│   ├── angular.json            # Angular 專案配置
│   ├── package.json            # Node.js 依賴
│   ├── tsconfig.json           # TypeScript 配置
│   ├── nginx.conf              # Nginx 配置
│   ├── Dockerfile              # 前端容器配置
│   └── .dockerignore          # Docker 忽略檔案
│
├── docker-compose.yml           # Docker Compose 配置
├── start.sh                     # 啟動腳本
├── README.md                    # 專案說明
├── QUICKSTART.md               # 快速開始指南
└── ARCHITECTURE.md             # 本文件
```

## API 規格

### GET /api/status
**功能**: 查詢知識庫狀態

**回應**:
```json
{
  "exists": true,
  "pdf_id": "97335d21-d15c-48dc-9e7d-38b3fca922b5",
  "name": "附件三_EnvSafety_atta3_知識庫",
  "chunk_count": 150,
  "last_update": "2026-01-08T06:25:00",
  "unit": "SYSTEM"
}
```

### POST /api/upload
**功能**: 上傳附件三 Excel 檔案

**請求**:
- Content-Type: multipart/form-data
- Body: file (Excel .xlsx)

**回應**:
```json
{
  "success": true,
  "pdf_id": "new-uuid",
  "pdf_name": "附件三_EnvSafety_atta3_知識庫",
  "chunk_count": 150,
  "unit": "SYSTEM"
}
```

### DELETE /api/delete
**功能**: 刪除知識庫

**回應**:
```json
{
  "success": true,
  "deleted_chunks": 150,
  "deleted_files": 1,
  "message": "刪除成功"
}
```

### GET /api/progress
**功能**: 查詢上傳進度

**回應**:
```json
{
  "stage": "embedding",
  "percent": 45,
  "message": "生成向量 3/6 批",
  "timestamp": "2026-01-08T06:25:30"
}
```

**階段 (stage)**:
- `idle`: 閒置
- `init`: 初始化
- `reading`: 讀取檔案
- `embedding`: 生成向量
- `database`: 寫入資料庫
- `complete`: 完成
- `error`: 錯誤

## 安全性考量

### 1. CORS 設定
- 目前允許所有來源 (`allow_origins=["*"]`)
- 生產環境建議限制特定域名

### 2. 檔案類型驗證
- 只接受 `.xlsx` 檔案
- 後端進行檔案類型檢查

### 3. 資料庫權限
- 使用專用資料庫使用者
- 避免使用 root 權限

### 4. 暫存檔案處理
- 上傳後立即刪除暫存檔案
- 避免磁碟空間浪費

## 效能優化

### 1. 批次處理
- Embedding 生成採用批次處理 (50 筆/批)
- 減少 API 呼叫次數

### 2. 進度追蹤
- 使用檔案進度追蹤 (`/tmp/attachment3_upload_progress.json`)
- 避免阻塞主執行緒

### 3. 資料庫索引
- `PdfFile.name` 和 `PdfFile.unit` 建議加索引
- `PdfChunk.pdf_id` 外鍵自動索引

### 4. 前端優化
- Angular 生產建置 (AOT 編譯)
- Nginx Gzip 壓縮

## 擴展性建議

### 1. 多檔案支援
- 修改 `PDF_NAME` 為動態參數
- 前端加入檔案名稱輸入欄位

### 2. 使用者認證
- 加入 JWT 或 OAuth2 認證
- 限制 API 訪問權限

### 3. 任務佇列
- 使用 Celery 或 RQ 處理長時間任務
- 避免 API 超時

### 4. 檔案儲存
- 使用 S3 或 MinIO 儲存原始檔案
- 避免單點故障

### 5. 快取機制
- 使用 Redis 快取狀態查詢
- 減少資料庫負載

---

**文件版本**: 1.0
**最後更新**: 2026-01-08
