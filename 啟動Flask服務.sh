#!/bin/bash
# 附件三上傳系統 - Flask API 服務啟動腳本

cd /home/lladm/frank/n8n/客戶問卷RPA

echo "========================================================================"
echo "🚀 啟動 Flask API 服務"
echo "========================================================================"

# 檢查服務是否已經在運行
if ps aux | grep -v grep | grep "server.py" > /dev/null; then
    echo "⚠️  Flask 服務已經在運行中"
    echo ""
    ps aux | grep -v grep | grep "server.py" | awk '{printf "   PID: %s, CPU: %s, MEM: %s\n", $2, $3"%", $4"%"}'
    echo ""
    echo "如果需要重啟服務，請先執行："
    echo "   pkill -f server.py"
    echo ""
    exit 0
fi

# 啟動服務
echo "📦 啟動 Flask 服務..."
source venv/bin/activate
nohup python server.py > /tmp/flask_server.log 2>&1 &
FLASK_PID=$!

echo "✅ Flask 服務已啟動"
echo "   PID: $FLASK_PID"
echo "   日誌: /tmp/flask_server.log"
echo ""

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 3

# 檢查服務狀態
if ps -p $FLASK_PID > /dev/null; then
    echo "✅ 服務運行正常"

    # 測試 API
    echo ""
    echo "🧪 測試 API..."
    timeout 3 curl -s http://127.0.0.1:5555/api/security-c/health | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('✅ API 正常')
    print(f\"   狀態: {data.get('status')}\")
except:
    print('❌ API 異常')
"
else
    echo "❌ 服務啟動失敗"
    echo ""
    echo "查看日誌："
    tail -20 /tmp/flask_server.log
    exit 1
fi

echo ""
echo "========================================================================"
echo "🎯 服務資訊"
echo "========================================================================"
echo "API 端點："
echo "   - 健康檢查: http://10.120.170.55:5555/api/security-c/health"
echo "   - 附件三上傳: http://10.120.170.55:5555/api/attachment3/upload"
echo ""
echo "n8n Workflow："
echo "   - http://10.80.15.16:5678/workflow/UikWrnAd5k5YzUa7"
echo ""
echo "查看日誌："
echo "   tail -f /tmp/flask_server.log"
echo ""
echo "停止服務："
echo "   pkill -f server.py"
echo "========================================================================"
