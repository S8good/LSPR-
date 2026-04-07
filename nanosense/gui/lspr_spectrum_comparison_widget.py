import pyqtgraph as pg
import pyqtgraph.exporters
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

    def set_comparison_result(self, result):
        self._current_result = result
        self.plot_widget.clear()
        self.plot_widget.addLegend()
        self._input_curve = self.plot_widget.plot(
            result.wavelengths,
            result.input_spectrum,
            pen=pg.mkPen("#1f77b4", width=2),
            name="Input",
        )
        self._generated_curve = self.plot_widget.plot(
            result.wavelengths,
            result.generated_spectrum,
            pen=pg.mkPen("#d62728", width=2),
            name="Generated",
        )
        self._aligned_curve = self.plot_widget.plot(
            result.wavelengths,
            result.aligned_spectrum,
            pen=pg.mkPen("#2ca02c", width=2),
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

        if len(visible_labels) == 1:
            self.status_label.setText(f"Showing {visible_labels[0]} spectrum only.")
            return

        if len(visible_labels) == 2:
            self.status_label.setText(f"Showing {visible_labels[0]} and {visible_labels[1]} spectra.")
            return

        self.status_label.setText("Showing input, generated, and aligned spectra.")

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
