#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 後端 - 附件三知識庫管理系統
提供上傳、查詢、刪除 API

修改：改為異步處理，支援實時進度反饋
"""
import os
import json
import base64
import tempfile
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, Response
from pydantic import BaseModel
from sqlmodel import Session, create_engine, select
from urllib.parse import quote, unquote
import openpyxl
import requests

# 導入資料庫模型
from models import PdfFile, PdfChunk, SQLModel

# ========== SSO 認證模組 ==========
from sso_fastapi import KeycloakFastAPI

# ========== 配置 ==========
DB_URL = os.getenv("DB_URL", "postgresql://dgtk:dgtk@10.100.40.5:8002/dgtk")
EMBED_API = os.getenv("EMBED_API", "http://10.100.40.5:8004/api/embed")
UNIT = "SYSTEM"
PDF_NAME = "附件三_EnvSafety_atta3_知識庫"
PROGRESS_FILE = "/app/attachment3_upload_progress.json"

# SSO 配置
SSO_REALM = os.getenv("SSO_REALM", "Infra")
SSO_CLIENT_ID = os.getenv("SSO_CLIENT_ID", "MeetBook")
SSO_CLIENT_SECRET = os.getenv("SSO_CLIENT_SECRET", "WKRuv36gORlne3DP3aVhx1sJwqoJP8tq")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://10.100.40.5:4201")

# ========== 全局狀態追蹤 ==========
upload_status = {
    "is_uploading": False,
    "start_time": None
}

# ========== FastAPI 應用 ==========
app = FastAPI(title="附件三知識庫管理系統", version="1.0.0")

# CORS 設定（允許前端跨域請求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境建議限制特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 建立資料庫引擎
engine = create_engine(DB_URL, echo=False)

# ========== 初始化 SSO ==========
keycloak = KeycloakFastAPI(
    realm=SSO_REALM,
    client_id=SSO_CLIENT_ID,
    client_secret=SSO_CLIENT_SECRET
)

# SSO 認證依賴
def require_sso(request: Request):
    """要求 SSO 認證，返回用戶資訊"""
    return keycloak.require_login(request)


# ========== Pydantic Models ==========
class StatusResponse(BaseModel):
    exists: bool
    pdf_id: Optional[str] = None
    name: Optional[str] = None
    chunk_count: Optional[int] = None
    last_update: Optional[str] = None
    unit: Optional[str] = None


class UploadResponse(BaseModel):
    success: bool
    message: str
    start_time: Optional[str] = None
    pdf_id: Optional[str] = None
    pdf_name: Optional[str] = None
    chunk_count: Optional[int] = None
    unit: Optional[str] = None
    error: Optional[str] = None


class DeleteResponse(BaseModel):
    success: bool
    deleted_chunks: int
    deleted_files: int
    message: str


class ProgressResponse(BaseModel):
    stage: str
    percent: int
    message: str
    timestamp: Optional[str] = None
    is_uploading: Optional[bool] = False  # ✅ 新增欄位


# ========== 輔助函數 ==========
def update_progress(stage: str, percent: int, message: str = ""):
    """更新進度到檔案"""
    progress = {
        "stage": stage,
        "percent": percent,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False)
        print(f"[PROGRESS] {stage} - {percent}% - {message}")  # ✅ 添加日誌
    except Exception as e:
        print(f"⚠️  無法寫入進度檔案: {e}")


def process_upload(file_path: str) -> dict:
    """處理上傳的附件三檔案 - 呼叫 upload_attachment3_to_rag.py 使用 LLM-first"""
    try:
        update_progress("init", 0, "開始處理")
        update_progress("processing", 5, "啟動 LLM-first 上傳流程")
        
        import subprocess
        import sys
        from pathlib import Path
        
        script_path = Path("/app/upload_attachment3_to_rag.py")
        env = os.environ.copy()
        env.update({
            "DB_URL": DB_URL,
            "EMBED_API": EMBED_API,
            "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT", "https://en-openai01.openai.azure.com"),
            "AZURE_OPENAI_KEY": os.getenv("AZURE_OPENAI_KEY", ""),
            "AZURE_OPENAI_DEPLOYMENT": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-chat"),
            "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        })
        
        update_progress("processing", 10, "執行 LLM-first 萃取")
        result = subprocess.run([sys.executable, "-u", str(script_path), file_path], env=env, timeout=1200)  # 20 分鐘超時
        
        if result.returncode != 0:
            raise RuntimeError(f"上傳腳本執行失敗，返回碼: {result.returncode}")
        
        with Session(engine) as db:
            existing = db.exec(select(PdfFile).where(PdfFile.name == PDF_NAME, PdfFile.unit == UNIT)).first()
            if not existing:
                raise RuntimeError("資料庫中找不到上傳結果")
            chunks = db.exec(select(PdfChunk).where(PdfChunk.pdf_id == existing.id)).all()
            pdf_id = existing.id
            chunk_count = len(chunks)
        
        update_progress("complete", 100, "上傳完成")
        
        # ✅ 上傳完成後自動重置為 idle，避免下次上傳卡住
        import time
        time.sleep(3)  # 等待 3 秒讓前端讀取完成狀態
        update_progress("idle", 0, "等待上傳")
        return {"success": True, "pdf_id": pdf_id, "pdf_name": PDF_NAME, "chunk_count": chunk_count, "unit": UNIT}
        
    except subprocess.TimeoutExpired:
        update_progress("error", 0, "處理超時（超過 10 分鐘）")
        raise RuntimeError("上傳處理超時")
    except Exception as e:
        update_progress("error", 0, f"處理失敗: {str(e)}")
        raise

def read_root(request: Request):
    """根路徑 - 檢查 SSO 登入狀態"""
    user_info = keycloak.get_user_info(request)

    if not user_info:
        # 未登入，重定向到登入頁面
        host_url = FRONTEND_URL.rstrip("/") + "/"
        login_url = keycloak.get_login_url(host_url)
        return RedirectResponse(url=login_url)

    # 已登入，返回歡迎訊息
    return {
        "message": "附件三知識庫管理系統 API (SSO 版本)",
        "version": "1.0.1 (async)",
        "user": user_info["family_name"],
        "username": user_info["preferred_username"]
    }


@app.get("/api/status", response_model=StatusResponse)
def get_status(request: Request, user_info: dict = Depends(require_sso)):
    """查詢知識庫狀態"""
    try:
        with Session(engine) as db:
            pdf_file = db.exec(
                select(PdfFile).where(
                    PdfFile.name == PDF_NAME,
                    PdfFile.unit == UNIT
                )
            ).first()

            if pdf_file:
                chunk_count = db.exec(
                    select(PdfChunk).where(PdfChunk.pdf_id == pdf_file.id)
                ).all()

                return StatusResponse(
                    exists=True,
                    pdf_id=pdf_file.id,
                    name=pdf_file.name,
                    chunk_count=len(chunk_count),
                    last_update=pdf_file.date.isoformat() if pdf_file.date else None,
                    unit=pdf_file.unit
                )
            else:
                return StatusResponse(exists=False)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(request: Request, file: UploadFile = File(...), user_info: dict = Depends(require_sso)):
    """
    ✅ 異步上傳 - 立即返回，後台處理
    前端應該在收到響應後立即開始輪詢 /api/progress
    """
    global upload_status

    try:
        # ✅ 檢查是否已有上傳在進行（基於進度檔案，更穩健）
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    progress = json.load(f)
                    # 如果進度不是 idle, complete, error，表示正在處理
                    if progress.get("stage") in ["init", "reading", "embedding", "database", "processing"]:
                        raise HTTPException(
                            status_code=409,
                            detail=f"已有上傳正在進行中（{progress.get('percent')}%），請稍後再試"
                        )
            except json.JSONDecodeError:
                pass  # 檔案損壞，允許繼續

        # 檢查檔案類型
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="只接受 .xlsx 檔案")

        # 儲存暫存檔案
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # ✅ 初始化進度（讓前端立即看到 0%）
        update_progress("init", 0, "開始處理")

        # 標記上傳中
        upload_status["is_uploading"] = True
        upload_status["start_time"] = datetime.now().isoformat()

        # ✅ 啟動後台執行緒處理
        def background_process():
            try:
                print(f"[UPLOAD] 開始後台處理: {file.filename}")
                result = process_upload(tmp_file_path)
                print(f"[UPLOAD] 處理完成: {result}")

                # 清理暫存檔案
                try:
                    os.unlink(tmp_file_path)
                except Exception as cleanup_error:
                    print(f"[UPLOAD] 清理暫存檔案失敗: {cleanup_error}")

            except Exception as e:
                print(f"[UPLOAD] 處理失敗: {e}")
                update_progress("error", 0, f"上傳失敗: {str(e)}")
            finally:
                upload_status["is_uploading"] = False
                print("[UPLOAD] 後台處理結束")

        thread = threading.Thread(target=background_process, daemon=True)
        thread.start()

        print(f"[UPLOAD] 已啟動後台處理，立即返回響應")

        # ✅ 立即返回（不等待處理完成）
        return UploadResponse(
            success=True,
            message="上傳已開始，請輪詢 /api/progress 查看進度（建議每 2 秒輪詢一次）",
            start_time=upload_status["start_time"],
            pdf_id="PROCESSING",
            pdf_name="處理中",
            chunk_count=0,
            unit="SYSTEM"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/delete", response_model=DeleteResponse)
def delete_knowledge_base(request: Request, user_info: dict = Depends(require_sso)):
    """刪除知識庫"""
    try:
        with Session(engine) as db:
            # 查詢檔案
            pdf_file = db.exec(
                select(PdfFile).where(
                    PdfFile.name == PDF_NAME,
                    PdfFile.unit == UNIT
                )
            ).first()

            if not pdf_file:
                return DeleteResponse(
                    success=True,
                    deleted_chunks=0,
                    deleted_files=0,
                    message="知識庫不存在"
                )

            # 刪除 chunks
            chunks = db.exec(select(PdfChunk).where(PdfChunk.pdf_id == pdf_file.id)).all()
            deleted_chunks = len(chunks)
            for chunk in chunks:
                db.delete(chunk)

            # 刪除 file
            db.delete(pdf_file)
            db.commit()

            return DeleteResponse(
                success=True,
                deleted_chunks=deleted_chunks,
                deleted_files=1,
                message="刪除成功"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/progress", response_model=ProgressResponse)
def get_progress(request: Request, user_info: dict = Depends(require_sso)):
    """
    ✅ 查詢上傳進度
    前端應該每 2 秒輪詢一次此 API
    """
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                progress = json.load(f)

                # ✅ 添加上傳狀態
                progress["is_uploading"] = upload_status.get("is_uploading", False)

                return ProgressResponse(**progress)
        else:
            return ProgressResponse(
                stage="idle",
                percent=0,
                message="尚未開始",
                is_uploading=upload_status.get("is_uploading", False)
            )
    except Exception as e:
        print(f"[PROGRESS] 讀取進度失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
