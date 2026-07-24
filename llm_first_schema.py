#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM-first 結構化抽取模組 - 職安問卷 RPA 系統

核心理念：
  1. 附件二（客戶問卷）→ QuestionItem（語意結構化）
  2. 附件三（知識庫）→ KnowledgeItem（語意結構化）
  3. 兩者在同一「語意座標系」中比對（intent + must_have_terms + topic_tags）

設計原則：
  - 最小侵入：不改現有流程，只提供結構化抽取
  - 可回退：LLM 失敗就回傳保守版 schema
  - 繁中優先：統一轉成繁體中文
"""

from __future__ import annotations

import json
import re
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Literal

import requests


# =========================================================
# 1) Schema 定義
# =========================================================

Language = Literal["zh-TW", "zh-CN", "en", "unknown"]


@dataclass
class SkipLogic:
    """跳題邏輯（附件二可能有）"""
    has_skip: bool = False
    when_answer: Literal["NO", "YES", "UNKNOWN"] = "UNKNOWN"
    target_clause_id: str = ""


@dataclass
class QuestionItem:
    """
    問卷題目 Schema（附件二）

    欄位對應：
      - clause_id: 條款編號（B 欄）
      - category: 類別（A 欄，如 "Labor 勞工"）
      - question_text_raw: 原始題目（C 欄）
      - question_text_zh: 繁中正規化後的題目
      - intent: 一句話意圖摘要（救那 7 題的關鍵！）
      - topic_tags: 主題標籤（如 fire_safety, child_labor）
      - must_have_terms: 必備錨點詞（關鍵詞列表）
      - skip_logic: 跳題規則
    """
    clause_id: str                   # 條款編號（如 "C.7.1"）
    category: str                    # 類別（如 "Labor 勞工"）
    question_text_raw: str           # 原始文字
    question_text_zh: str            # 繁體中文（LLM 轉換後）
    intent: str                      # 一句話意圖摘要
    topic_tags: List[str]            # 主題標籤
    must_have_terms: List[str]       # 必備錨點詞
    skip_logic: SkipLogic            # 跳題規則
    language: Language = "unknown"   # 來源語言
    confidence: float = 0.0          # LLM 抽取信心（0~1）


@dataclass
class KnowledgeItem:
    """
    知識庫條目 Schema（附件三）

    欄位對應：
      - row_id: 列 ID（如 "A2"）
      - category: 類別（A 欄）
      - behavior: 行為準則（B 欄）
      - keywords: 關鍵字列表（C 欄，換行分隔）
      - article: 條文內容（D 欄）
      - dept: 權責部門（E 欄）
      - impact: 目前現況/可能影響（F 欄）
      - source: 問卷出處（G 欄）
      - intent: LLM 抽取的意圖摘要
      - topic_tags: LLM 抽取的主題標籤
    """
    row_id: str                      # 列 ID
    category: str                    # 類別
    behavior: str                    # 行為準則
    keywords: List[str]              # 關鍵字列表
    article: str                     # 條文內容
    dept: str                        # 權責部門
    impact: str                      # 目前現況/可能影響
    source: str                      # 問卷出處
    intent: str = ""                 # LLM 抽取的意圖（可選）
    topic_tags: List[str] = None     # LLM 抽取的主題標籤（可選）
    confidence: float = 0.0          # LLM 抽取信心

    def __post_init__(self):
        if self.topic_tags is None:
            self.topic_tags = []


# =========================================================
# 2) 工具函式
# =========================================================

_INVALID_JSON_CHARS = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")

def _safe_json_text(s: str) -> str:
    """清理文字：移除控制字元、去除前後空白"""
    if s is None:
        return ""
    s = str(s)
    s = _INVALID_JSON_CHARS.sub("", s)
    return s.strip()


def _detect_lang(text: str) -> Language:
    """粗略語言偵測"""
    t = (text or "").strip()
    if not t:
        return "unknown"

    # 有大量英文字 → en
    if re.search(r"[A-Za-z]{4,}", t):
        # 仍可能是中英混雜
        if re.search(r"[\u4e00-\u9fff]", t):
            return "unknown"
        return "en"

    # 中日韓字元 → unknown（後續給 LLM 正規成 zh-TW）
    if re.search(r"[\u4e00-\u9fff]", t):
        return "unknown"

    return "unknown"


def _fallback_question(clause_id: str, category: str, raw: str) -> QuestionItem:
    """LLM 失敗時的 fallback"""
    raw = _safe_json_text(raw)
    return QuestionItem(
        clause_id=clause_id or "",
        category=category or "",
        question_text_raw=raw,
        question_text_zh=raw,           # fallback：不轉繁
        intent=raw[:80],                # 直接截斷
        topic_tags=[],
        must_have_terms=[],
        skip_logic=SkipLogic(False, "UNKNOWN", ""),
        language=_detect_lang(raw),
        confidence=0.0
    )


def _fallback_knowledge(row_id: str, category: str, behavior: str,
                        keywords: List[str], article: str, dept: str,
                        impact: str, source: str) -> KnowledgeItem:
    """LLM 失敗時的 fallback"""
    return KnowledgeItem(
        row_id=row_id,
        category=_safe_json_text(category),
        behavior=_safe_json_text(behavior),
        keywords=[_safe_json_text(k) for k in keywords if k],
        article=_safe_json_text(article),
        dept=_safe_json_text(dept),
        impact=_safe_json_text(impact),
        source=_safe_json_text(source),
        intent=_safe_json_text(behavior)[:100],  # fallback：用行為準則
        topic_tags=[],
        confidence=0.0
    )


# =========================================================
# 3) Azure OpenAI 配置
# =========================================================

@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI 配置（相容現有系統）"""
    endpoint: str
    api_key: str
    deployment: str
    api_version: str = "2024-12-01-preview"
    timeout: int = 30


# =========================================================
# 4) LLM 抽取函式
# =========================================================

def extract_question_schema_llm(
    cfg: AzureOpenAIConfig,
    clause_id: str,
    category: str,
    question_text: str,
    *,
    debug: bool = False,
) -> QuestionItem:
    """
    將「題目文字」抽取成 QuestionItem（LLM-first）

    核心功能：
      1. 簡轉繁（統一語言）
      2. 提取 intent（一句話摘要，去除模板字）
      3. 提取 must_have_terms（必備錨點詞，救那 7 題！）
      4. 提取 topic_tags（主題標籤）
      5. 偵測跳題邏輯（if no skip to...）

    回傳：
      - 成功：結構化的 QuestionItem
      - 失敗：fallback（用原文）
    """
    raw = _safe_json_text(question_text)
    if not raw:
        return _fallback_question(clause_id, category, raw)

    url = f"{cfg.endpoint}/openai/deployments/{cfg.deployment}/chat/completions"
    headers = {"api-key": cfg.api_key, "Content-Type": "application/json"}

    # ✅ 強制模型只輸出 JSON
    system_prompt = (
        "你是職安問卷的「結構化抽取器」。\n"
        "你的任務是把客戶問卷題目轉成結構化 JSON，包含：\n"
        "1. 繁體中文正規化（簡轉繁、統一用詞）\n"
        "2. 一句話意圖摘要（去除「是否」「請提供」等模板字）\n"
        "3. 必備錨點詞（該題不可缺少的關鍵詞，如：滅火器、消防演習、童工、危險作業）\n"
        "4. 主題標籤（如：fire_safety, child_labor, forced_labor, environment）\n"
        "5. 跳題規則（若題目包含 'if no skip to' 之類的邏輯）\n\n"
        "注意：\n"
        "- intent 要簡潔，去除冗餘詞\n"
        "- must_have_terms 要精準，不要泛用詞（如「公司」「員工」）\n"
        "- topic_tags 用英文蛇形命名（如 fire_safety, not 消防安全）\n"
        "- 只輸出 JSON，不要解釋"
    )

    user_prompt = (
        f"條款編號: {clause_id}\n"
        f"類別: {category}\n"
        f"題目: {raw}\n\n"
        "請依 schema 輸出 JSON。"
    )

    # Schema hint
    schema_hint = {
        "type": "object",
        "properties": {
            "clause_id": {"type": "string"},
            "category": {"type": "string"},
            "question_text_raw": {"type": "string"},
            "question_text_zh": {"type": "string", "description": "繁體中文正規化"},
            "intent": {"type": "string", "description": "一句話意圖摘要"},
            "topic_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "主題標籤（英文蛇形）"
            },
            "must_have_terms": {
                "type": "array",
                "items": {"type": "string"},
                "description": "必備錨點詞（不可缺少的關鍵詞）"
            },
            "skip_logic": {
                "type": "object",
                "properties": {
                    "has_skip": {"type": "boolean"},
                    "when_answer": {"type": "string", "enum": ["NO", "YES", "UNKNOWN"]},
                    "target_clause_id": {"type": "string"}
                }
            },
            "language": {"type": "string", "enum": ["zh-TW", "zh-CN", "en", "unknown"]},
            "confidence": {"type": "number", "description": "抽取信心（0~1）"}
        },
        "required": ["clause_id", "category", "question_text_zh", "intent",
                     "topic_tags", "must_have_terms", "skip_logic", "confidence"]
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt + f"\n\nschema: {json.dumps(schema_hint, ensure_ascii=False)}"}
        ],
        "response_format": {"type": "json_object"},  # ✅ Azure OpenAI 支援
        "seed": 42,                      # P0 Fix: 降低隨機抖動
        "max_completion_tokens": 2000,   # P0 Fix: gpt-5.3-chat 推理型模型用此參數
    }

    # [print-LFS0] 送出前
    if debug:
        print(f"[print-LFS0][上面] clause_id={clause_id} category={category} raw_preview={raw[:80]}")

    try:
        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            params={"api-version": cfg.api_version},
            timeout=cfg.timeout
        )
        resp.raise_for_status()
        data = resp.json()
        content = (data.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()

        # [print-LFS1] 收到 JSON
        if debug:
            print(f"[print-LFS1][下面] llm_json={content[:240]}...")

        obj = json.loads(content)

        skip = obj.get("skip_logic") or {}
        q = QuestionItem(
            clause_id=_safe_json_text(obj.get("clause_id", clause_id)),
            category=_safe_json_text(obj.get("category", category)),
            question_text_raw=_safe_json_text(obj.get("question_text_raw", raw)),
            question_text_zh=_safe_json_text(obj.get("question_text_zh", raw)),
            intent=_safe_json_text(obj.get("intent", raw[:80])),
            topic_tags=[_safe_json_text(x) for x in (obj.get("topic_tags") or []) if _safe_json_text(x)],
            must_have_terms=[_safe_json_text(x) for x in (obj.get("must_have_terms") or []) if _safe_json_text(x)],
            skip_logic=SkipLogic(
                bool(skip.get("has_skip", False)),
                (skip.get("when_answer") or "UNKNOWN"),
                _safe_json_text(skip.get("target_clause_id", "")),
            ),
            language=obj.get("language") or _detect_lang(raw),
            confidence=float(obj.get("confidence", 0.0) or 0.0),
        )

        # [print-LFS2] 成功
        if debug:
            print(f"[print-LFS2][下面] ✅ LLM 抽取成功: intent='{q.intent[:60]}' must_have={q.must_have_terms[:5]}")

        return q

    except Exception as e:
        # [print-LFS3] 失敗回退
        if debug:
            print(f"[print-LFS3][下面] ⚠️  LLM 抽取失敗={repr(e)} -> fallback")
        return _fallback_question(clause_id, category, raw)


def extract_knowledge_schema_llm(
    cfg: AzureOpenAIConfig,
    row_id: str,
    category: str,
    behavior: str,
    keywords: List[str],
    article: str,
    dept: str,
    impact: str,
    source: str,
    *,
    debug: bool = False,
) -> KnowledgeItem:
    """
    將附件三的一列抽取成 KnowledgeItem（LLM-first）

    核心功能：
      1. 從 behavior + article 抽取 intent（語意摘要）
      2. 從 keywords + behavior 擴展 topic_tags（主題標籤）
      3. 保持原有欄位完整性（row_id、dept、impact）

    回傳：
      - 成功：結構化的 KnowledgeItem
      - 失敗：fallback（用原文）
    """
    # 清理輸入
    behavior = _safe_json_text(behavior)
    article = _safe_json_text(article)
    dept = _safe_json_text(dept)
    impact = _safe_json_text(impact)

    if not behavior and not article:
        return _fallback_knowledge(row_id, category, behavior, keywords, article, dept, impact, source)

    url = f"{cfg.endpoint}/openai/deployments/{cfg.deployment}/chat/completions"
    headers = {"api-key": cfg.api_key, "Content-Type": "application/json"}

    # ✅ 強制模型只輸出 JSON
    system_prompt = (
        "你是職安問卷知識庫的「結構化抽取器」。\n"
        "你的任務是把知識庫條文轉成結構化 JSON，包含：\n"
        "1. 語意摘要（intent）：一句話總結此條文的核心要求\n"
        "2. 主題標籤（topic_tags）：用英文蛇形命名的主題標籤\n\n"
        "注意：\n"
        "- intent 要簡潔，聚焦核心要求\n"
        "- topic_tags 用英文（如 working_hours, fire_safety, anti_corruption）\n"
        "- 保持原有欄位的完整性\n"
        "- 只輸出 JSON，不要解釋"
    )

    user_prompt = (
        f"類別: {category}\n"
        f"行為準則: {behavior}\n"
        f"關鍵字: {', '.join(keywords[:10])}\n"
        f"條文內容: {article[:300]}\n"  # 限制長度避免 token 過多
        f"權責部門: {dept}\n\n"
        "請依 schema 輸出 JSON。"
    )

    # Schema hint
    schema_hint = {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "description": "一句話語意摘要（核心要求）"
            },
            "topic_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "主題標籤（英文蛇形，如 working_hours, fire_safety）"
            },
            "confidence": {
                "type": "number",
                "description": "抽取信心（0~1）"
            }
        },
        "required": ["intent", "topic_tags", "confidence"]
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt + f"\n\nschema: {json.dumps(schema_hint, ensure_ascii=False)}"}
        ],
        "response_format": {"type": "json_object"},  # ✅ Azure OpenAI 支援
        "seed": 42,                      # P0 Fix: 降低隨機抖動
        "max_completion_tokens": 2000,   # P0 Fix: gpt-5.3-chat 推理型模型用此參數
    }

    # [print-KS0] 送出前
    if debug:
        print(f"[print-KS0][上面] row_id={row_id} behavior={behavior[:40]}")

    try:
        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            params={"api-version": cfg.api_version},
            timeout=cfg.timeout
        )
        resp.raise_for_status()
        data = resp.json()
        content = (data.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()

        # [print-KS1] 收到 JSON
        if debug:
            print(f"[print-KS1][下面] llm_json={content[:200]}...")

        obj = json.loads(content)

        k = KnowledgeItem(
            row_id=row_id,
            category=_safe_json_text(category),
            behavior=behavior,
            keywords=[_safe_json_text(kw) for kw in keywords if kw],
            article=article,
            dept=dept,
            impact=impact,
            source=_safe_json_text(source),
            intent=_safe_json_text(obj.get("intent", behavior[:100])),
            topic_tags=[_safe_json_text(x) for x in (obj.get("topic_tags") or []) if _safe_json_text(x)],
            confidence=float(obj.get("confidence", 0.0) or 0.0),
        )

        # [print-KS2] 成功
        if debug:
            print(f"[print-KS2][下面] ✅ 知識庫萃取成功: intent='{k.intent[:60]}' tags={k.topic_tags[:3]}")

        return k

    except Exception as e:
        # [print-KS3] 失敗回退
        if debug:
            print(f"[print-KS3][下面] ⚠️  知識庫萃取失敗={repr(e)} -> fallback")
        return _fallback_knowledge(row_id, category, behavior, keywords, article, dept, impact, source)

# =========================================================
# 5) RAG 查詢組裝
# =========================================================

def build_rag_query_from_schema(q: QuestionItem) -> str:
    """
    用 QuestionItem 組裝 RAG 查詢字串

    策略：
      1. intent（核心意圖，去除模板字）
      2. must_have_terms（必備錨點詞，救那 7 題！）
      3. topic_tags（主題標籤，增加語意相關性）

    為什麼這個能「救那 7 題」？
      - 原本：長句 + 模板字 → RAG 被干擾 → 字面比對失真
      - 現在：intent + 錨點詞 → 乾淨查詢 → RAG 找到對的條文
    """
    parts = []

    # 1. Intent 優先（核心意圖）
    if q.intent:
        parts.append(q.intent)

    # 2. Must-have terms（必備錨點詞）
    if q.must_have_terms:
        # 限制數量，避免查詢過長
        terms = " ".join(q.must_have_terms[:12])
        parts.append(terms)

    # 3. Topic tags（主題標籤，用 # 標記）
    if q.topic_tags:
        tags = " ".join([f"#{t}" for t in q.topic_tags[:8]])
        parts.append(tags)

    query = " ".join([p for p in parts if p]).strip()

    # Fallback：如果 LLM 失敗，至少用原文
    if not query:
        query = q.question_text_zh or q.question_text_raw

    return query


# =========================================================
# 6) 輔助函式（給 rpa_security_c.py 使用）
# =========================================================

def normalize_question_to_schema(
    question: str,
    clause_id: str = "",
    category: str = "",
    azure_cfg: AzureOpenAIConfig = None,
    debug: bool = False
) -> QuestionItem:
    """
    快速入口：把問卷題目正規化成 QuestionItem

    使用範例：
        from llm_first_schema import normalize_question_to_schema, AzureOpenAIConfig

        cfg = AzureOpenAIConfig(
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            deployment=AZURE_OPENAI_DEPLOYMENT,
        )

        q_schema = normalize_question_to_schema(
            question="是否提供消防演習訓練？",
            clause_id="C.7.1",
            category="Health & Safety 健康安全",
            azure_cfg=cfg,
            debug=True
        )

        # 用 schema 組查詢
        rag_query = build_rag_query_from_schema(q_schema)
    """
    if azure_cfg is None:
        # Fallback：不使用 LLM
        return _fallback_question(clause_id, category, question)

    return extract_question_schema_llm(
        cfg=azure_cfg,
        clause_id=clause_id,
        category=category,
        question_text=question,
        debug=debug
    )


# =========================================================
# 7) 主程式測試（可選）
# =========================================================

if __name__ == "__main__":
    # 測試用
    print("LLM-first Schema 模組載入成功")

    # 測試 fallback
    q = _fallback_question("test", "Labor", "測試題目：是否有消防演習？")
    print(f"\nFallback Question:")
    print(f"  intent: {q.intent}")
    print(f"  must_have_terms: {q.must_have_terms}")
    print(f"  confidence: {q.confidence}")

    # 測試 query 組裝
    q.intent = "確認是否定期進行消防演習"
    q.must_have_terms = ["消防演習", "緊急疏散", "滅火器"]
    q.topic_tags = ["fire_safety", "emergency_response"]

    query = build_rag_query_from_schema(q)
    print(f"\nRAG Query:")
    print(f"  {query}")
