#!/bin/bash
# 啟動所有 RPA Security C 服務

cd /home/ifm02web/aiagent

echo "========================================"
echo "啟動 RPA Security C 服務"
echo "========================================"

# 檢查 venv
if [ ! -d "venv" ]; then
    echo "❌ 找不到 venv 虛擬環境"
    exit 1
fi

# 檢查 server.py 是否已運行
if pgrep -f "python.*server.py" > /dev/null; then
    echo "⚠️  server.py 已經在運行"
else
    echo "✅ 啟動 server.py (port 4204)..."
    source venv/bin/activate
    nohup python3 server.py > /tmp/server_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    sleep 2
fi

# 檢查 proxy_server.py 是否已運行
if pgrep -f "python.*proxy_server.py" > /dev/null; then
    echo "⚠️  proxy_server.py 已經在運行"
else
    echo "✅ 啟動 proxy_server.py..."
    nohup python3 -u proxy_server.py > /tmp/proxy_server.log 2>&1 &
    sleep 2
fi

echo ""
echo "========================================"
echo "服務狀態檢查"
echo "========================================"

# 檢查服務
if pgrep -f "python.*server.py" > /dev/null; then
    echo "✅ server.py 運行中 (PID: $(pgrep -f 'python.*server.py' | head -1))"
else
    echo "❌ server.py 未運行"
fi

if pgrep -f "python.*proxy_server.py" > /dev/null; then
    echo "✅ proxy_server.py 運行中 (PID: $(pgrep -f 'python.*proxy_server.py' | head -1))"
else
    echo "❌ proxy_server.py 未運行"
fi

# 檢查端口
echo ""
echo "端口監聽狀態："
ss -tlnp 2>/dev/null | grep ':4204' || echo "❌ port 4204 未監聽"

echo ""
echo "========================================"
echo "✅ 啟動完成"
echo "========================================"
