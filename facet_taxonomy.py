# -*- coding: utf-8 -*-
"""
facet_taxonomy.py - 受控 Facet 白名單系統

核心理念：
  LLM 不自由生成 must_have_terms（導致跨題域漂移），
  而是從每個條款預定義的 canonical_facets 中「選擇」。
  這就像選擇題而非申論題，LLM 仍做智慧判斷，但答案不會飄出題域。

設計原則：
  - allowed_categories：只允許來自這些 KB category 的候選
  - canonical_facets：每個 facet 的 id/中文名/必備關鍵詞
  - excluded_kw：出現這些詞 → 直接淘汰（跨題域黑名單）
"""

from __future__ import annotations
import hashlib
import json
import requests
from typing import Optional

# =========================================================
# 1) Facet 分類字典（條款白名單）
# =========================================================

FACET_TAXONOMY = {
    # ===== A. 勞工 =====
    "A-1": {
        "allowed_categories": ["Labor 勞工"],
        "canonical_facets": [
            {"id": "forced_labor",      "zh": "強迫勞動",   "required_kw": ["強迫", "保證金", "身份證", "證件", "護照"]},
            {"id": "debt_bondage",      "zh": "債役",       "required_kw": ["債役", "抵債", "契約勞工"]},
            {"id": "trafficking",       "zh": "人口販運",   "required_kw": ["販運", "人口", "威脅", "武力"]},
        ],
        "excluded_kw": ["工時", "加班", "薪資", "廢水", "環境"],
    },
    "A-2": {
        "allowed_categories": ["Labor 勞工"],
        "canonical_facets": [
            {"id": "youth_worker",      "zh": "青年勞工",   "required_kw": ["青年", "未成年", "童工", "年齡"]},
            {"id": "age_verification",  "zh": "年齡驗證",   "required_kw": ["驗證", "核查", "年齡", "文件"]},
            {"id": "remediation",       "zh": "補救程序",   "required_kw": ["補救", "誤用", "改善", "處理"]},
        ],
        "excluded_kw": ["工時上限", "加班", "廢水", "環境許可"],
    },
    "A-3": {
        "allowed_categories": ["Labor 勞工"],
        "canonical_facets": [
            {"id": "working_hours",     "zh": "工時限制",   "required_kw": ["工時", "上限", "小時"]},
            {"id": "overtime",          "zh": "加班規定",   "required_kw": ["加班", "超時", "補償"]},
            {"id": "rest_period",       "zh": "休息規定",   "required_kw": ["休息", "假期", "休假"]},
        ],
        "excluded_kw": ["童工", "人口販運", "廢水"],
    },
    "A-4": {
        "allowed_categories": ["Labor 勞工"],
        "canonical_facets": [
            {"id": "wages",             "zh": "薪資合規",   "required_kw": ["薪資", "工資", "薪酬", "基本工資"]},
            {"id": "benefits",          "zh": "福利",       "required_kw": ["福利", "保險", "津貼"]},
            {"id": "deductions",        "zh": "扣款規定",   "required_kw": ["扣款", "扣除", "合法"]},
        ],
        "excluded_kw": ["廢水", "化學品", "環境"],
    },
    "A-6": {
        "allowed_categories": ["Labor 勞工"],
        "canonical_facets": [
            {"id": "anti_discrimination","zh": "禁止歧視",  "required_kw": ["歧視", "種族", "性別", "年齡", "殘疾", "懷孕"]},
            {"id": "anti_harassment",   "zh": "禁止騷擾",   "required_kw": ["騷擾", "性騷擾", "霸凌", "欺凌"]},
            {"id": "reporting",         "zh": "申訴管道",   "required_kw": ["申訴", "舉報", "投訴", "管道"]},
        ],
        "excluded_kw": ["廢水", "化學品", "環境許可"],
    },
    "A-7": {
        "allowed_categories": ["Labor 勞工"],
        "canonical_facets": [
            {"id": "freedom_association","zh": "結社自由",  "required_kw": ["結社", "工會", "集會", "自由"]},
            {"id": "collective_bargain", "zh": "集體協商",  "required_kw": ["協商", "談判", "代表"]},
            {"id": "communication",     "zh": "溝通管道",   "required_kw": ["溝通", "管道", "意見", "回報"]},
        ],
        "excluded_kw": ["廢水", "化學品", "有害物質"],
    },

    # ===== B. 健康與安全 =====
    "B-1": {
        "allowed_categories": ["Health & Safety", "Safety 安全"],
        "canonical_facets": [
            {"id": "hazard_control",    "zh": "危害控制",   "required_kw": ["危害", "控制", "防護", "作業安全"]},
            {"id": "ppe",               "zh": "個人防護",   "required_kw": ["防護具", "PPE", "個人防護"]},
            {"id": "safety_training",   "zh": "安全培訓",   "required_kw": ["培訓", "訓練", "安全教育"]},
        ],
        "excluded_kw": ["廢水", "廢棄物", "廢氣", "個資"],
    },
    "B-2": {
        "allowed_categories": ["Health & Safety"],
        "canonical_facets": [
            {"id": "emergency_plan",    "zh": "緊急計畫",   "required_kw": ["緊急", "應急", "計畫", "演練"]},
            {"id": "fire_safety",       "zh": "消防安全",   "required_kw": ["消防", "滅火", "火警", "疏散"]},
            {"id": "first_aid",         "zh": "急救",       "required_kw": ["急救", "急救箱", "醫療"]},
        ],
        "excluded_kw": ["廢水排放", "個資", "道德"],
    },
    "B-3": {
        "allowed_categories": ["Health & Safety"],
        "canonical_facets": [
            {"id": "injury_recording",  "zh": "職傷記錄",   "required_kw": ["職業傷害", "工傷", "記錄", "統計"]},
            {"id": "occupational_disease","zh": "職業病",   "required_kw": ["職業病", "職病", "暴露"]},
            {"id": "investigation",     "zh": "事故調查",   "required_kw": ["調查", "原因", "改善", "事故"]},
        ],
        "excluded_kw": ["廢水", "個資", "採購"],
    },
    "B-4": {
        "allowed_categories": ["Health & Safety", "Environment 環境"],
        "canonical_facets": [
            {"id": "industrial_hygiene","zh": "工業衛生",   "required_kw": ["衛生", "暴露", "監測", "採樣"]},
            {"id": "chemical_exposure", "zh": "化學品暴露", "required_kw": ["化學品", "暴露", "劑量"]},
        ],
        "excluded_kw": ["廢水排放到河川", "個資", "採購"],
    },
    "B-9": {
        "allowed_categories": ["Health & Safety"],
        "canonical_facets": [
            {"id": "natural_disaster",  "zh": "自然災害",   "required_kw": ["自然災害", "地震", "颱風", "洪水"]},
            {"id": "fire_risk",         "zh": "火災風險",   "required_kw": ["火災", "消防", "防火"]},
            {"id": "pandemic",          "zh": "傳染病",     "required_kw": ["傳染病", "疫情", "健康管理"]},
            {"id": "strike_risk",       "zh": "罷工風險",   "required_kw": ["罷工", "勞資", "協商"]},
        ],
        "excluded_kw": ["廢水排放", "個資洩露"],
    },

    # ===== C. 環境 =====
    "環境許可和報告": {
        "allowed_categories": ["Environment 環境"],
        "canonical_facets": [
            {"id": "env_permit",        "zh": "環境許可",   "required_kw": ["許可", "執照", "申請", "法規"]},
            {"id": "env_reporting",     "zh": "環境申報",   "required_kw": ["申報", "報告", "監測", "記錄"]},
        ],
        "excluded_kw": ["沒收", "招募", "個資", "工資", "人口販運"],
    },
    "預防污染和節約資源": {
        "allowed_categories": ["Environment 環境"],
        "canonical_facets": [
            {"id": "pollution_prevention","zh": "污染預防", "required_kw": ["污染", "預防", "減少", "排放"]},
            {"id": "resource_conservation","zh": "節約資源","required_kw": ["節約", "資源", "能源", "水"]},
        ],
        "excluded_kw": ["個資", "工資", "沒收"],
    },
    "有害物質": {
        "allowed_categories": ["Environment 環境", "Health & Safety"],
        "canonical_facets": [
            {"id": "hazmat_id",         "zh": "有害物質鑑別","required_kw": ["有害物質", "化學品", "清單"]},
            {"id": "hazmat_mgmt",       "zh": "有害物質管理","required_kw": ["管理", "標示", "儲存", "處置"]},
            {"id": "hazmat_disposal",   "zh": "廢棄物處置", "required_kw": ["廢棄", "處置", "清理"]},
        ],
        "excluded_kw": ["個資", "工資", "沒收", "人口販運"],
    },

    # ===== D. 道德規範 =====
    "誠信經營": {
        "allowed_categories": ["Ethics 道德"],
        "canonical_facets": [
            {"id": "anti_corruption",   "zh": "禁止腐敗",   "required_kw": ["腐敗", "賄賂", "佣金", "回扣"]},
            {"id": "integrity_policy",  "zh": "誠信政策",   "required_kw": ["誠信", "政策", "準則", "道德"]},
        ],
        "excluded_kw": ["廢水", "化學品", "工傷", "職安"],
    },
    "隱私": {
        "allowed_categories": ["Ethics 道德"],
        "canonical_facets": [
            {"id": "data_privacy",      "zh": "個資保護",   "required_kw": ["個資", "個人資料", "隱私", "資料保護"]},
            {"id": "data_security",     "zh": "資料安全",   "required_kw": ["資安", "加密", "存取控制"]},
        ],
        "excluded_kw": ["廢水排放", "廢棄物", "化學品", "職安", "消防"],
    },
    "風險評估和風險管理": {
        "allowed_categories": ["Management System", "Ethics 道德", "Labor 勞工", "Health & Safety", "Environment 環境"],
        "canonical_facets": [
            {"id": "ehs_risk",          "zh": "環安衛風險", "required_kw": ["環安衛", "職安", "環境", "風險"]},
            {"id": "legal_risk",        "zh": "法律遵循風險","required_kw": ["法律", "法規", "合規", "違規"]},
            {"id": "info_security_risk","zh": "資安風險",   "required_kw": ["資安", "資訊安全", "個資"]},
            {"id": "ethics_risk",       "zh": "道德風險",   "required_kw": ["道德", "腐敗", "賄賂", "誠信"]},
        ],
        # 風險評估允許多類別，每個 facet 分別在自己的 domain 找
    },
    "員工意見、參與和申訴": {
        "allowed_categories": ["Labor 勞工", "Management System", "Ethics 道德"],
        "canonical_facets": [
            {"id": "complaint_channel", "zh": "申訴管道",   "required_kw": ["申訴", "投訴", "舉報", "管道"]},
            {"id": "participation",     "zh": "員工參與",   "required_kw": ["參與", "意見", "回饋", "員工"]},
            {"id": "whistleblower",     "zh": "舉報保護",   "required_kw": ["匿名", "檢舉", "保護", "報復"]},
        ],
        "excluded_kw": ["廢水", "化學品", "招募"],
    },
    # ===== 文件和紀錄（Row56 修復）=====
    "文件和紀錄": {
        "allowed_categories": ["Management System"],
        "canonical_facets": [
            {"id": "doc_record_mgmt",  "zh": "文件與紀錄管理", "required_kw": ["文件", "紀錄", "維護", "管理"]},
            {"id": "compliance_doc",   "zh": "法規符合文件",   "required_kw": ["法規", "符合", "要求", "保密"]},
        ],
        "excluded_kw": ["廢水", "廢棄物", "化學品"],  # 移除隱私/個資：allowed_categories已過濾，且article含「保護隱私」會誤殺正確答案
    },
}

# =========================================================
# 2) 條款 ID → taxonomy key 映射（處理中英文/簡繁差異）
# =========================================================

CLAUSE_TO_TAXONOMY = {
    # A 系列
    "A-1": "A-1", "A1": "A-1", "A-1自由選擇職業": "A-1",
    "A-2": "A-2", "A2": "A-2", "A-2 青年勞工": "A-2", "A-2青年勞工": "A-2",
    "A-3": "A-3", "A3": "A-3", "A-3 工時": "A-3", "A-3工時": "A-3",
    "A-4": "A-4", "A4": "A-4", "A-4工資與福利": "A-4",
    "A-6": "A-6", "A6": "A-6", "A-6不歧視 /不騷擾": "A-6", "A-6不歧視/不騷擾": "A-6",
    "A-7": "A-7", "A7": "A-7", "A-7自由結社": "A-7",
    # B 系列
    "B-1": "B-1", "B1": "B-1", "B-1職業安全": "B-1",
    "B-2": "B-2", "B2": "B-2", "B-2應急準備": "B-2",
    "B-3": "B-3", "B3": "B-3", "B-3工傷和職業病": "B-3",
    "B-4": "B-4", "B4": "B-4", "B-4工業衛生": "B-4",
    "B-9": "B-9", "B9": "B-9", "B-9自然災害風險減緩": "B-9",
    # 環境
    "環境許可和報告": "環境許可和報告",
    "预防污染和节约资源": "預防污染和節約資源",  # 簡體→繁體
    "預防污染和節約資源": "預防污染和節約資源",
    "有害物質": "有害物質", "有害物质": "有害物質",
    # 道德
    "誠信經營": "誠信經營", "诚信经营": "誠信經營",
    "隱私": "隱私", "隐私": "隱私",
    "風險評估和風險管理": "風險評估和風險管理", "风险评估和风险管理": "風險評估和風險管理",
    # 管理體系
    "員工意見、參與和申訴": "員工意見、參與和申訴",
    "员工意见、参与和申诉": "員工意見、參與和申訴",
    # 文件和紀錄
    "文件和紀錄": "文件和紀錄",
    "文件与纪录": "文件和紀錄",
    "文件與紀錄": "文件和紀錄",
    "Documents and Records": "文件和紀錄",
    "文檔和記錄": "文件和紀錄",   # ✅ 繁體別字（檔→件, 記→紀）
    "文档和记录": "文件和紀錄",   # ✅ 简体
}


# =========================================================
# 3) 題域閘門（Domain Gate）- 防跨題域漂移的核心防線
# =========================================================

def domain_gate_filter(candidates: list, allowed_categories: list, excluded_kw: list) -> list:
    """
    題域閘門：把不屬於允許類別、或含有排除關鍵詞的候選直接淘汰。
    防止「隱私→廢水排放」「青年勞工→工時上限」等跨題域漂移。
    
    寧可少一個候選，也不讓錯題域進來。
    """
    if not allowed_categories:
        return candidates

    filtered = []
    rejected = []
    for c in candidates:
        category = c.get("category", "")
        article_text = (c.get("article") or "").lower()
        behavior_text = (c.get("behavior") or "").lower()
        full_text = article_text + " " + behavior_text

        # 1. 類別白名單檢查（只要含有任一 allowed_category 即通過）
        category_ok = any(allowed_cat in category for allowed_cat in allowed_categories)
        if not category_ok:
            rejected.append((c.get("behavior", "")[:30], f"wrong_category:{category}"))
            continue

        # 2. 排除關鍵詞黑名單檢查
        excluded = False
        hit_kw = None
        for kw in (excluded_kw or []):
            if kw.lower() in full_text:
                excluded = True
                hit_kw = kw
                break
        if excluded:
            rejected.append((c.get("behavior", "")[:30], f"excluded_kw:{hit_kw}"))
            continue

        filtered.append(c)

    if rejected:
        import os
        if os.getenv("RAG_SKIP_DEBUG", "0") == "1":
            for behavior, reason in rejected:
                print(f"  [DomainGate] ❌ 淘汰: {behavior} ({reason})")
        else:
            print(f"  [DomainGate] 淘汰 {len(rejected)} 個跨題域候選，保留 {len(filtered)} 個")

    return filtered


# =========================================================
# 4) Facet 候選驗證
# =========================================================

def validate_facet_candidate(candidate: dict, facet_def: dict) -> tuple:
    """
    驗證候選是否真的對應到指定的 facet（required_kw 至少命中一個）。
    通不過→該 facet 標「未覆蓋」，不硬補鄰近答案。
    
    回傳：(is_valid: bool, reason: str)
    """
    if not candidate:
        return False, "no_candidate"

    required_kw = facet_def.get("required_kw", [])
    if not required_kw:
        return True, "no_constraint"

    texts = [
        candidate.get("article") or "",
        candidate.get("behavior") or "",
    ]
    for m in candidate.get("matches", []):
        texts.append(m.get("keyword") or "")
        texts.append(m.get("impact") or "")
    full_text = " ".join(texts)

    hit_kw = [kw for kw in required_kw if kw in full_text]
    if hit_kw:
        return True, f"kw_hit:{hit_kw[0]}"
    return False, f"missing_all_kw:{required_kw[:3]}"


# =========================================================
# 5) 受控 LLM Facet 選取（取代自由生成）
# =========================================================

_facet_cache: dict = {}  # Per-session 快取

def get_controlled_facets_cached(
    cfg,
    clause_id: str,
    question_text: str,
    taxonomy_entry: dict
) -> list:
    """
    快取版的受控 facet 選取。
    cache key = clause_id + question_text hash（同一題同一 session 只呼叫一次）
    """
    cache_key = hashlib.md5(
        f"{clause_id}|{question_text[:200]}".encode()
    ).hexdigest()

    if cache_key in _facet_cache:
        return _facet_cache[cache_key]

    result = extract_controlled_facets_llm(cfg, clause_id, question_text, taxonomy_entry)
    _facet_cache[cache_key] = result
    return result


def extract_controlled_facets_llm(
    cfg,
    clause_id: str,
    question_text: str,
    taxonomy_entry: dict
) -> list:
    """
    受控版 facet 選取：LLM 只能從 taxonomy_entry["canonical_facets"] 中選，不能自由創造。
    
    與舊版的差異：
    - 舊版：LLM 自由生成 must_have_terms（每次不同，導致漂移）
    - 新版：LLM 從固定 facet 白名單選 facet_id（選項固定，不能飄出去）
    
    Fallback：LLM 失敗 → 返回前兩個 facet（保守策略）
    """
    if not taxonomy_entry:
        return []

    canonical = taxonomy_entry.get("canonical_facets", [])
    if not canonical:
        return []

    # 若只有一個 facet，直接返回（不需要 LLM 選擇）
    if len(canonical) == 1:
        return [canonical[0]["id"]]

    # 建立 LLM prompt
    options_text = "\n".join(
        f"  - id=\"{f['id']}\", 面向=\"{f['zh']}\", 關鍵詞範例={f['required_kw'][:3]}"
        for f in canonical
    )

    try:
        url = f"{cfg.endpoint}/openai/deployments/{cfg.deployment}/chat/completions"
        headers = {"api-key": cfg.api_key, "Content-Type": "application/json"}

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是問卷題目面向分類器。\n"
                        "你的任務是判斷這道題目涉及哪些面向（facet）。\n"
                        "你只能從下方候選清單中選擇，不能創造新的 facet。\n"
                        "如果題目不涉及某個 facet，就不要選。\n"
                        "輸出 JSON：{\"selected_facet_ids\": [\"id1\", ...]}"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"條款：{clause_id}\n"
                        f"題目：{question_text[:300]}\n\n"
                        f"可選的 facet 清單：\n{options_text}\n\n"
                        "請選出這道題目涉及的 facet_id（只選真正相關的，輸出 JSON）。"
                    )
                }
            ],
            "response_format": {"type": "json_object"},
            "seed": 42,
            "max_completion_tokens": 200,
        }

        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            params={"api-version": cfg.api_version},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        obj = json.loads(content)
        selected_ids = obj.get("selected_facet_ids", [])

        # 驗證：只保留白名單內的 id
        valid_ids = {f["id"] for f in canonical}
        validated = [fid for fid in selected_ids if fid in valid_ids]

        # 若 LLM 一個都沒選，保守 fallback：取第一個 facet
        if not validated:
            print(f"  [FacetCtrl] ⚠️  LLM 未選任何 facet，fallback 到第一個: {canonical[0]['id']}")
            return [canonical[0]["id"]]

        return validated

    except Exception as e:
        # Fallback：取前兩個 facet（保守策略）
        print(f"  [FacetCtrl] ⚠️  LLM 選取失敗({e})，fallback 到前 2 個 facet")
        return [f["id"] for f in canonical[:2]]


def clear_facet_cache():
    """清除 facet 快取（換問卷批次時呼叫）"""
    _facet_cache.clear()


# =========================================================
# 6) 輔助函數：根據條款 ID 查找 taxonomy entry
# =========================================================

def get_taxonomy_entry(clause_id: str, question_text: str = "") -> Optional[dict]:
    """
    依 clause_id 查找 taxonomy entry。
    先精確比對，再模糊比對（question_text 中包含條款名稱）。
    """
    if not clause_id:
        return None

    # 1. 精確比對
    clause_stripped = clause_id.strip()
    key = CLAUSE_TO_TAXONOMY.get(clause_stripped)
    if key:
        return FACET_TAXONOMY.get(key)

    # 2. 前綴比對（去除後綴說明文字）
    for k, v in CLAUSE_TO_TAXONOMY.items():
        if clause_stripped.startswith(k) or k.startswith(clause_stripped):
            return FACET_TAXONOMY.get(v)

    # 3. 在 question_text 中找條款名稱
    if question_text:
        for key_name in FACET_TAXONOMY.keys():
            if key_name in question_text:
                return FACET_TAXONOMY.get(key_name)

    return None
