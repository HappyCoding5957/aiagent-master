"""
L4 - 推理層 (Reasoning Layer)
==============================
輸入：Question + Top-k 證據 Chunks
輸出：Answer 物件 (answer_text, confidence, citation, needs_review)

設計原則 (Design Principles)
----------------------------
可插拔 LLM (Pluggable LLM)：正式環境接 Claude/GPT，demo/離線環境用
MockReasoner，兩者實作同一個 Reasoner 介面，上層 pipeline 完全不用
知道底下是哪個模型 —— 這樣去客戶端做 Private Deployment 時，只要換
一個 Reasoner 實作，其他 4 層完全不用動。

信心分級 (Confidence Tiering)：
    >= 0.60        自動通過 (Auto-approve)
    0.30 - 0.60    建議人工覆核 (Human review suggested)
    <  0.30        證據不足，強制人工 (Insufficient evidence, forced review)

門檻校準說明 (Threshold Calibration)：
    這兩個門檻是針對「Fuzzy + 關鍵字」這個 baseline 檢索器的實際分數
    分布校準出來的（用 sample_data 跑過驗證），不是套用向量/Embedding
    模型常見的 0.85 高門檻。之後換成 EmbeddingRetriever + Reranker
    (如 Cohere Rerank) 後，分數分布會不同，門檻需要重新校準——這是
    正式上線前必須用真實客戶資料重跑的步驟，不能沿用這裡的數字。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from .l3_retrieval import ScoredChunk

AUTO_APPROVE_THRESHOLD = 0.60
REVIEW_THRESHOLD = 0.30


@dataclass
class Answer:
    question_id: str
    answer_text: str
    confidence: float
    citation: str          # 例如 "policy_iso27001.txt @ 全文"
    needs_review: bool
    status: str             # auto_approve / review_suggested / insufficient_evidence


class Reasoner(ABC):
    @abstractmethod
    def answer(self, question_text: str, question_id: str, evidence: List[ScoredChunk]) -> Answer:
        ...


class MockReasoner(Reasoner):
    """
    離線/demo 版本：不呼叫任何外部 LLM API，純規則邏輯。
    直接取最佳證據的文字片段當答案，confidence = 檢索分數。
    正式環境請換成 ClaudeReasoner / OpenAIReasoner（見下方骨架）。
    """

    def answer(self, question_text: str, question_id: str, evidence: List[ScoredChunk]) -> Answer:
        if not evidence:
            return Answer(
                question_id=question_id,
                answer_text="（查無足夠證據，需人工確認）",
                confidence=0.0,
                citation="無",
                needs_review=True,
                status="insufficient_evidence",
            )

        best = evidence[0]
        confidence = round(best.score, 3)
        citation = f"{best.chunk.source_file} @ {best.chunk.location}"

        if confidence >= AUTO_APPROVE_THRESHOLD:
            status, needs_review = "auto_approve", False
            answer_text = best.chunk.text[:200]
        elif confidence >= REVIEW_THRESHOLD:
            status, needs_review = "review_suggested", True
            answer_text = best.chunk.text[:200]
        else:
            status, needs_review = "insufficient_evidence", True
            answer_text = "（查無足夠證據，需人工確認）"

        return Answer(
            question_id=question_id,
            answer_text=answer_text,
            confidence=confidence,
            citation=citation,
            needs_review=needs_review,
            status=status,
        )


class ClaudeReasoner(Reasoner):
    """
    正式版骨架 (Production Skeleton)：接 Anthropic API。
    需要環境變數 ANTHROPIC_API_KEY，未設定時建構會直接失敗，
    讓呼叫端明確知道要切回 MockReasoner，而不是靜默降級。
    """

    def __init__(self, model: str = "claude-sonnet-5"):
        import os

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("未設定 ANTHROPIC_API_KEY，無法使用 ClaudeReasoner")
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def answer(self, question_text: str, question_id: str, evidence: List[ScoredChunk]) -> Answer:
        evidence_text = "\n---\n".join(
            f"[來源: {e.chunk.source_file} @ {e.chunk.location}]\n{e.chunk.text}" for e in evidence
        )
        prompt = (
            "你是企業問卷自動回答助手。根據以下證據回答問題，"
            "只根據證據內容回答，不要編造。若證據不足請明確說「證據不足」。\n\n"
            f"問題：{question_text}\n\n證據：\n{evidence_text}\n\n請給出簡潔答案："
        )
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        answer_text = resp.content[0].text.strip()
        # 正式版信心分數應該另外用 dual-LLM 驗證層算，這裡先沿用檢索分數當佔位邏輯
        confidence = round(evidence[0].score, 3) if evidence else 0.0
        citation = f"{evidence[0].chunk.source_file} @ {evidence[0].chunk.location}" if evidence else "無"

        if confidence >= AUTO_APPROVE_THRESHOLD:
            status, needs_review = "auto_approve", False
        elif confidence >= REVIEW_THRESHOLD:
            status, needs_review = "review_suggested", True
        else:
            status, needs_review = "insufficient_evidence", True

        return Answer(
            question_id=question_id,
            answer_text=answer_text,
            confidence=confidence,
            citation=citation,
            needs_review=needs_review,
            status=status,
        )


def get_reasoner() -> Reasoner:
    """工廠函式：有設定 API Key 就用正式版，否則自動降級成 Mock"""
    import os

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return ClaudeReasoner()
        except Exception:
            pass
    return MockReasoner()
