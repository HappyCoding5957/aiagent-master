"""
API 層 (n8n 相容)
===================
提供 HTTP 介面給 n8n 的 HTTP Request node 呼叫，或給客戶的
前端上傳介面呼叫。設計成單一 /process 端點收檔案、跑完整
pipeline、回傳結果路徑，符合 n8n webhook 「一來一回」的慣用模式。
"""

from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from src.pipeline import run_pipeline

app = FastAPI(title="DocAgent API", version="0.1.0")

JOBS_ROOT = Path(tempfile.gettempdir()) / "docagent_jobs"
JOBS_ROOT.mkdir(exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/process")
async def process(
    questionnaire: UploadFile = File(...),
    knowledge_files: list[UploadFile] = File(...),
):
    job_id = str(uuid.uuid4())[:8]
    job_dir = JOBS_ROOT / job_id
    knowledge_dir = job_dir / "knowledge"
    output_dir = job_dir / "output"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    questionnaire_path = job_dir / questionnaire.filename
    with questionnaire_path.open("wb") as f:
        shutil.copyfileobj(questionnaire.file, f)

    for kf in knowledge_files:
        kf_path = knowledge_dir / kf.filename
        with kf_path.open("wb") as f:
            shutil.copyfileobj(kf.file, f)

    try:
        summary = run_pipeline(
            questionnaire_path=str(questionnaire_path),
            knowledge_dir=str(knowledge_dir),
            output_dir=str(output_dir),
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "job_id": job_id})

    summary["job_id"] = job_id
    return summary
