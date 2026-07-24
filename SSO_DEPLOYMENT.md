# 客戶問卷 RPA - SSO 整合部署指南

## 📋 整合說明

已成功將 **Keycloak SSO** 整合到客戶問卷 RPA 系統！

### ✅ 整合內容

1. **SSO 登入保護** - 所有路由需先通過 Keycloak 驗證
2. **用戶資訊顯示** - 頁面自動顯示當前登入用戶姓名、工號、部門
3. **本地 API 處理** - 不再需要經過 n8n webhook，直接在 Flask 處理
4. **安全性增強** - 所有操作記錄使用者資訊

---

## 🔧 部署步驟

### 步驟 1：申請 SSO Client ID 和 Secret

向 IT 部門 (Keycloak 管理員) 申請：

- **Realm**: `Infra`
- **Client ID**: `客戶問卷RPA` (或您希望的名稱)
- **Client Type**: `confidential`
- **Valid Redirect URIs**: `http://10.100.40.5:4200/*`
- **回調路徑**: `http://10.100.40.5:4200/callback`

收到 **Client Secret** 後，更新 `config.json`。

---

### 步驟 2：設定 config.json

編輯 `/home/lladm/frank/n8n-MCP/客戶問卷RPA/config.json`：

```json
{
    "sso_realm": "Infra",
    "sso_client_id": "客戶問卷RPA",  // ← 替換為實際的 Client ID
    "sso_client_secret": "YOUR_REAL_SECRET_HERE",  // ← 替換為實際的 Secret
    "web_port": 4200,
    "admin_list": ["您的工號", "其他管理員工號"],
    "upload_dir": "security_c_uploads",
    "db_path": "附件三.xlsx"
}
```

---

### 步驟 3：啟動服務

```bash
cd /home/lladm/frank/n8n-MCP/客戶問卷RPA

# 啟動 venv 環境
source venv/bin/activate

# 啟動 Flask 服務 (Port 4200)
python server.py
```

或使用背景執行：

```bash
nohup python server.py > rpa_sso.log 2>&1 &
```

---

### 步驟 4：測試 SSO 登入

1. 開啟瀏覽器，訪問：`http://10.100.40.5:4200/`
2. 系統會自動跳轉到 Keycloak 登入頁面
3. 輸入公司工號和密碼
4. 登入成功後，跳轉回上傳頁面
5. 頁面應顯示您的姓名、工號、部門

---

### 步驟 5：測試上傳功能

1. 選擇客戶問卷 Excel 檔案 (附件2格式)
2. (選填) 輸入客戶名稱
3. 點擊「🚀 開始處理」
4. 系統自動比對資料庫並下載結果

**注意：** 現在所有請求都直接在 Flask 處理，不再經過 n8n webhook。

---

## 🏗️ 架構變更

### 原本架構 (n8n)
```
使用者 → test_upload.html → n8n webhook → Flask API → 處理 → 回傳
```

### 新架構 (SSO 整合)
```
使用者 → [SSO 驗證] → test_upload.html → Flask API → 處理 → 回傳
```

### 優勢

1. ✅ **安全性** - 所有操作需先登入
2. ✅ **效能** - 減少一次網路跳轉
3. ✅ **可追溯** - 記錄所有使用者操作
4. ✅ **簡化維護** - 不需要維護 n8n workflow

---

## 🔒 SSO 路由說明

| 路由 | 保護 | 說明 |
|------|------|------|
| `/` | ✅ SSO | 上傳頁面 (自動跳轉登入) |
| `/callback` | 🔓 | SSO 回調端點 |
| `/logout` | 🔓 | 登出並清除 Cookie |
| `/api/security-c/match-from-base64` | ✅ Cookie | 問卷比對 API |
| `/api/health` | 🔓 | 健康檢查 |

---

## 🐛 故障排除

### 問題 1：無法登入，一直跳轉

**原因：** SSO Client Secret 錯誤或未設定

**解決方法：**
1. 檢查 `config.json` 中的 `sso_client_secret` 是否正確
2. 確認 Keycloak 管理員已建立對應的 Client

---

### 問題 2：登入後顯示「未知用戶」

**原因：** Cookie 未正確設定

**解決方法：**
1. 清除瀏覽器 Cookie 後重新登入
2. 檢查 `sso.py` 的 `callback()` 函數是否正確執行

---

### 問題 3：API 回傳 401 錯誤

**原因：** SSO Cookie 已過期

**解決方法：**
1. 重新整理頁面（會自動跳轉登入）
2. 或點擊「登出」後重新登入

---

## 📝 日誌檢查

所有操作都會記錄到控制台，格式：

```
[SSO] 用戶 張三 (2305018) 存取上傳頁面
[SECURITY_C] 用戶 張三 (2305018) 發起問卷比對
[SECURITY_C] 客戶名稱: 測試客戶
[SECURITY_C] 比對完成, 輸出檔案路徑 = ...
```

---

## 🔄 關於 n8n webhook

**問：原本的 n8n webhook 還需要嗎？**

**答：** 不需要！新架構已完全整合到 Flask，可以：

1. ✅ **保留 workflow 作為備用** - 不影響
2. ✅ **移除 workflow** - 節省資源
3. ✅ **修改 workflow 為內部呼叫** - 如需要可加上 API Key 保護

---

## 📞 聯絡資訊

如有問題，請聯絡：
- **系統管理員**: (請填入)
- **Keycloak 管理員**: (請填入 IT 部門聯絡方式)

---

**部署完成日期**: 2026-01-13
**整合狀態**: ✅ 已完成
