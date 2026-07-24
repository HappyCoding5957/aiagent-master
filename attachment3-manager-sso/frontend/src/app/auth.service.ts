import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { environment } from '../environments/environment';

export interface UserInfo {
  family_name: string;
  preferred_username: string;
  dep: string;
  email: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiBase = environment.apiUrl;
  private userInfo: UserInfo | null = null;

  constructor(private http: HttpClient) {}

  /**
   * 檢查用戶是否已登入（通過呼叫後端 API）
   * 如果後端返回 401，表示未登入
   */
  checkAuthStatus(): Observable<boolean> {
    return this.http.get(`${this.apiBase}/api/status`, {
      withCredentials: true
    }).pipe(
      map(() => {
        // API 呼叫成功，表示已登入
        this.loadUserInfoFromCookies();
        return true;
      }),
      catchError((error) => {
        // 401 或其他錯誤，表示未登入
        console.log('[AuthService] 認證檢查失敗:', error.status);
        return of(false);
      })
    );
  }

  /**
   * 從 Cookie 載入用戶資訊
   */
  loadUserInfoFromCookies(): void {
    const familyName = this.getCookie('family_name');
    const preferredUsername = this.getCookie('preferred_username');
    const dep = this.getCookie('dep');
    const email = this.getCookie('email');

    if (preferredUsername) {
      this.userInfo = {
        family_name: decodeURIComponent(familyName || '未知用戶'),
        preferred_username: decodeURIComponent(preferredUsername),
        dep: decodeURIComponent(dep || ''),
        email: decodeURIComponent(email || '')
      };
    }
  }

  /**
   * 取得 Cookie
   */
  private getCookie(name: string): string {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop()?.split(';').shift() || '';
    }
    return '';
  }

  /**
   * 取得當前用戶資訊
   */
  getUserInfo(): UserInfo | null {
    return this.userInfo;
  }

  /**
   * 重定向到 SSO 登入頁面
   */
  redirectToLogin(): void {
    console.log('[AuthService] 重定向到 SSO 登入頁面');
    window.location.href = `${this.apiBase}/login`;
  }

  /**
   * 登出
   */
  logout(): void {
    if (confirm('確定要登出嗎？')) {
      window.location.href = `${this.apiBase}/logout`;
    }
  }
}
