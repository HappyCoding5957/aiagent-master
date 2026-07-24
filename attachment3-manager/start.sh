#!/bin/bash

echo "=========================================="
echo "  附件三知識庫管理系統 - 啟動腳本"
echo "=========================================="

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ 錯誤：未安裝 Docker"
    echo "請先安裝 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 檢查 Docker Compose 是否安裝（v2 使用 docker compose）
if ! docker compose version &> /dev/null; then
    echo "❌ 錯誤：未安裝 Docker Compose"
    echo "請先安裝 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo ""
echo "✅ Docker 和 Docker Compose 已安裝"
echo ""

# 停止並刪除舊容器
echo "🛑 停止舊容器..."
docker compose down

echo ""
echo "🏗️  開始建置並啟動服務..."
docker compose up -d --build

echo ""
echo "⏳ 等待服務啟動..."
sleep 5

echo ""
echo "📊 檢查服務狀態..."
docker compose ps

echo ""
echo "=========================================="
echo "  ✅ 系統已啟動！"
echo "=========================================="
echo ""
echo "📍 訪問地址："
echo "  - 前端介面: http://10.100.40.5:4200"
echo "  - 後端 API: http://10.100.40.5:8000"
echo "  - API 文檔: http://10.100.40.5:8000/docs"
echo ""
echo "🪟 Windows 用戶請在瀏覽器中訪問："
echo "  http://10.100.40.5:4200"
echo ""
echo "📝 查看日誌："
echo "  docker compose logs -f"
echo ""
echo "🛑 停止服務："
echo "  docker compose down"
echo "=========================================="
