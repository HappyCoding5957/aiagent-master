#!/bin/bash
# 停止所有 ESG Portal 服務（精確停止，避免誤殺其他服務）

echo "========================================"
echo "停止所有 ESG Portal 服務"
echo "========================================"

stop_service() {
    local name=$1
    local pattern=$2
    if pgrep -f "$pattern" > /dev/null; then
        echo "🛑 停止 $name..."
        pkill -f "$pattern"
        sleep 1
        if pgrep -f "$pattern" > /dev/null; then
            echo "⚠️  $name 未能正常停止，強制終止..."
            pkill -9 -f "$pattern"
        fi
        echo "✅ $name 已停止"
    else
        echo "⚠️  $name 未運行"
    fi
}

stop_service "Upload (8001)"       "upload_server\.py"
stop_service "Download (8002)"     "download_server\.py"
stop_service "PaddleOCR (8095)"    "PaddleOCR/server\.py"
stop_service "Proxy (4202)"        "proxy_fastapi\.py"

echo ""
echo "========================================"
echo "✅ 所有服務已停止"
echo "========================================"
