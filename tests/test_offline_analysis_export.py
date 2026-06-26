import json
import os
import warnings
from pathlib import Path

import numpy as np
from PIL import Image

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from nanosense.gui import analysis_window
from nanosense.gui.analysis_window import AnalysisWindow, SummaryReportWorker


def _spectrum_data(name, offset=0.0):
    wavelengths = np.linspace(450.0, 750.0, 121)
    absorbance = 0.2 * np.exp(-0.5 * ((wavelengths - (600.0 + offset)) / 35.0) ** 2)
    return {
        "name": name,
        "x": wavelengths,
        "y": absorbance,
    }


def _make_app():
    return QApplication.instance() or QApplication([])


def test_summary_report_export_uses_unified_structure_and_600dpi_png(tmp_path, monkeypatch):
    monkeypatch.setattr(analysis_window.time, "strftime", lambda _fmt: "20260626_130000")
    spectra = {
        "sample_1": _spectrum_data("sample_1", offset=0.0),
        "sample_2": _spectrum_data("sample_2", offset=2.0),
    }
    worker = SummaryReportWorker(
        spectra,
        str(tmp_path),
        preprocessing_params={"smoothing_method": "Savitzky-Golay"},
        apply_baseline=False,
        apply_smoothing=False,
        preprocessing_enabled=True,
        find_range=(500.0, 700.0),
        noise_range=(720.0, 750.0),
        peak_method="highest_point",
        min_height=0.1,
    )

    worker.run()

    report_dir = tmp_path / "OfflineAnalysis_Summary_20260626_130000"
    assert (report_dir / "reports" / "summary_metrics.xlsx").exists()
    assert (report_dir / "data" / "detailed_metrics.csv").exists()
    assert (report_dir / "data" / "statistics_summary.csv").exists()
    assert (report_dir / "data" / "all_spectra.csv").exists()
    assert (report_dir / "data" / "average_spectrum.csv").exists()
    assert (report_dir / "metadata" / "metadata.json").exists()
    assert (report_dir / "README.txt").exists()

    metadata = json.loads((report_dir / "metadata" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["export_type"] == "offline_summary"
    assert metadata["peak_method"] == "highest_point"
    assert metadata["figure_dpi"] == 600
    assert metadata["font_family"] == "Times New Roman"
    assert metadata["peak_marker_enabled"] is True
    assert metadata["peak_marker_source"] == "current_ui_peak_method"

    with Image.open(report_dir / "figures" / "overlay_spectrum.png") as image:
        dpi_x, dpi_y = image.info["dpi"]
        assert 590 <= dpi_x <= 610
        assert 590 <= dpi_y <= 610

    with Image.open(report_dir / "figures" / "peak_marked_overlay.png") as image:
        dpi_x, dpi_y = image.info["dpi"]
        assert 590 <= dpi_x <= 610
        assert 590 <= dpi_y <= 610


def test_summary_report_export_renders_chinese_legend_without_glyph_warnings(tmp_path, monkeypatch):
    monkeypatch.setattr(analysis_window.time, "strftime", lambda _fmt: "20260626_140000")
    spectra = {
        "sample_1": _spectrum_data("chip 01-光谱原始数据.xlsx - 1", offset=0.0),
        "sample_2": _spectrum_data("chip 01-光谱原始数据.xlsx - 2", offset=2.0),
    }
    worker = SummaryReportWorker(
        spectra,
        str(tmp_path),
        preprocessing_params={"smoothing_method": "Savitzky-Golay"},
        apply_baseline=False,
        apply_smoothing=False,
        preprocessing_enabled=True,
        find_range=(500.0, 700.0),
        noise_range=(720.0, 750.0),
        peak_method="highest_point",
        min_height=0.1,
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        worker.run()

    glyph_warnings = [
        item for item in caught
        if "Glyph" in str(item.message) and "missing from current font" in str(item.message)
    ]
    assert glyph_warnings == []


def test_single_publication_plot_draws_peak_marker(tmp_path):
    app = _make_app()
    window = AnalysisWindow([_spectrum_data("sample_1")])
    window.range_start_spinbox.setValue(500.0)
    window.range_end_spinbox.setValue(700.0)
    window.main_peak_wavelength_label.setText("600.0000")
    window.main_peak_intensity_label.setText("0.2000")
    window.main_peak_fwhm_label.setText("82.4180")

    image_path = tmp_path / "spectrum_plot.png"
    window._export_publication_plot(str(image_path))

    with Image.open(image_path).convert("RGB") as image:
        pixels = np.asarray(image)
        red_marker_pixels = (
            (pixels[:, :, 0] > 150)
            & (pixels[:, :, 1] < 120)
            & (pixels[:, :, 2] < 120)
        )
        assert int(np.count_nonzero(red_marker_pixels)) > 0

    window.close()
    app.processEvents()


def test_manual_plot_interaction_does_not_print_console_noise(capsys):
    app = _make_app()
    window = AnalysisWindow([])

    window._on_plot_interacted()

    assert window.user_has_interacted_with_plot is True
    assert capsys.readouterr().out == ""

    window.close()
    app.processEvents()
