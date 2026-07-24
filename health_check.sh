#!/bin/bash
# AI Agent 服務健康檢查腳本
# 可用於 cron 或監控系統

SERVICES=("proxy:4202" "upload:8001" "download:8002" "paddleocr:8095")
FAILED=0

echo "[2026-02-13 07:39:54] 開始健康檢查"

for svc_port in "${SERVICES[@]}"; do
    svc=${svc_port%%:*}
    port=${svc_port##*:}
    
    # 檢查 systemd 狀態
    if systemctl is-active --quiet $svc 2>/dev/null; then
        echo "  ✅ $svc (systemd) - 運行中"
    else
        echo "  ❌ $svc (systemd) - 未運行"
        FAILED=$((FAILED+1))
    fi
    
    # 檢查端口
    if ss -tlnp 2>/dev/null | grep -q ":$port.*LISTEN"; then
        echo "  ✅ $svc (port $port) - 監聽中"
    else
        echo "  ❌ $svc (port $port) - 未監聽"
        FAILED=$((FAILED+1))
    fi
done

# 檢查 HTTP 健康端點
echo ""
echo "HTTP 健康檢查:"
if curl -sf http://localhost:8001/esg/upload/api/health > /dev/null; then
    echo "  ✅ Upload API - 正常"
else
    echo "  ❌ Upload API - 異常"
    FAILED=$((FAILED+1))
fi

if curl -sf http://localhost:8002/api/health > /dev/null; then
    echo "  ✅ Download API - 正常"
else
    echo "  ❌ Download API - 異常"
    FAILED=$((FAILED+1))
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo "[2026-02-13 07:39:54] ✅ 所有服務正常"
    exit 0
else
    echo "[2026-02-13 07:39:54] ❌ 發現 $FAILED 個問題"
    exit 1
fi
