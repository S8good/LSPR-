from typing import Dict, List, Optional

import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nanosense.algorithms.preprocessing import baseline_als, smooth_savitzky_golay
from nanosense.algorithms.peak_analysis import PEAK_METHOD_KEYS, PEAK_METHOD_LABELS, calculate_fwhm, estimate_peak_position
from nanosense.utils.file_io import load_spectrum

from .lspr_batch_prediction_widget import LSPRBatchPredictionWidget
from .lspr_digital_twin_widget import LSPRDigitalTwinWidget
from .lspr_model_comparison_widget import LSPRModelComparisonWidget
from .lspr_result_summary_widget import LSPRResultSummaryWidget
from .lspr_spectrum_comparison_widget import LSPRSpectrumComparisonWidget
from ..ml.lspr_ai_service import LSPRAIService, LSPRSpectrumComparisonResult


class LSPRAIAnalysisWindow(QMainWindow):
    def __init__(self, spectra_data=None, config=None, service=None, parent=None):
        super().__init__(parent)
        self.config = config or {}
        self._service = None
        if service is not None:
            self._service = service
        self.spectra: Dict[str, Dict[str, object]] = {}
        self.current_spectrum_key: Optional[str] = None

        self.setWindowTitle("LSPR AI Analysis Window")
        self.resize(1360, 820)

        self._build_ui()
        if spectra_data is not None:
            self.set_initial_data(spectra_data)

    def _get_service(self):
        if self._service is None:
            self._service = LSPRAIService(config=self.config)
        return self._service

    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        control_panel = QWidget(self)
        control_layout = QVBoxLayout(control_panel)

        self.import_spectrum_button = QPushButton("Import Spectrum...")
        self.import_spectrum_button.clicked.connect(self._import_spectrum_file)
        control_layout.addWidget(self.import_spectrum_button)

        self.spectra_list_widget = QListWidget()
        self.spectra_list_widget.itemChanged.connect(self._update_curve_visibility)
        self.spectra_list_widget.currentItemChanged.connect(self._handle_spectrum_selection_changed)
        control_layout.addWidget(self.spectra_list_widget, stretch=1)

        selection_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.deselect_all_button = QPushButton("Deselect All")
        self.select_all_button.clicked.connect(self._select_all_spectra)
        self.deselect_all_button.clicked.connect(self._deselect_all_spectra)
        selection_layout.addWidget(self.select_all_button)
        selection_layout.addWidget(self.deselect_all_button)
        control_layout.addLayout(selection_layout)

        preprocessing_group = QGroupBox("Preprocessing")
        preprocessing_layout = QVBoxLayout(preprocessing_group)
        self.preprocessing_enabled_checkbox = QCheckBox("Enable preprocessing")
        self.baseline_checkbox = QCheckBox("ALS baseline")
        self.smoothing_checkbox = QCheckBox("Smoothing")
        preprocessing_layout.addWidget(self.preprocessing_enabled_checkbox)
        preprocessing_layout.addWidget(self.baseline_checkbox)
        preprocessing_layout.addWidget(self.smoothing_checkbox)
        control_layout.addWidget(preprocessing_group)

        ai_group = QGroupBox("AI Prediction")
        ai_layout = QVBoxLayout(ai_group)
        ai_mode_row = QHBoxLayout()
        ai_mode_row.addWidget(QLabel("Analysis Target:"))
        self.analysis_target_combo = QComboBox()
        self.analysis_target_combo.currentIndexChanged.connect(self._handle_analysis_target_changed)
        ai_mode_row.addWidget(self.analysis_target_combo)
        ai_mode_row.addWidget(QLabel("Model Mode:"))
        self.model_mode_combo = QComboBox()
        self.model_mode_combo.addItem("Auto", "auto")
        self.model_mode_combo.addItem("In-process", "inprocess")
        self.model_mode_combo.addItem("Subprocess", "subprocess")
        ai_mode_row.addWidget(self.model_mode_combo)
        ai_layout.addLayout(ai_mode_row)
        self.run_ai_button = QPushButton("Run AI Prediction")
        self.run_ai_button.clicked.connect(self._run_ai_prediction)
        ai_layout.addWidget(self.run_ai_button)
        self.summary_widget = LSPRResultSummaryWidget()
        ai_layout.addWidget(self.summary_widget)
        control_layout.addWidget(ai_group)

        analysis_group = QGroupBox("Peak Analysis")
        analysis_layout = QVBoxLayout(analysis_group)
        analysis_form = QFormLayout()
        self.peak_method_combo = QComboBox()
        for method_key in PEAK_METHOD_KEYS:
            self.peak_method_combo.addItem(PEAK_METHOD_LABELS[method_key], method_key)
        analysis_form.addRow("Peak Method:", self.peak_method_combo)
        analysis_layout.addLayout(analysis_form)
        self.find_main_peak_button = QPushButton("Find Main Peak")
        self.find_main_peak_button.clicked.connect(self._find_main_peak)
        analysis_layout.addWidget(self.find_main_peak_button)
        peak_result_form = QFormLayout()
        self.main_peak_wavelength_label = QLabel("N/A")
        self.main_peak_intensity_label = QLabel("N/A")
        self.main_peak_fwhm_label = QLabel("N/A")
        peak_result_form.addRow("Peak Wavelength:", self.main_peak_wavelength_label)
        peak_result_form.addRow("Peak Intensity:", self.main_peak_intensity_label)
        peak_result_form.addRow("FWHM:", self.main_peak_fwhm_label)
        analysis_layout.addLayout(peak_result_form)
        control_layout.addWidget(analysis_group)

        control_layout.addStretch(1)

        self.content_tabs = QTabWidget(self)
        analysis_tab = QWidget(self)
        analysis_tab_layout = QVBoxLayout(analysis_tab)
        self.source_label = QLabel("No spectrum loaded.")
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.export_plot_button = QPushButton("Export Current Plot")
        self.export_plot_button.clicked.connect(self._export_current_plot)
        self.comparison_metrics_row = QWidget(self)
        comparison_metrics_layout = QHBoxLayout(self.comparison_metrics_row)
        comparison_metrics_layout.setContentsMargins(0, 0, 0, 0)
        comparison_metrics_layout.setSpacing(16)
        self.comparison_concentration_label = QLabel("Conc: N/A")
        self.comparison_report_mode_label = QLabel("Mode: N/A")
        self.comparison_scale_label = QLabel("Scale: N/A")
        self.comparison_offset_label = QLabel("Offset: N/A")
        comparison_metrics_layout.addWidget(self.comparison_concentration_label)
        comparison_metrics_layout.addWidget(self.comparison_report_mode_label)
        comparison_metrics_layout.addWidget(self.comparison_scale_label)
        comparison_metrics_layout.addWidget(self.comparison_offset_label)
        comparison_metrics_layout.addStretch(1)
        self.comparison_widget = LSPRSpectrumComparisonWidget()
        analysis_tab_layout.addWidget(self.source_label)
        analysis_tab_layout.addWidget(self.plot_widget, stretch=2)
        analysis_tab_layout.addWidget(self.export_plot_button)
        analysis_tab_layout.addWidget(self.comparison_metrics_row)
        analysis_tab_layout.addWidget(self.comparison_widget, stretch=2)

        self.digital_twin_tab = LSPRDigitalTwinWidget(self._get_service, parent=self)
        self.model_comparison_tab = LSPRModelComparisonWidget(self._get_service, self._get_current_spectrum, parent=self)
        self.batch_prediction_tab = LSPRBatchPredictionWidget(self._get_service, config=self.config, parent=self)

        self.content_tabs.addTab(analysis_tab, "Analysis")
        self.content_tabs.addTab(self.digital_twin_tab, "Digital Twin")
        self.content_tabs.addTab(self.model_comparison_tab, "Model Comparison")
        self.content_tabs.addTab(self.batch_prediction_tab, "Batch Prediction")

        main_layout.addWidget(control_panel, stretch=1)
        main_layout.addWidget(self.content_tabs, stretch=2)

    def set_initial_data(self, spectra_data):
        spectra_list: List[Dict[str, object]]
        if isinstance(spectra_data, dict):
            spectra_list = [spectra_data]
        else:
            spectra_list = list(spectra_data)

        self.spectra.clear()
        self.spectra_list_widget.clear()
        self.analysis_target_combo.clear()

        for index, spec in enumerate(spectra_list):
            self._add_spectrum(
                spec.get("x", []),
                spec.get("y", []),
                spec.get("name", f"Spectrum {index + 1}"),
                metadata={
                    "source": spec.get("source", "preloaded"),
                    "source_file": spec.get("source_file"),
                },
            )

        if self.spectra_list_widget.count():
            self.spectra_list_widget.setCurrentRow(0)

    def set_input_spectrum(self, wavelengths, intensities, metadata=None):
        self._add_spectrum(
            wavelengths,
            intensities,
            (metadata or {}).get("name", "Imported Spectrum"),
            metadata=metadata or {},
        )
        self.spectra_list_widget.setCurrentRow(self.spectra_list_widget.count() - 1)

    def _add_spectrum(self, wavelengths, intensities, name, metadata=None):
        key = f"{name}___{len(self.spectra)}"
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)
        item.setData(Qt.UserRole, key)
        self.spectra_list_widget.addItem(item)
        self.analysis_target_combo.addItem(name, key)
        self.spectra[key] = {
            "name": name,
            "x": np.asarray(wavelengths, dtype=float),
            "y": np.asarray(intensities, dtype=float),
            "metadata": dict(metadata or {}),
        }

    def _import_spectrum_file(self):
        default_load_path = self.config.get("default_load_path", "")
        wavelengths, intensities, source_file = load_spectrum(self, default_load_path)
        if wavelengths is None or intensities is None:
            return

        self.set_input_spectrum(
            wavelengths,
            intensities,
            metadata={"source": "file_import", "source_file": source_file, "name": source_file},
        )

    def _handle_spectrum_selection_changed(self, current, previous):
        if current is None:
            return
        key = current.data(Qt.UserRole)
        self.current_spectrum_key = key
        combo_index = self.analysis_target_combo.findData(key)
        if combo_index >= 0:
            self.analysis_target_combo.setCurrentIndex(combo_index)
        spectrum = self.spectra[key]
        self.digital_twin_tab.set_experimental_spectrum(
            spectrum["x"].tolist(),
            self._get_display_intensity(spectrum["y"]).tolist(),
        )
        self._refresh_source_plot()

    def _handle_analysis_target_changed(self, index):
        key = self.analysis_target_combo.itemData(index)
        if not key:
            return
        self.current_spectrum_key = key
        for row in range(self.spectra_list_widget.count()):
            item = self.spectra_list_widget.item(row)
            if item.data(Qt.UserRole) == key:
                self.spectra_list_widget.setCurrentRow(row)
                break
        spectrum = self.spectra[key]
        self.digital_twin_tab.set_experimental_spectrum(
            spectrum["x"].tolist(),
            self._get_display_intensity(spectrum["y"]).tolist(),
        )
        self._refresh_source_plot()

    def _refresh_source_plot(self):
        self.plot_widget.clear()
        visible_keys = []
        for row in range(self.spectra_list_widget.count()):
            item = self.spectra_list_widget.item(row)
            if item.checkState() == Qt.Checked:
                visible_keys.append(item.data(Qt.UserRole))

        if not visible_keys:
            return

        for key in visible_keys:
            spectrum = self.spectra[key]
            display_y = self._get_display_intensity(spectrum["y"])
            pen = pg.mkPen("#d62728" if key == self.current_spectrum_key else "#1f77b4", width=2)
            self.plot_widget.plot(spectrum["x"], display_y, pen=pen, name=spectrum["name"])

        if not self.current_spectrum_key:
            self.current_spectrum_key = visible_keys[0]
        spectrum = self.spectra[self.current_spectrum_key]
        metadata = spectrum.get("metadata", {})
        source = metadata.get("source", "unknown")
        source_file = metadata.get("source_file")
        if source_file:
            self.source_label.setText(f"Source: {source} ({source_file})")
        else:
            self.source_label.setText(f"Source: {source}")

    def _get_current_spectrum(self):
        if not self.current_spectrum_key:
            return None
        spectrum = self.spectra.get(self.current_spectrum_key)
        if spectrum is None:
            return None
        return {
            'name': spectrum['name'],
            'x': np.asarray(spectrum['x'], dtype=float),
            'y': np.asarray(self._get_display_intensity(spectrum['y']), dtype=float),
            'metadata': dict(spectrum.get('metadata', {})),
        }

    def _get_display_intensity(self, intensity):
        working = np.asarray(intensity, dtype=float)
        if not self.preprocessing_enabled_checkbox.isChecked():
            return working
        if self.baseline_checkbox.isChecked():
            working = working - baseline_als(working, lam=1e9, p=0.01)
        if self.smoothing_checkbox.isChecked() and working.size >= 15:
            working = smooth_savitzky_golay(working, window_length=15, polyorder=3)
        return working

    def _select_all_spectra(self):
        for row in range(self.spectra_list_widget.count()):
            self.spectra_list_widget.item(row).setCheckState(Qt.Checked)
        self._refresh_source_plot()

    def _deselect_all_spectra(self):
        for row in range(self.spectra_list_widget.count()):
            self.spectra_list_widget.item(row).setCheckState(Qt.Unchecked)
        self._refresh_source_plot()

    def _update_curve_visibility(self, item):
        del item
        self._refresh_source_plot()

    def _export_current_plot(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Current Plot",
            self.config.get("default_save_path", ""),
            "PNG Files (*.png)",
        )
        if not file_path:
            return
        exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
        exporter.export(file_path)

    def _apply_comparison_result(self, comparison):
        self.comparison_widget.set_comparison_result(comparison)
        metrics = dict(getattr(comparison, "metrics", {}) or {})
        concentration = metrics.get("predicted_concentration_ng_ml")
        report_mode = metrics.get("report_mode")
        intensity_scale = metrics.get("intensity_scale")
        intensity_offset = metrics.get("intensity_offset")

        self.comparison_concentration_label.setText(
            "Conc: N/A" if concentration is None else f"Conc: {float(concentration):.4f} ng/ml"
        )
        self.comparison_report_mode_label.setText(
            "Mode: N/A" if report_mode is None else f"Mode: {str(report_mode)}"
        )
        self.comparison_scale_label.setText(
            "Scale: N/A" if intensity_scale is None else f"Scale: {float(intensity_scale):.4f}"
        )
        self.comparison_offset_label.setText(
            "Offset: N/A" if intensity_offset is None else f"Offset: {float(intensity_offset):.4f}"
        )

    def _find_main_peak(self):
        if not self.current_spectrum_key:
            QMessageBox.warning(self, "Peak Analysis", "Select or import a spectrum first.")
            return

        spectrum = self.spectra[self.current_spectrum_key]
        x_data = np.asarray(spectrum["x"], dtype=float)
        y_data = np.asarray(self._get_display_intensity(spectrum["y"]), dtype=float)
        if x_data.size < 3 or y_data.size < 3:
            QMessageBox.warning(self, "Peak Analysis", "Not enough points to analyze the main peak.")
            return

        method = self.peak_method_combo.currentData() or "highest_point"
        peak_index, peak_wavelength = estimate_peak_position(x_data, y_data, method=method)
        if peak_index is None or peak_wavelength is None:
            self.main_peak_wavelength_label.setText("N/A")
            self.main_peak_intensity_label.setText("N/A")
            self.main_peak_fwhm_label.setText("N/A")
            return

        peak_intensity = float(y_data[peak_index])
        fwhm_values = calculate_fwhm(x_data, y_data, [peak_index])
        fwhm = float(fwhm_values[0]) if fwhm_values else 0.0

        self.main_peak_wavelength_label.setText(f"{float(peak_wavelength):.4f} nm")
        self.main_peak_intensity_label.setText(f"{peak_intensity:.6f}")
        self.main_peak_fwhm_label.setText(f"{fwhm:.4f} nm")

    def _run_ai_prediction(self):
        if not self.current_spectrum_key:
            QMessageBox.warning(self, "LSPR AI", "Select or import a spectrum first.")
            return

        spectrum = self.spectra[self.current_spectrum_key]
        wavelengths = spectrum["x"].tolist()
        intensities = self._get_display_intensity(spectrum["y"]).tolist()
        metadata = dict(spectrum.get("metadata", {}))
        metadata["spectrum_name"] = spectrum["name"]

        service = self._get_service()
        model_mode = self.model_mode_combo.currentData()

        try:
            result = service.predict_single_spectrum(
                wavelengths=wavelengths,
                intensities=intensities,
                model_mode=model_mode,
                metadata=metadata,
            )
            self.summary_widget.set_result(result)
            self.digital_twin_tab.set_concentration(result.predicted_concentration_ng_ml)
            try:
                comparison = service.build_spectrum_comparison(
                    wavelengths=wavelengths,
                    intensities=intensities,
                    model_mode=model_mode,
                    metadata=metadata,
                )
            except Exception:
                comparison = LSPRSpectrumComparisonResult(
                    wavelengths=wavelengths,
                    input_spectrum=intensities,
                    generated_spectrum=intensities,
                    aligned_spectrum=intensities,
                    physical_spectrum=None,
                    metrics={},
                    backend=result.backend,
                    model_mode=result.model_mode,
                )
            self._apply_comparison_result(comparison)
        except Exception as exc:
            QMessageBox.critical(self, "LSPR AI", str(exc))
