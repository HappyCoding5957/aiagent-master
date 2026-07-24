#!/bin/bash
# 統一 FastAPI 架構 - 服務管理腳本

case "$1" in
  start)
    echo "🚀 啟動所有服務..."
    
    # 啟動 Proxy (4202)
    cd /home/ifm02web/aiagent/fastapi_proxy
    nohup python3 proxy_server.py > /tmp/proxy.log 2>&1 &
    echo $! > /tmp/proxy.pid
    echo "✅ Proxy (4202) 已啟動，PID: $(cat /tmp/proxy.pid)"
    
    # 啟動 Upload (8001)
    cd /home/ifm02web/aiagent/upload_fastapi
    nohup python3 upload_server.py > /tmp/upload.log 2>&1 &
    echo $! > /tmp/upload.pid
    echo "✅ Upload (8001) 已啟動，PID: $(cat /tmp/upload.pid)"
    
    # 啟動 Download (8002)
    cd /home/ifm02web/aiagent/download_fastapi
    nohup python3 download_server.py > /tmp/download.log 2>&1 &
    echo $! > /tmp/download.pid
    echo "✅ Download (8002) 已啟動，PID: $(cat /tmp/download.pid)"
    
    # 啟動 PaddleOCR (8095)
    cd /home/ifm02web/PaddleOCR
    nohup python3 server.py > /tmp/paddle.log 2>&1 &
    echo $! > /tmp/paddle.pid
    echo "✅ PaddleOCR (8095) 已啟動，PID: $(cat /tmp/paddle.pid)"
    
    echo ""
    echo "📋 服務狀態："
    sleep 2
    ss -tlnp 2>/dev/null | grep -E ':4202|:8001|:8002|:8095' | grep LISTEN
    ;;
    
  stop)
    echo "🛑 停止所有服務..."
    
    for service in proxy upload download paddle; do
      if [ -f /tmp/${service}.pid ]; then
        PID=$(cat /tmp/${service}.pid)
        if kill -0 $PID 2>/dev/null; then
          kill $PID && echo "✅ ${service} (PID: $PID) 已停止"
        else
          echo "⚠️  ${service} 未運行"
        fi
        rm -f /tmp/${service}.pid
      fi
    done
    ;;
    
  restart)
    echo "🔄 重啟所有服務..."
    $0 stop
    sleep 2
    $0 start
    ;;
    
  status)
    echo "📊 服務狀態檢查"
    echo "═══════════════════════════════════════════"
    echo ""
    
    for port in 4202 8001 8002 8095; do
      if ss -tlnp 2>/dev/null | grep -q ":.*LISTEN"; then
        echo "✅ Port $port - 運行中"
      else
        echo "❌ Port $port - 未運行"
      fi
    done
    
    echo ""
    echo "健康檢查："
    curl -s http://localhost:8001/esg/upload/api/health 2>/dev/null && echo "" || echo "❌ 8001 Upload 無回應"
    curl -s http://localhost:8002/api/health 2>/dev/null && echo "" || echo "❌ 8002 Download 無回應"
    ;;
    
  logs)
    echo "📋 服務日誌"
    echo "═══════════════════════════════════════════"
    echo ""
    echo "選擇要查看的日誌："
    echo "  1) Proxy (4202)"
    echo "  2) Upload (8001)"
    echo "  3) Download (8002)"
    echo "  4) PaddleOCR (8095)"
    echo ""
    read -p "請輸入編號 (1-4): " choice
    
    case $choice in
      1) tail -f /tmp/proxy.log ;;
      2) tail -f /tmp/upload.log ;;
      3) tail -f /tmp/download.log ;;
      4) tail -f /tmp/paddle.log ;;
      *) echo "無效選擇" ;;
    esac
    ;;
    
  *)
    echo "統一 FastAPI 架構 - 服務管理"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs}"
    echo ""
    echo "指令說明："
    echo "  start   - 啟動所有服務 (Proxy, Upload, Download, PaddleOCR)"
    echo "  stop    - 停止所有服務"
    echo "  restart - 重啟所有服務"
    echo "  status  - 查看服務狀態與健康檢查"
    echo "  logs    - 查看服務日誌"
    echo ""
    echo "服務列表："
    echo "  - 4202: FastAPI Proxy (統一入口)"
    echo "  - 8001: Upload System (FastAPI + HTML)"
    echo "  - 8002: Download System (FastAPI + HTML)"
    echo "  - 8095: PaddleOCR (FastAPI + HTML)"
    ;;
esac
