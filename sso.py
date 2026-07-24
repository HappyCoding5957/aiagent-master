from flask import request, redirect, make_response
from functools import wraps
from urllib.parse import quote, unquote, urlparse

# [使用方式]
# keycloak = Keycloak(app)
# keycloak.realm = "Infra"
# keycloak.client_id = "WebexMS"
# keycloak.client_secret = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# keycloak.frontend_url = "https://ssw01.ennostar.com/"  # ✅ 建議：只放網域，不含 path

class Keycloak:
    def __init__(self, app):
        self.pythonsso_api = "http://espython-sso-api.epistar.com.tw:8080"
        self.host_url = None
        self.realm = None
        self.client_id = None
        self.client_secret = None
        self.frontend_url = None
        self.app = app
        self.app.route("/callback", methods=["POST", "GET"])(self.callback)
        self.app.route("/logout")(self.logout)
        self.app.route("/logout_cookie")(self.logout_cookie)
        self.app.route("/login", methods=["GET", "POST"])(self.login)
        # ✅ 新增：logout_callback 路由（只接受 GET）
        self.app.route("/logout_callback", methods=["GET"])(self.logout_callback)

    def _origin_from_frontend_url(self):
        """
        ✅ 只取 scheme://host，不帶 path
        避免 frontend_url=.../esg/download/ 時 callback_url 變成 /esg/download/callback
        """
        if not self.frontend_url:
            return None
        try:
            p = urlparse(self.frontend_url)
            if p.scheme and p.netloc:
                return f"{p.scheme}://{p.netloc}"
        except Exception:
            pass
        return None

    def login(self):
        # ✅ callback_url 一律走 origin + /callback（不帶 path）
        origin = self._origin_from_frontend_url()
        callback_base_url = origin if origin else request.url_root.rstrip("/")
        self.host_url = callback_base_url  # 儲存以便其他地方使用

        callback_url = f"{callback_base_url}/callback"
        login_url = f"{self.pythonsso_api}?realm={self.realm}&client_id={self.client_id}&callback_url={callback_url}"

        # ✅ 修正 next_path 計算邏輯
        next_arg = request.args.get("next")

        if next_arg:
            next_path = next_arg
        else:
            # 若是直接打 /login，就不能用 request.path（會循環）
            next_path = "/" if request.path == "/login" else request.path

        # ★ PRINT-1：顯示完整的 next_path 決策過程
        print(
            f"[SSO][PRINT-1] Login 請求 - "
            f"path={request.path}, "
            f"next_arg={request.args.get('next', 'N/A')}, "
            f"resolved_next={next_path}"
        )

        # 安全：只允許站內相對路徑
        if not next_path.startswith("/"):
            next_path = "/"

        resp = make_response(redirect(login_url))

        # ★ PRINT-1-2：顯示最終存入 cookie 的值
        print(f"[SSO][PRINT-1-2] set sso_next_path={next_path}")

        # ✅ path 必須是 '/'，callback 才讀得到
        resp.set_cookie("sso_next_path", quote(next_path), max_age=300, path="/")
        return resp

    def callback(self):
        if request.method == "GET":
            code = request.args.get('code')
            if code == "None":
                return "Keycloak_Down"

        elif request.method == 'POST':
            preferred_username = request.form.get('preferred_username')
            family_name = request.form.get('family_name')
            email = request.form.get('email')
            dep = request.form.get('dep')
            client_secret = request.form.get('client_secret')
            refresh_token = request.form.get('refresh_token')

            # ✅ 修改：logout_url 改用 /logout_callback
            origin = self._origin_from_frontend_url()
            callback_url_base = (origin if origin else request.url_root.rstrip("/"))
            logout_url = f"{self.pythonsso_api}/logout?realm={self.realm}&client_id={self.client_id}&callback_url={callback_url_base}/logout_callback&refresh_token={refresh_token}"

            if self.client_secret == client_secret:
                # ✅ 優先用 state（若 SSO 有回），再用 cookie 的 next
                state = request.form.get("state") or request.args.get("state") or ""
                raw_next = request.cookies.get("sso_next_path", "/")

                # ★ PRINT-2：顯示 state 和 cookie 的值
                print(f"[SSO][PRINT-2] callback state={state} cookie_next={raw_next}")

                next_path = unquote(state) if state else unquote(raw_next)
                if not next_path:
                    next_path = "/"
                if not next_path.startswith("/"):
                    next_path = "/"

                redirect_to = next_path if next_path != "/" else "/"

                # ★ PRINT-3：顯示最終的 redirect_to
                print(f"[SSO][PRINT-3] callback redirect_to={redirect_to}")

                resp = make_response(redirect(redirect_to))

                # ✅ 清掉 next cookie，避免下次污染
                resp.set_cookie("sso_next_path", "", expires=0, path="/")

                # cookies（保留你原本做法）
                resp.set_cookie('preferred_username', quote(preferred_username) if preferred_username else '', max_age=7200, path='/')
                resp.set_cookie('family_name', quote(family_name) if family_name else '', max_age=7200, path='/')
                resp.set_cookie('email', quote(email) if email else '', max_age=7200, path='/')
                resp.set_cookie('dep', quote(dep) if dep else '', max_age=7200, path='/')
                resp.set_cookie('client_secret', client_secret, max_age=7200, path='/')
                resp.set_cookie('logout_url', logout_url, max_age=7200, path='/')
                return resp
            else:
                return "client_secret錯誤"

    def logout(self):
        """登出：保存原始頁面，重定向到 SSO logout"""
        logout_url_cookie = request.cookies.get('logout_url')
        if not logout_url_cookie:
            return redirect("/")
        
        # ✅ 保存當前頁面到 cookie（從 Referer 提取）
        origin_path = request.headers.get('Referer', '/')
        try:
            origin_path = urlparse(origin_path).path or "/"
        except:
            origin_path = "/"
        
        # ★ PRINT-LOGOUT-1：顯示登出來源頁（在 redirect 上面）
        print(f"[SSO][PRINT-LOGOUT-1] 登出來源頁: {origin_path}")
        
        resp = make_response(redirect(logout_url_cookie))
        
        # 清除所有登入相關 cookies
        resp.set_cookie('preferred_username', '', expires=0, path='/')
        resp.set_cookie('family_name', '', expires=0, path='/')
        resp.set_cookie('email', '', expires=0, path='/')
        resp.set_cookie('dep', '', expires=0, path='/')
        resp.set_cookie('client_secret', '', expires=0, path='/')
        resp.set_cookie('logout_url', '', expires=0, path='/')
        
        # ⚠️ 重要：logout_next 一定要最後設置，避免被上面清掉
        resp.set_cookie('logout_next', origin_path, max_age=300, path='/')
        
        return resp

    def logout_callback(self):
        """登出回調：重定向到原始頁面"""
        next_path = request.cookies.get('logout_next', '/')
        
        # ★ PRINT-LOGOUT-2：顯示登出完成的返回頁面（在 redirect 上面）
        print(f"[SSO][PRINT-LOGOUT-2] 登出完成，返回: {next_path}")
        
        resp = make_response(redirect(next_path))
        
        # 清除 logout_next cookie
        resp.set_cookie('logout_next', '', expires=0, path='/')
        
        return resp

    def logout_cookie(self):
        resp = make_response()
        resp.set_cookie('preferred_username', '', expires=0, path='/')
        resp.set_cookie('family_name', '', expires=0, path='/')
        resp.set_cookie('email', '', expires=0, path='/')
        resp.set_cookie('dep', '', expires=0, path='/')
        resp.set_cookie('client_secret', '', expires=0, path='/')
        resp.set_cookie('logout_url', '', expires=0, path='/')
        return f'''
        <h1>您已成功登出</h1>
        <button class="button is-primary" onclick="location.href='{request.url_root}'" type="button">點擊這裡重新登入</button>
        '''

    def logined(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.cookies.get('preferred_username'):
                return self.login()
            return f(*args, **kwargs)
        return decorated_function
