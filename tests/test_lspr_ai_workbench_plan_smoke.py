from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from nanosense.utils.config_manager import get_default_settings


def test_default_settings_include_lspr_ai_workbench_keys():
    settings = get_default_settings()

    assert settings["lspr_master_root"] == ""
    assert settings["lspr_default_model_mode"] == "auto"
    assert settings["lspr_default_artifact_dir"] == ""
    assert settings["lspr_enable_digital_twin_overlay"] is True
    assert settings["lspr_batch_export_dir"] == ""


def test_settings_dialog_contains_lspr_ai_controls():
    settings_dialog_source = (PROJECT_ROOT / "nanosense" / "gui" / "settings_dialog.py").read_text(encoding="utf-8")

    assert "LSPR AI" in settings_dialog_source
    assert "lspr_master_root" in settings_dialog_source
    assert "lspr_default_model_mode" in settings_dialog_source
    assert "lspr_default_artifact_dir" in settings_dialog_source
    assert "lspr_batch_export_dir" in settings_dialog_source
    assert "lspr_enable_digital_twin_overlay" in settings_dialog_source


def test_main_window_wires_lspr_ai_workbench_opening():
    main_window_source = (PROJECT_ROOT / "nanosense" / "gui" / "main_window.py").read_text(encoding="utf-8")

    assert "_open_lspr_ai_workbench" in main_window_source
    assert "lspr_ai_workbench_action" in main_window_source
    assert "lspr_workbench_window" in main_window_source
    assert "LSPRAIAnalysisWindow" in main_window_source


def test_new_lspr_ai_analysis_window_copies_analysis_capabilities():
    workbench_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_ai_analysis_window.py"
    ).read_text(encoding="utf-8")

    assert "QListWidget" in workbench_source
    assert "PlotWidget" in workbench_source
    assert "preprocessing_enabled_checkbox" in workbench_source
    assert "baseline_checkbox" in workbench_source
    assert "smoothing_checkbox" in workbench_source
    assert "set_input_spectrum" in workbench_source
    assert "comparison_widget" in workbench_source
    assert "summary_widget" in workbench_source
    assert "analysis_target_combo" in workbench_source
    assert "select_all_button" in workbench_source
    assert "deselect_all_button" in workbench_source
    assert "export_plot_button" in workbench_source
    assert "peak_method_combo" in workbench_source
    assert "find_main_peak_button" in workbench_source
    assert "main_peak_wavelength_label" in workbench_source
    assert "main_peak_fwhm_label" in workbench_source
    assert "comparison_metrics_row" in workbench_source
    assert "comparison_concentration_label" in workbench_source
    assert "comparison_scale_label" in workbench_source
    assert "comparison_offset_label" in workbench_source
    assert "comparison_report_mode_label" in workbench_source
    assert "Digital Twin" in workbench_source
    assert "lspr_digital_twin_widget" in workbench_source
    assert "Model Comparison" in workbench_source
    assert "Batch Prediction" in workbench_source
    assert "lspr_model_comparison_widget" in workbench_source
    assert "lspr_batch_prediction_widget" in workbench_source


def test_digital_twin_widget_exists_with_minimal_controls():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_digital_twin_widget.py"
    ).read_text(encoding="utf-8")

    assert "Generate Digital Twin" in widget_source
    assert "concentration_spinbox" in widget_source
    assert "concentration_slider" in widget_source
    assert "digital_twin_plot" in widget_source
    assert "peak_wavelength_label" in widget_source
    assert "delta_lambda_label" in widget_source
    assert "peak_intensity_label" in widget_source
    assert "_sync_slider_to_spinbox" in widget_source
    assert "_sync_spinbox_to_slider" in widget_source
    assert "overlay_experimental_checkbox" in widget_source
    assert "set_experimental_spectrum" in widget_source
    assert "export_plot_button" in widget_source
    assert "_export_current_plot" in widget_source
    assert "_update_status_text" in widget_source
    assert "_last_result" in widget_source


def test_comparison_widget_supports_curve_visibility_toggles():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_spectrum_comparison_widget.py"
    ).read_text(encoding="utf-8")

    assert "show_input_checkbox" in widget_source
    assert "show_generated_checkbox" in widget_source
    assert "show_aligned_checkbox" in widget_source
    assert "_refresh_curve_visibility" in widget_source
    assert "export_plot_button" in widget_source
    assert "_export_current_plot" in widget_source
    assert "_update_status_text" in widget_source


def test_analysis_window_uses_lazy_service_creation():
    workbench_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_ai_analysis_window.py"
    ).read_text(encoding="utf-8")

    assert "def _get_service" in workbench_source
    assert "self._service = None" in workbench_source


def test_single_prediction_widget_supports_importing_a_spectrum_file():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_ai_analysis_window.py"
    ).read_text(encoding="utf-8")

    assert "Import Spectrum..." in widget_source
    assert "load_spectrum(" in widget_source
    assert "source_file" in widget_source


def test_analysis_window_supports_selection_controls_and_plot_export():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_ai_analysis_window.py"
    ).read_text(encoding="utf-8")

    assert "_select_all_spectra" in widget_source
    assert "_deselect_all_spectra" in widget_source
    assert "_update_curve_visibility" in widget_source
    assert "_export_current_plot" in widget_source
    assert "_find_main_peak" in widget_source
    assert "_apply_comparison_result" in widget_source


def test_model_comparison_widget_exists_with_minimal_controls():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_model_comparison_widget.py"
    ).read_text(encoding="utf-8")

    assert "Run Model Comparison" in widget_source
    assert "comparison_table" in widget_source
    assert "comparison_plot" in widget_source


def test_batch_prediction_widget_exists_with_minimal_controls():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_batch_prediction_widget.py"
    ).read_text(encoding="utf-8")

    assert "Load Folder..." in widget_source
    assert "Load Multi-column File..." in widget_source
    assert "Run Batch Prediction" in widget_source
    assert "results_table" in widget_source
