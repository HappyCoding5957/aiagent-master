#!/bin/bash
# 測試 n8n webhook 上傳功能（完整流程）

echo "========================================================================"
echo "🧪 測試 n8n Webhook 附件三上傳（端到端測試）"
echo "========================================================================"

# 檢查 Flask 服務
echo "1️⃣  檢查 Flask 服務狀態..."
if ! ps aux | grep -v grep | grep "server.py" > /dev/null; then
    echo "❌ Flask 服務未運行"
    echo "   請先執行: ./啟動Flask服務.sh"
    exit 1
fi
echo "✅ Flask 服務運行中"
echo ""

# 創建測試 Excel
echo "2️⃣  創建測試 Excel 檔案..."
python3 << 'PYEOF'
import openpyxl
import base64
import json
from datetime import datetime

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "附件三"

# 添加標題行
ws.append(['廠商料號', '廠牌', '類別', '品名', '規格'])

# 添加測試數據（帶時間戳）
timestamp = datetime.now().strftime('%H:%M:%S')
ws.append([f'TEST-{timestamp}-001', '測試廠牌A', '電子零件', '測試產品A', '規格A'])
ws.append([f'TEST-{timestamp}-002', '測試廠牌B', '機械零件', '測試產品B', '規格B'])
ws.append([f'TEST-{timestamp}-003', '測試廠牌C', '化學材料', '測試產品C', '規格C'])
ws.append([f'TEST-{timestamp}-004', '測試廠牌D', '電氣設備', '測試產品D', '規格D'])
ws.append([f'TEST-{timestamp}-005', '測試廠牌E', '安全裝備', '測試產品E', '規格E'])

test_file = '/tmp/test_n8n_upload.xlsx'
wb.save(test_file)

print(f"✅ 測試檔案已創建: {test_file}")
print(f"   包含 5 筆測試資料（時間戳: {timestamp}）")
PYEOF

if [ $? -ne 0 ]; then
    echo "❌ 創建測試檔案失敗"
    exit 1
fi
echo ""

# 上傳到 n8n webhook
echo "3️⃣  上傳到 n8n webhook..."
echo "   URL: http://10.80.15.16:5678/webhook/attachment3-upload"
echo ""

timeout 30 curl -X POST "http://10.80.15.16:5678/webhook/attachment3-upload" \
  -F "file=@/tmp/test_n8n_upload.xlsx" \
  -H "Accept: application/json" \
  -s -w "\n   HTTP 狀態碼: %{http_code}\n" \
  > /tmp/n8n_upload_response.txt 2>&1

UPLOAD_STATUS=$?

if [ $UPLOAD_STATUS -eq 0 ]; then
    echo "✅ 上傳請求完成"
    echo ""
    echo "📋 n8n 回應:"
    cat /tmp/n8n_upload_response.txt | python3 << 'PYEOF'
import json
import sys

try:
    lines = sys.stdin.read().strip().split('\n')

    # 找到 JSON 部分（排除 HTTP 狀態碼行）
    json_lines = [line for line in lines if not line.strip().startswith('HTTP')]
    json_text = '\n'.join(json_lines)

    if json_text:
        data = json.loads(json_text)

        if data.get('success'):
            print("   ✅ 上傳成功")
            print(f"   PDF ID: {data.get('pdf_id')}")
            print(f"   資料筆數: {data.get('chunk_count')}")
            print(f"   訊息: {data.get('message')}")
            sys.exit(0)
        else:
            print("   ❌ 上傳失敗")
            print(f"   錯誤: {data.get('error')}")
            sys.exit(1)
    else:
        print("   ⚠️  收到空回應")
        sys.exit(1)

except json.JSONDecodeError as e:
    print(f"   ⚠️  JSON 解析失敗: {e}")
    print("   原始回應:")
    print(sys.stdin.read())
    sys.exit(1)
except Exception as e:
    print(f"   ❌ 錯誤: {e}")
    sys.exit(1)
PYEOF

    TEST_RESULT=$?

    if [ $TEST_RESULT -eq 0 ]; then
        echo ""
        echo "========================================================================"
        echo "✅ 完整流程測試通過！"
        echo "========================================================================"
        echo ""
        echo "🎯 測試結論："
        echo "   ✅ Flask API 服務正常"
        echo "   ✅ n8n Webhook 正常"
        echo "   ✅ HTTP Request 節點正常"
        echo "   ✅ 資料庫寫入正常"
        echo ""
        echo "📝 系統可以正常使用了！"
        echo ""
        echo "從 Windows 測試："
        echo "   訪問 http://10.80.15.16:5678/webhook/attachment3-upload"
        echo "   或訪問管理頁面："
        echo "   http://10.80.15.16:5678/webhook/attachment3-management"
        echo "========================================================================"
    else
        echo ""
        echo "========================================================================"
        echo "❌ 測試失敗"
        echo "========================================================================"
        echo ""
        echo "請檢查："
        echo "   1. Flask 日誌: tail -f /tmp/flask_server.log"
        echo "   2. n8n workflow: http://10.80.15.16:5678/workflow/UikWrnAd5k5YzUa7"
        echo "   3. n8n 執行記錄: http://10.80.15.16:5678/workflow/UikWrnAd5k5YzUa7/executions"
        echo ""
        echo "原始回應內容："
        cat /tmp/n8n_upload_response.txt
        echo ""
        echo "========================================================================"
        exit 1
    fi
else
    echo "❌ 上傳請求失敗 (退出碼: $UPLOAD_STATUS)"
    echo ""
    echo "可能的原因："
    echo "   1. 網路連線問題"
    echo "   2. n8n 伺服器未運行"
    echo "   3. webhook URL 不正確"
    echo ""
    echo "請檢查："
    echo "   - n8n 是否運行: ssh ifm02web@10.80.15.16 'ps aux | grep n8n'"
    echo "   - 網路連線: ping 10.80.15.16"
    echo "========================================================================"
    exit 1
fi
