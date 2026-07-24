"""
產生示範用的問卷 Excel（純合成資料，虛構公司 Acme Manufacturing）。
知識庫的 3 份政策文件（policy_*.txt）已經是純文字，直接放在
sample_data/knowledge/ 底下即可，不需要另外產生。
"""

from pathlib import Path

from openpyxl import Workbook

QUESTIONS = [
    ("Q1", "貴公司是否已取得 ISO 27001 資訊安全管理系統認證？請說明證書編號與有效期。"),
    ("Q2", "貴公司是否設有專職的資訊安全長（CISO）或同等職位？"),
    ("Q3", "貴公司員工多久進行一次資訊安全教育訓練？"),
    ("Q4", "貴公司是否遵循 GDPR 或當地個人資料保護法規？"),
    ("Q5", "客戶個人資料的存取紀錄會保留多久？"),
    ("Q6", "貴公司的系統復原時間目標（RTO）與復原點目標（RPO）分別是多久？"),
    ("Q7", "貴公司是否投保網路資安保險（Cyber Insurance）？"),
    ("Q8", "個資外洩事件應於多久內通報主管機關？"),
    ("Q9", "貴公司的核心系統備份頻率與備份地點為何？"),
    ("Q10", "貴公司是否有量子加密相關的專利技術？"),  # 故意放一題知識庫沒有答案的題目，驗證「證據不足」邏輯
]


def main():
    wb = Workbook()
    ws = wb.active
    ws.title = "Security Questionnaire"

    ws.append(["題號", "問題", "供應商回覆", "備註"])
    for qid, qtext in QUESTIONS:
        ws.append([qid, qtext, "", ""])

    out_path = Path(__file__).parent / "questionnaire.xlsx"
    wb.save(out_path)
    print(f"已產生範例問卷：{out_path}")


if __name__ == "__main__":
    main()
