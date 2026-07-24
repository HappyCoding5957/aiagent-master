"""
簡單的 Cookie 驗證模組
用於後端服務驗證 SSO cookie（由 Proxy 設置）
"""
from fastapi import Request, HTTPException
from urllib.parse import unquote
from typing import Optional


def get_current_user(request: Request) -> Optional[dict]:
    """
    從 cookie 獲取當前用戶資訊
    
    Returns:
        dict: 用戶資訊 {preferred_username, family_name, email, dep}
        None: 未登入
    """
    username = request.cookies.get("preferred_username")
    if not username:
        return None
    
    return {
        "preferred_username": unquote(username),
        "family_name": unquote(request.cookies.get("family_name", "")),
        "email": unquote(request.cookies.get("email", "")),
        "dep": unquote(request.cookies.get("dep", "")),
    }


def require_login(request: Request) -> dict:
    """
    要求登入的依賴注入函數
    
    用法：
        @app.get("/protected")
        async def protected_route(request: Request, user: dict = Depends(require_login)):
            return {"message": f"Hello {user['family_name']}"}
    
    未登入時拋出 307 重定向到 /login?next={當前路徑}
    """
    user = get_current_user(request)
    if not user:
        # 重定向到 Proxy 的統一登入入口
        login_url = f"/login?next={request.url.path}"
        raise HTTPException(
            status_code=307,
            detail="Not authenticated",
            headers={"Location": login_url}
        )
    return user


def check_cookie_auth(request: Request) -> bool:
    """
    簡單的 cookie 檢查（不拋出異常）
    
    Returns:
        bool: True 已登入，False 未登入
    """
    return bool(request.cookies.get("preferred_username"))
