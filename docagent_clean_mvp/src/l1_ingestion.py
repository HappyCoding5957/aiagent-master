"""
L1 - 擷取層 (Ingestion Layer)
=============================
負責讀取各種格式的原始文件（PDF / Excel / CSV / 圖片 / 純文字），
統一轉換成內部資料結構 Chunk，供後續 L2 Schema 偵測與 L3 檢索使用。

設計原則 (Design Principles)
----------------------------
1. 可插拔 OCR 引擎 (Pluggable OCR Engine)
   預設嘗試 Tesseract，若環境沒有安裝則自動降級為 MockOCR
   （回傳提示文字而非報錯），確保 pipeline 不會因為缺套件而整條中斷。
   正式上線時只要把 get_ocr_engine() 換成 PaddleOCR 的 wrapper 即可，
   其餘程式碼完全不用動 —— 這是策略模式 (Strategy Pattern)。

2. 統一輸出格式 Chunk
   不管來源是 PDF 第幾頁、Excel 第幾列，最終都變成同一種資料結構，
   讓 L3 檢索層完全不用管文件原始格式是什麼。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Chunk:
    """統一的文件片段結構 (Unified document fragment)"""

    text: str
    source_file: str
    location: str          # 例如 "第 3 頁" 或 "Sheet1!A5"
    doc_type: str = "text"  # text / table_row / ocr


# ---------------------------------------------------------------------------
# OCR 引擎 (Pluggable OCR Engine)
# ---------------------------------------------------------------------------

class OCREngine(ABC):
    @abstractmethod
    def extract(self, image_path: str) -> str:
        ...


class TesseractOCR(OCREngine):
    """正式版：需要系統安裝 tesseract-ocr 與 pytesseract 套件"""

    def __init__(self):
        import pytesseract  # noqa: F401  (延遲載入，確保沒裝時不會擋住 import)
        from PIL import Image  # noqa: F401

        self._pytesseract = pytesseract
        self._Image = Image

    def extract(self, image_path: str) -> str:
        img = self._Image.open(image_path)
        return self._pytesseract.image_to_string(img, lang="chi_tra+eng")


class MockOCR(OCREngine):
    """
    離線/demo 降級版：沒有安裝 tesseract 時使用。
    不假裝有結果，而是明確標示「此為 Mock OCR 佔位輸出」，
    避免 demo 時誤以為是真的辨識結果。
    """

    def extract(self, image_path: str) -> str:
        name = Path(image_path).name
        return f"[MockOCR 佔位輸出：{name} 尚未經過真實 OCR，正式環境請安裝 pytesseract + tesseract-ocr]"


def get_ocr_engine() -> OCREngine:
    try:
        return TesseractOCR()
    except Exception:
        return MockOCR()


# ---------------------------------------------------------------------------
# 各格式讀取器 (Format Loaders)
# ---------------------------------------------------------------------------

def load_text_file(path: str) -> List[Chunk]:
    """
    按行/段落切塊 (Context-aware Chunking)，而不是整份文件當一個 Chunk。
    企業政策文件通常一行一個條款，切成行級 Chunk 能大幅提升 L3 檢索的
    精準度——這是「暴力整份塞給檢索器」和「context-aware 分塊」的差異，
    也是競品矩陣裡列出的稀缺架構模組之一。
    """
    raw_text = Path(path).read_text(encoding="utf-8", errors="ignore")
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

    if not lines:
        return []

    chunks: List[Chunk] = []
    for i, line in enumerate(lines, start=1):
        chunks.append(
            Chunk(text=line, source_file=Path(path).name, location=f"第 {i} 行", doc_type="text")
        )
    return chunks


def load_excel_file(path: str) -> List[Chunk]:
    """每一列轉成一個 Chunk，location 記錄 Sheet 與列號，方便 L5 稽核回溯來源"""
    import pandas as pd

    chunks: List[Chunk] = []
    xls = pd.ExcelFile(path)
    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name, header=None, dtype=str).fillna("")
        for row_idx, row in df.iterrows():
            row_text = " | ".join(str(v) for v in row.tolist() if str(v).strip())
            if row_text:
                chunks.append(
                    Chunk(
                        text=row_text,
                        source_file=Path(path).name,
                        location=f"{sheet_name}!row{row_idx + 1}",
                        doc_type="table_row",
                    )
                )
    return chunks


def load_pdf_file(path: str) -> List[Chunk]:
    """優先用 pypdf 抽文字層；若該頁沒有文字層（掃描件），標記需要 OCR"""
    from pypdf import PdfReader

    chunks: List[Chunk] = []
    reader = PdfReader(path)
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if not text:
            text = "[此頁無文字層，屬於掃描件，建議接 OCR 引擎重新處理]"
        chunks.append(
            Chunk(text=text, source_file=Path(path).name, location=f"第 {i + 1} 頁", doc_type="text")
        )
    return chunks


def load_image_file(path: str, ocr: OCREngine | None = None) -> List[Chunk]:
    ocr = ocr or get_ocr_engine()
    text = ocr.extract(path)
    return [Chunk(text=text, source_file=Path(path).name, location="OCR", doc_type="ocr")]


def load_document(path: str, ocr: OCREngine | None = None) -> List[Chunk]:
    """統一入口 (Dispatcher)：依副檔名分派到對應的讀取器"""
    suffix = Path(path).suffix.lower()
    if suffix in (".txt", ".md"):
        return load_text_file(path)
    if suffix in (".xlsx", ".xls", ".csv"):
        return load_excel_file(path)
    if suffix == ".pdf":
        return load_pdf_file(path)
    if suffix in (".png", ".jpg", ".jpeg"):
        return load_image_file(path, ocr)
    raise ValueError(f"不支援的檔案格式 (Unsupported file type): {suffix}")


def load_knowledge_dir(dir_path: str) -> List[Chunk]:
    """把整個知識庫資料夾（多種格式混合）一次讀成 Chunk 清單"""
    chunks: List[Chunk] = []
    ocr = get_ocr_engine()
    for p in sorted(Path(dir_path).glob("**/*")):
        if p.is_file() and p.suffix.lower() in (".txt", ".md", ".xlsx", ".xls", ".csv", ".pdf", ".png", ".jpg", ".jpeg"):
            try:
                chunks.extend(load_document(str(p), ocr))
            except Exception as e:  # 單一檔案失敗不應該讓整個知識庫載入中斷
                chunks.append(
                    Chunk(text=f"[讀取失敗: {e}]", source_file=p.name, location="ERROR", doc_type="error")
                )
    return chunks
