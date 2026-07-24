"""
一鍵跑完整 pipeline 的 demo 腳本，也是錄 90 秒影片時可以直接
展示終端機輸出的地方。跑完會印出自動化率、各狀態題數統計。
"""

from pathlib import Path

from src.pipeline import run_pipeline

BASE_DIR = Path(__file__).parent
QUESTIONNAIRE = BASE_DIR / "sample_data" / "questionnaire.xlsx"
KNOWLEDGE_DIR = BASE_DIR / "sample_data" / "knowledge"
OUTPUT_DIR = BASE_DIR / "output"


def main():
    if not QUESTIONNAIRE.exists():
        print("找不到範例問卷，請先執行：python sample_data/generate_sample.py")
        return

    print("=" * 60)
    print("DocAgent Demo — Acme Manufacturing Security Questionnaire")
    print("=" * 60)

    summary = run_pipeline(
        questionnaire_path=str(QUESTIONNAIRE),
        knowledge_dir=str(KNOWLEDGE_DIR),
        output_dir=str(OUTPUT_DIR),
    )

    print(f"知識庫載入片段數：{summary['knowledge_chunks_loaded']}")
    print(f"問卷總題數：      {summary['total_questions']}")
    print(f"自動通過：        {summary['auto_approved']} 題")
    print(f"建議人工覆核：    {summary['review_suggested']} 題")
    print(f"證據不足：        {summary['insufficient_evidence']} 題")
    print(f"自動化率：        {summary['automation_rate'] * 100:.1f}%")
    print(f"自動通過率：      {summary['auto_approve_rate'] * 100:.1f}%")
    print(f"回填後 Excel：    {summary['output_excel']}")
    print(f"稽核報告 JSON：   {summary['output_audit_json']}")


if __name__ == "__main__":
    main()
