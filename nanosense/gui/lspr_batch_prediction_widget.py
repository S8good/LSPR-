import csv
from typing import Callable, List, Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton

from nanosense.utils.file_io import load_spectra_from_path


class LSPRBatchPredictionWidget(QWidget):
    row_activated = pyqtSignal(dict)

    def __init__(self, get_service: Callable, config: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self._get_service = get_service
        self.config = config or {}
        self._items: List[dict] = []
        self._last_rows: List[dict] = []

        layout = QVBoxLayout(self)
        self.load_folder_button = QPushButton("Load Folder...")
        self.load_folder_button.clicked.connect(self._load_folder)
        layout.addWidget(self.load_folder_button)

        self.load_file_button = QPushButton("Load Multi-column File...")
        self.load_file_button.clicked.connect(self._load_multi_column_file)
        layout.addWidget(self.load_file_button)

        self.run_button = QPushButton("Run Batch Prediction")
        self.run_button.clicked.connect(self._run_batch_prediction)
        layout.addWidget(self.run_button)

        self.export_csv_button = QPushButton("Export CSV...")
        self.export_csv_button.clicked.connect(self._export_csv)
        layout.addWidget(self.export_csv_button)

        summary_group = QGroupBox("Batch Summary")
        summary_layout = QFormLayout(summary_group)
        self.status_label = QLabel("No spectra loaded.")
        self.loaded_count_label = QLabel("Loaded: 0")
        self.predicted_count_label = QLabel("Predicted: 0")
        counts_row = QWidget(self)
        counts_row_layout = QHBoxLayout(counts_row)
        counts_row_layout.setContentsMargins(0, 0, 0, 0)
        counts_row_layout.setSpacing(12)
        counts_row_layout.addWidget(self.loaded_count_label)
        counts_row_layout.addWidget(self.predicted_count_label)
        counts_row_layout.addStretch(1)
        summary_layout.addRow("Status:", self.status_label)
        summary_layout.addRow("Counts:", counts_row)
        layout.addWidget(summary_group)

        self.results_table = QTableWidget(0, 5, self)
        self.results_table.setHorizontalHeaderLabels(["Label", "Model", "Concentration", "Mode", "Reported"])
        self.results_table.cellDoubleClicked.connect(self._emit_selected_row)
        layout.addWidget(self.results_table)
        self._update_summary_labels()
        self.refresh_theme()

    def _load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", self.config.get("default_load_path", ""))
        if not folder:
            return
        spectra = load_spectra_from_path(folder, mode="folder")
        self._apply_loaded_items(spectra, "folder")

    def _load_multi_column_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Multi-column File",
            self.config.get("default_load_path", ""),
            "All Supported Files (*.xlsx *.xls *.csv *.txt)",
        )
        if not file_path:
            return
        spectra = load_spectra_from_path(file_path, mode="file")
        self._apply_loaded_items(spectra, "file")

    def _apply_loaded_items(self, spectra, source_kind: str):
        items = [
            {
                "label": spec["name"],
                "wavelengths": spec["x"].tolist(),
                "intensities": spec["y"].tolist(),
            }
            for spec in spectra
            if spec.get("x") is not None and spec.get("y") is not None
        ]
        self._items = items
        self._last_rows = []
        if not items:
            self.results_table.setRowCount(0)
            self.status_label.setText("No spectra loaded.")
            self._update_summary_labels()
            QMessageBox.information(self, "Batch Prediction", f"No spectra were loaded from the selected {source_kind}.")
            return
        self.status_label.setText(f"Loaded {len(items)} spectra. Click Run Batch Prediction to start inference.")
        self._update_summary_labels()
        self._populate_pending_results()

    def _update_summary_labels(self):
        loaded_count = len(self._items)
        predicted_count = len(self._last_rows)
        self.loaded_count_label.setText(f"Loaded: {loaded_count}")
        self.predicted_count_label.setText(f"Predicted: {predicted_count}")

    def _populate_pending_results(self):
        self.results_table.setRowCount(len(self._items))
        for row_index, item in enumerate(self._items):
            self.results_table.setItem(row_index, 0, QTableWidgetItem(str(item.get("label", ""))))
            self.results_table.setItem(row_index, 1, QTableWidgetItem("Pending"))
            self.results_table.setItem(row_index, 2, QTableWidgetItem("-"))
            self.results_table.setItem(row_index, 3, QTableWidgetItem("Awaiting run"))
            self.results_table.setItem(row_index, 4, QTableWidgetItem(""))

    def _run_batch_prediction(self):
        if not self._items:
            QMessageBox.warning(self, "Batch Prediction", "Load spectra before running batch prediction.")
            return
        service = self._get_service()
        try:
            result = service.predict_batch(items=self._items, model_mode="auto")
        except Exception as exc:
            self.status_label.setText("Batch prediction failed.")
            self._update_summary_labels()
            QMessageBox.critical(self, "Batch Prediction", str(exc))
            return
        rows = result["rows"]
        backend = str(result.get("backend", ""))
        enriched_rows = []
        for row in rows:
            enriched = dict(row)
            enriched.setdefault("prediction_model_mode", enriched.get("model_mode", "auto"))
            enriched.setdefault("prediction_backend", backend or enriched.get("backend", ""))
            enriched_rows.append(enriched)
        self._last_rows = enriched_rows
        self.results_table.setRowCount(len(enriched_rows))
        for row_index, row in enumerate(enriched_rows):
            self.results_table.setItem(row_index, 0, QTableWidgetItem(str(row.get("label", ""))))
            self.results_table.setItem(row_index, 1, QTableWidgetItem(str(row.get("model_mode", ""))))
            self.results_table.setItem(row_index, 2, QTableWidgetItem(f"{float(row.get('predicted_concentration_ng_ml', 0.0)):.4f}"))
            self.results_table.setItem(row_index, 3, QTableWidgetItem(str(row.get("report_mode", ""))))
            self.results_table.setItem(row_index, 4, QTableWidgetItem(str(row.get("reported_text", ""))))
        self.status_label.setText(f"Predicted {len(enriched_rows)} spectra. Double-click a row to inspect details.")
        self._update_summary_labels()

    def _export_csv(self):
        if not self._last_rows:
            return
        default_dir = self.config.get("lspr_batch_export_dir", "") or self.config.get("default_save_path", "")
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Batch Results", default_dir, "CSV Files (*.csv)")
        if not file_path:
            return
        with open(file_path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["label", "model_mode", "predicted_concentration_ng_ml", "report_mode", "reported_text"],
            )
            writer.writeheader()
            for row in self._last_rows:
                writer.writerow(
                    {
                        "label": row.get("label", ""),
                        "model_mode": row.get("model_mode", ""),
                        "predicted_concentration_ng_ml": row.get("predicted_concentration_ng_ml", ""),
                        "report_mode": row.get("report_mode", ""),
                        "reported_text": row.get("reported_text", ""),
                    }
                )

    def _emit_selected_row(self, row_index, _column_index):
        if 0 <= row_index < len(self._items):
            payload = dict(self._items[row_index])
            if row_index < len(self._last_rows):
                payload.update(self._last_rows[row_index])
            self.row_activated.emit(payload)

    def refresh_theme(self):
        try:
            from nanosense.utils.config_manager import load_settings
            theme = str(load_settings().get("theme", "dark")).lower()
        except Exception:
            theme = "dark"

        text_color = "#000000" if theme == "light" else "#E2E8F0"
        table_bg = "#FFFFFF" if theme == "light" else "#2D3748"
        alt_bg = "#F3F4F6" if theme == "light" else "#374151"
        border = "#D1D5DB" if theme == "light" else "#4A5568"
        self.status_label.setStyleSheet(f"color: {text_color};")
        self.loaded_count_label.setStyleSheet(f"color: {text_color};")
        self.predicted_count_label.setStyleSheet(f"color: {text_color};")
        self.results_table.setStyleSheet(
            "QTableWidget {{ background-color: {bg}; alternate-background-color: {alt}; color: {fg}; "
            "gridline-color: {border}; border: 1px solid {border}; }}"
            "QHeaderView::section {{ background-color: {bg}; color: {fg}; border: 1px solid {border}; }}"
            .format(bg=table_bg, alt=alt_bg, fg=text_color, border=border)
        )
        self.results_table.setAlternatingRowColors(True)
