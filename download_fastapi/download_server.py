"""
ESG Download 系統 - FastAPI 版本 (統一版)
端口：8002
功能：提供 ESG 問卷下載功能，整合統一 SSO、Security-C API
"""
import sys
from pathlib import Path

# 加入父目錄到 Python 路徑（讓 rpa_security_c 等模組可被 import）
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from urllib.parse import unquote, quote
import os
import base64
import uuid
import threading
import traceback
import logging
from datetime import datetime

# 統一 SSO 中間件
from unified_sso import UnifiedSSO

# 問卷比對模組（父目錄）
from rpa_security_c import process_workbook

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI app
app = FastAPI(title="ESG Download System", version="2.0")

# 配置路徑
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
DOCS_DIR = BASE_DIR / "docs"
DOWNLOAD_LOG_FILE = str(BASE_DIR / "download_logs.jsonl")

# 資料路徑（父目錄）
DB_PATH = str(PARENT_DIR / "附件三.xlsx")
UPLOAD_DIR = str(PARENT_DIR / "security_c_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 掛載靜態文件
app.mount("/esg/download/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/esg/download/docs/assets", StaticFiles(directory=str(DOCS_DIR / "assets")), name="docs_assets")

# SSO 設定
SSO_CONFIG = {
    "realm": "Infra",
    "client_id": "MeetBook",
    "client_secret": "WKRuv36gORlne3DP3aVhx1sJwqoJP8tq",
    "frontend_url": "https://ssw01.ennostar.com",
    "sso_api": "http://espython-sso-api.epistar.com.tw:8080"
}

# 初始化統一 SSO（自動註冊 /login, /callback, /logout, /logout_callback）
sso = UnifiedSSO(app, SSO_CONFIG)


def require_login(request: Request) -> dict:
    """登入驗證（用於 Depends）"""
    return sso.require_login(request)

def log_download(user: str, user_name: str, action: str, status: str, details: str = "", file_name: str = "", chunks: int = 0):
    """記錄下載日誌至 PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect(host="10.100.40.5", port=8002, user="dgtk", password="dgtk", database="dgtk")
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO esg_usage_logs (timestamp, service, user_id, user_name, file_name, status, chunks, details)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (datetime.now(), "download", user, user_name, file_name, status, chunks, details or action)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"[LOG] 無法寫入 DB 日誌: {e}")





# ========== 非同步任務狀態存儲 ==========
tasks = {}
tasks_lock = threading.Lock()


def _cleanup_old_tasks():
    from datetime import timedelta
    now = datetime.now()
    to_delete = []
    for tid, task in tasks.items():
        try:
            created = datetime.fromisoformat(task.get('created_at', ''))
            if now - created > timedelta(hours=2):
                to_delete.append(tid)
        except Exception:
            pass
    for tid in to_delete:
        del tasks[tid]


def run_task(task_id, temp_path, db_path, client_name):
    try:
        with tasks_lock:
            tasks[task_id]['status'] = 'processing'
        logger.info(f"[TASK] {task_id} 開始處理")

        result = process_workbook(temp_path, db_path, client_name)
        output_path = result["output_path"]
        report = result.get("report", {})

        with open(output_path, "rb") as f:
            result_bytes = f.read()
        result_b64 = base64.b64encode(result_bytes).decode("utf-8")
        file_name = f"security_c_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        with tasks_lock:
            tasks[task_id].update({
                'status': 'done',
                'file_name': file_name,
                'file_base64': result_b64,
                'report': report,
            })
        logger.info(f"[TASK] {task_id} 完成，題數={report.get('total_questions', 0)}")
        log_download(
            tasks[task_id].get('user', 'unknown'),
            tasks[task_id].get('user_name', '未知'),
            'security_c_complete',
            'success',
            f'題數={report.get("total_questions", 0)}',
            file_name=tasks[task_id].get('client_name', ''),
            chunks=report.get('total_questions', 0)
        )

    except Exception as e:
        logger.error(f"[TASK] {task_id} 失敗: {repr(e)}\n{traceback.format_exc()}")
        with tasks_lock:
            tasks[task_id].update({'status': 'error', 'error': str(e)})
    finally:
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass


# ========== 靜態資源 ==========
@app.get("/esg/download/favicon.ico")
async def favicon():
    favicon_path = STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return Response("Not Found", status_code=404)


# ========== 主要頁面 ==========
@app.get("/esg/download/", response_class=HTMLResponse)
async def download_page(request: Request, user: dict = Depends(require_login)):
    logger.info(f"[SSO] 用戶 {user['family_name']} ({user['preferred_username']}) 存取下載頁面")

    html_file = TEMPLATES_DIR / "test_upload.html"
    if html_file.exists():
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        html_content = html_content.replace("{{user_name}}", user['family_name'])
        html_content = html_content.replace("{{user_id}}", user['preferred_username'])
        html_content = html_content.replace("{{user_dep}}", user.get('dep', ''))
        return HTMLResponse(content=html_content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return HTMLResponse("<h1>ESG Download System</h1><p>模板文件不存在</p>")


# ========== Health / Status API ==========
@app.get("/api/health")
async def health_check():
    db_exists = os.path.exists(DB_PATH)
    return JSONResponse({
        "status": "healthy" if db_exists else "warning",
        "service": "ESG Download System (FastAPI)",
        "version": "2.0",
        "port": 8002,
        "database_exists": db_exists,
        "database_path": DB_PATH,
    })


@app.get("/api/status")
async def status_check(request: Request):
    user = sso.get_current_user(request)
    if user:
        return JSONResponse({"logged_in": True, "user": user})
    return JSONResponse({"logged_in": False}, status_code=401)


@app.get("/api/logout")
async def api_logout(request: Request):
    """供前端 AJAX 調用登出"""
    return sso.logout(request)


# ========== Security-C API ==========
@app.post("/api/security-c/submit")
async def security_c_submit(request: Request, user: dict = Depends(require_login)):
    """非同步提交：立即返回 task_id，後台開始比對"""
    try:
        data = await request.json()
        if isinstance(data, list):
            data = data[0]
    except Exception:
        return JSONResponse({"success": False, "error": "無法解析請求"}, status_code=400)

    file_base64 = data.get("file_base64")
    client_name = data.get("client_name", "未指定客戶")

    if not file_base64:
        return JSONResponse({"success": False, "error": "缺少 file_base64"}, status_code=400)

    if not os.path.exists(DB_PATH):
        return JSONResponse({"success": False, "error": f"資料庫檔案不存在: {DB_PATH}"}, status_code=500)

    temp_name = f"survey_input_{uuid.uuid4().hex[:8]}.xlsx"
    temp_path = os.path.join(UPLOAD_DIR, temp_name)
    try:
        with open(temp_path, "wb") as f:
            f.write(base64.b64decode(file_base64))
    except Exception as e:
        return JSONResponse({"success": False, "error": f"解碼 base64 失敗: {str(e)}"}, status_code=400)

    task_id = uuid.uuid4().hex
    with tasks_lock:
        _cleanup_old_tasks()
        tasks[task_id] = {
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
            'user': user['preferred_username'],
            'user_name': user.get('family_name', '未知'),
            'client_name': client_name,
        }

    t = threading.Thread(target=run_task, args=(task_id, temp_path, DB_PATH, client_name))
    t.daemon = True
    t.start()

    logger.info(f"[SUBMIT] 用戶 {user['family_name']} ({user['preferred_username']}) 提交任務 task_id={task_id}")
    return JSONResponse({"success": True, "task_id": task_id, "message": "任務已提交，請輪詢狀態"})


@app.get("/api/security-c/status/{task_id}")
async def security_c_status(task_id: str):
    """查詢任務處理狀態"""
    with tasks_lock:
        task = tasks.get(task_id)

    if not task:
        return JSONResponse(
            {"success": False, "error": "找不到此任務，可能已過期或 server 已重啟"},
            status_code=404
        )

    status = task['status']
    if status == 'done':
        return JSONResponse({
            "success": True, "status": "done",
            "file_name": task['file_name'],
            "file_base64": task['file_base64'],
            "report": task.get('report', {}),
        })
    elif status == 'error':
        return JSONResponse({
            "success": False, "status": "error",
            "error": task.get('error', '未知錯誤'),
        })
    return JSONResponse({"success": True, "status": status})



# ========== 統計 API ==========
@app.get("/esg/download/api/stats")
async def get_download_stats(request: Request, user: dict = Depends(require_login)):
    """查詢下載統計資訊（從 PostgreSQL）"""
    try:
        import psycopg2
        conn = psycopg2.connect(host="10.100.40.5", port=8002, user="dgtk", password="dgtk", database="dgtk")
        cur = conn.cursor()

        today = datetime.now().date()

        cur.execute("SELECT COUNT(*) FROM esg_usage_logs WHERE service='download'")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM esg_usage_logs WHERE service='download' AND timestamp::date = %s", (today,))
        today_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT user_id) FROM esg_usage_logs WHERE service='download'")
        total_users = cur.fetchone()[0]

        cur.execute("""SELECT timestamp, user_id, user_name, file_name, status, chunks
                        FROM esg_usage_logs WHERE service='download'
                        ORDER BY timestamp DESC LIMIT 200""")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        logs = [
            {"timestamp": r[0].isoformat(), "user": r[1], "user_name": r[2],
             "file_name": r[3], "status": r[4], "chunks": r[5], "action": "security_c_complete"}
            for r in rows
        ]
        return {"total_requests": total, "today_requests": today_count,
                "total_users": total_users, "logs": logs}
    except Exception as e:
        logger.error(f"[STATS] DB 查詢失敗: {e}")
        return {"total_requests": 0, "today_requests": 0, "total_users": 0, "logs": []}

@app.get("/esg/download/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: dict = Depends(require_login)):
    """管理員統計頁面"""
    html_file = TEMPLATES_DIR / "admin.html"
    if html_file.exists():
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        html_content = html_content.replace("{{user_name}}", user['family_name'])
        html_content = html_content.replace("{{user_id}}", user['preferred_username'])
        html_content = html_content.replace("上傳系統", "下載系統")
        return HTMLResponse(content=html_content)
    return HTMLResponse("<h1>Admin</h1><p>模板文件不存在</p>")

# ========== Attachment3 API ==========
@app.post("/api/attachment3/upload")
async def attachment3_upload(request: Request, user: dict = Depends(require_login)):
    """附件三上傳 API"""
    import subprocess
    import re as _re
    import tempfile

    logger.info(f"[ATTACHMENT3] 用戶 {user['preferred_username']} 收到上傳請求")
    try:
        data = await request.json()
        if isinstance(data, list):
            data = data[0]
    except Exception:
        return JSONResponse({"success": False, "error": "無法解析請求"}, status_code=400)

    base64_data = data.get("base64Data")
    if not base64_data:
        return JSONResponse({"success": False, "error": "缺少 base64Data"}, status_code=400)

    try:
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp_file:
            tmp_file.write(base64.b64decode(base64_data))
            tmp_path = tmp_file.name

        VENV_PYTHON = "/home/lladm/frank/n8n-MCP/aiagent/venv/bin/python3"
        UPLOAD_SCRIPT = "/home/lladm/frank/n8n-MCP/aiagent/upload_attachment3_to_rag.py"

        result = subprocess.run(
            [VENV_PYTHON, UPLOAD_SCRIPT, tmp_path],
            capture_output=True, text=True, timeout=600
        )
        stdout = result.stdout
        stderr = result.stderr
        os.unlink(tmp_path)

        pdf_id_match = _re.search(r'PDF ID: ([a-f0-9-]+)', stdout)
        chunk_match = _re.search(r'資料筆數: (\d+)', stdout)

        if pdf_id_match and chunk_match:
            return JSONResponse({
                'success': True,
                'pdf_id': pdf_id_match.group(1),
                'chunk_count': int(chunk_match.group(1)),
                'message': '上傳成功'
            })
        return JSONResponse({
            'success': False, 'error': '無法解析上傳結果',
            'stdout': stdout, 'stderr': stderr
        }, status_code=500)
    except Exception as e:
        logger.error(f"[ATTACHMENT3][ERROR] {repr(e)}")
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


# ========== 啟動入口 ==========
if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print("ESG Download System (FastAPI) 啟動中")
    print("=" * 80)
    print("監聽 Port: 8002")
    print(f"DB_PATH: {DB_PATH} (存在: {os.path.exists(DB_PATH)})")
    print(f"UPLOAD_DIR: {UPLOAD_DIR}")
    print("端點:")
    print("  /esg/download/        - 下載頁面")
    print("  /api/health           - 健康檢查")
    print("  /api/status           - 登入狀態")
    print("  /api/security-c/submit          - 非同步提交")
    print("  /api/security-c/status/{task_id} - 查詢狀態")
    print("  /api/attachment3/upload          - 附件三上傳")
    print("  /login /callback /logout /logout_callback (SSO)")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
