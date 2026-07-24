"""
L2 - Schema 偵測層 (Schema Detection Layer)
============================================
輸入：L1 讀進來的 Excel/CSV 原始表格（任意欄位排列）
輸出：標準化的 Question 物件清單

設計原則 (Design Principles)
----------------------------
不假設客戶的問卷格式欄位順序固定，而是用「關鍵字啟發式」
(keyword heuristics) 掃描表頭列，自動找出「題號」「問題」「答案」
「備註」對應到哪一欄。這樣同一套引擎可以吃不同客戶、不同語言的問卷，
不需要為每個客戶重新寫解析邏輯。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

ID_KEYWORDS = ["題號", "編號", "no", "no.", "id", "item", "序號"]
QUESTION_KEYWORDS = ["問題", "題目", "question", "questionnaire item", "詢問事項", "審查項目", "查核項目"]
ANSWER_KEYWORDS = ["答案", "回覆", "回答", "answer", "response", "供應商回覆", "廠商回覆"]
NOTE_KEYWORDS = ["備註", "說明", "note", "remark", "comment"]


@dataclass
class Question:
    id: str
    text: str
    sheet: str
    row: int
    question_col: int
    answer_col: Optional[int]


def _match_col(header_row: List[str], keywords: List[str]) -> Optional[int]:
    for idx, cell in enumerate(header_row):
        cell_lower = str(cell).strip().lower()
        if any(kw in cell_lower for kw in keywords):
            return idx
    return None


def detect_schema(excel_path: str) -> List[Question]:
    """
    掃描每個 Sheet 的前 5 列找表頭，命中「問題欄」關鍵字即視為問卷表；
    找不到表頭就跳過該 Sheet（可能是說明頁、封面頁）。
    """
    import pandas as pd

    questions: List[Question] = []
    xls = pd.ExcelFile(excel_path)

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name, header=None, dtype=str).fillna("")
        header_row_idx = None
        question_col = None
        answer_col = None
        id_col = None

        for r in range(min(5, len(df))):
            row = df.iloc[r].tolist()
            q_col = _match_col(row, QUESTION_KEYWORDS)
            if q_col is not None:
                header_row_idx = r
                question_col = q_col
                answer_col = _match_col(row, ANSWER_KEYWORDS)
                id_col = _match_col(row, ID_KEYWORDS)
                break

        if header_row_idx is None:
            continue  # 這個 Sheet 不是問卷表，略過

        for r in range(header_row_idx + 1, len(df)):
            q_text = str(df.iat[r, question_col]).strip()
            if not q_text:
                continue
            q_id = str(df.iat[r, id_col]).strip() if id_col is not None else str(r - header_row_idx)
            questions.append(
                Question(
                    id=q_id or str(r - header_row_idx),
                    text=q_text,
                    sheet=sheet_name,
                    row=r,
                    question_col=question_col,
                    answer_col=answer_col,
                )
            )

    return questions
