# 🚀 快速開始指南

## ✅ 系統已啟動

恭喜！附件三知識庫管理系統已成功部署並運行。

## 📍 訪問地址

### Windows 用戶
在 Windows 電腦的瀏覽器中，直接訪問以下地址：

```
http://10.100.40.5:4200
```

### Linux 本機用戶
```bash
# 前端介面
http://localhost:4200

# 後端 API
http://localhost:8000

# API 文檔（Swagger）
http://localhost:8000/docs
```

## 🎯 系統功能

### 1. 查看知識庫狀態
- 進入首頁後，系統會自動顯示當前知識庫狀態
- 包含：檔案名稱、資料筆數、最後更新時間、PDF ID

### 2. 上傳附件三
- 點擊「選擇附件三.xlsx」按鈕
- 選擇 Excel 檔案（.xlsx 格式）
- 點擊「上傳並更新知識庫」
- 系統會顯示即時進度條
- 上傳完成後會顯示成功訊息

### 3. 刪除知識庫
- 點擊「刪除附件三知識庫」按鈕
- 確認刪除操作
- 系統會刪除所有相關資料

## 🔧 系統管理

### 查看服務狀態
```bash
cd /home/lladm/frank/n8n/客戶問卷RPA/attachment3-manager
docker compose ps
```

### 查看日誌
```bash
# 查看後端日誌
docker compose logs -f backend

# 查看前端日誌
docker compose logs -f frontend

# 查看所有日誌
docker compose logs -f
```

### 停止服務
```bash
docker compose down
```

### 重新啟動服務
```bash
docker compose restart
```

### 重新建置並啟動
```bash
docker compose down
docker compose up -d --build
```

## 🌐 網路訪問

### 確保防火牆允許訪問
```bash
# 檢查端口是否開放
sudo ufw status

# 如果需要開放端口
sudo ufw allow 4200/tcp
sudo ufw allow 8000/tcp
```

### 從 Windows 訪問
1. 確保 Windows 和 Linux 在同一網路
2. 確認 Linux IP 地址：`ip addr show`
3. 在 Windows 瀏覽器訪問：`http://10.100.40.5:4200`

## 📊 API 測試

### 測試後端 API
```bash
# 根路徑
curl http://localhost:8000/

# 查詢狀態
curl http://localhost:8000/api/status

# 查詢進度
curl http://localhost:8000/api/progress
```

## 🐛 常見問題

### 1. 無法訪問前端
- 檢查 Docker 容器是否運行：`docker compose ps`
- 檢查防火牆設定
- 檢查前端日誌：`docker compose logs frontend`

### 2. 上傳失敗
- 檢查後端日誌：`docker compose logs backend`
- 確認資料庫連線正常
- 確認 Embedding API 可訪問

### 3. 資料庫連線錯誤
- 檢查 `docker-compose.yml` 中的 `DB_URL` 設定
- 確認資料庫服務可訪問：`psql -h 10.100.40.5 -p 8002 -U dgtk -d dgtk`

## 📝 配置修改

### 修改資料庫連線
編輯 `docker-compose.yml`：
```yaml
environment:
  - DB_URL=postgresql://user:pass@host:port/dbname
```

### 修改 API 端點
編輯 `frontend/src/environments/environment.ts`：
```typescript
export const environment = {
  apiUrl: 'http://your-backend-url:8000'
};
```

## 🔄 更新系統

### 更新後端程式碼
```bash
# 修改 backend/ 下的檔案後
docker compose restart backend
```

### 更新前端程式碼
```bash
# 修改 frontend/src/ 下的檔案後
cd /home/lladm/frank/n8n/客戶問卷RPA/attachment3-manager
docker compose up -d --build frontend
```

## 📞 技術支援

如有問題，請檢查：
1. Docker 日誌
2. 網路連線
3. 資料庫狀態
4. API 端點配置

---

**系統版本**: 1.0.0
**建立日期**: 2026-01-08
**技術棧**: Angular 17 + FastAPI + PostgreSQL + Docker
