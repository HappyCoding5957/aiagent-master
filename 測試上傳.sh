#!/bin/bash
# 附件三上傳系統 - 測試腳本

echo "========================================================================"
echo "🧪 測試附件三上傳功能"
echo "========================================================================"

# 檢查 Flask 服務
echo "1️⃣  檢查 Flask 服務..."
if ! ps aux | grep -v grep | grep "server.py" > /dev/null; then
    echo "❌ Flask 服務未運行"
    echo "   請先執行: ./啟動Flask服務.sh"
    exit 1
fi
echo "✅ Flask 服務運行中"
echo ""

# 測試健康檢查
echo "2️⃣  測試健康檢查 API..."
HEALTH=$(timeout 3 curl -s http://127.0.0.1:5555/api/security-c/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ 健康檢查通過"
else
    echo "❌ 健康檢查失敗"
    exit 1
fi
echo ""

# 創建測試 Excel
echo "3️⃣  創建測試 Excel 檔案..."
python3 << 'PYEOF'
import openpyxl
import base64
import json

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "附件三"

# 添加標題行
ws.append(['廠商料號', '廠牌', '類別', '品名', '規格'])

# 添加測試數據
ws.append(['TEST001', '測試廠牌A', '測試類別A', '測試產品A', '測試規格A'])
ws.append(['TEST002', '測試廠牌B', '測試類別B', '測試產品B', '測試規格B'])
ws.append(['TEST003', '測試廠牌C', '測試類別C', '測試產品C', '測試規格C'])

test_file = '/tmp/test_upload.xlsx'
wb.save(test_file)

with open(test_file, 'rb') as f:
    base64_data = base64.b64encode(f.read()).decode()

payload = {"base64Data": base64_data}
with open('/tmp/test_upload_payload.json', 'w') as f:
    json.dump(payload, f)

print(f"✅ 測試檔案已創建 (3 筆資料)")
PYEOF

if [ $? -ne 0 ]; then
    echo "❌ 創建測試檔案失敗"
    exit 1
fi
echo ""

# 測試上傳
echo "4️⃣  測試上傳 API..."
timeout 10 curl -s -X POST http://127.0.0.1:5555/api/attachment3/upload \
  -H "Content-Type: application/json" \
  -d @/tmp/test_upload_payload.json \
  > /tmp/test_upload_response.json

python3 << 'PYEOF'
import json
import sys

try:
    with open('/tmp/test_upload_response.json') as f:
        data = json.load(f)
    if data.get('success'):
        print("✅ 上傳測試成功")
        print(f"   PDF ID: {data.get('pdf_id')}")
        print(f"   資料筆數: {data.get('chunk_count')}")
        sys.exit(0)
    else:
        print(f"❌ 上傳失敗: {data.get('error')}")
        sys.exit(1)
except Exception as e:
    print(f"❌ 解析回應失敗: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✅ 所有測試通過！"
    echo "========================================================================"
    echo "系統可以正常使用"
    echo ""
    echo "📝 從 Windows 測試："
    echo "   訪問 http://10.80.15.16:5678/webhook/attachment3-upload"
    echo "   上傳 Excel 檔案"
    echo "========================================================================"
else
    echo ""
    echo "========================================================================"
    echo "❌ 測試失敗"
    echo "========================================================================"
    echo "請檢查："
    echo "   - Flask 服務日誌: tail -f /tmp/flask_server.log"
    echo "   - 資料庫連線: PGPASSWORD=dgtk psql -h 10.100.40.5 -p 8002 -U dgtk -d dgtk"
    echo "========================================================================"
    exit 1
fi
