# 客戶問卷 RPA - 部署指令清單

## 📋 部署前檢查清單

- [ ] 確認 Python 3.10+ 已安裝
- [ ] 確認 n8n 伺服器運行正常
- [ ] 確認附件三資料庫檔案存在且內容完整
- [ ] 確認網路連線正常（Flask ↔ n8n）

---

## 🚀 完整部署流程

### 步驟 1：建立專案目錄

```bash
# 切換到專案目錄
cd /home/lladm/frank/n8n/客戶問卷RPA

# 確認所有檔案都在
ls -lh
```

### 步驟 2：安裝 Python 套件

```bash
# 安裝依賴套件
pip3 install -r requirements.txt --break-system-packages

# 驗證安裝
python3 -c "import flask, openpyxl, rapidfuzz, jieba; print('✅ 所有套件安裝成功')"
```

### 步驟 3：測試 Flask API

```bash
# 啟動 Flask 伺服器（前台測試）
python3 server.py

# 開啟另一個終端，測試健康檢查
curl http://127.0.0.1:5555/api/security-c/health | python3 -m json.tool

# 測試完整流程
python3 test_api.py

# 確認無誤後，停止 Flask（Ctrl+C）
```

### 步驟 4：配置 systemd 服務（生產環境）

```bash
# 建立服務檔案
sudo tee /etc/systemd/system/security-c-rpa.service > /dev/null <<'EOF'
[Unit]
Description=Security C RPA Flask API
After=network.target

[Service]
Type=simple
User=lladm
WorkingDirectory=/home/lladm/frank/n8n/客戶問卷RPA
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /home/lladm/frank/n8n/客戶問卷RPA/server.py
Restart=always
RestartSec=10
StandardOutput=append:/home/lladm/frank/n8n/客戶問卷RPA/logs/flask.log
StandardError=append:/home/lladm/frank/n8n/客戶問卷RPA/logs/flask_error.log

[Install]
WantedBy=multi-user.target
EOF

# 建立日誌目錄
mkdir -p /home/lladm/frank/n8n/客戶問卷RPA/logs

# 重新載入 systemd
sudo systemctl daemon-reload

# 啟動服務
sudo systemctl start security-c-rpa

# 設定開機自動啟動
sudo systemctl enable security-c-rpa

# 檢查服務狀態
sudo systemctl status security-c-rpa
```

### 步驟 5：配置 Nginx 反向代理（選配）

```bash
# 建立 Nginx 配置
sudo tee /etc/nginx/sites-available/security-c-rpa > /dev/null <<'EOF'
server {
    listen 80;
    server_name security-c.ennostar.com;  # 改成你的域名

    location / {
        proxy_pass http://127.0.0.1:5555;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
EOF

# 啟用配置
sudo ln -s /etc/nginx/sites-available/security-c-rpa /etc/nginx/sites-enabled/

# 測試 Nginx 配置
sudo nginx -t

# 重新載入 Nginx
sudo systemctl reload nginx
```

### 步驟 6：匯入 n8n Workflow

```bash
# 方式一：透過 n8n Web UI
# 1. 訪問 http://10.80.15.16:5678/
# 2. 點選 "Import from File"
# 3. 選擇 workflow_security_c.json
# 4. 啟動 Workflow

# 方式二：使用 n8n API（如果有配置）
curl -X POST http://10.80.15.16:5678/rest/workflows/import \
  -H "Content-Type: application/json" \
  -d @workflow_security_c.json
```

### 步驟 7：測試完整流程

```bash
# 測試 n8n Webhook
curl -X POST http://10.80.15.16:5678/webhook/security-c-upload \
  -F "file=@附件二.xlsx" \
  -F "client_name=測試客戶" \
  --output 測試結果.xlsx

# 檢查輸出檔案
ls -lh 測試結果.xlsx

# 用 Python 檢查內容
python3 << 'EOF'
import openpyxl
wb = openpyxl.load_workbook('測試結果.xlsx')
ws = wb.active
print(f"✅ 檔案讀取成功，共 {ws.max_row} 行")
print(f"第3行 D欄: {ws['D3'].value}")
print(f"第3行 E欄: {ws['E3'].value[:50]}...")
wb.close()
EOF
```

---

## 🔧 常用維護指令

### 查看 Flask 日誌

```bash
# 即時查看日誌
tail -f /home/lladm/frank/n8n/客戶問卷RPA/logs/flask.log

# 查看錯誤日誌
tail -f /home/lladm/frank/n8n/客戶問卷RPA/logs/flask_error.log

# 查看最近 100 行
tail -n 100 /home/lladm/frank/n8n/客戶問卷RPA/logs/flask.log
```

### 重新啟動服務

```bash
# 重新啟動 Flask
sudo systemctl restart security-c-rpa

# 查看狀態
sudo systemctl status security-c-rpa

# 如果有問題，查看詳細日誌
sudo journalctl -u security-c-rpa -f
```

### 更新資料庫（附件三）

```bash
# 1. 備份舊資料庫
cp 附件三.xlsx 附件三_備份_$(date +%Y%m%d).xlsx

# 2. 上傳新的附件三.xlsx 到專案目錄

# 3. 驗證資料庫格式
python3 << 'EOF'
import openpyxl
wb = openpyxl.load_workbook('附件三.xlsx')
ws = wb.active
print(f"✅ 資料庫載入成功，共 {ws.max_row} 行")
print(f"B2: {ws['B2'].value}")
print(f"C2: {ws['C2'].value[:30]}...")
wb.close()
EOF

# 4. 不需要重啟服務，Flask 每次都會重新讀取
```

### 更新程式碼

```bash
# 1. 備份現有程式碼
cp server.py server.py.backup
cp rpa_security_c.py rpa_security_c.py.backup

# 2. 上傳新的程式碼檔案

# 3. 重新啟動服務
sudo systemctl restart security-c-rpa

# 4. 驗證服務正常
curl http://127.0.0.1:5555/api/security-c/health
```

---

## 📊 監控與告警

### 檢查服務健康狀態

```bash
# 建立健康檢查腳本
cat > /home/lladm/frank/n8n/客戶問卷RPA/health_check.sh <<'EOF'
#!/bin/bash

HEALTH_URL="http://127.0.0.1:5555/api/security-c/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" = "200" ]; then
    echo "✅ Security C RPA 服務運行正常"
    exit 0
else
    echo "❌ Security C RPA 服務異常 (HTTP $RESPONSE)"
    exit 1
fi
EOF

chmod +x /home/lladm/frank/n8n/客戶問卷RPA/health_check.sh

# 執行檢查
./health_check.sh
```

### 設定 Cron 定時檢查

```bash
# 編輯 crontab
crontab -e

# 新增以下行（每 5 分鐘檢查一次）
*/5 * * * * /home/lladm/frank/n8n/客戶問卷RPA/health_check.sh >> /home/lladm/frank/n8n/客戶問卷RPA/logs/health_check.log 2>&1
```

---

## 🐛 故障排除

### 問題 1：Flask 無法啟動

```bash
# 檢查 Port 是否被佔用
sudo netstat -tulpn | grep 5555

# 如果被佔用，找出進程並終止
sudo lsof -i :5555
sudo kill -9 <PID>

# 檢查 Python 環境
python3 --version
python3 -c "import flask; print(flask.__version__)"
```

### 問題 2：找不到附件三

```bash
# 檢查檔案路徑
ls -lh /home/lladm/frank/n8n/客戶問卷RPA/附件三.xlsx

# 檢查檔案權限
chmod 644 /home/lladm/frank/n8n/客戶問卷RPA/附件三.xlsx
```

### 問題 3：API 超時

```bash
# 增加 gunicorn timeout
gunicorn -w 4 -b 0.0.0.0:5555 --timeout 1200 server:app

# 或在 systemd 服務中修改
sudo nano /etc/systemd/system/security-c-rpa.service

# 改為
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:5555 --timeout 1200 server:app

# 重新載入並重啟
sudo systemctl daemon-reload
sudo systemctl restart security-c-rpa
```

### 問題 4：中文亂碼

```bash
# 設定系統編碼
export LANG=zh_TW.UTF-8
export LC_ALL=zh_TW.UTF-8

# 寫入 ~/.bashrc
echo 'export LANG=zh_TW.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=zh_TW.UTF-8' >> ~/.bashrc
```

---

## 🔒 安全性設定

### 限制 API 訪問

```python
# 在 server.py 中新增
from flask import request, abort

@app.before_request
def check_ip():
    allowed_ips = ['10.80.15.16', '127.0.0.1', '10.100.40.5']
    if request.remote_addr not in allowed_ips:
        abort(403)
```

### 新增 API Key 驗證

```python
# 在 server.py 中新增
API_KEY = "your-secret-api-key-here"

@app.before_request
def verify_api_key():
    if request.endpoint == 'static':
        return
    api_key = request.headers.get('X-API-Key')
    if api_key != API_KEY:
        abort(401)
```

---

## 📝 備份策略

```bash
# 建立每日備份腳本
cat > /home/lladm/frank/n8n/客戶問卷RPA/backup.sh <<'EOF'
#!/bin/bash

BACKUP_DIR="/home/lladm/frank/n8n/客戶問卷RPA/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 備份資料庫
cp 附件三.xlsx $BACKUP_DIR/附件三_$DATE.xlsx

# 備份程式碼
tar -czf $BACKUP_DIR/code_$DATE.tar.gz \
    server.py \
    rpa_security_c.py \
    requirements.txt \
    workflow_security_c.json

# 清理 30 天前的備份
find $BACKUP_DIR -name "*.xlsx" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "✅ 備份完成: $DATE"
EOF

chmod +x backup.sh

# 設定每日 02:00 自動備份
crontab -e
# 新增：0 2 * * * /home/lladm/frank/n8n/客戶問卷RPA/backup.sh >> /home/lladm/frank/n8n/客戶問卷RPA/logs/backup.log 2>&1
```

---

## 📞 緊急聯絡

- **開發者**: Frank Fu
- **系統管理員**: Jovi Chou
- **業務窗口**: Irene Chen
- **IT 支援**: IT 部門

---

**✅ 部署完成後，請進行完整測試並更新此文件！**
