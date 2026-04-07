from typing import Callable, Optional

import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    QLabel,
)


class LSPRDigitalTwinWidget(QWidget):
    def __init__(self, get_service: Callable, parent=None):
        super().__init__(parent)
        self._get_service = get_service
        self._slider_scale = 1000
        self._experimental_wavelengths: Optional[list] = None
        self._experimental_intensities: Optional[list] = None
        self._last_result = None

        layout = QVBoxLayout(self)

        controls_group = QGroupBox("Digital Twin")
        controls_form = QFormLayout(controls_group)
        self.concentration_spinbox = QDoubleSpinBox()
        self.concentration_spinbox.setRange(0.0, 1000.0)
        self.concentration_spinbox.setDecimals(4)
        self.concentration_spinbox.setValue(5.0)
        self.concentration_spinbox.setSuffix(" ng/ml")
        self.concentration_spinbox.valueChanged.connect(self._sync_spinbox_to_slider)
        controls_form.addRow("Concentration:", self.concentration_spinbox)

        self.concentration_slider = QSlider(Qt.Horizontal)
        self.concentration_slider.setRange(0, int(1000.0 * self._slider_scale))
        self.concentration_slider.setValue(int(self.concentration_spinbox.value() * self._slider_scale))
        self.concentration_slider.valueChanged.connect(self._sync_slider_to_spinbox)
        controls_form.addRow("Slider:", self.concentration_slider)

        self.overlay_experimental_checkbox = QCheckBox("Overlay Experimental Spectrum")
        self.overlay_experimental_checkbox.setChecked(True)
        self.overlay_experimental_checkbox.toggled.connect(self._refresh_plot)
        controls_form.addRow("Experimental:", self.overlay_experimental_checkbox)
        layout.addWidget(controls_group)

        self.generate_button = QPushButton("Generate Digital Twin")
        self.generate_button.clicked.connect(self._generate_digital_twin)
        layout.addWidget(self.generate_button)

        self.export_plot_button = QPushButton("Export Digital Twin Plot")
        self.export_plot_button.clicked.connect(self._export_current_plot)
        layout.addWidget(self.export_plot_button)

        metrics_group = QGroupBox("Digital Twin Metrics")
        metrics_form = QFormLayout(metrics_group)
        self.peak_wavelength_label = QLabel("N/A")
        self.delta_lambda_label = QLabel("N/A")
        self.peak_intensity_label = QLabel("N/A")
        metrics_form.addRow("Peak Wavelength:", self.peak_wavelength_label)
        metrics_form.addRow("Delta Lambda:", self.delta_lambda_label)
        metrics_form.addRow("Peak Intensity:", self.peak_intensity_label)
        layout.addWidget(metrics_group)

        self.status_label = QLabel("No digital twin generated.")
        layout.addWidget(self.status_label)

        self.digital_twin_plot = pg.PlotWidget()
        self.digital_twin_plot.addLegend()
        self.digital_twin_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.digital_twin_plot)

    def set_concentration(self, concentration_ng_ml: float):
        self.concentration_spinbox.setValue(float(concentration_ng_ml))

    def set_experimental_spectrum(self, wavelengths, intensities):
        self._experimental_wavelengths = list(wavelengths)
        self._experimental_intensities = list(intensities)
        self._refresh_plot()

    def _sync_slider_to_spinbox(self, value):
        concentration = float(value) / float(self._slider_scale)
        if abs(self.concentration_spinbox.value() - concentration) > 1e-9:
            self.concentration_spinbox.blockSignals(True)
            self.concentration_spinbox.setValue(concentration)
            self.concentration_spinbox.blockSignals(False)
        if self._last_result is not None:
            self._generate_digital_twin()

    def _sync_spinbox_to_slider(self, value):
        slider_value = int(round(float(value) * self._slider_scale))
        if self.concentration_slider.value() != slider_value:
            self.concentration_slider.blockSignals(True)
            self.concentration_slider.setValue(slider_value)
            self.concentration_slider.blockSignals(False)

    def _generate_digital_twin(self):
        service = self._get_service()
        self._last_result = service.build_digital_twin_context(concentration_ng_ml=self.concentration_spinbox.value())
        self._refresh_plot()

    def _refresh_plot(self):
        self.digital_twin_plot.clear()
        self.digital_twin_plot.addLegend()
        if self._last_result is None:
            self._update_status_text()
            return

        result = self._last_result
        self.digital_twin_plot.plot(result.wavelengths, result.physical_spectrum, pen=pg.mkPen("#d18f00", width=2), name="Physical")
        self.digital_twin_plot.plot(result.wavelengths, result.baseline_spectrum, pen=pg.mkPen("#1f77b4", width=2), name="Baseline")
        if result.ai_spectrum is not None:
            self.digital_twin_plot.plot(result.wavelengths, result.ai_spectrum, pen=pg.mkPen("#2ca02c", width=2), name="AI")
        if (
            self.overlay_experimental_checkbox.isChecked()
            and self._experimental_wavelengths is not None
            and self._experimental_intensities is not None
        ):
            self.digital_twin_plot.plot(
                self._experimental_wavelengths,
                self._experimental_intensities,
                pen=pg.mkPen("#9467bd", width=2),
                name="Experimental",
            )

        self.peak_wavelength_label.setText(
            "N/A" if result.metrics.get("peak_wavelength_nm") is None else f"{float(result.metrics['peak_wavelength_nm']):.4f} nm"
        )
        self.delta_lambda_label.setText(
            "N/A" if result.metrics.get("delta_lambda_nm") is None else f"{float(result.metrics['delta_lambda_nm']):.4f} nm"
        )
        self.peak_intensity_label.setText(
            "N/A" if result.metrics.get("peak_intensity") is None else f"{float(result.metrics['peak_intensity']):.6f}"
        )
        self._update_status_text()

    def _update_status_text(self):
        if self._last_result is None:
            self.status_label.setText("No digital twin generated.")
            return

        visible = ["baseline", "physical"]
        if self._last_result.ai_spectrum is not None:
            visible.append("ai")
        if (
            self.overlay_experimental_checkbox.isChecked()
            and self._experimental_wavelengths is not None
            and self._experimental_intensities is not None
        ):
            visible.append("experimental")
        self.status_label.setText("Showing " + ", ".join(visible) + " spectra.")

    def _export_current_plot(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Digital Twin Plot",
            "",
            "PNG Files (*.png)",
        )
        if not file_path:
            return
        exporter = pg.exporters.ImageExporter(self.digital_twin_plot.plotItem)
        exporter.export(file_path)
