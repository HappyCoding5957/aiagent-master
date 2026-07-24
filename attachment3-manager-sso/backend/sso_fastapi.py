"""
FastAPI 版本的 SSO 認證模組
"""
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from urllib.parse import quote, unquote


class KeycloakFastAPI:
    """FastAPI 版本的 Keycloak SSO 認證"""

    def __init__(self, realm: str, client_id: str, client_secret: str):
        self.pythonsso_api = "http://espython-sso-api.epistar.com.tw:8080"
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret

    def get_login_url(self, host_url: str) -> str:
        """生成 SSO 登入 URL"""
        callback_url = f"{host_url}callback"
        login_url = f"{self.pythonsso_api}?realm={self.realm}&client_id={self.client_id}&callback_url={callback_url}"
        return login_url

    def get_user_info(self, request: Request) -> dict:
        """從 Cookie 取得用戶資訊"""
        preferred_username = request.cookies.get("preferred_username")
        family_name = request.cookies.get("family_name")
        email = request.cookies.get("email")
        dep = request.cookies.get("dep")

        if not preferred_username:
            return None

        return {
            "preferred_username": unquote(preferred_username) if preferred_username else "",
            "family_name": unquote(family_name) if family_name else "",
            "email": unquote(email) if email else "",
            "dep": unquote(dep) if dep else "",
        }

    def require_login(self, request: Request):
        """要求登入，如果未登入則拋出異常"""
        user_info = self.get_user_info(request)
        if not user_info:
            # 返回 401，前端會攔截並重定向到登入頁面
            raise HTTPException(
                status_code=401,
                detail="未登入或 Session 已過期，請先登入 SSO"
            )
        return user_info
