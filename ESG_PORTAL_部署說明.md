# ESG Portal 反向代理部署說明

## 架構概覽

外部訪問固定 Port 4202
- http://ssw01.ennostar.com:4202
- 透過反向代理分流到內部服務

## 訪問路徑

- 首頁: http://ssw01.ennostar.com:4202/ (重定向到 /esg/upload/)
- 上傳: http://ssw01.ennostar.com:4202/esg/upload/ (代理到 4203)
- 下載: http://ssw01.ennostar.com:4202/esg/download/ (代理到 4204)
- SSO Callback: http://ssw01.ennostar.com:4202/callback (代理到 4204)

## 服務組件

### 1. 反向代理服務 (4202)
- 檔案: proxy_server.py
- 功能: 路由分流、URL 重寫
- 日誌: proxy.log

### 2. 上傳系統 (4203)
- 類型: Docker 容器
- 配置: attachment3-manager-sso/docker-compose.yml

### 3. 下載系統 (4204)
- 檔案: server.py
- 配置: config.json
- SSO Callback URL: http://ssw01.ennostar.com:4202/callback

## 服務管理指令

啟動所有服務:
  ./start_all_services.sh

停止所有服務:
  ./stop_all_services.sh

檢查服務狀態:
  ./check_services.sh

## 故障排除

檢查端口:
  ss -tulnp | grep -E '4202|4203|4204'

查看日誌:
  tail -f proxy.log
  tail -f server.log
  docker logs -f attachment3-frontend-sso

重啟服務:
  ./stop_all_services.sh
  ./start_all_services.sh
