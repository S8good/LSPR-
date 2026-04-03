import pyqtgraph as pg
import pyqtgraph.exporters
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class LSPRSpectrumComparisonWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_result = None
        self._input_curve = None
        self._generated_curve = None
        self._aligned_curve = None

        layout = QVBoxLayout(self)

        self.status_label = QLabel("No comparison loaded.")

        controls_row = QHBoxLayout()
        self.show_input_checkbox = QCheckBox("Input")
        self.show_generated_checkbox = QCheckBox("Generated")
        self.show_aligned_checkbox = QCheckBox("Aligned")
        self.show_input_checkbox.setToolTip("Measured/preprocessed input spectrum.")
        self.show_generated_checkbox.setToolTip("AI-generated spectrum before scale/offset alignment.")
        self.show_aligned_checkbox.setToolTip("AI-generated spectrum after alignment to the input intensity range.")
        for checkbox in (
            self.show_input_checkbox,
            self.show_generated_checkbox,
            self.show_aligned_checkbox,
        ):
            checkbox.setChecked(True)
            checkbox.toggled.connect(self._refresh_curve_visibility)
            controls_row.addWidget(checkbox)
        controls_row.addStretch(1)

        self.export_plot_button = QPushButton("Export Comparison Plot")
        self.export_plot_button.clicked.connect(self._export_current_plot)
        controls_row.addWidget(self.export_plot_button)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        layout.addWidget(self.status_label)
        layout.addLayout(controls_row)
        layout.addWidget(self.plot_widget)
        self._apply_theme_styles()

    @staticmethod
    def _safe_float_array(values):
        if values is None:
            return []
        try:
            return list(np.asarray(values, dtype=float))
        except Exception:
            return []

    def _apply_theme_styles(self):
        try:
            from nanosense.utils.config_manager import load_settings
            theme = str(load_settings().get("theme", "dark")).lower()
        except Exception:
            theme = "dark"

        background = "#F0F0F0" if theme == "light" else "#1F2735"
        axis_color = "#000000" if theme == "light" else "#FFFFFF"
        text_color = "#000000" if theme == "light" else "#E2E8F0"
        self.plot_widget.setBackground(background)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.12 if theme == "light" else 0.3)
        for axis_name in ("left", "bottom"):
            axis = self.plot_widget.getPlotItem().getAxis(axis_name)
            axis.setPen(pg.mkPen(axis_color, width=1))
            axis.setTextPen(pg.mkPen(axis_color, width=1))
        legend = self.plot_widget.getPlotItem().legend
        if legend:
            for item in legend.items:
                label = item[1]
                label.setText(label.text, color=text_color)

    def set_comparison_result(self, result):
        self._current_result = result
        self.plot_widget.clear()
        self.plot_widget.addLegend()
        self._apply_theme_styles()

        wavelengths = self._safe_float_array(getattr(result, "wavelengths", None))
        input_spectrum = self._safe_float_array(getattr(result, "input_spectrum", None))
        generated_spectrum = self._safe_float_array(getattr(result, "generated_spectrum", None))
        aligned_spectrum = self._safe_float_array(getattr(result, "aligned_spectrum", None))

        self._input_curve = self.plot_widget.plot(
            wavelengths,
            input_spectrum,
            pen=pg.mkPen("#1f77b4", width=2),
            name="Input",
        )
        self._generated_curve = self.plot_widget.plot(
            wavelengths,
            generated_spectrum,
            pen=pg.mkPen("#d62728", width=2, style=Qt.DashLine),
            name="Generated",
        )
        self._aligned_curve = self.plot_widget.plot(
            wavelengths,
            aligned_spectrum,
            pen=pg.mkPen("#2ca02c", width=2, style=Qt.DotLine),
            name="Aligned",
        )
        self._refresh_curve_visibility()

    def _refresh_curve_visibility(self):
        if self._input_curve is not None:
            self._input_curve.setVisible(self.show_input_checkbox.isChecked())
        if self._generated_curve is not None:
            self._generated_curve.setVisible(self.show_generated_checkbox.isChecked())
        if self._aligned_curve is not None:
            self._aligned_curve.setVisible(self.show_aligned_checkbox.isChecked())
        self._update_status_text()

    def _update_status_text(self):
        visible_labels = []
        if self.show_input_checkbox.isChecked():
            visible_labels.append("input")
        if self.show_generated_checkbox.isChecked():
            visible_labels.append("generated")
        if self.show_aligned_checkbox.isChecked():
            visible_labels.append("aligned")

        if not visible_labels:
            self.status_label.setText("No comparison curves are visible.")
            return

        hint = " Input=measured, Generated=AI raw output, Aligned=scale/offset aligned output."
        if len(visible_labels) == 1:
            self.status_label.setText(f"Showing {visible_labels[0]} spectrum only.{hint}")
            return

        if len(visible_labels) == 2:
            self.status_label.setText(f"Showing {visible_labels[0]} and {visible_labels[1]} spectra.{hint}")
            return

        self.status_label.setText(f"Showing input, generated, and aligned spectra.{hint}")

    def _export_current_plot(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Comparison Plot",
            "",
            "PNG Files (*.png)",
        )
        if not file_path:
            return
        exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
        exporter.export(file_path)
