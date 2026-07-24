import { Component, OnInit, HostListener } from '@angular/core';
import { HttpClient, HttpEventType } from '@angular/common/http';
import { interval } from 'rxjs';
import { environment } from '../environments/environment';
import { AuthService } from './auth.service';

interface StatusData {
  exists: boolean;
  pdf_id?: string;
  name?: string;
  chunk_count?: number;
  last_update?: string;
  unit?: string;
}

interface ProgressData {
  stage: string;
  percent: number;
  message: string;
  timestamp?: string;
}

interface UploadResult {
  success: boolean;
  pdf_id?: string;
  pdf_name?: string;
  chunk_count?: number;
  unit?: string;
  error?: string;
}

interface DeleteResult {
  success: boolean;
  deleted_chunks: number;
  deleted_files: number;
  message: string;
}

interface AlertInfo {
  message: string;
  type: 'success' | 'error' | 'info';
  show: boolean;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  // API 基礎 URL
  apiBase = environment.apiUrl;

  // 狀態資料
  statusData: StatusData = { exists: false };

  // 進度資料
  progressData: ProgressData = { stage: 'idle', percent: 0, message: '' };
  showProgress = false;
  progressInterval: any = null;

  // 提示訊息
  alert: AlertInfo = { message: '', type: 'info', show: false };

  // 上傳檔案
  selectedFile: File | null = null;

  // 用戶資訊
  userInfo: any = null;

  // Help Modal 控制
  showHelpModal = false;
  currentSopPage = 1;

  // 階段名稱對應
  stageNames: { [key: string]: string } = {
    'init': '初始化',
    'reading': '讀取檔案',
    'embedding': '生成向量',
    'database': '寫入資料庫',
    'complete': '完成',
    'error': '錯誤',
    'idle': '閒置'
  };

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  ngOnInit() {
    // ✅ 啟動時立即檢查 SSO 認證狀態
    console.log('[AppComponent] 檢查 SSO 認證狀態...');
    this.authService.checkAuthStatus().subscribe({
      next: (isAuthenticated) => {
        if (!isAuthenticated) {
          // 未登入，立即重定向到 SSO 登入頁面
          console.log('[AppComponent] 未登入，重定向到 SSO...');
          this.authService.redirectToLogin();
        } else {
          // 已登入，載入應用資料
          console.log('[AppComponent] 已登入，載入應用資料');
          this.loadUserInfo();
          this.checkStatus();
        }
      },
      error: (error) => {
        console.error('[AppComponent] 認證檢查失敗:', error);
        this.authService.redirectToLogin();
      }
    });
  }

  // ESC 鍵關閉 Help Modal
  @HostListener('document:keydown.escape', [''])
  onEscapeKey(event: KeyboardEvent) {
    if (this.showHelpModal) {
      this.closeHelpModal();
    }
  }

  // 從 Cookie 載入用戶資訊
  loadUserInfo() {
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

  // 取得 Cookie
  getCookie(name: string): string {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop()?.split(';').shift() || '';
    }
    return '';
  }

  // 登出
  logout() {
    this.authService.logout();
  }

  // ========== Help Modal 控制 ==========
  openHelpModal() {
    this.showHelpModal = true;
    this.currentSopPage = 1;
  }

  closeHelpModal() {
    this.showHelpModal = false;
  }

  nextPage() {
    if (this.currentSopPage < 2) {
      this.currentSopPage++;
    }
  }

  previousPage() {
    if (this.currentSopPage > 1) {
      this.currentSopPage--;
    }
  }

  // 檢查知識庫狀態
  checkStatus() {
    this.http.get<StatusData>(`${this.apiBase}/api/status`, { withCredentials: true }).subscribe({
      next: (data) => {
        this.statusData = data;
      },
      error: (error) => {
        console.error('檢查狀態失敗:', error);
        // 如果是 401 未授權，立即重定向到 SSO 登入頁面
        if (error.status === 401) {
          console.log('[checkStatus] Session 已過期，重定向到 SSO');
          this.authService.redirectToLogin();
        } else {
          this.showAlert('⚠️ 連線失敗', 'error');
        }
      }
    });
  }

  // 選擇檔案
  onFileSelected(event: any) {
    console.log('[DEBUG] onFileSelected() called');
    console.log('[DEBUG] Event:', event);
    console.log('[DEBUG] Files:', event.target.files);

    const file = event.target.files[0];
    console.log('[DEBUG] Selected file:', file);

    if (file && file.name.endsWith('.xlsx')) {
      this.selectedFile = file;
      console.log('[DEBUG] File accepted:', file.name);
    } else {
      console.error('[DEBUG] File rejected:', file ? file.name : 'no file');
      this.showAlert('❌ 請選擇 .xlsx 檔案', 'error');
      this.selectedFile = null;
    }
  }

  // 上傳檔案
  uploadFile() {
    console.log('[DEBUG] uploadFile() called');
    console.log('[DEBUG] selectedFile:', this.selectedFile);

    if (!this.selectedFile) {
      console.error('[DEBUG] No file selected!');
      this.showAlert('❌ 請選擇檔案', 'error');
      return;
    }

    console.log('[DEBUG] File info:', {
      name: this.selectedFile.name,
      size: this.selectedFile.size,
      type: this.selectedFile.type
    });

    const formData = new FormData();
    formData.append('file', this.selectedFile);
    console.log('[DEBUG] FormData created');

    // 開始輪詢進度
    this.startProgressPolling();
    console.log('[DEBUG] Progress polling started');

    const uploadUrl = `${this.apiBase}/api/upload`;
    console.log('[DEBUG] Upload URL:', uploadUrl);
    console.log('[DEBUG] Sending POST request...');

    this.http.post<UploadResult>(uploadUrl, formData, { withCredentials: true }).subscribe({
      next: (result) => {
        console.log('[DEBUG] Upload response received:', result);
        if (result.success) {
          console.log('[DEBUG] Upload successful! 後台處理中，請等待進度完成...');
        } else {
          console.error('[DEBUG] Upload failed:', result.error);
          this.stopProgressPolling();
          this.showAlert(`❌ 上傳失敗：${result.error}`, 'error');
        }
      },
      error: (error) => {
        console.error('[DEBUG] HTTP Error:', error);
        console.error('[DEBUG] Error status:', error.status);
        console.error('[DEBUG] Error message:', error.message);
        console.error('[DEBUG] Error details:', JSON.stringify(error, null, 2));
        this.stopProgressPolling();
        if (error.status === 401) {
          console.log('[uploadFile] Session 已過期，重定向到 SSO');
          this.authService.redirectToLogin();
        } else {
          this.showAlert(`❌ 上傳失敗：${error.message || error.statusText || '未知錯誤'}`, 'error');
        }
      }
    });
  }

  // 刪除知識庫
  deleteKnowledgeBase() {
    if (!confirm('⚠️ 確定要刪除附件三知識庫嗎？\n\n此操作將刪除所有相關資料，且無法復原！')) {
      return;
    }

    this.http.delete<DeleteResult>(`${this.apiBase}/api/delete`, { withCredentials: true }).subscribe({
      next: (result) => {
        if (result.success) {
          this.showAlert(
            `✅ 刪除成功！<br>已刪除 ${result.deleted_chunks} 個 chunks 和 ${result.deleted_files} 個 files`,
            'success'
          );
          this.checkStatus();
        } else {
          this.showAlert('❌ 刪除失敗', 'error');
        }
      },
      error: (error) => {
        console.error('刪除失敗:', error);
        if (error.status === 401) {
          console.log('[deleteKnowledgeBase] Session 已過期，重定向到 SSO');
          this.authService.redirectToLogin();
        } else {
          this.showAlert(`❌ 刪除失敗：${error.message}`, 'error');
        }
      }
    });
  }

  // 開始輪詢進度
  startProgressPolling() {
    this.showProgress = true;
    this.progressInterval = setInterval(() => {
      this.checkProgress();
    }, 1000);
  }

  // 停止輪詢進度
  stopProgressPolling() {
    if (this.progressInterval) {
      clearInterval(this.progressInterval);
      this.progressInterval = null;
    }
    setTimeout(() => {
      this.showProgress = false;
    }, 2000);
  }

  // 查詢進度
  checkProgress() {
    this.http.get<ProgressData>(`${this.apiBase}/api/progress`, { withCredentials: true }).subscribe({
      next: (progress) => {
        console.log('[DEBUG] Progress update:', progress);
        this.progressData = progress;

        // ✅ 如果完成或錯誤，停止輪詢並顯示結果
        if (progress.stage === 'complete') {
          console.log('[DEBUG] Upload complete! Stopping polling...');
          this.stopProgressPolling();
          this.showAlert('✅ 上傳完成！', 'success');
          this.selectedFile = null;
          this.checkStatus();
        } else if (progress.stage === 'error') {
          console.log('[DEBUG] Upload error! Stopping polling...');
          this.stopProgressPolling();
          this.showAlert(`❌ 上傳失敗：${progress.message}`, 'error');
        }
      },
      error: (error) => {
        console.error('查詢進度失敗:', error);
        if (error.status === 401) {
          this.stopProgressPolling();
          console.log('[checkProgress] Session 已過期，重定向到 SSO');
          this.authService.redirectToLogin();
        }
      }
    });
  }

  // 顯示提示訊息
  showAlert(message: string, type: 'success' | 'error' | 'info') {
    this.alert = { message, type, show: true };
    setTimeout(() => {
      this.alert.show = false;
    }, 5000);
  }

  // 取得階段名稱
  getStageName(stage: string): string {
    return this.stageNames[stage] || stage;
  }

  // 取得格式化的最後更新時間
  getFormattedDate(dateStr?: string): string {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-TW');
  }
}
