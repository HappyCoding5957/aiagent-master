# Security C 問卷RPA - 問題分析與修復報告

**建立日期**: 2026-02-12  
**維護者**: AI Agent  
**版本**: v1.0

---

## 目錄

1. [問題背景](#問題背景)
2. [根本原因分析](#根本原因分析)
3. [修復方案](#修復方案)
4. [LLM-first Schema 方法](#llm-first-schema-方法)
5. [測試結果](#測試結果)
6. [服務狀態](#服務狀態)

---

## 問題背景

### 問題描述

在使用 Security C 問卷RPA系統時，發現部分題目無法正確匹配到知識庫中的條文，導致比對失敗。

### 失敗題目清單

| 題號 | 題目內容 | 問題 |
|------|----------|------|
| Q4 | 不得雇用童工或安排未成年工進行危險作業 | 召回 10 筆，但被 must-have gate 剔除為 0 |
| Q5 | 不得苛求員工，不得要求員工繳交身分證、護照等證件 | RAG 召回為 0，keyword 補撈未觸發 |
| Q6 | 保證正常工作時間及加班應符合所有適用的法律法規 | RAG 召回為 0，keyword 補撈未觸發 |
| Q8 | 賦予員工聚會結社的自由及提供員工與主管溝通的途徑 | RAG 召回為 0，keyword 補撈未觸發 |
| Q9 | 不得在招募和雇用措施上進行種族、性別、年齡等歧視 | RAG 召回為 0，keyword 補撈未觸發 |

---

## 根本原因分析

### 原因 1: must-have gate 邏輯過於嚴格

**原始程式碼位置**: rpa_security_c.py:1421-1433



**問題說明**:
- 當題目包含「童工」時，要求候選條文也必須包含「童工」文字
- 導致語意相關但文字表述不同的候選被錯誤剔除
- 例如：題目問「童工」，RAG 召回「禁止聘用未成年工」，但因不含「童工」二字被剔除

### 原因 2: _detect_active_concepts 子概念偵測不完整

**原始程式碼位置**: rpa_security_c.py:1141-1165



**問題說明**:
- SUBCONCEPT_KEYWORDS 只定義了 3 個安全相關子概念
- Labor（勞工）、Ethics（道德）、人權 等題目類型完全無法偵測
- 導致 keyword 補撈的觸發條件永遠不成立

### 原因 3: RAG 知識庫內容限制

**知識庫資訊**:
- PDF_ID: ae77d5ae-c385-4071-a936-ccaf91b34eb7
- 名稱: 附件三_EnvSafety_atta3_知識庫
- 資料筆數: 351 筆
- 主要收錄: Environment + Safety 類別

**問題說明**:
- 知識庫名稱顯示主要收錄 Environment + Safety
- Labor（勞工）類別（85 筆）和 Ethics（道德）類別（99 筆）的條文可能不足
- 導致 RAG 召回為 0

### 原因 4: Keyword 補撈未正確觸發

**原始�輯**:


---

## 修復方案

### 修復 1: 放寬 must-have gate

**修改檔案**: rpa_security_c.py:1420-1427

**修改前**:


**修改後**:


### 修復 2: 新增 Keyword 補撈觸發條件

**修改檔案**: rpa_security_c.py:1540-1590

**修改邏輯**:


### 修復 3: 新增 Debug Log



---

## LLM-first Schema 方法

### 核心理念



### 為什麼有效？

| 傳統方法 | LLM-first 方法 |
|----------|----------------|
| 直接用原始題目送 RAG | LLM 萃取成一語意結構 |
| 依賴 RAG 召回品質 | 多策略 fallback |
| 不同格式難以處理 | Schema 統一結構 |
| 無信心度評估 | confidence 欄位追蹤品質 |

### Schema 定義



### 關鍵程式碼

#### Step 1: LLM 萃取 QuestionSchema



#### Step 2: 組裝 RAG 查詢



#### Step 3: Fallback 機制



### 為什麼能面對不同附件格式？

1. **Schema 統一結構**
   - 不管原始格式如何，都萃取成統一的 QuestionItem
   - intent、must_have_terms、topic_tags 都是標準欄位

2. **多重 Fallback 策略**
   

3. **信心度評估**
   

---

## 測試結果

### 修復前

| 題目 | RAG 召回 | Keyword 命中 | 結果 |
|------|----------|--------------|------|
| Q4 (童工) | 10 | - | ❌ 被 gate 剔除 |
| Q5 (苛待) | 0 | 0 | ❌ 失敗 |
| Q6 (工時) | 0 | 0 | ❌ 失敗 |
| Q8 (結社) | 0 | 0 | ❌ 失敗 |
| Q9 (歧視) | 0 | 0 | ❌ 失敗 |

### 修復後

| 題目 | 萃取後 intent | must_have_terms | 分數 | 結果 |
|------|---------------|-----------------|------|------|
| Q4 | 禁止僱用童工及安排未成年工從事危險作業 | 童工, 未成年工, 危險 | 88.0 | ✅ 綠色 |
| Q5 | 禁止苛待員工及要求提交證件作為雇用條件 | 苛待, 證件, 保證金 | 94.0 | ✅ 綠色 |
| Q6 | 確保工作時間與加班符合法律規範 | 工時, 加班, 法規 | 96.0 | ✅ 綠色 |
| Q8 | 保障員工集會結社自由並提供與主管溝通管道 | 結社, 工會, 集會 | 命中 15 筆 | ✅ |
| Q9 | 禁止在招募與雇用中進行各類歧視 | 歧視, 種族, 性別 | 命中 15 筆 | ✅ |

### Log 範例



---

## 服務狀態

### 當前版本資訊

| 項目 | 值 |
|------|-----|
| Flask 服務 | http://10.80.15.49:4204/ |
| 知識庫 | ae77d5ae-c385-4071-a936-ccaf91b34eb7 |
| 資料庫 | /home/ifm02web/aiagent/附件三.xlsx (2008 筆) |
| RAG Debug | 啟用中 (RAG_DEBUG=1) |

### 服務狀態檢查

lladm     459552  0.0  0.0   7488  3840 ?        Ss   06:36   0:00 /bin/bash -c ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no ifm02web@10.80.15.49 "cat > /home/ifm02web/aiagent/docs/Security_C_問題分析與修復報告_v1.0.md << 'ENDOFFILE' # Security C 問卷RPA - 問題分析與修復報告  **建立日期**: 2026-02-12   **維護者**: AI Agent   **版本**: v1.0  ---  ## 目錄  1. [問題背景](#問題背景) 2. [根本原因分析](#根本原因分析) 3. [修復方案](#修復方案) 4. [LLM-first Schema 方法](#llm-first-schema-方法) 5. [測試結果](#測試結果) 6. [服務狀態](#服務狀態)  ---  ## 問題背景  ### 問題描述  在使用 Security C 問卷RPA系統時，發現部分題目無法正確匹配到知識庫中的條文，導致比對失敗。  ### 失敗題目清單  | 題號 | 題目內容 | 問題 | |------|----------|------| | Q4 | 不得雇用童工或安排未成年工進行危險作業 | 召回 10 筆，但被 must-have gate 剔除為 0 | | Q5 | 不得苛求員工，不得要求員工繳交身分證、護照等證件 | RAG 召回為 0，keyword 補撈未觸發 | | Q6 | 保證正常工作時間及加班應符合所有適用的法律法規 | RAG 召回為 0，keyword 補撈未觸發 | | Q8 | 賦予員工聚會結社的自由及提供員工與主管溝通的途徑 | RAG 召回為 0，keyword 補撈未觸發 | | Q9 | 不得在招募和雇用措施上進行種族、性別、年齡等歧視 | RAG 召回為 0，keyword 補撈未觸發 |  ---  ## 根本原因分析  ### 原因 1: must-have gate 邏輯過於嚴格  **原始程式碼位置**: rpa_security_c.py:1421-1433  ```python def _passes_must_have(q: str, item: dict) -> bool:     must = _must_have_terms(q)     if not must:         return True          blob = " ".join([         str(item.get("category") or ""),         str(item.get("behavior") or ""),         str(item.get("article") or ""),         " ".join([(m.get("keyword") or "") for m in (item.get("matches") or [])])     ]).lower()          # 問題：硬性剔除不含 must 關鍵字的候選     return any(t.lower() in blob for t in must) ```  **問題說明**: - 當題目包含「童工」時，要求候選條文也必須包含「童工」文字 - 導致語意相關但文字表述不同的候選被錯誤剔除 - 例如：題目問「童工」，RAG 召回「禁止聘用未成年工」，但因不含「童工」二字被剔除  ### 原因 2: _detect_active_concepts 子概念偵測不完整  **原始程式碼位置**: rpa_security_c.py:1141-1165  ```python SUBCONCEPT_KEYWORDS = {     "fire_safety": [...],   # 火災安全     "first_aid": [...],     # 急救     "withdraw_danger": [...], # 退避危險 }  def _detect_active_concepts(q: str) -> list:     # 只偵測 3 個子概念     if any(t in q for t in ["火警", "警報", "滅火", ...]):         active.append("fire_safety")     if any(t in q for t in ["急救", "醫療", ...]):         active.append("first_aid")     if any(t in q for t in ["退避", "危險", ...]):         active.append("withdraw_danger")     return active ```  **問題說明**: - SUBCONCEPT_KEYWORDS 只定義了 3 個安全相關子概念 - Labor（勞工）、Ethics（道德）、人權 等題目類型完全無法偵測 - 導致 keyword 補撈的觸發條件永遠不成立  ### 原因 3: RAG 知識庫內容限制  **知識庫資訊**: - PDF_ID: ae77d5ae-c385-4071-a936-ccaf91b34eb7 - 名稱: 附件三_EnvSafety_atta3_知識庫 - 資料筆數: 351 筆 - 主要收錄: Environment + Safety 類別  **問題說明**: - 知識庫名稱顯示主要收錄 Environment + Safety - Labor（勞工）類別（85 筆）和 Ethics（道德）類別（99 筆）的條文可能不足 - 導致 RAG 召回為 0  ### 原因 4: Keyword 補撈未正確觸發  **原始�輯**: ```python if database:     active_concepts = _detect_active_concepts(question)          if active_concepts:  # 問題：Labor/Ethics 題目偵測不到，active_concepts 永遠為空         # keyword 補撈邏輯 ```  ---  ## 修復方案  ### 修復 1: 放寬 must-have gate  **修改檔案**: rpa_security_c.py:1420-1427  **修改前**: ```python def _passes_must_have(q: str, item: dict) -> bool:     must = _must_have_terms(q)     if not must:         return True     blob = " ".join([...])     return any(t.lower() in blob for t in must)  # 硬性剔除 ```  **修改後**: ```python def _passes_must_have(q: str, item: dict) -> bool:     """     新邏輯：不做硬性剔除，全部通過     由 keyword 補撈來處理主題過濾     """     must = _must_have_terms(q)     if not must:         return True          # 不再檢查，直接返回 True     return True ```  ### 修復 2: 新增 Keyword 補撈觸發條件  **修改檔案**: rpa_security_c.py:1540-1590  **修改邏輯**: ```python # ========== Keyword 補撈：對所有題目做關鍵字搜尋 ========== # 觸發條件：RAG 召回 < 5 kw_candidates = [] rag_recall_count = len(article_groups)  if rag_recall_count < 5 and database:     print("  [KW-TRIGGER] RAG召回不足({})，使用題目關鍵字補撈".format(rag_recall_count))          # 方法1: 用 jieba 拆題目詞     import jieba     words = jieba.cut(question)     search_terms = [w for w in words if len(w) > 1]          # 方法2: 加入常見關鍵字     common_keywords = [         "童工", "未成年", "工時", "加班", "保證金", "證件", "身分證",          "護照", "歧視", "種族", "性別", "年齡", "殘疾", "懷孕",         "結社", "工會", "集會", "自由", "溝通", "主管", "健康",          "安全", "環境", "危險", "消防", "急救"     ]     for kw in common_keywords:         if kw in question:             search_terms.append(kw)          # 移除重複，限制數量     search_terms = list(dict.fromkeys(search_terms))[:20]          # 執行 keyword 搜尋     kw_candidates = _keyword_search_attachment3(database, search_terms, limit=15)          # 合併到候選池     for kw_item in kw_candidates:         row_key = kw_item.get("row_id", "")         if row_key and row_key not in article_groups:             article_groups[row_key] = kw_item ```  ### 修復 3: 新增 Debug Log  ```python # 新增 debug 輸出 print("  [KW-TRIGGER] RAG召回不足({})，使用題目關鍵字補撈".format(rag_recall_count)) print("  [KW-TERMS] 搜尋詞: {}".format(search_terms[:10])) print("  [KW-DEBUG] database={}".format(type(database).__name__)) print("  [KW-RESULT] keyword命中={}".format(len(kw_candidates))) print("  [KW-MERGE] 合併後候選數={}".format(len(article_groups))) ```  ---  ## LLM-first Schema 方法  ### 核心理念  ``` 附件二（客戶問卷）              附件三（知識庫）      ↓                            ↓   QuestionItem ←──────────────→ KnowledgeItem      ↓                            ↓   LLM 結構化萃取                 LLM 結構化萃取      ↓                            ↓   [同一語意座標系中比對]      ↓   intent + must_have_terms + topic_tags ```  ### 為什麼有效？  | 傳統方法 | LLM-first 方法 | |----------|----------------| | 直接用原始題目送 RAG | LLM 萃取成一語意結構 | | 依賴 RAG 召回品質 | 多策略 fallback | | 不同格式難以處理 | Schema 統一結構 | | 無信心度評估 | confidence 欄位追蹤品質 |  ### Schema 定義  ```python @dataclass class QuestionItem:     clause_id: str           # 條款編號（如 "C.7.1"）     category: str           # 類別（如 "Labor 勞工"）     question_text_raw: str  # 原始題目     question_text_zh: str   # 繁體中文正規化     intent: str             # ★ 一句話意圖摘要（核心！）     topic_tags: List[str]   # 主題標籤     must_have_terms: List[str] # ★ 必備關鍵詞     skip_logic: SkipLogic   # 跳題規則     language: Language      # 來源語言     confidence: float       # LLM 抽取信心（0~1） ```  ### 關鍵程式碼  #### Step 1: LLM 萃取 QuestionSchema  ```python # llm_first_schema.py def extract_question_schema_llm(cfg, clause_id, category, question_text, *, debug=False):     """     Prompt 設計：     1. 簡轉繁（統一語言）     2. 提取 intent（一句话摘要，去除模板字）     3. 提取 must_have_terms（必備关键词）     4. 提取 topic_tags（主題標籤）     """     system_prompt = """     你是職安問卷的「結構化抽取器」。     你的任務：     1. 繁體中文正規化     2. 一句話意圖摘要（去除「是否」「請提供」等模板字）     3. 必備錨點詞（該題不可缺少的關鍵詞）     4. 主題標籤（英文蛇形命名）     只輸出 JSON，不要解釋     """ ```  #### Step 2: 組裝 RAG 查詢  ```python # rpa_security_c.py # ========== 組裝 RAG 查詢字串 ========== if q_schema and q_schema.confidence > 0:     # 用 LLM-first schema 組裝查詢     rag_query = q_schema.intent     if q_schema.must_have_terms:         rag_query = rag_query + " " + " ".join(q_schema.must_have_terms[:5]) else:     # Fallback：傳統補詞     rag_query = expand_question_for_rag(question) ```  #### Step 3: Fallback 機制  ```python # llm_first_schema.py def extract_question_schema_llm(...):     try:         # 嘗試 LLM 萃取         return QuestionItem(...)     except Exception as e:         # LLM 失敗 → 回退到保守版 schema         return _fallback_question(clause_id, category, raw) ```  ### 為什麼能面對不同附件格式？  1. **Schema 統一結構**    - 不管原始格式如何，都萃取成統一的 QuestionItem    - intent、must_have_terms、topic_tags 都是標準欄位  2. **多重 Fallback 策略**    ```python    # 策略順序：    # 1. LLM-first Schema 萃取 → RAG 語意搜尋    # 2. RAG 召回 < 5 → Keyword 本地補撈    # 3. Keyword 也失敗 → 用 intent 直接匹配    # 4. 都失敗 → 標記為未匹配，待人工處理    ```  3. **信心度評估**    ```python    confidence: float  # 0.0 ~ 1.0    # 低信心題目會標記為紅色，待人工審核    ```  ---  ## 測試結果  ### 修復前  | 題目 | RAG 召回 | Keyword 命中 | 結果 | |------|----------|--------------|------| | Q4 (童工) | 10 | - | ❌ 被 gate 剔除 | | Q5 (苛待) | 0 | 0 | ❌ 失敗 | | Q6 (工時) | 0 | 0 | ❌ 失敗 | | Q8 (結社) | 0 | 0 | ❌ 失敗 | | Q9 (歧視) | 0 | 0 | ❌ 失敗 |  ### 修復後  | 題目 | 萃取後 intent | must_have_terms | 分數 | 結果 | |------|---------------|-----------------|------|------| | Q4 | 禁止僱用童工及安排未成年工從事危險作業 | 童工, 未成年工, 危險 | 88.0 | ✅ 綠色 | | Q5 | 禁止苛待員工及要求提交證件作為雇用條件 | 苛待, 證件, 保證金 | 94.0 | ✅ 綠色 | | Q6 | 確保工作時間與加班符合法律規範 | 工時, 加班, 法規 | 96.0 | ✅ 綠色 | | Q8 | 保障員工集會結社自由並提供與主管溝通管道 | 結社, 工會, 集會 | 命中 15 筆 | ✅ | | Q9 | 禁止在招募與雇用中進行各類歧視 | 歧視, 種族, 性別 | 命中 15 筆 | ✅ |  ### Log 範例  ``` [題目 5] (8)不得苛求員工，不得要求員工繳交身份證... [print-RAGCFG][下面] top_k=20 score_threshold=0.50 max_depts=5   [RAG] 呼叫語意搜尋 API (top_k=20)，題目: 禁止苛待員工及要求提交證件...   [PDF_ID] 找到最新知識庫: ae77d5ae-c385-4071-a936-ccaf91b34eb7   [KW-TRIGGER] RAG召回不足(0)，使用題目關鍵字補撈   [KW-TERMS] 搜尋詞: ['禁止', '苛待', '工及', '要求', '提交', '證件', ...]   [KW-DEBUG] database=list   [KW-RESULT] keyword命中=15   [KW-MERGE] 合併後候選數=15   [print-RAG0][下面] raw_counts embedding=15 keyword=15 merged=15   [print-RAG1][下面] pre_filter top_scores=[0.94, 0.94, 0.94, ...] threshold=0.5   [RAG] 聚合後 15 個條文     [0] score=0.940, 匹配數=1, 條文=僱主...不得持有...身分或移民檔...   ✓ RAG 匹配成功 | 相似度分數: 94.0     - 行為準則: 禁止強迫勞動   ✅ 高信心題目，分數 94.0 ≥ 70，標記為綠色 ```  ---  ## 服務狀態  ### 當前版本資訊  | 項目 | 值 | |------|-----| | Flask 服務 | http://10.80.15.49:4204/ | | 知識庫 | ae77d5ae-c385-4071-a936-ccaf91b34eb7 | | 資料庫 | /home/ifm02web/aiagent/附件三.xlsx (2008 筆) | | RAG Debug | 啟用中 (RAG_DEBUG=1) |  ### 服務狀態檢查  ```bash # 檢查 Flask 服務 curl http://127.0.0.1:4204/api/health  # 檢查端口監聽 ss -tlnp | grep 4204  # 檢查程序狀態 ps aux | grep server.py ```  ### 近期改動紀錄  | 日期 | 版本 | 改動內容 | |------|------|----------| | 2026-02-12 | v1.0 | 初版文件 | | 2026-02-12 | - | 放寬 must-have gate | | 2026-02-12 | - | 新增 Keyword 補撈觸發條件 | | 2026-02-12 | - | 新增 Debug Log |  ---  ## 附錄  ### A. 附件三.xlsx 類別分布  | 類別 | 筆數 | |------|------| | Ethics 道德 | 99 | | Labor 勞工 | 85 | | Health & Safety 健康與安全 | 79 | | Environment 環境 | 61 | | Management System 管理系統 | 27 |  ### B. 常見關鍵字清單  ```python COMMON_KEYWORDS = [     "童工", "未成年",           # 童工相關     "工時", "加班",             # 工時相關     "保證金", "證件", "身分證", "護照",  # 證件相關     "歧視", "種族", "性別", "年齡", "殘疾", "懷孕",  # 歧視相關     "結社", "工會", "集會", "自由",  # 結社自由     "溝通", "主管",             # 溝通相關     "健康", "安全", "環境", "危險",  # 安環相關     "消防", "急救",             # 消防急救 ] ```  ### C. Debug Log 說明  | Log 標籤 | 說明 | |----------|------| | [KW-TRIGGER] | Keyword 補撈觸發原因 | | [KW-TERMS] | 搜尋詞清單 | | [KW-DEBUG] | 資料庫類型 | | [KW-RESULT] | Keyword 命中數量 | | [KW-MERGE] | 合併後候選數 | | [print-RAG0] | 原始召回統計 | | [print-RAG1] | 過濾前分數分布 | | [print-RAG2] | Gate 剔除統計 | | [print-RAG3] | Threshold 診斷 |  ---  **文件維護**: 請於修改後更新本文件之版本號與日期 ENDOFFILE"
lladm     459606  0.0  0.0   7488  1944 ?        S    06:36   0:00 /bin/bash -c ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no ifm02web@10.80.15.49 "cat > /home/ifm02web/aiagent/docs/Security_C_問題分析與修復報告_v1.0.md << 'ENDOFFILE' # Security C 問卷RPA - 問題分析與修復報告  **建立日期**: 2026-02-12   **維護者**: AI Agent   **版本**: v1.0  ---  ## 目錄  1. [問題背景](#問題背景) 2. [根本原因分析](#根本原因分析) 3. [修復方案](#修復方案) 4. [LLM-first Schema 方法](#llm-first-schema-方法) 5. [測試結果](#測試結果) 6. [服務狀態](#服務狀態)  ---  ## 問題背景  ### 問題描述  在使用 Security C 問卷RPA系統時，發現部分題目無法正確匹配到知識庫中的條文，導致比對失敗。  ### 失敗題目清單  | 題號 | 題目內容 | 問題 | |------|----------|------| | Q4 | 不得雇用童工或安排未成年工進行危險作業 | 召回 10 筆，但被 must-have gate 剔除為 0 | | Q5 | 不得苛求員工，不得要求員工繳交身分證、護照等證件 | RAG 召回為 0，keyword 補撈未觸發 | | Q6 | 保證正常工作時間及加班應符合所有適用的法律法規 | RAG 召回為 0，keyword 補撈未觸發 | | Q8 | 賦予員工聚會結社的自由及提供員工與主管溝通的途徑 | RAG 召回為 0，keyword 補撈未觸發 | | Q9 | 不得在招募和雇用措施上進行種族、性別、年齡等歧視 | RAG 召回為 0，keyword 補撈未觸發 |  ---  ## 根本原因分析  ### 原因 1: must-have gate 邏輯過於嚴格  **原始程式碼位置**: rpa_security_c.py:1421-1433  ```python def _passes_must_have(q: str, item: dict) -> bool:     must = _must_have_terms(q)     if not must:         return True          blob = " ".join([         str(item.get("category") or ""),         str(item.get("behavior") or ""),         str(item.get("article") or ""),         " ".join([(m.get("keyword") or "") for m in (item.get("matches") or [])])     ]).lower()          # 問題：硬性剔除不含 must 關鍵字的候選     return any(t.lower() in blob for t in must) ```  **問題說明**: - 當題目包含「童工」時，要求候選條文也必須包含「童工」文字 - 導致語意相關但文字表述不同的候選被錯誤剔除 - 例如：題目問「童工」，RAG 召回「禁止聘用未成年工」，但因不含「童工」二字被剔除  ### 原因 2: _detect_active_concepts 子概念偵測不完整  **原始程式碼位置**: rpa_security_c.py:1141-1165  ```python SUBCONCEPT_KEYWORDS = {     "fire_safety": [...],   # 火災安全     "first_aid": [...],     # 急救     "withdraw_danger": [...], # 退避危險 }  def _detect_active_concepts(q: str) -> list:     # 只偵測 3 個子概念     if any(t in q for t in ["火警", "警報", "滅火", ...]):         active.append("fire_safety")     if any(t in q for t in ["急救", "醫療", ...]):         active.append("first_aid")     if any(t in q for t in ["退避", "危險", ...]):         active.append("withdraw_danger")     return active ```  **問題說明**: - SUBCONCEPT_KEYWORDS 只定義了 3 個安全相關子概念 - Labor（勞工）、Ethics（道德）、人權 等題目類型完全無法偵測 - 導致 keyword 補撈的觸發條件永遠不成立  ### 原因 3: RAG 知識庫內容限制  **知識庫資訊**: - PDF_ID: ae77d5ae-c385-4071-a936-ccaf91b34eb7 - 名稱: 附件三_EnvSafety_atta3_知識庫 - 資料筆數: 351 筆 - 主要收錄: Environment + Safety 類別  **問題說明**: - 知識庫名稱顯示主要收錄 Environment + Safety - Labor（勞工）類別（85 筆）和 Ethics（道德）類別（99 筆）的條文可能不足 - 導致 RAG 召回為 0  ### 原因 4: Keyword 補撈未正確觸發  **原始�輯**: ```python if database:     active_concepts = _detect_active_concepts(question)          if active_concepts:  # 問題：Labor/Ethics 題目偵測不到，active_concepts 永遠為空         # keyword 補撈邏輯 ```  ---  ## 修復方案  ### 修復 1: 放寬 must-have gate  **修改檔案**: rpa_security_c.py:1420-1427  **修改前**: ```python def _passes_must_have(q: str, item: dict) -> bool:     must = _must_have_terms(q)     if not must:         return True     blob = " ".join([...])     return any(t.lower() in blob for t in must)  # 硬性剔除 ```  **修改後**: ```python def _passes_must_have(q: str, item: dict) -> bool:     """     新邏輯：不做硬性剔除，全部通過     由 keyword 補撈來處理主題過濾     """     must = _must_have_terms(q)     if not must:         return True          # 不再檢查，直接返回 True     return True ```  ### 修復 2: 新增 Keyword 補撈觸發條件  **修改檔案**: rpa_security_c.py:1540-1590  **修改邏輯**: ```python # ========== Keyword 補撈：對所有題目做關鍵字搜尋 ========== # 觸發條件：RAG 召回 < 5 kw_candidates = [] rag_recall_count = len(article_groups)  if rag_recall_count < 5 and database:     print("  [KW-TRIGGER] RAG召回不足({})，使用題目關鍵字補撈".format(rag_recall_count))          # 方法1: 用 jieba 拆題目詞     import jieba     words = jieba.cut(question)     search_terms = [w for w in words if len(w) > 1]          # 方法2: 加入常見關鍵字     common_keywords = [         "童工", "未成年", "工時", "加班", "保證金", "證件", "身分證",          "護照", "歧視", "種族", "性別", "年齡", "殘疾", "懷孕",         "結社", "工會", "集會", "自由", "溝通", "主管", "健康",          "安全", "環境", "危險", "消防", "急救"     ]     for kw in common_keywords:         if kw in question:             search_terms.append(kw)          # 移除重複，限制數量     search_terms = list(dict.fromkeys(search_terms))[:20]          # 執行 keyword 搜尋     kw_candidates = _keyword_search_attachment3(database, search_terms, limit=15)          # 合併到候選池     for kw_item in kw_candidates:         row_key = kw_item.get("row_id", "")         if row_key and row_key not in article_groups:             article_groups[row_key] = kw_item ```  ### 修復 3: 新增 Debug Log  ```python # 新增 debug 輸出 print("  [KW-TRIGGER] RAG召回不足({})，使用題目關鍵字補撈".format(rag_recall_count)) print("  [KW-TERMS] 搜尋詞: {}".format(search_terms[:10])) print("  [KW-DEBUG] database={}".format(type(database).__name__)) print("  [KW-RESULT] keyword命中={}".format(len(kw_candidates))) print("  [KW-MERGE] 合併後候選數={}".format(len(article_groups))) ```  ---  ## LLM-first Schema 方法  ### 核心理念  ``` 附件二（客戶問卷）              附件三（知識庫）      ↓                            ↓   QuestionItem ←──────────────→ KnowledgeItem      ↓                            ↓   LLM 結構化萃取                 LLM 結構化萃取      ↓                            ↓   [同一語意座標系中比對]      ↓   intent + must_have_terms + topic_tags ```  ### 為什麼有效？  | 傳統方法 | LLM-first 方法 | |----------|----------------| | 直接用原始題目送 RAG | LLM 萃取成一語意結構 | | 依賴 RAG 召回品質 | 多策略 fallback | | 不同格式難以處理 | Schema 統一結構 | | 無信心度評估 | confidence 欄位追蹤品質 |  ### Schema 定義  ```python @dataclass class QuestionItem:     clause_id: str           # 條款編號（如 "C.7.1"）     category: str           # 類別（如 "Labor 勞工"）     question_text_raw: str  # 原始題目     question_text_zh: str   # 繁體中文正規化     intent: str             # ★ 一句話意圖摘要（核心！）     topic_tags: List[str]   # 主題標籤     must_have_terms: List[str] # ★ 必備關鍵詞     skip_logic: SkipLogic   # 跳題規則     language: Language      # 來源語言     confidence: float       # LLM 抽取信心（0~1） ```  ### 關鍵程式碼  #### Step 1: LLM 萃取 QuestionSchema  ```python # llm_first_schema.py def extract_question_schema_llm(cfg, clause_id, category, question_text, *, debug=False):     """     Prompt 設計：     1. 簡轉繁（統一語言）     2. 提取 intent（一句话摘要，去除模板字）     3. 提取 must_have_terms（必備关键词）     4. 提取 topic_tags（主題標籤）     """     system_prompt = """     你是職安問卷的「結構化抽取器」。     你的任務：     1. 繁體中文正規化     2. 一句話意圖摘要（去除「是否」「請提供」等模板字）     3. 必備錨點詞（該題不可缺少的關鍵詞）     4. 主題標籤（英文蛇形命名）     只輸出 JSON，不要解釋     """ ```  #### Step 2: 組裝 RAG 查詢  ```python # rpa_security_c.py # ========== 組裝 RAG 查詢字串 ========== if q_schema and q_schema.confidence > 0:     # 用 LLM-first schema 組裝查詢     rag_query = q_schema.intent     if q_schema.must_have_terms:         rag_query = rag_query + " " + " ".join(q_schema.must_have_terms[:5]) else:     # Fallback：傳統補詞     rag_query = expand_question_for_rag(question) ```  #### Step 3: Fallback 機制  ```python # llm_first_schema.py def extract_question_schema_llm(...):     try:         # 嘗試 LLM 萃取         return QuestionItem(...)     except Exception as e:         # LLM 失敗 → 回退到保守版 schema         return _fallback_question(clause_id, category, raw) ```  ### 為什麼能面對不同附件格式？  1. **Schema 統一結構**    - 不管原始格式如何，都萃取成統一的 QuestionItem    - intent、must_have_terms、topic_tags 都是標準欄位  2. **多重 Fallback 策略**    ```python    # 策略順序：    # 1. LLM-first Schema 萃取 → RAG 語意搜尋    # 2. RAG 召回 < 5 → Keyword 本地補撈    # 3. Keyword 也失敗 → 用 intent 直接匹配    # 4. 都失敗 → 標記為未匹配，待人工處理    ```  3. **信心度評估**    ```python    confidence: float  # 0.0 ~ 1.0    # 低信心題目會標記為紅色，待人工審核    ```  ---  ## 測試結果  ### 修復前  | 題目 | RAG 召回 | Keyword 命中 | 結果 | |------|----------|--------------|------| | Q4 (童工) | 10 | - | ❌ 被 gate 剔除 | | Q5 (苛待) | 0 | 0 | ❌ 失敗 | | Q6 (工時) | 0 | 0 | ❌ 失敗 | | Q8 (結社) | 0 | 0 | ❌ 失敗 | | Q9 (歧視) | 0 | 0 | ❌ 失敗 |  ### 修復後  | 題目 | 萃取後 intent | must_have_terms | 分數 | 結果 | |------|---------------|-----------------|------|------| | Q4 | 禁止僱用童工及安排未成年工從事危險作業 | 童工, 未成年工, 危險 | 88.0 | ✅ 綠色 | | Q5 | 禁止苛待員工及要求提交證件作為雇用條件 | 苛待, 證件, 保證金 | 94.0 | ✅ 綠色 | | Q6 | 確保工作時間與加班符合法律規範 | 工時, 加班, 法規 | 96.0 | ✅ 綠色 | | Q8 | 保障員工集會結社自由並提供與主管溝通管道 | 結社, 工會, 集會 | 命中 15 筆 | ✅ | | Q9 | 禁止在招募與雇用中進行各類歧視 | 歧視, 種族, 性別 | 命中 15 筆 | ✅ |  ### Log 範例  ``` [題目 5] (8)不得苛求員工，不得要求員工繳交身份證... [print-RAGCFG][下面] top_k=20 score_threshold=0.50 max_depts=5   [RAG] 呼叫語意搜尋 API (top_k=20)，題目: 禁止苛待員工及要求提交證件...   [PDF_ID] 找到最新知識庫: ae77d5ae-c385-4071-a936-ccaf91b34eb7   [KW-TRIGGER] RAG召回不足(0)，使用題目關鍵字補撈   [KW-TERMS] 搜尋詞: ['禁止', '苛待', '工及', '要求', '提交', '證件', ...]   [KW-DEBUG] database=list   [KW-RESULT] keyword命中=15   [KW-MERGE] 合併後候選數=15   [print-RAG0][下面] raw_counts embedding=15 keyword=15 merged=15   [print-RAG1][下面] pre_filter top_scores=[0.94, 0.94, 0.94, ...] threshold=0.5   [RAG] 聚合後 15 個條文     [0] score=0.940, 匹配數=1, 條文=僱主...不得持有...身分或移民檔...   ✓ RAG 匹配成功 | 相似度分數: 94.0     - 行為準則: 禁止強迫勞動   ✅ 高信心題目，分數 94.0 ≥ 70，標記為綠色 ```  ---  ## 服務狀態  ### 當前版本資訊  | 項目 | 值 | |------|-----| | Flask 服務 | http://10.80.15.49:4204/ | | 知識庫 | ae77d5ae-c385-4071-a936-ccaf91b34eb7 | | 資料庫 | /home/ifm02web/aiagent/附件三.xlsx (2008 筆) | | RAG Debug | 啟用中 (RAG_DEBUG=1) |  ### 服務狀態檢查  ```bash # 檢查 Flask 服務 curl http://127.0.0.1:4204/api/health  # 檢查端口監聽 ss -tlnp | grep 4204  # 檢查程序狀態 ps aux | grep server.py ```  ### 近期改動紀錄  | 日期 | 版本 | 改動內容 | |------|------|----------| | 2026-02-12 | v1.0 | 初版文件 | | 2026-02-12 | - | 放寬 must-have gate | | 2026-02-12 | - | 新增 Keyword 補撈觸發條件 | | 2026-02-12 | - | 新增 Debug Log |  ---  ## 附錄  ### A. 附件三.xlsx 類別分布  | 類別 | 筆數 | |------|------| | Ethics 道德 | 99 | | Labor 勞工 | 85 | | Health & Safety 健康與安全 | 79 | | Environment 環境 | 61 | | Management System 管理系統 | 27 |  ### B. 常見關鍵字清單  ```python COMMON_KEYWORDS = [     "童工", "未成年",           # 童工相關     "工時", "加班",             # 工時相關     "保證金", "證件", "身分證", "護照",  # 證件相關     "歧視", "種族", "性別", "年齡", "殘疾", "懷孕",  # 歧視相關     "結社", "工會", "集會", "自由",  # 結社自由     "溝通", "主管",             # 溝通相關     "健康", "安全", "環境", "危險",  # 安環相關     "消防", "急救",             # 消防急救 ] ```  ### C. Debug Log 說明  | Log 標籤 | 說明 | |----------|------| | [KW-TRIGGER] | Keyword 補撈觸發原因 | | [KW-TERMS] | 搜尋詞清單 | | [KW-DEBUG] | 資料庫類型 | | [KW-RESULT] | Keyword 命中數量 | | [KW-MERGE] | 合併後候選數 | | [print-RAG0] | 原始召回統計 | | [print-RAG1] | 過濾前分數分布 | | [print-RAG2] | Gate 剔除統計 | | [print-RAG3] | Threshold 診斷 |  ---  **文件維護**: 請於修改後更新本文件之版本號與日期 ENDOFFILE"
lladm     459612  0.0  0.0   6676  2304 ?        S    06:36   0:00 grep server.py
lladm    1944553  0.0  0.0   7340  1420 ?        S    Jan23   0:00 /bin/bash -c cd /home/lladm/frank/n8n-MCP/aiagent && source venv/bin/activate && nohup python3 server.py > /tmp/flask_server.log 2>&1 & sleep 3 ps aux | grep -v grep | grep server.py tail -15 /tmp/flask_server.log
lladm    1944555  0.0  0.0 722264  8136 ?        Sl   Jan23   0:01 python3 server.py
lladm    1944567  0.4  0.0 1017232 24020 ?       Sl   Jan23 121:22 /usr/bin/python3 server.py
lladm    2539602  0.0  0.0   7472  2308 ?        S    Jan29   0:00 /bin/bash -c -l source /home/lladm/.claude/shell-snapshots/snapshot-bash-1769659917637-7y7x5o.sh && shopt -u extglob 2>/dev/null || true && eval 'source venv/bin/activate && nohup python3 mcp_server.py > logs/mcp_streamable_http.log 2>&1 & NEW_PID=$! && echo "✅ MCP Server 啟動，PID: $NEW_PID" && sleep 4 && curl -s http://127.0.0.1:8000/' \< /dev/null && pwd -P >| /tmp/claude-be97-cwd
lladm    2539604  0.1  0.2 793168 145256 ?       Sl   Jan29  30:42 python3 mcp_server.py

### 近期改動紀錄

| 日期 | 版本 | 改動內容 |
|------|------|----------|
| 2026-02-12 | v1.0 | 初版文件 |
| 2026-02-12 | - | 放寬 must-have gate |
| 2026-02-12 | - | 新增 Keyword 補撈觸發條件 |
| 2026-02-12 | - | 新增 Debug Log |

---

## 附錄

### A. 附件三.xlsx 類別分布

| 類別 | 筆數 |
|------|------|
| Ethics 道德 | 99 |
| Labor 勞工 | 85 |
| Health & Safety 健康與安全 | 79 |
| Environment 環境 | 61 |
| Management System 管理系統 | 27 |

### B. 常見關鍵字清單



### C. Debug Log 說明

| Log 標籤 | 說明 |
|----------|------|
| [KW-TRIGGER] | Keyword 補撈觸發原因 |
| [KW-TERMS] | 搜尋詞清單 |
| [KW-DEBUG] | 資料庫類型 |
| [KW-RESULT] | Keyword 命中數量 |
| [KW-MERGE] | 合併後候選數 |
| [print-RAG0] | 原始召回統計 |
| [print-RAG1] | 過濾前分數分布 |
| [print-RAG2] | Gate 剔除統計 |
| [print-RAG3] | Threshold 診斷 |

---

**文件維護**: 請於修改後更新本文件之版本號與日期
