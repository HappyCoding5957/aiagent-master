#!/bin/bash
# 客戶問卷 RPA - SSO 整合版啟動腳本

cd /home/lladm/frank/n8n-MCP/客戶問卷RPA

echo "=================================="
echo "客戶問卷 RPA - SSO 整合版"
echo "=================================="

# 檢查 venv 是否存在
if [ ! -d "venv" ]; then
    echo "❌ 找不到 venv 虛擬環境"
    echo "請先建立虛擬環境：python3 -m venv venv"
    exit 1
fi

# 檢查 config.json 是否存在
if [ ! -f "config.json" ]; then
    echo "❌ 找不到 config.json"
    echo "請先建立配置檔案"
    exit 1
fi

# 檢查 SSO Secret 是否已設定
if grep -q "PLEASE_REPLACE_WITH_REAL_SECRET" config.json; then
    echo "⚠️  警告：請先在 config.json 設定正確的 sso_client_secret"
    echo ""
    echo "請向 IT 部門申請 Keycloak Client Secret，然後更新："
    echo "  vim config.json"
    echo ""
    read -p "是否繼續啟動（用於測試）？ [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 檢查資料庫檔案
if [ ! -f "附件三.xlsx" ]; then
    echo "⚠️  警告：找不到附件三.xlsx"
    echo "請確保資料庫檔案存在"
fi

# 啟動服務
echo ""
echo "✅ 正在啟動服務..."
source venv/bin/activate
python server.py
