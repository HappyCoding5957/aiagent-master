# 附件三知識庫管理系統

這是一個完整的前後端系統，用於管理「附件三」（環境安全知識庫）的上傳、查詢和刪除。

## 🏗️ 系統架構

- **前端**: Angular 17 + Nginx
- **後端**: FastAPI (Python 3.11)
- **資料庫**: PostgreSQL (with pgvector)
- **容器化**: Docker + Docker Compose

## 📁 專案結構

```
attachment3-manager/
├── backend/                # FastAPI 後端
│   ├── main.py            # 主要 API 端點
│   ├── models.py          # 資料庫模型
│   ├── requirements.txt   # Python 依賴
│   └── Dockerfile         # 後端 Docker 配置
├── frontend/              # Angular 前端
│   ├── src/
│   │   ├── app/          # Angular 組件
│   │   ├── environments/ # 環境配置
│   │   └── index.html    # 首頁
│   ├── nginx.conf        # Nginx 配置
│   ├── package.json      # Node.js 依賴
│   └── Dockerfile        # 前端 Docker 配置
├── docker-compose.yml     # Docker Compose 配置
└── README.md             # 本文件
```

## 🚀 快速開始

### 前置需求

- Docker 20.10+
- Docker Compose 1.29+

### 1. 啟動服務

在專案根目錄執行：

```bash
cd /home/lladm/frank/n8n/客戶問卷RPA/attachment3-manager
docker-compose up -d --build
```

### 2. 檢查服務狀態

```bash
docker-compose ps
```

應該看到兩個服務正在運行：
- `attachment3-backend` (port 8000)
- `attachment3-frontend` (port 4200)

### 3. 訪問系統

- **前端介面**: http://10.100.40.5:4200
- **後端 API**: http://10.100.40.5:8000
- **API 文檔**: http://10.100.40.5:8000/docs

### 4. Windows 訪問

在 Windows 電腦的瀏覽器中，訪問以下 URL：

```
http://10.100.40.5:4200
```

## 📡 API 端點

### 1. 查詢知識庫狀態
```
GET /api/status
```

### 2. 上傳附件三
```
POST /api/upload
Content-Type: multipart/form-data
Body: file (Excel .xlsx)
```

### 3. 刪除知識庫
```
DELETE /api/delete
```

### 4. 查詢上傳進度
```
GET /api/progress
```

## 🔧 開發模式

### 後端開發

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端開發

```bash
cd frontend
npm install
npm start
```

訪問 http://localhost:4200

## 🛑 停止服務

```bash
docker-compose down
```

## 🔄 重新建置

```bash
docker-compose down
docker-compose up -d --build
```

## 📝 環境變數

可以在 `docker-compose.yml` 中修改以下環境變數：

- `DB_URL`: PostgreSQL 連線字串
- `EMBED_API`: Embedding API 端點

## 🐛 除錯

### 查看後端日誌
```bash
docker-compose logs -f backend
```

### 查看前端日誌
```bash
docker-compose logs -f frontend
```

### 進入容器內部
```bash
# 後端
docker exec -it attachment3-backend /bin/bash

# 前端
docker exec -it attachment3-frontend /bin/sh
```

## 📊 系統功能

### 1. 知識庫狀態查詢
- 顯示當前知識庫是否已建立
- 顯示檔案名稱、資料筆數、最後更新時間
- 顯示 PDF ID（用於 RAG 查詢）

### 2. 上傳附件三
- 選擇 Excel (.xlsx) 檔案
- 自動讀取並解析資料
- 生成 Embedding 向量
- 寫入 PostgreSQL 資料庫
- 即時顯示上傳進度

### 3. 刪除知識庫
- 一鍵刪除所有相關資料
- 包含 PdfFile 和 PdfChunk 資料表

## 🎨 UIUX 特色

- 漸層背景設計
- 即時進度條顯示
- 響應式佈局
- 繁體中文介面
- 友善的錯誤提示

## 🔐 安全性建議

生產環境部署時，建議：
1. 修改 CORS 設定，限制允許的來源域名
2. 使用環境變數管理敏感資訊
3. 啟用 HTTPS
4. 設定防火牆規則
5. 定期更新依賴套件

## 📞 問題回報

如有問題，請聯繫系統管理員。

## 📄 授權

內部使用。
