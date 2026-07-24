#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
附件三上傳 HTTP API 服務
提供給 n8n Execute Command 調用
"""

from flask import Flask, request, jsonify
import subprocess
import os
import base64
import tempfile
import json

app = Flask(__name__)

UPLOAD_SCRIPT = "/home/lladm/frank/n8n/客戶問卷RPA/upload_attachment3_to_rag.py"
VENV_PYTHON = "/home/lladm/frank/n8n/客戶問卷RPA/venv/bin/python3"

@app.route('/upload-attachment3', methods=['POST'])
def upload_attachment3():
    """接收 base64 編碼的 Excel 檔案並執行上傳腳本"""
    try:
        # 取得 base64 數據
        data = request.get_json()
        base64_data = data.get('base64Data')
        
        if not base64_data:
            return jsonify({'success': False, 'error': '缺少 base64Data'}), 400
        
        # 解碼並寫入臨時檔案
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp_file:
            tmp_file.write(base64.b64decode(base64_data))
            tmp_path = tmp_file.name
        
        try:
            # 執行上傳腳本
            result = subprocess.run(
                [VENV_PYTHON, UPLOAD_SCRIPT, tmp_path],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # 解析輸出
            stdout = result.stdout
            
            # 提取 PDF ID 和資料筆數
            import re
            pdf_id_match = re.search(r'PDF ID: ([a-f0-9-]+)', stdout)
            chunk_match = re.search(r'資料筆數: (\d+)', stdout)
            
            if pdf_id_match and chunk_match:
                return jsonify({
                    'success': True,
                    'pdf_id': pdf_id_match.group(1),
                    'chunk_count': int(chunk_match.group(1)),
                    'message': '上傳成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '無法解析上傳結果',
                    'stdout': stdout,
                    'stderr': result.stderr
                }), 500
                
        finally:
            # 清理臨時檔案
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """健康檢查"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5679, debug=False)
