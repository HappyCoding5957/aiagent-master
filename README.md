# 客戶問卷 RPA (Security C) - 使用說明

## 📋 系統概述

這是一個自動化客戶問卷處理系統，用於處理「供應商企業社會責任承諾書」相關問卷。系統會自動比對問卷題目與資料庫，並填入對應的「權責部門」和「目前現況/可能影響」欄位。

### 核心功能

- ✅ **兩階段智能比對**：先比對行為準則（B 欄），再比對關鍵字（C 欄）
- ✅ **自動填寫欄位**：自動填入 D 欄（權責部門）和 E 欄（現況/影響）
- ✅ **信心分數標記**：低信心題目會用黃色標記，提醒需要人工確認
- ✅ **未匹配標記**：完全未匹配的題目用紅色標記
- ✅ **處理報告**：提供詳細的比對統計報告

### 預期效益

- ⏱️ **作業時間**：從 2 小時 → 3 分鐘（減少 97.5%）
- 🎯 **準確率**：預估 85-90%（高信心項目）
- 👤 **人工介入**：僅需確認 10-15% 的低信心項目

---

## 📁 檔案結構

```
客戶問卷RPA/
├── server.py                    # Flask API 伺服器
├── rpa_security_c.py            # 核心比對邏輯
├── requirements.txt             # Python 套件依賴
├── workflow_security_c.json     # n8n Workflow 定義檔
├── test_upload.html             # 測試用上傳頁面
├── test_api.py                  # API 測試腳本
├── README.md                    # 本說明文件
│
├── 附件一_空白表_手動彙整.xlsx  # 空白模板
├── 附件二.xlsx                  # 測試樣本（輸入）
├── 附件三.xlsx                  # 資料庫（知識庫）
│
└── security_c_uploads/          # 暫存上傳檔案目錄
```

---

## 🚀 安裝與啟動

### 1. 安裝 Python 套件

```bash
cd /home/lladm/frank/n8n/客戶問卷RPA
pip3 install -r requirements.txt --break-system-packages
```

### 2. 啟動 Flask 伺服器

```bash
# 開發模式（測試用）
python3 server.py

# 生產模式（正式使用）
gunicorn -w 4 -b 0.0.0.0:5555 --timeout 600 server:app
```

### 3. 匯入 n8n Workflow

1. 登入 n8n: http://10.80.15.16:5678/
2. 點選「Import from File」
3. 選擇 `workflow_security_c.json`
4. 啟動 Workflow

---

## 📝 使用方式

### 方式一：透過網頁上傳（推薦）

1. 開啟上傳頁面：`test_upload.html`
2. 選擇或拖曳問卷 Excel 檔案（附件2格式）
3. 輸入客戶名稱（選填）
4. 點擊「開始處理」
5. 等待處理完成後，自動下載結果檔案

### 方式二：直接呼叫 API

```python
import requests
import base64

# 讀取 Excel 並轉為 base64
with open("附件二.xlsx", "rb") as f:
    file_base64 = base64.b64encode(f.read()).decode('utf-8')

# 呼叫 API
response = requests.post(
    "http://10.80.15.16:5555/api/security-c/match-from-base64",
    json={
        "file_base64": file_base64,
        "client_name": "客戶名稱"
    },
    timeout=600
)

result = response.json()

# 儲存結果
if result["success"]:
    result_bytes = base64.b64decode(result["file_base64"])
    with open("結果.xlsx", "wb") as f:
        f.write(result_bytes)
```

### 方式三：透過 n8n Webhook

```bash
curl -X POST http://10.80.15.16:5678/webhook/security-c-upload \
  -F "file=@附件二.xlsx" \
  -F "client_name=客戶名稱" \
  --output 結果.xlsx
```

---

## 📊 輸入檔案格式要求（附件2）

### 必要欄位

| 欄位 | 說明 | 範例 |
|------|------|------|
| A | 類別/項次 | Labor 勞工、Health & Safety |
| B | 行為準則（選填） | 禁止強迫勞動、青年勞工 |
| **C** | **題目內容（必填）** | [自由選擇職業] 供應商禁止使用強逼... |
| **D** | **鑑別權責部門（RPA 填寫）** | 招募、薪酬、採購 |
| **E** | **目前現況/可能影響（RPA 填寫）** | (SAS100019)人員進用作業辦法... |

### 注意事項

- C 欄必須有題目內容，不可空白
- D、E 欄會被 RPA 自動覆寫
- 建議從第 3 行開始填寫題目（第 1 行空白、第 2 行標題）

---

## 🗄️ 資料庫格式要求（附件3）

### 欄位對應

| 欄位 | 說明 | 比對用途 |
|------|------|----------|
| A | 類別 | 分組參考 |
| **B** | **行為準則** | ✅ 第一階段比對目標 |
| **C** | **關鍵字（換行分隔）** | ✅ 第二階段比對目標 |
| D | 中文條文內容 | 回答主體 |
| **E** | **權責部門** | ✅ 寫入附件2 D欄 |
| **F** | **目前現況/可能影響** | ✅ 寫入附件2 E欄 |
| G | 問卷出處 | 追蹤來源 |

### 關鍵字格式範例（C 欄）

```
強迫勞動
自由選擇就業
外籍移工
人口販運
```

### 彙整版識別規則

系統會自動判斷「彙整版」（若條文內容 > 500 字）。彙整版在比對時會獲得額外加分，優先被選中。

---

## ⚙️ 比對邏輯說明

### 兩階段比對流程

```
問卷題目（C 欄）
    ↓
【第一階段】比對行為準則（附件3 B 欄）
    ├─ 計算相似度分數（fuzz.partial_ratio）
    ├─ 閾值：60（主要）/ 50（備援）
    └─ 篩選出候選項目
    ↓
【第二階段】比對關鍵字（附件3 C 欄）
    ├─ 計算關鍵字重複次數
    ├─ 支援模糊匹配（fuzz.ratio > 85）
    └─ 關鍵字越多，分數越高
    ↓
【綜合評分】
    ├─ 總分 = 第一階段 × 40% + 第二階段 × 60%
    ├─ 彙整版加 5 分
    └─ 選擇分數最高的項目
    ↓
寫入 D 欄（權責部門）、E 欄（現況/影響）
```

### 比對配置參數

可在 `rpa_security_c.py` 中調整：

```python
MATCH_CONFIG = {
    "phase1_primary_threshold": 60,      # 第一階段主要閾值
    "phase1_fallback_threshold": 50,     # 第一階段備援閾值
    "keyword_weight": 0.6,               # 關鍵字權重
    "behavior_weight": 0.4,              # 行為準則權重
    "aggregate_bonus": 5,                # 彙整版加分
    "low_confidence_threshold": 70,      # 低信心閾值
}
```

---

## 🎨 輸出檔案說明

### 欄位標記

- ⚪ **正常匹配**：無顏色標記
- 🟡 **低信心匹配**：黃色背景（信心分數 < 70）
- 🔴 **未匹配**：紅色背景，顯示「未匹配」、「請人工填寫」

### 檔案命名

```
security_c_result_{客戶名稱}_{時間戳}.xlsx

範例：
security_c_result_宏齊_20251204_123456.xlsx
```

---

## 📈 API 回應格式

### 成功回應

```json
{
  "success": true,
  "file_name": "security_c_result_宏齊_20251204_123456.xlsx",
  "file_base64": "UEsDBBQABgAIA...（省略）",
  "report": {
    "client_name": "宏齊",
    "total_questions": 18,
    "matched_count": 18,
    "unmatched_count": 0,
    "low_confidence_count": 5,
    "match_rate": "100.0%",
    "details": [...]
  }
}
```

### 錯誤回應

```json
{
  "success": false,
  "error": "錯誤訊息說明"
}
```

---

## 🧪 測試

### 測試 API 功能

```bash
python3 test_api.py
```

### 測試健康檢查

```bash
curl http://127.0.0.1:5555/api/security-c/health | python3 -m json.tool
```

### 查看服務狀態

```bash
curl http://127.0.0.1:5555/ | python3 -m json.tool
```

---

## 🔧 常見問題

### Q1: 為什麼所有題目都是低信心？

**A:** 可能需要調整閾值參數：

```python
# 在 rpa_security_c.py 中
MATCH_CONFIG["low_confidence_threshold"] = 50  # 降低閾值
```

### Q2: 如何新增資料庫內容？

**A:** 直接編輯 `附件三.xlsx`，新增行並填入 B、C、E、F 欄位即可。

### Q3: 如何處理多個關鍵字？

**A:** 在附件三 C 欄中，每行一個關鍵字：

```
關鍵字1
關鍵字2
關鍵字3
```

### Q4: API 超時怎麼辦？

**A:** 增加 timeout 設定：

```python
# 在呼叫 API 時
requests.post(url, json=payload, timeout=1200)  # 20 分鐘
```

或在 n8n HTTP 節點中設定更長的 timeout（600000 ms = 10 分鐘）。

### Q5: 如何優化匹配準確度？

**A:**
1. 增加資料庫（附件三）的內容豐富度
2. 確保關鍵字欄位填寫完整
3. 調整 `MATCH_CONFIG` 參數
4. 建立「已確認配對表」學習機制（未來功能）

---

## 📞 聯絡資訊

- **開發者**: Frank Fu
- **維護單位**: IT 部門
- **Irene Chen**: 業務需求窗口

---

## 📝 版本記錄

### v1.0.0 (2025-12-04)

- ✅ 完成 Flask API 開發
- ✅ 完成兩階段比對邏輯
- ✅ 完成 n8n Workflow 整合
- ✅ 完成測試與驗證
- ✅ 達成 100% 匹配率（測試樣本）

---

## 🎯 未來規劃

- [ ] 建立 Dashboard 顯示處理歷史
- [ ] 新增 survey_batch / survey_items 資料表
- [ ] 實作學習機制（已確認配對表）
- [ ] 支援批次處理多個檔案
- [ ] 整合 LLM 提升比對準確度
- [ ] 新增更多統計報表功能

---

**🎉 感謝使用客戶問卷 RPA 系統！**
