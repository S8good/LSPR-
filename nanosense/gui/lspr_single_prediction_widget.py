from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .lspr_result_summary_widget import LSPRResultSummaryWidget
from ..ml.lspr_ai_service import LSPRAIService, LSPRSpectrumComparisonResult


class LSPRSinglePredictionWidget(QWidget):
    comparison_ready = pyqtSignal(object)

    def __init__(self, service: LSPRAIService, config: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.service = service
        self.config = config or {}
        self._wavelengths = []
        self._intensities = []
        self._metadata = {}

        layout = QVBoxLayout(self)
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Model Mode:"))
        self.model_mode_combo = QComboBox()
        self.model_mode_combo.addItem("Auto", "auto")
        self.model_mode_combo.addItem("In-process", "inprocess")
        self.model_mode_combo.addItem("Subprocess", "subprocess")
        self.model_mode_combo.setCurrentIndex(
            max(0, self.model_mode_combo.findData(self.config.get("lspr_default_model_mode", "auto")))
        )
        controls_layout.addWidget(self.model_mode_combo)

        self.predict_button = QPushButton("Run Prediction")
        self.predict_button.clicked.connect(self._run_prediction)
        controls_layout.addWidget(self.predict_button)
        controls_layout.addStretch(1)

        self.input_status_label = QLabel("No input spectrum loaded.")
        self.summary_widget = LSPRResultSummaryWidget()

        layout.addLayout(controls_layout)
        layout.addWidget(self.input_status_label)
        layout.addWidget(self.summary_widget)

    def set_input_spectrum(self, wavelengths, intensities, metadata=None):
        self._wavelengths = list(wavelengths)
        self._intensities = list(intensities)
        self._metadata = dict(metadata or {})
        self.input_status_label.setText(f"Loaded spectrum with {len(self._wavelengths)} points.")

    def _run_prediction(self):
        if not self._wavelengths or not self._intensities:
            QMessageBox.warning(self, "LSPR AI Workbench", "Load a spectrum before running prediction.")
            return

        model_mode = self.model_mode_combo.currentData()

        try:
            result = self.service.predict_single_spectrum(
                self._wavelengths,
                self._intensities,
                model_mode=model_mode,
                metadata=self._metadata,
            )
            self.summary_widget.set_result(result)
            try:
                comparison = self.service.build_spectrum_comparison(
                    self._wavelengths,
                    self._intensities,
                    model_mode=model_mode,
                    metadata=self._metadata,
                )
            except Exception:
                comparison = LSPRSpectrumComparisonResult(
                    wavelengths=list(self._wavelengths),
                    input_spectrum=list(self._intensities),
                    generated_spectrum=list(self._intensities),
                    aligned_spectrum=list(self._intensities),
                    physical_spectrum=None,
                    metrics={},
                    backend=result.backend,
                    model_mode=result.model_mode,
                )
            self.comparison_ready.emit(comparison)
        except Exception as exc:
            QMessageBox.critical(self, "LSPR AI Workbench", str(exc))
