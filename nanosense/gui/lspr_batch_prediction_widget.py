from typing import Callable, List, Optional

from PyQt5.QtWidgets import QFileDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton

from nanosense.utils.file_io import load_spectra_from_path


class LSPRBatchPredictionWidget(QWidget):
    def __init__(self, get_service: Callable, config: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self._get_service = get_service
        self.config = config or {}
        self._items: List[dict] = []

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

        self.results_table = QTableWidget(0, 5, self)
        self.results_table.setHorizontalHeaderLabels(["Label", "Model", "Concentration", "Mode", "Reported"])
        layout.addWidget(self.results_table)

    def _load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", self.config.get("default_load_path", ""))
        if not folder:
            return
        spectra = load_spectra_from_path(folder, mode="folder")
        self._items = [{"label": spec["name"], "wavelengths": spec["x"].tolist(), "intensities": spec["y"].tolist()} for spec in spectra]

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
        self._items = [{"label": spec["name"], "wavelengths": spec["x"].tolist(), "intensities": spec["y"].tolist()} for spec in spectra]

    def _run_batch_prediction(self):
        service = self._get_service()
        result = service.predict_batch(items=self._items, model_mode="auto")
        rows = result["rows"]
        self.results_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self.results_table.setItem(row_index, 0, QTableWidgetItem(str(row.get("label", ""))))
            self.results_table.setItem(row_index, 1, QTableWidgetItem(str(row.get("model_mode", ""))))
            self.results_table.setItem(row_index, 2, QTableWidgetItem(f"{float(row.get('predicted_concentration_ng_ml', 0.0)):.4f}"))
            self.results_table.setItem(row_index, 3, QTableWidgetItem(str(row.get("report_mode", ""))))
            self.results_table.setItem(row_index, 4, QTableWidgetItem(str(row.get("reported_text", ""))))
