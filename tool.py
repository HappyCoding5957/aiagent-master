import os, json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from flask import request, redirect, url_for
from functools import wraps
import uuid

#取得config.json檔裡的設定值
class LoadConfig:
    def  __init__(self, client_id):
        self.client_id = client_id
    def get_data(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, 'config.json'), 'r') as f:
            json_data = json.load(f)
        return json_data[self.client_id]

#發送access_token更新通知mail
def send_email(id):
    mail_content = f'{id} access_token成功更新'
    # 設置SMTP伺服器
    server = smtplib.SMTP('10.80.10.6')
    server.starttls()
    # 創建新的電子郵件
    email = MIMEMultipart()
    email['From'] = 'MeetSrvs101@epistar.com.tw'
    email['To'] = '14Z2100@ennostar.com'
    email['Subject'] = f'{id} access_token更新通知'
    email.attach(MIMEText(mail_content, 'plain'))
    # 發送電子郵件
    server.send_message(email)
    server.quit()

# 裝飾器@，判斷是否為管理者帳號(權限從config.json裡的admin_list設定)
def check_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        job_num = request.cookies.get('preferred_username')
        admin_list = LoadConfig('admin_list').get_data()
        if job_num in admin_list:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return decorated_function