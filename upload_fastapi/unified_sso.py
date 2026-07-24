"""
統一 FastAPI SSO 中間件
適用於所有服務：Upload, Download, PaddleOCR

核心特性：
1. 根據請求路徑自動判斷 callback URL
2. 使用 state 參數保存 next_path（避免 cookie 跨域問題）
3. 統一的 logout 處理
"""
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse, Response
from urllib.parse import quote, unquote
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class UnifiedSSO:
    """統一 SSO 認證中間件"""
    
    def __init__(self, app, config: dict):
        """
        初始化 SSO
        
        config = {
            "realm": "Infra",
            "client_id": "MeetBook",
            "client_secret": "xxx",
            "frontend_url": "https://ssw01.ennostar.com",
            "sso_api": "http://espython-sso-api.epistar.com.tw:8080"
        }
        """
        self.app = app
        self.realm = config["realm"]
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.frontend_url = config["frontend_url"].rstrip("/")
        self.sso_api = config["sso_api"]
        
        # 註冊統一路由
        self.app.add_api_route("/login", self.login, methods=["GET", "POST"])
        self.app.add_api_route("/callback", self.callback, methods=["GET", "POST"])
        self.app.add_api_route("/logout", self.logout, methods=["GET"])
        self.app.add_api_route("/logout_callback", self.logout_callback, methods=["GET"])
    
    def _get_service_from_path(self, path: str) -> str:
        """根據路徑判斷服務"""
        if path.startswith("/esg/upload"):
            return "upload"
        elif path.startswith("/esg/download"):
            return "download"
        elif path.startswith("/paddleocr"):
            return "paddleocr"
        else:
            return "unknown"
    
    def _get_default_path(self, service: str) -> str:
        """獲取服務的預設路徑"""
        defaults = {
            "upload": "/esg/upload/",
            "download": "/esg/download/",
            "paddleocr": "/paddleocr/query/",
        }
        return defaults.get(service, "/")
    
    def login(self, request: Request):
        """統一登入入口"""
        # 獲取 next 參數或從 Referer 推斷
        next_path = request.query_params.get("next")
        
        if not next_path:
            referer = request.headers.get("referer", "")
            if referer:
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                next_path = parsed.path or "/"
            else:
                next_path = request.url.path
        
        # 如果是 /login 本身，根據來源判斷
        if next_path == "/login":
            referer = request.headers.get("referer", "")
            if referer:
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                next_path = parsed.path or "/"
            else:
                next_path = "/"
        
        # 確保路徑有效
        if not next_path.startswith("/"):
            next_path = "/"
        
        logger.info(f"[SSO] Login request - path={request.url.path}, next={next_path}")
        
        # 構建 SSO 登入 URL
        callback_url = f"{self.frontend_url}/callback"
        state = quote(next_path, safe="")
        
        login_url = (
            f"{self.sso_api}"
            f"?realm={self.realm}"
            f"&client_id={self.client_id}"
            f"&callback_url={callback_url}"
            f"&state={state}"
        )
        
        resp = RedirectResponse(login_url, status_code=302)
        # 備援：也設置 cookie
        resp.set_cookie("sso_next_path", quote(next_path, safe=""), max_age=300, path="/")
        
        return resp
    
    async def callback(self, request: Request):
        """統一 callback 處理"""
        if request.method == "GET":
            code = request.query_params.get("code")
            if code == "None":
                return Response("SSO Service Down", status_code=503)
        
        elif request.method == "POST":
            form = await request.form()
            
            # 驗證 client_secret
            client_secret = form.get("client_secret")
            if client_secret != self.client_secret:
                raise HTTPException(status_code=401, detail="Invalid client_secret")
            
            # 獲取用戶資訊
            preferred_username = form.get("preferred_username", "")
            family_name = form.get("family_name", "")
            email = form.get("email", "")
            dep = form.get("dep", "")
            refresh_token = form.get("refresh_token", "")
            
            # 獲取 next_path：優先使用 cookie（因為 espython-sso-api 不轉發 state）
            cookie_next = request.cookies.get("sso_next_path", "/")
            state = (form.get("state") or request.query_params.get("state") or "").strip()
            
            # 優先使用 cookie，fallback 到 state
            next_path = unquote(cookie_next) if cookie_next and cookie_next != "/" else (unquote(state) if state else "/")
            
            if not next_path or not next_path.startswith("/"):
                next_path = "/"
            
            logger.info(f"[SSO] Callback - state={state or 'N/A'}, cookie={cookie_next}, final_next={next_path}")
            
            # 構建 logout URL
            logout_url = (
                f"{self.sso_api}/logout"
                f"?realm={self.realm}"
                f"&client_id={self.client_id}"
                f"&callback_url={self.frontend_url}/logout_callback"
                f"&refresh_token={refresh_token}"
            )
            
            # 設置 cookies 並重定向
            resp = RedirectResponse(next_path, status_code=302)
            
            cookie_config = {
                "httponly": True,
                "samesite": "lax",
                "max_age": 14400,  # 4小時
                "path": "/",
            }
            
            resp.set_cookie("preferred_username", quote(preferred_username), **cookie_config)
            resp.set_cookie("family_name", quote(family_name), **cookie_config)
            resp.set_cookie("email", quote(email), **cookie_config)
            resp.set_cookie("dep", quote(dep), **cookie_config)
            resp.set_cookie("client_secret", client_secret, **cookie_config)
            resp.set_cookie("logout_url", logout_url, **cookie_config)
            
            # 清除 sso_next_path
            resp.delete_cookie("sso_next_path", path="/")
            
            return resp
        
        return Response("Invalid Request", status_code=400)
    
    def logout(self, request: Request):
        """統一登出"""
        logout_url_cookie = request.cookies.get("logout_url")
        
        if not logout_url_cookie:
            logger.warning("[SSO] Logout - no logout_url cookie, redirect to login")
            return RedirectResponse("/login", status_code=302)
        
        # 從 Referer 獲取原始頁面
        referer = request.headers.get("referer", "")
        origin_path = "/"
        
        if referer:
            from urllib.parse import urlparse
            try:
                parsed = urlparse(referer)
                origin_path = parsed.path or "/"
            except:
                pass
        
        logger.info(f"[SSO] Logout - origin_path={origin_path}")
        
        # 在 logout_url 中加入 state
        logout_url_with_state = f"{logout_url_cookie}&state={quote(origin_path, safe='')}"
        
        resp = RedirectResponse(logout_url_with_state, status_code=302)
        
        # 設置 logout_next cookie 作為備援
        resp.set_cookie("logout_next", origin_path, max_age=300, path="/")
        
        # 清除登入相關 cookies
        for cookie_name in ["preferred_username", "family_name", "email", "dep", "client_secret", "logout_url"]:
            resp.delete_cookie(cookie_name, path="/")
        
        return resp
    
    def logout_callback(self, request: Request):
        """統一登出回調"""
        # 優先使用 state，其次使用 cookie
        state = request.query_params.get("state", "").strip()
        cookie_next = request.cookies.get("logout_next", "/")
        
        next_path = unquote(state) if state else cookie_next
        
        if not next_path or not next_path.startswith("/"):
            next_path = "/"
        
        logger.info(f"[SSO] Logout callback - state={state or 'N/A'}, cookie={cookie_next}, final_next={next_path}")
        
        resp = RedirectResponse(next_path, status_code=302)
        resp.delete_cookie("logout_next", path="/")
        
        return resp
    
    def get_current_user(self, request: Request) -> Optional[dict]:
        """獲取當前登入用戶"""
        username = request.cookies.get("preferred_username")
        if not username:
            return None
        
        return {
            "preferred_username": unquote(username),
            "family_name": unquote(request.cookies.get("family_name", "")),
            "email": unquote(request.cookies.get("email", "")),
            "dep": unquote(request.cookies.get("dep", "")),
        }
    
    def require_login(self, request: Request):
        """要求登入裝飾器"""
        user = self.get_current_user(request)
        if not user:
            # 重定向到登入頁，並帶上當前路徑
            login_url = f"/login?next={quote(str(request.url.path), safe='')}"
            raise HTTPException(
                status_code=307,  # Temporary Redirect
                detail="Not authenticated",
                headers={"Location": login_url}
            )
        return user
