#!/usr/bin/env python3
import sys

# 讀取原始檔案
with open('proxy_server_fixed.py.bak', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到插入位置
marker = "# ========== 舊的統一 callback（向下兼容）=========="
if marker not in content:
    print("找不到插入位置")
    sys.exit(1)

# 插入 logout 路由
logout_code = '''
# ========== Logout 路由 ==========
@app.route('/logout')
def logout_proxy():
    """統一 logout 導向下載系統"""
    return proxy_request(DOWNLOAD_BACKEND, "/logout")


@app.route('/esg/upload/logout')
def upload_logout_proxy():
    """上傳系統 logout"""
    return proxy_request(UPLOAD_BACKEND, "/logout")


@app.route('/esg/download/logout')
def download_logout_proxy():
    """下載系統 logout"""
    return proxy_request(DOWNLOAD_BACKEND, "/logout")


'''

# 在 marker 之前插入
new_content = content.replace(marker, logout_code + marker)

# 寫入新檔案
with open('proxy_server_fixed.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ logout 路由已加入")
