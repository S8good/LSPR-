from typing import Callable

import pyqtgraph as pg
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton


class LSPRModelComparisonWidget(QWidget):
    def __init__(self, get_service: Callable, get_current_spectrum: Callable, parent=None):
        super().__init__(parent)
        self._get_service = get_service
        self._get_current_spectrum = get_current_spectrum

        layout = QVBoxLayout(self)
        self.run_button = QPushButton("Run Model Comparison")
        self.run_button.clicked.connect(self._run_model_comparison)
        layout.addWidget(self.run_button)

        self.comparison_table = QTableWidget(0, 4, self)
        self.comparison_table.setHorizontalHeaderLabels(["Model", "Concentration", "Mode", "Reported"])
        layout.addWidget(self.comparison_table)

        self.comparison_plot = pg.PlotWidget()
        self.comparison_plot.addLegend()
        self.comparison_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.comparison_plot)

    def _run_model_comparison(self):
        current = self._get_current_spectrum()
        if current is None:
            return
        service = self._get_service()
        result = service.compare_models(
            wavelengths=current["x"].tolist(),
            intensities=current["y"].tolist(),
            metadata=current.get("metadata", {}),
        )

        rows = result["rows"]
        self.comparison_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self.comparison_table.setItem(row_index, 0, QTableWidgetItem(str(row["model_mode"])))
            self.comparison_table.setItem(row_index, 1, QTableWidgetItem(f"{float(row['predicted_concentration_ng_ml']):.4f}"))
            self.comparison_table.setItem(row_index, 2, QTableWidgetItem(str(row["report_mode"])))
            self.comparison_table.setItem(row_index, 3, QTableWidgetItem(str(row["reported_text"])))

        self.comparison_plot.clear()
        self.comparison_plot.addLegend()
        for comparison in result["comparisons"]:
            self.comparison_plot.plot(
                comparison.wavelengths,
                comparison.aligned_spectrum,
                pen=pg.mkPen(width=2),
                name=str(comparison.model_mode),
            )
