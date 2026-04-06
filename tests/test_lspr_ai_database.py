from pathlib import Path
import sqlite3
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from nanosense.core.database_manager import DatabaseManager


def _fresh_manager(db_path):
    DatabaseManager._instance = None
    manager = DatabaseManager(str(db_path))
    return manager


def test_save_lspr_ai_prediction_creates_analysis_run_and_metrics(tmp_path):
    db_path = tmp_path / "lspr.db"
    manager = _fresh_manager(db_path)
    project_id = manager.find_or_create_project("Demo")
    experiment_id = manager.create_experiment(project_id, "Exp 1", "LSPR", "2025-01-01 10:00:00")

    analysis_run_id = manager.save_lspr_ai_prediction(
        experiment_id=experiment_id,
        metrics={
            "predicted_concentration_ng_ml": 12.34,
            "report_mode": "quantitative",
            "reported_text": "12.3400 ng/ml",
            "peak_wavelength_nm": 612.5,
            "delta_lambda_nm": 2.5,
        },
        input_context={
            "model_mode": "v2",
            "backend_mode": "subprocess",
            "source_type": "file_import",
            "source_file": "demo.csv",
        },
    )

    assert analysis_run_id is not None

    row = manager.conn.execute(
        "SELECT analysis_type, input_context FROM analysis_runs WHERE analysis_run_id = ?",
        (analysis_run_id,),
    ).fetchone()
    assert row[0] == "lspr_ai_prediction"
    assert '"model_mode": "v2"' in row[1]

    metrics = dict(
        manager.conn.execute(
            "SELECT metric_key, metric_value FROM analysis_metrics WHERE analysis_run_id = ?",
            (analysis_run_id,),
        ).fetchall()
    )
    assert metrics["predicted_concentration_ng_ml"] == "12.34"
    assert metrics["report_mode"] == "quantitative"


def test_save_lspr_ai_prediction_returns_none_for_missing_connection(tmp_path):
    db_path = tmp_path / "lspr.db"
    manager = _fresh_manager(db_path)
    manager.close()

    result = manager.save_lspr_ai_prediction(
        experiment_id=1,
        metrics={"predicted_concentration_ng_ml": 1.23},
        input_context={"model_mode": "auto"},
    )

    assert result is None
