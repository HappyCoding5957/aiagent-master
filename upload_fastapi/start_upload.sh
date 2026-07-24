#!/bin/bash
cd /home/ifm02web/aiagent/upload_fastapi
echo "🚀 啟動 ESG Upload System (FastAPI) - Port 8001"
nohup python3 upload_server.py > /tmp/upload.log 2>&1 &
echo $! > /tmp/upload.pid
echo "✅ 服務已啟動，PID: $(cat /tmp/upload.pid)"
echo "📋 日誌：tail -f /tmp/upload.log"
