#!/bin/bash
# AI Agent 服務管理工具（需要 sudo）

show_help() {
    cat << EOF
╔════════════════════════════════════════════════════════════════╗
║  🛠️  AI Agent 服務管理工具 (Systemd 版本)                     ║
╚════════════════════════════════════════════════════════════════╝

用法: sudo bash manage_systemd.sh [指令]

指令:
  status     - 查看所有服務狀態
  start      - 啟動所有服務
  stop       - 停止所有服務
  restart    - 重啟所有服務
  logs       - 查看服務日誌（互動式）
  health     - 健康檢查
  help       - 顯示此幫助訊息

單一服務操作:
  sudo systemctl status proxy
  sudo systemctl restart upload
  sudo journalctl -u download -f

服務列表:
  - proxy      (4202) FastAPI Proxy
  - upload     (8001) Upload System
  - download   (8002) Download System
  - paddleocr  (8095) PaddleOCR Service
EOF
}

check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        echo "❌ 請使用 sudo 執行此腳本"
        echo "用法: sudo bash manage_systemd.sh $1"
        exit 1
    fi
}

case "$1" in
    status)
        check_sudo
        echo "📊 服務狀態檢查"
        echo "════════════════════════════════════════"
        for svc in proxy upload download paddleocr; do
            if systemctl is-active --quiet $svc; then
                echo "✅ $svc - 運行中"
            else
                echo "❌ $svc - 未運行"
            fi
        done
        echo ""
        echo "健康檢查:"
        curl -s http://localhost:8001/esg/upload/api/health 2>/dev/null && echo "" || echo "❌ 8001 Upload 無回應"
        curl -s http://localhost:8002/api/health 2>/dev/null && echo "" || echo "❌ 8002 Download 無回應"
        ;;
        
    start)
        check_sudo
        echo "🚀 啟動所有服務..."
        for svc in proxy upload download paddleocr; do
            systemctl start $svc && echo "✅ $svc 已啟動" || echo "❌ $svc 啟動失敗"
        done
        ;;
        
    stop)
        check_sudo
        echo "🛑 停止所有服務..."
        for svc in proxy upload download paddleocr; do
            systemctl stop $svc && echo "✅ $svc 已停止" || echo "❌ $svc 停止失敗"
        done
        ;;
        
    restart)
        check_sudo
        echo "🔄 重啟所有服務..."
        for svc in proxy upload download paddleocr; do
            systemctl restart $svc && echo "✅ $svc 已重啟" || echo "❌ $svc 重啟失敗"
        done
        ;;
        
    logs)
        check_sudo
        echo "📋 選擇要查看的日誌:"
        echo "  1) Proxy (4202)"
        echo "  2) Upload (8001)"
        echo "  3) Download (8002)"
        echo "  4) PaddleOCR (8095)"
        echo ""
        read -p "請輸入編號 (1-4): " choice
        
        case $choice in
            1) journalctl -u proxy -f ;;
            2) journalctl -u upload -f ;;
            3) journalctl -u download -f ;;
            4) journalctl -u paddleocr -f ;;
            *) echo "無效選擇" ;;
        esac
        ;;
        
    health)
        echo "🧪 健康檢查"
        echo "════════════════════════════════════════"
        echo ""
        echo "✅ 8001 Upload:"
        curl -s http://localhost:8001/esg/upload/api/health | python3 -m json.tool 2>/dev/null || echo "❌ 無回應"
        echo ""
        echo "✅ 8002 Download:"
        curl -s http://localhost:8002/api/health | python3 -m json.tool 2>/dev/null || echo "❌ 無回應"
        echo ""
        ;;
        
    help|*)
        show_help
        ;;
esac
