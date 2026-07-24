# 附件三上傳系統 - 完整文檔

## 📋 系統概述

這是一個完整的附件三 Excel 上傳和處理系統，可以將 Excel 檔案上傳到 RAG 知識庫。

## 🏗️ 系統架構

```
Windows 電腦 (使用者)
    ↓ 上傳 Excel 到 n8n webhook
n8n 伺服器 (10.80.15.16)
    ↓ Execute Command 執行 curl
本機 Flask API (10.120.170.55:5555)
    ↓ Python 腳本處理 Excel
資料庫伺服器 (10.100.40.5:8002)
    ↓ 儲存到 PostgreSQL RAG 系統
```

### 為什麼這樣設計？

**問題**：
- n8n 運行在獨立伺服器 (10.80.15.16)
- Python 處理腳本在本機 (10.120.170.55)
- n8n 的 Execute Command 無法直接訪問本機的檔案和 venv

**解決方案**：
- 在本機運行 Flask API 服務 (port 5555)
- n8n 通過 HTTP 調用本機 API
- API 負責處理 Excel 和上傳到資料庫

## 🚀 快速開始

### 1. 啟動 Flask 服務

```bash
cd /home/lladm/frank/n8n/客戶問卷RPA
./啟動Flask服務.sh
```

**或手動啟動**：
```bash
cd /home/lladm/frank/n8n/客戶問卷RPA
source venv/bin/activate
nohup python server.py > /tmp/flask_server.log 2>&1 &
```

### 2. 測試系統

```bash
./測試上傳.sh
```

### 3. 從 Windows 使用

訪問 n8n webhook：
```
http://10.80.15.16:5678/webhook/attachment3-upload
```

上傳 Excel 檔案（附件三.xlsx），系統會自動處理並返回結果。

## 🔧 API 端點

### 健康檢查
```bash
curl http://10.120.170.55:5555/api/security-c/health
```

### 附件三上傳
```bash
curl -X POST http://10.120.170.55:5555/api/attachment3/upload \
  -H "Content-Type: application/json" \
  -d '{"base64Data": "BASE64_ENCODED_EXCEL"}'
```

**回應格式**：
```json
{
  "success": true,
  "pdf_id": "uuid",
  "chunk_count": 123,
  "message": "上傳成功"
}
```

## 📁 檔案結構

```
/home/lladm/frank/n8n/客戶問卷RPA/
├── server.py                      # Flask API 服務
├── upload_attachment3_to_rag.py  # Excel 處理和上傳腳本
├── 啟動Flask服務.sh               # 啟動服務腳本
├── 測試上傳.sh                    # 測試腳本
├── venv/                          # Python 虛擬環境
├── security_c_uploads/            # 上傳檔案暫存目錄
└── 附件三.xlsx                    # Excel 資料庫檔案
```

## 🔍 故障排除

### 檢查 Flask 服務狀態

```bash
# 檢查進程
ps aux | grep server.py

# 檢查端口
ss -tlnp | grep 5555

# 查看日誌
tail -f /tmp/flask_server.log
```

### 重啟服務

```bash
# 停止服務
pkill -f server.py

# 啟動服務
./啟動Flask服務.sh
```

### 測試連線

```bash
# 從本機測試
curl http://127.0.0.1:5555/api/security-c/health

# 從 n8n 伺服器測試
ssh ifm02web@10.80.15.16
curl http://10.120.170.55:5555/api/security-c/health
```

### 查看資料庫

```bash
PGPASSWORD=dgtk psql -h 10.100.40.5 -p 8002 -U dgtk -d dgtk

# 查詢上傳的資料
SELECT id, name, unit, size, date
FROM pdffile
WHERE name LIKE '%附件三%'
ORDER BY date DESC
LIMIT 10;
```

## 🔗 重要連結

- **n8n Workflow**: http://10.80.15.16:5678/workflow/UikWrnAd5k5YzUa7
- **n8n Webhook**: http://10.80.15.16:5678/webhook/attachment3-upload
- **API 健康檢查**: http://10.120.170.55:5555/api/security-c/health
- **上傳 API**: http://10.120.170.55:5555/api/attachment3/upload

## 📝 n8n Workflow 配置

**Workflow ID**: `UikWrnAd5k5YzUa7`

**關鍵節點**：
1. **上傳API** (webhook) - 接收 Excel 檔案
2. **儲存上傳檔案** (code) - 提取 base64 數據
3. **執行上傳腳本** (executeCommand) - 調用 Flask API
4. **解析上傳結果** (code) - 處理回應
5. **回傳上傳結果** (respondToWebhook) - 返回給用戶

**執行命令**：
```bash
BASE64_DATA='{{ $json.base64Data }}'

curl -X POST http://10.120.170.55:5555/api/attachment3/upload \
  -H "Content-Type: application/json" \
  -d "{\"base64Data\": \"$BASE64_DATA\"}" \
  -s
```

## 🛡️ 安全注意事項

1. Flask 運行在 0.0.0.0:5555，可以從內網訪問
2. 確保防火牆只允許內網訪問
3. 臨時檔案會自動清理
4. 上傳的檔案會驗證格式

## 📊 監控和日誌

### Flask 日誌
```bash
tail -f /tmp/flask_server.log
```

### n8n 執行日誌
在 n8n UI 中查看 workflow 的執行記錄

### 系統資源監控
```bash
# CPU 和記憶體使用
ps aux | grep server.py

# 磁碟空間
df -h /tmp
```

## 🔄 維護

### 定期清理

```bash
# 清理臨時檔案
rm -f /tmp/test_*.json /tmp/test_*.xlsx

# 清理舊日誌（保留最近 1000 行）
tail -1000 /tmp/flask_server.log > /tmp/flask_server.log.tmp
mv /tmp/flask_server.log.tmp /tmp/flask_server.log
```

### 更新腳本

如果修改了 `upload_attachment3_to_rag.py` 或 `server.py`，需要重啟服務：

```bash
pkill -f server.py
./啟動Flask服務.sh
```

## 📞 聯絡資訊

如有問題，請聯繫系統管理員。

---

**最後更新**: 2026-01-07
**版本**: 1.0
**狀態**: ✅ 生產環境運行中
