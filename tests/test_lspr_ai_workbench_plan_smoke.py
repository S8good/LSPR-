import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import nanosense.utils.config_manager as config_manager
from nanosense.ml.lspr_master_bridge import LSPRMasterBridge
from nanosense.utils.config_manager import get_default_settings, load_settings


def test_default_settings_include_lspr_ai_workbench_keys():
    settings = get_default_settings()

    assert settings["lspr_master_root"] == ""
    assert settings["lspr_backend_mode"] == "auto"
    assert settings["lspr_subprocess_python"] == ""
    assert settings["lspr_subprocess_timeout_seconds"] == 20
    assert settings["lspr_default_inference_model"] == "auto"
    assert settings["lspr_default_prediction_model"] == "auto"
    assert settings["lspr_default_generator_model"] == "auto"
    assert settings["lspr_default_artifact_dir"] == ""
    assert settings["lspr_enable_digital_twin_overlay"] is True
    assert settings["lspr_batch_export_dir"] == ""


def test_load_settings_migrates_legacy_lspr_default_model_mode_to_backend_mode(tmp_path, monkeypatch):
    config_dir = tmp_path / ".nanosense"
    config_file = config_dir / "config.json"
    config_dir.mkdir()
    config_file.write_text(
        json.dumps(
            {
                "lspr_default_model_mode": "subprocess",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config_manager, "CONFIG_DIR", str(config_dir))
    monkeypatch.setattr(config_manager, "CONFIG_FILE", str(config_file))

    settings = load_settings()

    assert settings["lspr_backend_mode"] == "subprocess"
    assert settings["lspr_default_inference_model"] == "auto"


def test_load_settings_migrates_legacy_lspr_default_model_mode_to_default_inference_model(tmp_path, monkeypatch):
    config_dir = tmp_path / ".nanosense"
    config_file = config_dir / "config.json"
    config_dir.mkdir()
    config_file.write_text(
        json.dumps(
            {
                "lspr_default_model_mode": "v2_fusion",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config_manager, "CONFIG_DIR", str(config_dir))
    monkeypatch.setattr(config_manager, "CONFIG_FILE", str(config_file))

    settings = load_settings()

    assert settings["lspr_backend_mode"] == "auto"
    assert settings["lspr_default_inference_model"] == "v2_fusion"


def test_settings_dialog_contains_lspr_ai_controls():
    settings_dialog_source = (PROJECT_ROOT / "nanosense" / "gui" / "settings_dialog.py").read_text(encoding="utf-8")

    assert "LSPR AI" in settings_dialog_source
    assert "lspr_master_root" in settings_dialog_source
    assert "lspr_backend_mode" in settings_dialog_source
    assert "lspr_subprocess_python" in settings_dialog_source
    assert "lspr_subprocess_timeout_seconds" in settings_dialog_source
    assert "lspr_default_inference_model" in settings_dialog_source
    assert "lspr_default_prediction_model" in settings_dialog_source
    assert "lspr_default_generator_model" in settings_dialog_source
    assert "lspr_default_artifact_dir" in settings_dialog_source
    assert "lspr_batch_export_dir" in settings_dialog_source
    assert "lspr_enable_digital_twin_overlay" in settings_dialog_source


def test_main_window_wires_lspr_ai_workbench_opening():
    main_window_source = (PROJECT_ROOT / "nanosense" / "gui" / "main_window.py").read_text(encoding="utf-8")

    assert "_open_lspr_ai_workbench" in main_window_source
    assert "lspr_ai_workbench_action" in main_window_source
    assert "lspr_workbench_window" in main_window_source
    assert "LSPRAIAnalysisWindow" in main_window_source
    assert "send_to_lspr_ai_requested.connect" in main_window_source
    assert "open_lspr_ai_requested.connect" in main_window_source


def test_workbench_module_is_compatibility_wrapper_for_analysis_window():
    workbench_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_ai_workbench.py"
    ).read_text(encoding="utf-8")

    assert "from .lspr_ai_analysis_window import LSPRAIAnalysisWindow" in workbench_source
    assert "class LSPRAIWorkbench(LSPRAIAnalysisWindow)" in workbench_source


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
    assert "prediction_model_label" in workbench_source
    assert "generator_model_label" in workbench_source
    assert "fallback_applied_label" in workbench_source
    assert "Digital Twin" in workbench_source
    assert "lspr_digital_twin_widget" in workbench_source
    assert "Model Comparison" in workbench_source
    assert "Batch Prediction" in workbench_source
    assert "lspr_model_comparison_widget" in workbench_source
    assert "lspr_batch_prediction_widget" in workbench_source
    assert "def refresh_theme" in workbench_source
    assert "self.setStyleSheet(" in workbench_source


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
    assert "_apply_theme_styles" in widget_source
    assert 'axis_color = "#000000" if theme == "light" else "#FFFFFF"' in widget_source


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
    assert "backend_mode_combo" in workbench_source
    assert "model_mode_combo" in workbench_source
    assert "generator_model_combo" in workbench_source
    assert "Backend:" in workbench_source
    assert "Prediction Model:" in workbench_source
    assert "Spectrum Generator:" in workbench_source
    assert "_get_service_for_backend_mode" in workbench_source


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


def test_analysis_window_refreshes_plot_when_preprocessing_toggles_change():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_ai_analysis_window.py"
    ).read_text(encoding="utf-8")

    assert "_on_preprocessing_controls_changed" in widget_source
    assert "self.preprocessing_enabled_checkbox.toggled.connect(self._on_preprocessing_controls_changed)" in widget_source
    assert "self.baseline_checkbox.toggled.connect(self._on_preprocessing_controls_changed)" in widget_source
    assert "self.smoothing_checkbox.toggled.connect(self._on_preprocessing_controls_changed)" in widget_source


def test_analysis_window_marks_peak_on_plot_and_clears_old_marker():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_ai_analysis_window.py"
    ).read_text(encoding="utf-8")

    assert "self.main_peak_marker = pg.ScatterPlotItem(" in widget_source
    assert "self.plot_widget.addItem(self.main_peak_marker)" in widget_source
    assert "self.main_peak_marker.clear()" in widget_source
    assert "self.main_peak_marker.setData([float(peak_wavelength)], [peak_intensity])" in widget_source


def test_analysis_and_comparison_plots_use_theme_aware_axis_colors():
    analysis_window_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_ai_analysis_window.py"
    ).read_text(encoding="utf-8")
    comparison_widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_spectrum_comparison_widget.py"
    ).read_text(encoding="utf-8")

    assert 'axis_color = "#000000" if theme == "light" else "#FFFFFF"' in analysis_window_source
    assert 'axis_color = "#000000" if theme == "light" else "#FFFFFF"' in comparison_widget_source

def test_model_comparison_widget_exists_with_minimal_controls():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_model_comparison_widget.py"
    ).read_text(encoding="utf-8")

    assert "Run Model Comparison" in widget_source
    assert "comparison_table" in widget_source
    assert "comparison_plot" in widget_source
    assert "model_selection_list" in widget_source
    assert "recommended_model_label" in widget_source
    assert "def refresh_theme" in widget_source
    assert "setBackground(" in widget_source


def test_batch_prediction_widget_exists_with_minimal_controls():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_batch_prediction_widget.py"
    ).read_text(encoding="utf-8")

    assert "Load Folder..." in widget_source
    assert "Load Multi-column File..." in widget_source
    assert "Run Batch Prediction" in widget_source
    assert "results_table" in widget_source
    assert "Export CSV..." in widget_source
    assert "row_activated" in widget_source
    assert "def refresh_theme" in widget_source


def test_analysis_window_connects_batch_rows_back_to_current_analysis_view():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "lspr_ai_analysis_window.py"
    ).read_text(encoding="utf-8")

    assert "row_activated.connect" in widget_source
    assert "_open_batch_prediction_detail" in widget_source


def test_measurement_widget_exposes_signal_for_sending_current_spectrum_to_lspr_ai():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "measurement_widget.py"
    ).read_text(encoding="utf-8")

    assert "send_to_lspr_ai_requested = pyqtSignal(dict)" in widget_source
    assert "Send to LSPR AI Workbench" in widget_source
    assert "send_to_lspr_ai_requested.emit" in widget_source


def test_database_explorer_supports_ai_runs_and_reopen_to_lspr_ai():
    widget_source = (
        PROJECT_ROOT / "nanosense" / "gui" / "database_explorer.py"
    ).read_text(encoding="utf-8")

    assert "open_lspr_ai_requested = pyqtSignal(dict)" in widget_source
    assert "AI Runs" in widget_source
    assert "_update_ai_runs_tab" in widget_source
    assert "_open_selected_lspr_ai" in widget_source
    assert "open_lspr_ai_requested.emit" in widget_source


def test_archived_ai_context_tracks_prediction_and_generator_models():
    database_manager_source = (
        PROJECT_ROOT / "nanosense" / "core" / "database_manager.py"
    ).read_text(encoding="utf-8")

    assert "requested_prediction_model" in database_manager_source
    assert "resolved_prediction_model" in database_manager_source
    assert "requested_generator_model" in database_manager_source
    assert "resolved_generator_model" in database_manager_source
    assert "fallback_applied" in database_manager_source


def test_main_window_updates_lspr_workbench_theme_when_theme_changes():
    main_window_source = (PROJECT_ROOT / "nanosense" / "gui" / "main_window.py").read_text(encoding="utf-8")

    assert "refresh_theme()" in main_window_source
    assert "lspr_workbench_window" in main_window_source


def test_ai_engine_maps_stage3_modes_to_fusion_predictor():
    ai_engine_source = (
        LSPRMasterBridge().master_root / "src" / "core" / "ai_engine.py"
    ).read_text(encoding="utf-8")

    assert "add_mode('v2_cycle', 'fusion'" in ai_engine_source
    assert "add_mode('stage3_3a_fixed_frozen', 'fusion'" in ai_engine_source
    assert "add_mode('stage3_3b_fixed_regressor', 'fusion'" in ai_engine_source
    assert "add_mode('stage3_3c_learnable_regressor', 'fusion'" in ai_engine_source
    assert "add_mode('stage3_ch_fixed_regressor', 'fusion'" in ai_engine_source
    assert "if 'raw_med' in norm_params and 'raw_iqr' in norm_params:" in ai_engine_source
