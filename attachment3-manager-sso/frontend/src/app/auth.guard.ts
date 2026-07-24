import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(private authService: AuthService) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> {
    console.log('[AuthGuard] 檢查認證狀態...');

    return this.authService.checkAuthStatus().pipe(
      map(isAuthenticated => {
        if (!isAuthenticated) {
          console.log('[AuthGuard] 未登入，重定向到 SSO 登入頁面');
          this.authService.redirectToLogin();
          return false;
        }

        console.log('[AuthGuard] 已登入，允許訪問');
        return true;
      })
    );
  }
}
