"""
Pipeline 編排器 (Orchestrator)
================================
把 L1 ~ L5 串成一條完整的處理流程。這是唯一知道「5 層怎麼接在一起」
的地方，其他每一層都只知道自己的輸入輸出介面 —— 這樣未來要插入新的
一層（例如 L3.5 Reranker）只需要改這個檔案，不用動其他層的內部邏輯。
"""

from __future__ import annotations

from typing import Dict

from .l1_ingestion import load_knowledge_dir
from .l2_schema import detect_schema
from .l3_retrieval import HybridRetriever
from .l4_reasoning import Answer, get_reasoner
from .l5_output import write_audit_json, write_excel


def run_pipeline(
    questionnaire_path: str,
    knowledge_dir: str,
    output_dir: str,
    top_k: int = 3,
) -> dict:
    # L1：讀取知識庫（所有格式混合）
    corpus = load_knowledge_dir(knowledge_dir)

    # L2：偵測問卷 Schema，抽出所有問題
    questions = detect_schema(questionnaire_path)

    # L3 + L4：對每一題做混合檢索 + 推理
    retriever = HybridRetriever()
    reasoner = get_reasoner()

    answers: Dict[str, Answer] = {}
    for q in questions:
        evidence = retriever.search(q.text, corpus, top_k=top_k)
        answers[q.id] = reasoner.answer(q.text, q.id, evidence)

    # L5：回填 Excel + 產出稽核 JSON
    from pathlib import Path

    output_excel = str(Path(output_dir) / "questionnaire_completed.xlsx")
    output_json = str(Path(output_dir) / "audit_report.json")

    write_excel(questionnaire_path, questions, answers, output_excel)
    write_audit_json(questions, answers, output_json)

    import json

    summary = json.loads(Path(output_json).read_text(encoding="utf-8"))["summary"]
    summary["output_excel"] = output_excel
    summary["output_audit_json"] = output_json
    summary["knowledge_chunks_loaded"] = len(corpus)
    return summary
