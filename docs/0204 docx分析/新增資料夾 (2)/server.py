#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
職安問卷智慧彙整系統 - Flask API 伺服器（已整合 SSO）
用途：提供受 SSO 保護的問卷上傳介面與 API
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from datetime import datetime
from urllib.parse import unquote
import os
import base64
import uuid
import traceback

# ★ SSO 整合模組
from sso import Keycloak
from tool import LoadConfig
# ★ print-0：在 import 區塊「下面」新增安全 log
def safe_log(*args, **kwargs):
    """安全的 print：避免 BrokenPipeError 讓整個 API 掛掉"""
    try:
        print(*args, **kwargs)
    except BrokenPipeError:
        # pipe 被關掉就忽略，不要讓整個 request 500
        pass

import re

def safe_filename(name: str):
    # 移除不可用字元，只留下中文字母數字底線
    name = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9_]", "_", name)
    return name

from rpa_security_c import process_workbook

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# ★ 初始化 Keycloak SSO
keycloak = Keycloak(app)
keycloak.realm = LoadConfig("sso_realm").get_data()
keycloak.client_id = LoadConfig("sso_client_id").get_data()
keycloak.client_secret = LoadConfig("sso_client_secret").get_data()
# ✅ 設定固定的前端 URL（確保登入後返回正確的站台）
keycloak.frontend_url = LoadConfig("frontend_url").get_data()

# 配置
WEB_PORT = LoadConfig("web_port").get_data()
UPLOAD_DIR = os.path.join(os.getcwd(), LoadConfig("upload_dir").get_data())
DB_PATH = os.path.join(os.getcwd(), LoadConfig("db_path").get_data())

# 確保上傳目錄存在
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ★ SSO 輔助函數：取得當前登入用戶
def get_current_user():
    """從 SSO Cookie 取得當前用戶資訊"""
    username = request.cookies.get('family_name', '未知用戶')
    job_num = request.cookies.get('preferred_username', '')
    dep = request.cookies.get('dep', '')
    email = request.cookies.get('email', '')

    if not job_num:
        return None

    return {
        'username': unquote(username),
        'job_num': unquote(job_num),
        'dep': unquote(dep),
        'email': unquote(email)
    }


# ========== 靜態檔案路由 ==========
@app.route('/docs/assets/<path:filename>')
def serve_assets(filename):
    """提供 docs/assets 目錄的靜態檔案（Logo、SOP 圖片等）"""
    import os
    assets_dir = os.path.join(os.path.dirname(__file__), 'docs', 'assets')
    return send_from_directory(assets_dir, filename)


@app.route("/", methods=["GET"])
@keycloak.logined  # ★ SSO 保護
def index():
    """受 SSO 保護的上傳頁面"""
    user = get_current_user()
    safe_log(f"[SSO] 用戶 {user['username']} ({user['job_num']}) 存取上傳頁面")
    return send_file("test_upload.html")


@app.route("/esg/download/", methods=["GET"])
@keycloak.logined
def download_index():
    """Download 系統首頁（SSO 保護）"""
    user = get_current_user()
    safe_log("[SSO] 用戶存取 Download 頁面")
    return send_file("test_upload.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """健康檢查：確認資料庫檔案和 SSO 設定是否正常"""
    db_exists = os.path.exists(DB_PATH)

    # 檢查 SSO 是否已初始化
    sso_configured = keycloak.client_id is not None

    return jsonify({
        "status": "healthy" if (db_exists and sso_configured) else "warning",
        "service": "職安問卷智慧彙整系統",
        "database_path": DB_PATH,
        "database_exists": db_exists,
        "upload_dir": UPLOAD_DIR,
        "sso_configured": sso_configured,
        "sso_realm": keycloak.realm,
        "sso_client_id": keycloak.client_id
    })




@app.route("/api/status", methods=["GET"])
def status_check():
    """狀態檢查：供前端確認用戶登入狀態"""
    user = get_current_user()
    
    if user:
        return jsonify({
            "status": "authenticated",
            "user": {
                "username": user['username'],
                "job_num": user['job_num'],
                "dep": user['dep'],
                "email": user['email']
            }
        })
    else:
        return jsonify({
            "status": "unauthenticated"
        }), 401


@app.route("/api/attachment3/upload", methods=["POST"])
def attachment3_upload():
    """
    附件三上傳 API

    接收：
      - base64Data: Excel 檔案的 base64 字串

    回傳：
      - success: True/False
      - pdf_id: PDF ID
      - chunk_count: 資料筆數
    """
    import subprocess
    import tempfile
    import re

    safe_log("[ATTACHMENT3] 收到上傳請求")

    data = request.get_json(force=True, silent=True)
    if isinstance(data, list):
        data = data[0]

    base64_data = data.get("base64Data")

    if not base64_data:
        safe_log("[ATTACHMENT3][ERROR] 缺少 base64Data")
        return jsonify({"success": False, "error": "缺少 base64Data"}), 400

    safe_log(f"[ATTACHMENT3] base64Data 長度 = {len(base64_data)}")

    # 寫入臨時檔案
    try:
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp_file:
            tmp_file.write(base64.b64decode(base64_data))
            tmp_path = tmp_file.name

        safe_log(f"[ATTACHMENT3] 已儲存臨時檔案: {tmp_path}")

        # 執行上傳腳本
        VENV_PYTHON = "/home/lladm/frank/n8n-MCP/aiagent/venv/bin/python3"
        UPLOAD_SCRIPT = "/home/lladm/frank/n8n-MCP/aiagent/upload_attachment3_to_rag.py"

        safe_log(f"[ATTACHMENT3] 執行上傳腳本...")
        result = subprocess.run(
            [VENV_PYTHON, UPLOAD_SCRIPT, tmp_path],
            capture_output=True,
            text=True,
            timeout=600
        )

        stdout = result.stdout
        stderr = result.stderr

        safe_log(f"[ATTACHMENT3] 腳本執行完成 (return code: {result.returncode})")

        # 解析輸出
        pdf_id_match = re.search(r'PDF ID: ([a-f0-9-]+)', stdout)
        chunk_match = re.search(r'資料筆數: (\d+)', stdout)

        # 清理臨時檔案
        os.unlink(tmp_path)

        if pdf_id_match and chunk_match:
            safe_log(f"[ATTACHMENT3] 上傳成功: PDF ID = {pdf_id_match.group(1)}, Chunks = {chunk_match.group(1)}")
            return jsonify({
                'success': True,
                'pdf_id': pdf_id_match.group(1),
                'chunk_count': int(chunk_match.group(1)),
                'message': '上傳成功'
            })
        else:
            safe_log(f"[ATTACHMENT3][ERROR] 無法解析輸出")
            safe_log(f"[ATTACHMENT3] stdout: {stdout[:500]}")
            safe_log(f"[ATTACHMENT3] stderr: {stderr[:500]}")
            return jsonify({
                'success': False,
                'error': '無法解析上傳結果',
                'stdout': stdout,
                'stderr': stderr
            }), 500

    except Exception as e:
        safe_log(f"[ATTACHMENT3][ERROR] {repr(e)}")
        safe_log(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route("/api/security-c/match-from-base64", methods=["POST"])
def security_c_match_from_base64():
    """
    職安問卷智慧彙整系統 主 API（受 SSO 保護）

    接收：
      - file_base64: 問卷附件2 Excel 的 base64 字串
      - (選配) client_name: 客戶名稱

    步驟：
      1. 驗證 SSO 登入（從 Cookie 取得使用者）
      2. 解析 request.json
      3. 將 base64 還原成暫存檔
      4. 呼叫 process_workbook() 跑比對
      5. 把輸出 Excel 轉回 base64 回傳

    回傳：
      - success: True/False
      - file_name: 輸出檔名
      - file_base64: 結果 Excel 的 base64
      - (選配) report: 比對報告摘要
    """

    # ★ SSO 驗證：取得當前用戶
    user = get_current_user()
    if not user:
        return jsonify({
            "success": False,
            "error": "SSO 未登入，請重新整理頁面"
        }), 401

    # ★ print-1：在取得 request.json「下面」→ 先看整個 payload 長什麼樣
    data = request.get_json(force=True, silent=True)
    # 如果 data 是 list，取第一個
    if isinstance(data, list):
        data = data[0]
    safe_log(f"[SECURITY_C] 用戶 {user['username']} ({user['job_num']}) 發起問卷比對")
    safe_log("[SECURITY_C] 收到請求 payload keys:", list(data.keys()))

    # 取得 base64
    file_base64 = data.get("file_base64")
    client_name = data.get("client_name", "未指定客戶")

    if not file_base64:
        safe_log("[SECURITY_C][ERROR] 缺少 file_base64 參數")
        return jsonify({"success": False, "error": "缺少 file_base64"}), 400

    # ★ print-2：在檢查 file_base64「下面」→ 印出長度即可，避免 log 爆掉
    safe_log(f"[SECURITY_C] 客戶名稱: {client_name}")
    safe_log(f"[SECURITY_C] file_base64 長度 = {len(file_base64)}")

    # 檢查資料庫檔案是否存在
    if not os.path.exists(DB_PATH):
        safe_log(f"[SECURITY_C][ERROR] 資料庫檔案不存在: {DB_PATH}")
        return jsonify({
            "success": False,
            "error": f"資料庫檔案不存在: {DB_PATH}"
        }), 500

    # 決定暫存檔名
    temp_name = f"survey_input_{uuid.uuid4().hex[:8]}.xlsx"
    temp_path = os.path.join(UPLOAD_DIR, temp_name)

    # 還原 base64 成 Excel 檔
    try:
        with open(temp_path, "wb") as f:
            f.write(base64.b64decode(file_base64))

        # ★ print-3：在暫存檔寫完「下面」→ 確認實際檔案路徑
        safe_log(f"[SECURITY_C] 已儲存附件2暫存檔: {temp_path}")

    except Exception as e:
        safe_log(f"[SECURITY_C][ERROR] 解碼 base64 失敗: {repr(e)}")
        return jsonify({
            "success": False,
            "error": f"解碼 base64 失敗: {str(e)}"
        }), 400

    # ★ print-4：在呼叫 process_workbook「上面」→ 先印出路徑
    safe_log(f"[SECURITY_C] 準備開始比對")
    safe_log(f"[SECURITY_C]   - 問卷檔案: {temp_path}")
    safe_log(f"[SECURITY_C]   - 資料庫: {DB_PATH}")

    try:
        # 呼叫問卷核心邏輯：輸入附件2、附件3 → 回傳輸出檔路徑 + 報告
        result = process_workbook(temp_path, DB_PATH, client_name)

        output_path = result["output_path"]
        report = result.get("report", {})

    except Exception as e:
        # ★ print-5：Exception 在 return「上面」→ 印出錯誤細節
        safe_log(f"[SECURITY_C][ERROR] 比對過程發生錯誤:")
        safe_log(traceback.format_exc())

        error_msg = str(e)

        # ✅ 如果是 RAG 認證錯誤，提供更明確的提示
        if "RAG 服務認證失敗" in error_msg or "RAG_AUTH_ERROR" in error_msg:
            return jsonify({
                "success": False,
                "error": "❌ RAG 服務認證失敗\n\n無法連接到知識庫服務進行問卷比對。\n\n可能原因：\n1. RAG 服務（port 8004）已啟用 SSO 保護\n2. 服務間認證配置錯誤\n\n請聯繫系統管理員檢查 RAG 服務配置。",
                "technical_details": error_msg
            }), 503
        else:
            return jsonify({
                "success": False,
                "error": f"比對過程發生錯誤: {error_msg}"
            }), 500

    # ★ print-6：在讀 output 檔案「上面」→ 確認路徑
    safe_log(f"[SECURITY_C] 比對完成, 輸出檔案路徑 = {output_path}")

    # 讀取輸出 Excel，轉回 base64 給 n8n
    try:
        with open(output_path, "rb") as f:
            result_bytes = f.read()
        result_b64 = base64.b64encode(result_bytes).decode("utf-8")

        # 使用純 ASCII 檔名（避免 n8n content-disposition header 錯誤）
        timestamp_now = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"security_c_result_{timestamp_now}.xlsx"

        # ★ print-7：在 return JSON「上面」→ 確認 file_name / size
        safe_log(f"[SECURITY_C] 回傳結果檔案: {file_name}")
        safe_log(f"[SECURITY_C]   - 檔案大小: {len(result_bytes)} bytes")
        safe_log(f"[SECURITY_C]   - 總題數: {report.get('total_questions', 0)}")
        safe_log(f"[SECURITY_C]   - 成功匹配: {report.get('matched_count', 0)}")
        safe_log(f"[SECURITY_C]   - 低信心題目: {report.get('low_confidence_count', 0)}")

        return jsonify({
            "success": True,
            "file_name": file_name,
            "file_base64": result_b64,
            "report": report
        })

    except Exception as e:
        safe_log(f"[SECURITY_C][ERROR] 讀取輸出檔案失敗: {repr(e)}")
        return jsonify({
            "success": False,
            "error": f"讀取輸出檔案失敗: {str(e)}"
        }), 500


if __name__ == "__main__":
    print("=" * 80)
    print("職安問卷智慧彙整系統 - Flask API 伺服器啟動中（SSO 整合版）")
    print("=" * 80)
    print(f"服務網址: http://10.80.15.49:{WEB_PORT}/")
    print(f"上傳目錄: {UPLOAD_DIR}")
    print(f"資料庫路徑: {DB_PATH}")
    print(f"資料庫存在: {os.path.exists(DB_PATH)}")
    print(f"SSO Realm: {keycloak.realm}")
    print(f"SSO Client ID: {keycloak.client_id}")
    print("=" * 80)
    print("✅ SSO 保護已啟用，所有路由需先登入 Keycloak")
    print("=" * 80)

    # 開發模式：使用 config.json 設定的 port
    # 生產模式：建議用 gunicorn
    app.run(host="0.0.0.0", port=WEB_PORT, debug=True)
