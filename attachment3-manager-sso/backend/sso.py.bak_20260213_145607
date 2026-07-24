from flask import request, redirect, make_response
from functools import wraps
from urllib.parse import quote

# [使用方式]

# 1.實例化Keycloak類別並指定realm、client_id、client_secret，範例如下：
# ========================================================================
# keycloak = Keycloak(app)
# keycloak.realm = "Infra"
# keycloak.client_id = "WebexMS"
# keycloak.client_secret = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# ========================================================================

# 2.使用@logined裝飾器，對欲卡控的網頁做權控管，如未登入會自動被導向Keycloak登入頁面，範例如下：
# ========================================================================
# @app.route('/', methods=['GET', 'POST'])
# @keycloak.logined
# def index():
    # return ...
# ========================================================================

class Keycloak:
    def __init__(self, app):
        self.pythonsso_api = "http://espython-sso-api.epistar.com.tw:8080"
        self.host_url = None       # 本機網址
        self.realm = None          # keycloak的realm
        self.client_id = None      # keycloak的client_id
        self.client_secret = None  # keycloak的client_secret
        self.app = app
        self.app.route("/callback", methods=["POST","GET"])(self.callback)
        self.app.route("/logout")(self.logout)
        self.app.route("/logout_cookie")(self.logout_cookie)

    def login(self):
        self.host_url = request.url_root # 取得本機網址
        login_url = f"{self.pythonsso_api}?realm={self.realm}&client_id={self.client_id}&callback_url={self.host_url}callback" # Keycloak登入頁面網址
        return redirect(login_url)

    def callback(self):
        if request.method == "GET":
            code = request.args.get('code')
            if code=="None": return "Keycloak_Down"
        elif request.method == 'POST':
            preferred_username = request.form.get('preferred_username') # 接收pythonsso_api回傳的工號
            family_name = request.form.get('family_name')               # 接收pythonsso_api回傳的姓名
            email = request.form.get('email')                           # 接收python_api回傳的信箱
            dep = request.form.get('dep')                               # 接收python_api回傳的部門
            client_secret = request.form.get('client_secret')           # 接收pythonsso_api回傳的client_secret
            refresh_token = request.form.get('refresh_token')           # 接收pythonsso_api回傳的refresh_token
            logout_url = f"{self.pythonsso_api}/logout?realm={self.realm}&client_id={self.client_id}&callback_url={self.host_url}&refresh_token={refresh_token}"
            if self.client_secret == client_secret:
                # 導到首頁
                resp = make_response(redirect('/'))
                # 儲存cookies（修復：正確編碼 UTF-8 中文）
                resp.set_cookie('preferred_username', quote(preferred_username) if preferred_username else '')
                resp.set_cookie('family_name', quote(family_name) if family_name else '')
                resp.set_cookie('email', quote(email) if email else '')
                resp.set_cookie('dep', quote(dep) if dep else '')
                resp.set_cookie('client_secret', client_secret)
                resp.set_cookie('logout_url', logout_url)
                return resp
            else:
                return "client_secret錯誤"

    def logout(self):
        logout_url = request.cookies.get('logout_url') # 從cookie中讀取logout_url
        resp = make_response(redirect(logout_url))     # 導到sso登出網址
        # 清空cookies
        resp.set_cookie('preferred_username', '', expires=0)
        resp.set_cookie('family_name', '', expires=0)
        resp.set_cookie('email', '', expires=0)
        resp.set_cookie('dep', '', expires=0)
        resp.set_cookie('client_secret', '', expires=0)
        resp.set_cookie('logout_url', '', expires=0)
        return resp

    def logout_cookie(self):
        # 清空cookies
        resp = make_response()
        resp.set_cookie('preferred_username', '', expires=0)
        resp.set_cookie('family_name', '', expires=0)
        resp.set_cookie('email', '', expires=0)
        resp.set_cookie('dep', '', expires=0)
        resp.set_cookie('client_secret', '', expires=0)
        resp.set_cookie('logout_url', '', expires=0)

        # 返回包含登出成功訊息和重新登入按鈕的HTML頁面
        return f'''
        <h1>您已成功登出</h1>
        <button class="button is-primary" onclick="location.href='{request.url_root}'" type="button">點擊這裡重新登入</button>
        '''

    # 裝飾器@，判斷是否已登入
    def logined(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.cookies.get('preferred_username'):
                return self.login()
            return f(*args, **kwargs)
        return decorated_function