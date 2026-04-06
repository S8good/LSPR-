from typing import Callable

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton


class LSPRModelComparisonWidget(QWidget):
    def __init__(self, get_service: Callable, get_current_spectrum: Callable, parent=None):
        super().__init__(parent)
        self._get_service = get_service
        self._get_current_spectrum = get_current_spectrum

        layout = QVBoxLayout(self)
        self.recommended_model_label = QLabel("Recommended: auto")
        layout.addWidget(self.recommended_model_label)

        self.model_selection_list = QListWidget(self)
        layout.addWidget(self.model_selection_list)

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
        self._refresh_model_selection()
        self.refresh_theme()

    def _refresh_model_selection(self):
        self.model_selection_list.clear()
        try:
            modes = list(self._get_service().discover_model_modes())
        except Exception:
            modes = []
        for mode in ["auto"] + [mode for mode in modes if mode != "auto"]:
            item = QListWidgetItem(str(mode))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if mode == "auto" else Qt.Unchecked)
            item.setData(Qt.UserRole, str(mode))
            self.model_selection_list.addItem(item)

    def _selected_model_modes(self):
        selected = []
        for index in range(self.model_selection_list.count()):
            item = self.model_selection_list.item(index)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected or ["auto"]

    def _run_model_comparison(self):
        current = self._get_current_spectrum()
        if current is None:
            return
        service = self._get_service()
        result = service.compare_models(
            wavelengths=current["x"].tolist(),
            intensities=current["y"].tolist(),
            model_modes=self._selected_model_modes(),
            metadata=current.get("metadata", {}),
        )
        self.recommended_model_label.setText(f"Recommended: {result.get('recommended_model_mode', 'auto')}")

        rows = result["rows"]
        self.comparison_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            conc_value = row.get("predicted_concentration_ng_ml")
            if conc_value is None:
                conc_text = "N/A"
            else:
                conc_text = f"{float(conc_value):.4f}"
            self.comparison_table.setItem(row_index, 0, QTableWidgetItem(str(row["model_mode"])))
            self.comparison_table.setItem(row_index, 1, QTableWidgetItem(conc_text))
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
        self.refresh_theme()

    def refresh_theme(self):
        try:
            from nanosense.utils.config_manager import load_settings
            theme = str(load_settings().get("theme", "dark")).lower()
        except Exception:
            theme = "dark"

        background = "#F0F0F0" if theme == "light" else "#1F2735"
        axis_color = "#000000" if theme == "light" else "#FFFFFF"
        text_color = "#000000" if theme == "light" else "#E2E8F0"
        table_bg = "#FFFFFF" if theme == "light" else "#2D3748"
        alt_bg = "#F3F4F6" if theme == "light" else "#374151"
        border = "#D1D5DB" if theme == "light" else "#4A5568"

        self.comparison_plot.setBackground(background)
        self.comparison_plot.showGrid(x=True, y=True, alpha=0.12 if theme == "light" else 0.3)
        for axis_name in ("left", "bottom"):
            axis = self.comparison_plot.getPlotItem().getAxis(axis_name)
            axis.setPen(pg.mkPen(axis_color, width=1))
            axis.setTextPen(pg.mkPen(axis_color, width=1))

        self.recommended_model_label.setStyleSheet(f"color: {text_color};")
        self.model_selection_list.setStyleSheet(
            f"background-color: {table_bg}; color: {text_color}; border: 1px solid {border};"
        )
        self.comparison_table.setStyleSheet(
            "QTableWidget {{ background-color: {bg}; alternate-background-color: {alt}; color: {fg}; "
            "gridline-color: {border}; border: 1px solid {border}; }}"
            "QHeaderView::section {{ background-color: {bg}; color: {fg}; border: 1px solid {border}; }}"
            .format(bg=table_bg, alt=alt_bg, fg=text_color, border=border)
        )
        self.comparison_table.setAlternatingRowColors(True)
