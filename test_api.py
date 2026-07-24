#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Security C API 完整流程
"""

import requests
import base64
import json
import sys

def test_api():
    """測試完整 API 流程"""

    print("=" * 80)
    print("測試 Security C API")
    print("=" * 80)

    # 1. 讀取附件二 Excel
    excel_file = "附件二.xlsx"
    print(f"\n[1] 讀取測試檔案: {excel_file}")

    try:
        with open(excel_file, "rb") as f:
            excel_bytes = f.read()
        print(f"    ✓ 檔案大小: {len(excel_bytes)} bytes")
    except FileNotFoundError:
        print(f"    ✗ 找不到檔案: {excel_file}")
        return False

    # 2. 轉換為 base64
    print("\n[2] 轉換為 base64")
    file_base64 = base64.b64encode(excel_bytes).decode('utf-8')
    print(f"    ✓ base64 長度: {len(file_base64)}")

    # 3. 呼叫 API
    print("\n[3] 呼叫 API: /api/security-c/match-from-base64")
    url = "http://127.0.0.1:5555/api/security-c/match-from-base64"

    payload = {
        "file_base64": file_base64,
        "client_name": "測試客戶_宏齊"
    }

    print("    發送請求中...")

    try:
        response = requests.post(url, json=payload, timeout=600)

        print(f"    ✓ HTTP 狀態碼: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            if result.get("success"):
                print("\n[4] API 回應成功")
                print(f"    ✓ 檔案名稱: {result.get('file_name')}")
                print(f"    ✓ base64 長度: {len(result.get('file_base64', ''))}")

                report = result.get("report", {})
                if report:
                    print("\n[5] 處理報告:")
                    print(f"    - 客戶名稱: {report.get('client_name')}")
                    print(f"    - 總題數: {report.get('total_questions')}")
                    print(f"    - 成功匹配: {report.get('matched_count')}")
                    print(f"    - 未匹配: {report.get('unmatched_count')}")
                    print(f"    - 低信心題目: {report.get('low_confidence_count')}")
                    print(f"    - 匹配率: {report.get('match_rate')}")

                # 6. 儲存結果檔案
                print("\n[6] 儲存結果檔案")
                output_file = "test_result.xlsx"
                result_bytes = base64.b64decode(result.get('file_base64'))

                with open(output_file, "wb") as f:
                    f.write(result_bytes)

                print(f"    ✓ 已儲存: {output_file} ({len(result_bytes)} bytes)")

                print("\n" + "=" * 80)
                print("✅ 測試成功！")
                print("=" * 80)
                return True

            else:
                print(f"\n✗ API 回應失敗: {result.get('error')}")
                return False
        else:
            print(f"\n✗ HTTP 錯誤 {response.status_code}")
            print(f"    回應內容: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"\n✗ 呼叫 API 失敗: {e}")
        return False


if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
