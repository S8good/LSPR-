from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_cnn_predict_menu_entry_removed_from_menu_bar():
    menu_bar_source = (PROJECT_ROOT / "nanosense" / "gui" / "menu_bar.py").read_text(encoding="utf-8")

    assert "Single Spectrum CNN Predict Compare..." not in menu_bar_source
    assert "cnn_predict_compare_action" not in menu_bar_source


def test_legacy_cnn_predict_hook_removed_from_main_window():
    main_window_source = (PROJECT_ROOT / "nanosense" / "gui" / "main_window.py").read_text(encoding="utf-8")

    assert "_trigger_cnn_predict_compare" not in main_window_source
    assert "cnn_predict_compare_action" not in main_window_source


def test_lspr_ai_workbench_action_added_to_menu_bar():
    menu_bar_source = (PROJECT_ROOT / "nanosense" / "gui" / "menu_bar.py").read_text(encoding="utf-8")

    assert "lspr_ai_workbench_action" in menu_bar_source
    assert "LSPR AI Workbench..." in menu_bar_source
