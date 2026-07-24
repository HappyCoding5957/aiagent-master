#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫模型定義
"""
from typing import Optional, List
from datetime import datetime
from uuid import uuid4

from sqlmodel import SQLModel, Field, Column
from pgvector.sqlalchemy import Vector


class PdfFile(SQLModel, table=True):
    """PDF 檔案資料表"""
    id: Optional[str] = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    hash: str
    unit: str
    name: str
    size: str
    date: Optional[datetime] = Field(default_factory=datetime.now)


class PdfChunk(SQLModel, table=True):
    """PDF 區塊資料表"""
    id: Optional[str] = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    pdf_id: str = Field(foreign_key="pdffile.id")
    page_hash: str
    chunk_index: int
    xywh: str
    text: str
    embed: List[float] = Field(sa_column=Column(Vector(1024)))
