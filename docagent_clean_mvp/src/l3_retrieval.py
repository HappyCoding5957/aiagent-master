"""
L3 - 混合檢索層 (Hybrid Retrieval Layer)
=========================================
輸入：L2 找到的 Question + L1 讀進來的知識庫 Chunks
輸出：每題最相關的 top-k 證據（含來源、頁碼/列號、相似度分數）

設計原則 (Design Principles)
----------------------------
Hybrid = Fuzzy 字串相似度 (rapidfuzz) + 關鍵字命中飽和計分
(keyword saturation scoring)。單用向量檢索容易漏掉專有名詞/編號，
單用關鍵字比對容易漏掉同義詞，兩者加權平均後比較穩定。

之後要接正式的 Embeddings + Reranker（如 Cohere Rerank），
只需要新增一個 EmbeddingRetriever 類別實作同一個 Retriever 介面，
pipeline.py 完全不用改 —— Strategy Pattern。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from .l1_ingestion import Chunk

try:
    from rapidfuzz import fuzz

    _HAS_RAPIDFUZZ = True
except ImportError:  # 降級：沒裝 rapidfuzz 時用標準庫 difflib
    import difflib

    _HAS_RAPIDFUZZ = False


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float  # 0.0 - 1.0


class Retriever(ABC):
    @abstractmethod
    def search(self, query: str, corpus: List[Chunk], top_k: int = 3) -> List[ScoredChunk]:
        ...


def _fuzzy_ratio(a: str, b: str) -> float:
    if _HAS_RAPIDFUZZ:
        return fuzz.token_set_ratio(a, b) / 100.0
    return difflib.SequenceMatcher(None, a, b).ratio()


# 問句常見的疑問語助詞/敬語，會稀釋關鍵字命中率但不帶語意，
# 檢索前先從「問題句」濾掉（answer/chunk 是陳述句，不需要濾）。
QUESTION_STOPWORDS = [
    "貴公司", "請說明", "請問", "是否", "為何", "多久", "多少",
    "分別", "相關", "有無", "貴司", "說明", "請敘明",
]


def _strip_question_stopwords(text: str) -> str:
    cleaned = text
    for sw in QUESTION_STOPWORDS:
        cleaned = cleaned.replace(sw, "")
    return cleaned


def _tokenize(text: str) -> set[str]:
    """簡易中英混合斷詞：英文按空白，中文按 2-gram 滑動窗口"""
    tokens: set[str] = set()
    for word in text.replace("，", " ").replace("。", " ").split():
        tokens.add(word.lower())
    # 中文 2-gram，補足關鍵字命中率
    cleaned = "".join(ch for ch in text if "一" <= ch <= "鿿")
    for i in range(len(cleaned) - 1):
        tokens.add(cleaned[i : i + 2])
    return tokens


def _keyword_saturation(query: str, chunk_text: str) -> float:
    q_tokens = _tokenize(_strip_question_stopwords(query))
    if not q_tokens:
        return 0.0
    c_tokens = _tokenize(chunk_text)
    hit = len(q_tokens & c_tokens)
    return min(hit / len(q_tokens), 1.0)


class HybridRetriever(Retriever):
    def __init__(self, fuzzy_weight: float = 0.6, keyword_weight: float = 0.4):
        self.fuzzy_weight = fuzzy_weight
        self.keyword_weight = keyword_weight

    def search(self, query: str, corpus: List[Chunk], top_k: int = 3) -> List[ScoredChunk]:
        scored: List[ScoredChunk] = []
        for chunk in corpus:
            fuzzy = _fuzzy_ratio(query, chunk.text)
            keyword = _keyword_saturation(query, chunk.text)
            final = self.fuzzy_weight * fuzzy + self.keyword_weight * keyword
            scored.append(ScoredChunk(chunk=chunk, score=final))
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]
