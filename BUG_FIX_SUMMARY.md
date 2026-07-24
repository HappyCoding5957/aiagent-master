# Bug 修復總結

## 🐛 問題描述

使用者回報兩個問題：

1. **中文顯示亂碼**
   ```
   👤 當前用戶： "Frank Fu \345\202\205\345\243\253\350\273\222" (2508105)
   ```

2. **登出功能 404 錯誤**
   ```
   Failed to load resource: the server responded with a status of 404 (NOT FOUND)
   ```

---

## 🔍 根本原因分析

### 問題 1：中文亂碼
- **原因**：sso.py 在設定 cookie 時，沒有對中文字進行 URL 編碼
- **影響**：瀏覽器無法正確解碼 cookie 中的中文資訊（姓名、部門）
- **位置**：`sso.py` 的 `callback()` 函數 line 55-58

### 問題 2：登出 404
- **原因**：前端呼叫 `/logout` 路由，但該路由需要 `logout_url` cookie，而該 cookie 並未被設定或已過期
- **影響**：點擊登出按鈕時，跳轉到 `None`，導致 404 錯誤
- **位置**：
  - `test_upload.html` line 226 呼叫 `/logout`
  - `sso.py` line 66 讀取 `logout_url` cookie 失敗

---

## ✅ 修復方案

### 修復 1：中文編碼問題

**檔案：** `sso.py`

**修改前：**
```python
resp.set_cookie('preferred_username', preferred_username)
resp.set_cookie('family_name', family_name)
resp.set_cookie('email', email)
resp.set_cookie('dep', dep)
```

**修改後：**
```python
from urllib.parse import quote

resp.set_cookie('preferred_username', quote(preferred_username) if preferred_username else '')
resp.set_cookie('family_name', quote(family_name) if family_name else '')
resp.set_cookie('email', quote(email) if email else '')
resp.set_cookie('dep', quote(dep) if dep else '')
```

**效果：** 使用 `quote()` 進行 URL 編碼，確保中文正確儲存在 cookie

---

### 修復 2：登出功能

**檔案：** `test_upload.html`

**修改前：**
```javascript
function logout() {
    if (confirm('確定要登出嗎？')) {
        window.location.href = '/logout';
    }
}
```

**修改後：**
```javascript
function logout() {
    if (confirm('確定要登出嗎？')) {
        window.location.href = '/logout_cookie';  // ← 改用 logout_cookie
    }
}
```

**說明：**
- `/logout` 路由需要 `logout_url` cookie（跳轉到 Keycloak 登出）
- `/logout_cookie` 路由只清除本地 cookie，不依賴 `logout_url`
- 更適合前端呼叫，避免 404 錯誤

---

### 修復 3：增強錯誤處理

**檔案：** `test_upload.html`

**新增錯誤處理：**
```javascript
try {
    document.getElementById('userName').textContent = decodeURIComponent(userName);
    document.getElementById('userJobNum').textContent = decodeURIComponent(jobNum);
    document.getElementById('userDep').textContent = decodeURIComponent(dep);
} catch (e) {
    // 如果解碼失敗，嘗試直接顯示
    document.getElementById('userName').textContent = userName;
    document.getElementById('userJobNum').textContent = jobNum;
    document.getElementById('userDep').textContent = dep;
}
```

**效果：** 避免解碼錯誤導致頁面崩潰

---

## 🧪 測試步驟

### 測試 1：中文顯示正常

1. 清除瀏覽器 cookie
2. 訪問 `http://10.100.40.5:4201/`
3. SSO 登入
4. 檢查用戶資訊是否正確顯示中文

**預期結果：**
```
👤 當前用戶： Frank Fu 傅士軒 (2508105) | 部門：資訊中心數位架構運營發展處數位應用發展部
```

---

### 測試 2：登出功能正常

1. 在登入狀態下，點擊「🚪 登出」按鈕
2. 確認彈出提示
3. 點擊確定

**預期結果：**
- 顯示「您已成功登出」頁面
- Cookie 被清除
- 可點擊「重新登入」按鈕

---

## 📝 修改檔案清單

| 檔案 | 修改內容 | 行數 |
|------|---------|------|
| `sso.py` | 新增 `quote` 匯入 | Line 3 |
| `sso.py` | Cookie 設定加入 URL 編碼 | Line 56-59 |
| `test_upload.html` | 登出改用 `/logout_cookie` | Line 234 |
| `test_upload.html` | 增加解碼錯誤處理 | Line 211-220 |

---

## 🚀 部署狀態

- ✅ 程式碼已修改
- ✅ 服務已重啟（PID: 1701798）
- ✅ 監聽 Port 4201
- ⏳ 等待使用者測試確認

---

## 📞 後續追蹤

請使用者測試以下項目並回報：

1. [ ] 中文顯示是否正常
2. [ ] 登出功能是否正常
3. [ ] 重新登入是否正常
4. [ ] 上傳功能是否正常

---

**修復時間：** 2026-01-13
**服務網址：** http://10.100.40.5:4201/
**日誌位置：** `/home/lladm/frank/n8n-MCP/客戶問卷RPA/rpa_sso.log`
