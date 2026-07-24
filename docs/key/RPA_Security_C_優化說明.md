# RPA Security-C 優化技術說明

> 版本：2026-05-15  
> 測試結果：一致性 31% → **96.4%**，正確性 80% → **87~91%**

---

## 一、問題背景

同一份問卷（聯穎光電供應商行為準則.xlsx）在不同時間執行，答案不穩定：

- 不一致率高達 **69%（38/55 題）**
- 代表性漂移案例：「隱私」條款→ 找到廢水排放候選；「青年勞工」→ 找到工時上限候選

根本原因有**兩層**：

| 層次 | 問題 | 症狀 |
|------|------|------|
| **模型層** | `gpt-5.3-chat` 是推理型模型，`max_tokens` 參數名稱已廢棄，且無法設定 `temperature` | 回覆被截斷 → 輸出空值；每次措辭 10~20% 機率不同 |
| **架構層** | LLM 自由生成 `must_have_terms`（不受約束）+ RAG 召回後無題域過濾 | 答案漂到完全不同的條款題域 |

---

## 二、修改清單總覽

| 優先 | 檔案 | 修改性質 | 行數 |
|------|------|---------|------|
| P0 | `rpa_security_c.py` | `max_tokens` → `max_completion_tokens` | 1 行 |
| P0 | `rpa_security_c.py` | `azure_llm_upgrade_yellow` 加 `seed:42` | 2 行 |
| P0 | `llm_first_schema.py` | 兩個 LLM payload 加 `seed:42` + `max_completion_tokens` | 各 2 行 |
| P1 | `facet_taxonomy.py` | **新建**：受控 Facet 白名單 + 題域閘門 + 驗證函數 | 468 行 |
| P1 | `rpa_security_c.py` | import + domain_gate_filter 插入 + 受控 facet 選取 | ~40 行 |

---

## 三、P0 修復：`max_tokens` → `max_completion_tokens`

### 3.1 問題說明

Azure OpenAI 的 **推理型模型**（`gpt-5.3-chat`、`o1`、`o3` 系列）在推理時會先消耗 **thinking tokens**，再輸出結果。這兩部分合稱 `max_completion_tokens`。

舊參數名稱 `max_tokens` 在推理型模型中**被忽略**（不報錯但無效），導致模型以預設 token 上限運作。若預設上限偏低，輸出就會**被截斷 → JSON 解析失敗 → 回傳空值**。

### 3.2 修改前（有 Bug）

```python
# rpa_security_c.py 第 1975 行（_detect_format_with_llm）
payload = {
    "messages": [...],
    "max_tokens": 300,        # ❌ 推理型模型忽略此參數，300 根本不夠
}
```

```python
# rpa_security_c.py 第 746 行（azure_llm_upgrade_yellow）
payload = {
    "messages": [...],
    # ❌ 完全沒有 token 限制，也沒有 seed，每次輸出都可能不同
}
```

```python
# llm_first_schema.py 第 279 行（extract_question_schema_llm）
payload = {
    "messages": [...],
    "response_format": {"type": "json_object"},
    # ❌ 沒有 seed，每次生成的 must_have_terms 都可能不同
}
```

### 3.3 修改後（已修復）

```python
# rpa_security_c.py - _detect_format_with_llm（格式偵測）
payload = {
    "messages": [...],
    "max_completion_tokens": 2000,  # ✅ 推理型模型必須用此參數
                                     #    200 reasoning tokens + 輸出 ≈ 至少需 1000
}
```

```python
# rpa_security_c.py - azure_llm_upgrade_yellow（黃色升級審查）
payload = {
    "messages": [...],
    "seed": 42,                     # ✅ 相同輸入 → 更穩定的輸出（盡力而為）
    "max_completion_tokens": 200,   # ✅ 此處只需 Y/N，200 足夠
}
```

```python
# llm_first_schema.py - extract_question_schema_llm 和 extract_knowledge_schema_llm
payload = {
    "messages": [...],
    "response_format": {"type": "json_object"},
    "seed": 42,                      # ✅ 降低隨機抖動
    "max_completion_tokens": 2000,   # ✅ JSON 輸出需足夠空間
}
```

### 3.4 為什麼這樣能提高一致性？

```
seed=42 的作用機制：
─────────────────────────────────────────────────────────────
相同 prompt + 相同 seed → LLM 使用相同的隨機數種子
→ 生成路徑更接近（不能保證 100%，但顯著降低抖動）
→ 同一題的 must_have_terms 重複呼叫更穩定
→ 下游 facet 選取結果更穩定
→ RAG 查詢字串更穩定 → 召回的候選更穩定 → 答案更穩定

max_completion_tokens 的作用機制：
─────────────────────────────────────────────────────────────
舊：max_tokens 被推理模型忽略 → 輸出隨機截斷 → JSON 解析失敗 → 回傳空
新：max_completion_tokens=2000 → 給足空間 → 輸出完整 → 正確解析
```

---

## 四、P1 修復：受控 Facet 白名單 + 題域閘門

### 4.1 漂移的根本原因：自由生成鏈

修改前的執行流程（有問題的路徑）：

```
題目輸入
  ↓
extract_question_schema_llm()
  → temperature=1，seed 無效
  → 自由生成 must_have_terms
    第1次：["童工", "年齡"]
    第2次：["童工", "工時", "年齡"]   ← 多出「工時」
  ↓
is_multifacet_question_expected()
  → must_have_terms >= 2 → True（多面向）
  ↓
call_rag_semantic_search()
  → 多面向題補撈：用「工時」去 RAG 搜尋
  → 搜回了「A-3工時限制」的候選            ← 跨題域混入！
  ↓
select_per_facet_candidates()
  → 選了「工時上限」這筆錯誤知識庫列
  ↓
輸出：dept=薪酬（工時相關部門），impact=工時上限說明  ← 完全漂移
```

**問題本質**：`must_have_terms` 是 LLM 自由生成的，每次都可能不同，且沒有機制阻止它生成「工時」這個屬於 A-3 的詞。一旦生成錯誤詞彙，RAG 就會拉入錯題域的候選。

### 4.2 新增 `facet_taxonomy.py`：受控 Facet 白名單

**設計理念**：不硬編死答案，而是**限制 LLM 的選擇範圍**。

就像考試從「申論題」改為「選擇題」：
- ❌ 申論題（舊）：LLM 自由生成任何詞彙，可能飄到任何方向
- ✅ 選擇題（新）：LLM 只能從固定選項中選，智慧判斷仍在，但邊界固定

```python
# facet_taxonomy.py - 核心資料結構

FACET_TAXONOMY = {
    "A-2": {
        # ① 只允許這個類別的知識庫候選進來
        "allowed_categories": ["Labor 勞工"],

        # ② LLM 只能從這 3 個 facet 中選，不能自創新詞
        "canonical_facets": [
            {"id": "youth_worker",     "zh": "青年勞工",
             "required_kw": ["青年", "未成年", "童工", "年齡"]},
            {"id": "age_verification", "zh": "年齡驗證",
             "required_kw": ["驗證", "核查", "年齡", "文件"]},
            {"id": "remediation",      "zh": "補救程序",
             "required_kw": ["補救", "誤用", "改善", "處理"]},
        ],

        # ③ 這些詞出現在候選中 → 直接淘汰（防 A-3/環境混入）
        "excluded_kw": ["工時上限", "加班", "廢水", "環境許可"],
    },

    "隱私": {
        "allowed_categories": ["Ethics 道德"],
        "canonical_facets": [
            {"id": "data_privacy",  "zh": "個資保護",
             "required_kw": ["個資", "個人資料", "隱私", "資料保護"]},
            {"id": "data_security", "zh": "資料安全",
             "required_kw": ["資安", "加密", "存取控制"]},
        ],
        # 這就是防止「隱私→廢水排放」的關鍵黑名單
        "excluded_kw": ["廢水排放", "廢棄物", "化學品", "職安", "消防"],
    },
    # ... 共 18 個條款
}
```

**三個防護層的設計邏輯**：

| 層次 | 欄位 | 作用 |
|------|------|------|
| ① 類別白名單 | `allowed_categories` | RAG 召回後，只保留屬於正確類別的候選 |
| ② 受控選取 | `canonical_facets` | LLM 從固定清單選 facet，不自由創造 |
| ③ 排除黑名單 | `excluded_kw` | 含有跨題域關鍵詞的候選直接淘汰 |

### 4.3 修改點一：RAG 召回後插入題域閘門

**在哪裡插入**：`call_rag_semantic_search()` 回傳後、`if candidates:` 判斷前

```python
# rpa_security_c.py 第 2373 行附近（新增區塊）

# 修改前（無過濾）：
candidates = call_rag_semantic_search(rag_query, top_k=20, ...)
if candidates:
    # 直接進入候選處理，可能包含跨題域候選
    ...


# 修改後（加入題域閘門）：
candidates = call_rag_semantic_search(rag_query, top_k=20, ...)

# ✅ [題域閘門] 在進入候選處理前，過濾掉跨題域的候選
if candidates and _HAS_FACET_TAXONOMY:
    _taxonomy_entry = get_taxonomy_entry(clause or "", question)
    if _taxonomy_entry:
        _before = len(candidates)
        candidates = domain_gate_filter(
            candidates,
            allowed_categories=_taxonomy_entry.get("allowed_categories", []),
            excluded_kw=_taxonomy_entry.get("excluded_kw", []),
        )
        print(f"  [DomainGate] {_before}→{len(candidates)} 個候選（條款:{clause}）")
        # 實測效果：隱私條款：21→6 個（淘汰 15 個跨題域候選）

if candidates:
    ...
```

**`domain_gate_filter` 的核心邏輯**（`facet_taxonomy.py`）：

```python
def domain_gate_filter(candidates, allowed_categories, excluded_kw):
    """
    雙重過濾：
    1. 類別不在白名單 → 淘汰
    2. 文字包含排除關鍵詞 → 淘汰
    寧可少一個候選，也不讓錯題域進來。
    """
    filtered = []
    for c in candidates:
        category = c.get("category", "")
        full_text = (c.get("article") or "") + " " + (c.get("behavior") or "")

        # 關卡 1：類別白名單
        if not any(allowed in category for allowed in allowed_categories):
            continue  # 淘汰：錯誤類別

        # 關卡 2：排除黑名單
        if any(kw.lower() in full_text.lower() for kw in excluded_kw):
            continue  # 淘汰：含禁止詞

        filtered.append(c)
    return filtered
```

### 4.4 修改點二：受控 Facet 選取（取代自由生成）

**在哪裡修改**：`facets_expected` 計算區塊（`rpa_security_c.py` 第 2414 行附近）

```python
# 修改前（自由生成，每次不同）：
facets_expected = get_facets_expected_from_question(question, q_schema=q_schema)
# q_schema.must_have_terms 是 LLM 自由生成的，例如：
#   第1次 → ["童工", "年齡"]
#   第2次 → ["童工", "工時", "年齡"]   ← 多出工時，導致漂移


# 修改後（受控選取，選項固定）：
_taxonomy_entry_facet = get_taxonomy_entry(clause or "", question) if _HAS_FACET_TAXONOMY else None

if _taxonomy_entry_facet and llm_cfg:
    # ✅ 受控路徑：LLM 只能從白名單選 facet_id
    _facet_ids = get_controlled_facets_cached(
        llm_cfg, clause or "", question, _taxonomy_entry_facet
    )
    # 轉換為中文 facet 名稱
    facets_expected = [
        f["zh"] for f in _taxonomy_entry_facet.get("canonical_facets", [])
        if f["id"] in _facet_ids
    ]
    # 例如 A-2 青年勞工題：
    # LLM 選了 ["youth_worker", "age_verification"]
    # → facets_expected = ["青年勞工", "年齡驗證"]  ← 永遠不會出現「工時」
else:
    # Fallback：原有自由生成邏輯（未在 taxonomy 的條款）
    facets_expected = get_facets_expected_from_question(question, q_schema=q_schema)

multifacet_tag = len(facets_expected) >= 2
```

**受控選取的 LLM Prompt 設計**（`facet_taxonomy.py`）：

```python
def extract_controlled_facets_llm(cfg, clause_id, question_text, taxonomy_entry):
    canonical = taxonomy_entry["canonical_facets"]

    # 把選項格式化成清單，LLM 只能從這裡選
    options_text = "\n".join(
        f'  - id="{f["id"]}", 面向="{f["zh"]}", 關鍵詞={f["required_kw"][:3]}'
        for f in canonical
    )

    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是問卷題目面向分類器。\n"
                    "你只能從下方候選清單中選擇，不能創造新的 facet。\n"
                    "輸出 JSON：{\"selected_facet_ids\": [\"id1\", ...]}"
                )
            },
            {
                "role": "user",
                "content": (
                    f"條款：{clause_id}\n"
                    f"題目：{question_text[:300]}\n\n"
                    f"可選的 facet 清單：\n{options_text}\n\n"
                    "請選出這道題目涉及的 facet_id。"
                )
            }
        ],
        "response_format": {"type": "json_object"},
        "seed": 42,
        "max_completion_tokens": 200,
    }
    # ...回傳後驗證只保留白名單內的 id
    valid_ids = {f["id"] for f in canonical}
    return [fid for fid in selected_ids if fid in valid_ids]
```

### 4.5 修改點三：per-facet 候選驗證

**在哪裡插入**：`select_per_facet_candidates()` 回傳後，合併 matches 之前

```python
# 修改前（無驗證，任何候選都能進入合併）：
per_facet_list = select_per_facet_candidates(candidates, facets_expected)
if len(per_facet_list) > 1:
    # 直接合併所有 facet 的 matches
    matches = [m for c in per_facet_list for m in c["matches"]]


# 修改後（加入 required_kw 驗證）：
per_facet_list = select_per_facet_candidates(candidates, facets_expected)

# ✅ [Per-Facet 驗證] 過濾掉不符合 required_kw 的候選
if _HAS_FACET_TAXONOMY and _taxonomy_entry_facet:
    _canonical_map = {
        f["zh"]: f for f in _taxonomy_entry_facet.get("canonical_facets", [])
    }
    _validated_list = []
    for _cand in per_facet_list:
        # 找此候選最可能對應的 facet_def
        _best_facet_def = max(
            _canonical_map.values(),
            key=lambda fd: sum(
                1 for kw in fd.get("required_kw", [])
                if kw in (_cand.get("behavior","") + _cand.get("article",""))
            )
        )
        is_valid, reason = validate_facet_candidate(_cand, _best_facet_def)
        if is_valid:
            _validated_list.append(_cand)
        # 通不過 → 留空，不硬補錯誤候選

    if _validated_list:
        per_facet_list = _validated_list  # 只用通過驗證的候選

if len(per_facet_list) > 1:
    matches = [m for c in per_facet_list for m in c["matches"]]
```

**`validate_facet_candidate` 的邏輯**：

```python
def validate_facet_candidate(candidate, facet_def):
    """
    驗證候選是否真的對應此 facet。
    required_kw 至少命中一個 → 通過
    一個都沒命中 → 拒絕（寧可留空，不硬補）
    """
    required_kw = facet_def.get("required_kw", [])
    full_text = (candidate.get("article") or "") + " " + (candidate.get("behavior") or "")
    for m in candidate.get("matches", []):
        full_text += " " + (m.get("keyword") or "") + " " + (m.get("impact") or "")

    hit = [kw for kw in required_kw if kw in full_text]
    if hit:
        return True, f"kw_hit:{hit[0]}"
    return False, f"missing_all_kw:{required_kw[:3]}"
```

---

## 五、為什麼這樣設計能提高精準度、一致性、正確性？

### 5.1 提高「一致性」的機制

```
修改前的不一致路徑：
  題目 → LLM 自由生成 must_have_terms（每次不同）
        → 多面向判定結果不同
        → RAG 查詢字串不同
        → 召回的候選不同
        → 最終答案不同
  一致性：31%（嚴重不穩定）

修改後的穩定路徑：
  題目 → CLAUSE_TO_TAXONOMY 查表（確定性操作）
        → LLM 從固定白名單選（seed=42，選項範圍固定）
        → facets_expected 固定
        → domain_gate 過濾（規則性操作，無隨機性）
        → 召回候選的題域已鎖定
        → 最終答案穩定
  一致性：96.4%（大幅提升）
```

**關鍵設計**：越多環節用「確定性操作」（查表、規則過濾），越少環節依賴「隨機性操作」（自由 LLM 生成），整體輸出就越穩定。

### 5.2 提高「正確性」的機制

```
舊問題：正確答案有時因為漂移而被錯誤候選覆蓋
  → 即使 RAG 向量搜尋找到了正確候選（score=0.65）
  → 但同時也找到了廢水排放候選（score=0.62）
  → select_per_facet 把廢水排放選進來（因為 must_have_terms 包含錯誤詞）
  → 輸出的 dept 就包含了廢水相關部門

新設計：錯誤候選在進入選取流程前已被淘汰
  → domain_gate 淘汰廢水排放（category=Environment，而隱私題只允許 Ethics）
  → 即使 RAG 初始召回了廢水候選，它也無法進入選取流程
  → 正確的 Ethics 候選被選中
  → 輸出正確
```

### 5.3 提高「精準度」的機制

```
受控 facet 選取的精準度 vs 自由生成：

自由生成（舊）：
  LLM 生成 ["童工", "工時", "年齡"]
  → "工時" 是錯的 → RAG 補撈 A-3 相關內容
  → 最終合併了 A-2 + A-3 的內容（混雜）
  精準度：內容混雜，dept 同時包含招募部門和薪酬部門

受控選取（新）：
  LLM 從 [youth_worker, age_verification, remediation] 中選
  → 選 ["youth_worker", "age_verification"]
  → RAG 只在 Labor 類別找「青年、未成年」和「驗證、核查」相關內容
  → 最終只包含真正屬於 A-2 的內容
  精準度：內容純淨，dept 只包含招募部門（正確）
```

---

## 六、實測數據驗證

### DomainGate 實際攔截情況（測試 Log）

| 條款 | 召回 | 淘汰 | 保留 | 說明 |
|------|------|------|------|------|
| **隱私** | 21 | **15** | 6 | 防止「隱私→廢水排放/消防/化學品」 |
| **B-9 自然災害** | 21 | **15** | 6 | 防止混入非 H&S 類別 |
| **文檔和記錄** | 21 | **15** | 6 | 防止混入勞工/環境類別 |
| **A-7 自由結社** | 20 | **11** | 9 | 防止混入環境/道德類別 |
| **B-4 工業衛生** | 20 | **9** | 11 | 防止混入廢水/採購類別 |
| **B-3 工傷職業病** | 20 | **5** | 15 | 防止個資/採購混入 |

### 前後對比總結

| 指標 | 修改前 | 修改後 | 提升幅度 |
|------|-------|-------|---------|
| **一致性**（Run1 vs Run2 部門+現況） | ~31% | **96.4%** | +65.4% |
| **正確性**（vs 0327 參考，部門+現況） | ~80% | **87~91%** | +7~11% |
| **截斷空值問題** | 偶發 | **0 題** | 完全解決 |
| DomainGate 攔截跨題域 | 無 | **每題最多淘汰 15 個候選** | — |

---

## 七、設計哲學總結

> **「受控白名單」≠「硬編碼」**

- ❌ **硬編碼**：答案事先寫死，LLM 完全不參與，無法適應新公司的部門名稱
- ✅ **受控白名單**：LLM **仍然**做智慧判斷（從選項中選最相關的 facet），只是**選擇範圍被框住**

就像讓工程師從「已核准方案清單」中選方案，而不是讓他自由提案任何方案：
- 智慧：工程師仍需判斷哪個方案最適合這個問題
- 約束：選出來的方案一定在合規邊界內，不會飄到不相關的方向

這個設計讓系統兼顧了：
1. **靈活性**：LLM 的語意理解能力仍在發揮作用
2. **穩定性**：facet 的邊界由預定義白名單保證
3. **可維護性**：新增條款只需在 `FACET_TAXONOMY` 中增加一筆設定

---

*文件產生：2026-05-15*  
*測試版本：rpa_security_c.py + facet_taxonomy.py (新建)*  
*測試問卷：聯穎光電供應商行為準則.xlsx（55 題）*
