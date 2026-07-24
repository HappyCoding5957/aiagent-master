"""煙霧測試 (Smoke Test)：確保整條 pipeline 可以從頭跑到尾，不看準確率，只看跑不跑得通。"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def test_generate_sample_runs():
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / "sample_data" / "generate_sample.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (BASE_DIR / "sample_data" / "questionnaire.xlsx").exists()


def test_pipeline_end_to_end():
    from src.pipeline import run_pipeline

    summary = run_pipeline(
        questionnaire_path=str(BASE_DIR / "sample_data" / "questionnaire.xlsx"),
        knowledge_dir=str(BASE_DIR / "sample_data" / "knowledge"),
        output_dir=str(BASE_DIR / "output"),
    )

    assert summary["total_questions"] == 10
    assert summary["knowledge_chunks_loaded"] > 0
    assert Path(summary["output_excel"]).exists()
    assert Path(summary["output_audit_json"]).exists()
    # 至少要能自動通過或建議覆核幾題，不能全部都是查無證據
    assert summary["auto_approved"] + summary["review_suggested"] >= 1
