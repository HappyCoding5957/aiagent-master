# 🚀 AI Agent 多服務穩定部署指南（Systemd 版本）

## 📋 目錄結構

```
/home/ifm02web/aiagent/
├── fastapi_proxy/          # Proxy 服務 (4202)
│   └── proxy_fastapi.py
├── upload_fastapi/         # Upload 服務 (8001)
│   └── upload_server.py
├── download_fastapi/       # Download 服務 (8002)
│   └── download_server.py
├── manage_systemd.sh       # 服務管理腳本
└── health_check.sh         # 健康檢查腳本

/home/ifm02web/PaddleOCR/
└── server.py               # PaddleOCR 服務 (8095)

/etc/systemd/system/
├── proxy.service
├── upload.service
├── download.service
└── paddleocr.service

/var/log/aiagent/
├── proxy.log
├── upload.log
├── download.log
└── paddleocr.log
```

---

## 🔧 安裝步驟

### Step 1: 複製 systemd 服務檔

所有服務檔已創建在 `/tmp/` 目錄：

```bash
ls -la /tmp/*.service
```

### Step 2: 執行安裝腳本（需要 sudo）

```bash
sudo bash /tmp/install_systemd_services.sh
```

這個腳本會：
1. 創建日誌目錄 `/var/log/aiagent/`
2. 安裝 systemd 服務檔到 `/etc/systemd/system/`
3. 停止舊的 nohup 進程
4. 啟用並啟動所有服務
5. 顯示服務狀態

---

## 🛠️ 服務管理指令

### 基本指令

```bash
# 查看所有服務狀態
sudo systemctl status proxy upload download paddleocr

# 啟動所有服務
sudo systemctl start proxy upload download paddleocr

# 停止所有服務
sudo systemctl stop proxy upload download paddleocr

# 重啟所有服務
sudo systemctl restart proxy upload download paddleocr
```

### 單一服務操作

```bash
# 重啟 Proxy
sudo systemctl restart proxy

# 查看 Upload 狀態
sudo systemctl status upload

# 停止 Download
sudo systemctl stop download

# 啟動 PaddleOCR
sudo systemctl start paddleocr
```

### 使用管理腳本

```bash
# 查看狀態
sudo bash /home/ifm02web/aiagent/manage_systemd.sh status

# 重啟所有服務
sudo bash /home/ifm02web/aiagent/manage_systemd.sh restart

# 查看日誌（互動式）
sudo bash /home/ifm02web/aiagent/manage_systemd.sh logs

# 健康檢查
sudo bash /home/ifm02web/aiagent/manage_systemd.sh health
```

---

## 📋 查看日誌

### 使用 journalctl（推薦）

```bash
# 即時查看 Proxy 日誌
sudo journalctl -u proxy -f

# 查看 Upload 最近 50 行日誌
sudo journalctl -u upload -n 50

# 查看 Download 今天的日誌
sudo journalctl -u download --since today

# 查看所有服務的錯誤日誌
sudo journalctl -u proxy -u upload -u download -u paddleocr --priority=err
```

### 使用檔案日誌

```bash
# 即時查看 Proxy 日誌
tail -f /var/log/aiagent/proxy.log

# 查看 Upload 錯誤日誌
tail -f /var/log/aiagent/upload.error.log

# 查看所有日誌
tail -f /var/log/aiagent/*.log
```

---

## 🔍 健康檢查

### 自動健康檢查

```bash
# 執行健康檢查腳本
bash /home/ifm02web/aiagent/health_check.sh
```

### 手動健康檢查

```bash
# 檢查 systemd 服務狀態
systemctl is-active proxy upload download paddleocr

# 檢查端口監聽
ss -tlnp | grep -E ':(4202|8001|8002|8095)'

# 檢查 HTTP API
curl http://localhost:8001/esg/upload/api/health
curl http://localhost:8002/api/health
```

---

## 🔄 自動重啟配置

所有服務已配置 `Restart=always`，當服務崩潰時會自動重啟。

重啟策略：
- `RestartSec=5` - 等待 5 秒後重啟
- `Restart=always` - 無論何種原因停止都會重啟

---

## 📊 資源限制

各服務資源配置：

| 服務 | 記憶體限制 | CPU 限制 | 文件描述符 |
|------|-----------|----------|-----------|
| Proxy | 1GB | 200% | 65535 |
| Upload | 2GB | 200% | 65535 |
| Download | 2GB | 200% | 65535 |
| PaddleOCR | 4GB | 400% | 65535 |

如需調整，編輯服務檔：

```bash
sudo nano /etc/systemd/system/proxy.service
sudo systemctl daemon-reload
sudo systemctl restart proxy
```

---

## 🔄 日誌輪轉（Logrotate）

安裝 logrotate 配置：

```bash
sudo cp /tmp/aiagent-logrotate /etc/logrotate.d/aiagent
sudo chmod 644 /etc/logrotate.d/aiagent
```

配置說明：
- 每日輪轉
- 保留 7 天
- 壓縮舊日誌
- 自動創建新日誌檔

---

## 🚨 故障排除

### 服務無法啟動

```bash
# 查看詳細錯誤
sudo journalctl -u proxy -xe

# 檢查服務配置
sudo systemctl cat proxy

# 驗證服務檔語法
sudo systemd-analyze verify /etc/systemd/system/proxy.service
```

### 端口被佔用

```bash
# 查找佔用端口的進程
sudo lsof -i :4202

# 停止衝突的進程
sudo kill -9 PID
```

### 服務頻繁重啟

```bash
# 查看重啟原因
sudo journalctl -u proxy | grep -i restart

# 暫時停用自動重啟（測試用）
sudo systemctl stop proxy
```

---

## ✅ 驗證部署成功

執行以下命令確認所有服務正常：

```bash
# 1. 檢查 systemd 狀態
sudo systemctl status proxy upload download paddleocr

# 2. 檢查端口監聽
ss -tlnp | grep -E ':(4202|8001|8002|8095)'

# 3. 檢查 HTTP API
curl http://localhost:8001/esg/upload/api/health
curl http://localhost:8002/api/health

# 4. 執行健康檢查腳本
bash /home/ifm02web/aiagent/health_check.sh
```

所有檢查通過後，即完成部署！🎉

---

## 📞 常見問題

**Q: 如何查看某個服務的完整啟動日誌？**
```bash
sudo journalctl -u proxy --no-pager
```

**Q: 如何臨時停止自動重啟？**
```bash
sudo systemctl stop proxy
sudo systemctl disable proxy  # 禁用開機自動啟動
```

**Q: 如何修改服務配置？**
```bash
sudo nano /etc/systemd/system/proxy.service
sudo systemctl daemon-reload
sudo systemctl restart proxy
```

**Q: 如何永久刪除服務？**
```bash
sudo systemctl stop proxy
sudo systemctl disable proxy
sudo rm /etc/systemd/system/proxy.service
sudo systemctl daemon-reload
```

---

## 🎯 最佳實踐

1. **定期檢查日誌**
   ```bash
   sudo journalctl -u proxy --since "1 hour ago"
   ```

2. **設置日誌警報**（可選）
   - 配置 logwatch 或其他監控工具
   - 當服務重啟時發送通知

3. **定期備份配置**
   ```bash
   sudo cp /etc/systemd/system/*.service /home/ifm02web/backup/
   ```

4. **資源監控**
   ```bash
   htop  # 查看 CPU/記憶體使用
   df -h  # 查看磁碟空間
   ```

---

## 📚 相關文檔

- [Systemd 官方文檔](https://www.freedesktop.org/wiki/Software/systemd/)
- [Systemd Service 配置](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Journalctl 使用指南](https://www.freedesktop.org/software/systemd/man/journalctl.html)

