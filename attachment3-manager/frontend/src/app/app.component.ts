import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpEventType } from '@angular/common/http';
import { interval } from 'rxjs';
import { environment } from '../environments/environment';

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

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.checkStatus();
  }

  // 檢查知識庫狀態
  checkStatus() {
    this.http.get<StatusData>(`${this.apiBase}/api/status`).subscribe({
      next: (data) => {
        this.statusData = data;
      },
      error: (error) => {
        console.error('檢查狀態失敗:', error);
        this.showAlert('⚠️ 連線失敗', 'error');
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

    this.http.post<UploadResult>(uploadUrl, formData).subscribe({
      next: (result) => {
        console.log('[DEBUG] Upload response received:', result);
        // ✅ 修正：POST 返回後不要停止輪詢，讓進度繼續更新
        // this.stopProgressPolling(); // ❌ 移除這行
        if (result.success) {
          console.log('[DEBUG] Upload successful! 後台處理中，請等待進度完成...');
          // 不顯示成功訊息，等進度完成再顯示
          // 輪詢會在 checkProgress() 中偵測 stage === 'complete' 時自動停止
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
        this.showAlert(`❌ 上傳失敗：${error.message || error.statusText || '未知錯誤'}`, 'error');
      }
    });
  }

  // 刪除知識庫
  deleteKnowledgeBase() {
    if (!confirm('⚠️ 確定要刪除附件三知識庫嗎？\n\n此操作將刪除所有相關資料，且無法復原！')) {
      return;
    }

    this.http.delete<DeleteResult>(`${this.apiBase}/api/delete`).subscribe({
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
        this.showAlert(`❌ 刪除失敗：${error.message}`, 'error');
        console.error('刪除失敗:', error);
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
    this.http.get<ProgressData>(`${this.apiBase}/api/progress`).subscribe({
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
