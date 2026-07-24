#!/bin/bash
# FastAPI Proxy 啟動腳本

cd /home/ifm02web/aiagent/fastapi_proxy

echo "========================================="
echo "🚀 啟動 FastAPI Proxy (Port 4202)"
echo "========================================="

# 檢查是否有舊進程
OLD_PID=$(ps aux | grep "proxy_fastapi.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$OLD_PID" ]; then
    echo "⚠️  發現舊進程 (PID: $OLD_PID)，正在停止..."
    kill -9 $OLD_PID
    sleep 1
fi

# 啟動新服務
nohup python3 proxy_fastapi.py > /tmp/fastapi_proxy.log 2>&1 &
NEW_PID=$!

sleep 2

# 檢查是否啟動成功
if ps -p $NEW_PID > /dev/null; then
    echo "✅ FastAPI Proxy 已啟動 (PID: $NEW_PID)"
    echo "📋 日誌: tail -f /tmp/fastapi_proxy.log"
    
    # 檢查端口
    sleep 1
    if ss -tlnp | grep :4202 > /dev/null; then
        echo "✅ 端口 4202 監聽中"
    else
        echo "❌ 端口 4202 未監聽，請檢查日誌"
    fi
else
    echo "❌ 啟動失敗，請檢查日誌: tail /tmp/fastapi_proxy.log"
    exit 1
fi

echo "========================================="
