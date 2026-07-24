#!/bin/bash
# ESG Download FastAPI 啟動腳本

cd /home/ifm02web/aiagent/download_fastapi

echo "========================================="
echo "🚀 啟動 ESG Download (FastAPI - Port 8002)"
echo "========================================="

# 檢查舊進程
OLD_PID=$(ps aux | grep "download_server.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$OLD_PID" ]; then
    echo "⚠️  發現舊進程 (PID: $OLD_PID)，正在停止..."
    kill -9 $OLD_PID
    sleep 1
fi

# 啟動服務
nohup python3 download_server.py > /tmp/download_fastapi.log 2>&1 &
NEW_PID=$!

sleep 3

# 檢查啟動狀態
if ps -p $NEW_PID > /dev/null; then
    echo "✅ ESG Download 已啟動 (PID: $NEW_PID)"
    echo "📋 日誌: tail -f /tmp/download_fastapi.log"
    
    # 檢查端口
    if ss -tlnp | grep :8002 > /dev/null; then
        echo "✅ 端口 8002 監聽中"
    else
        echo "❌ 端口 8002 未監聽，請檢查日誌"
    fi
else
    echo "❌ 啟動失敗，請檢查日誌: tail /tmp/download_fastapi.log"
    exit 1
fi

echo "========================================="
