from PyQt5.QtWidgets import QFormLayout, QLabel, QGroupBox


class LSPRResultSummaryWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Prediction Summary")

        layout = QFormLayout(self)
        self.reported_text_value = QLabel("-")
        self.report_mode_value = QLabel("-")
        self.concentration_value = QLabel("-")
        self.uloq_value = QLabel("-")
        self.model_mode_value = QLabel("-")
        self.backend_value = QLabel("-")
        self.prediction_model_value = QLabel("-")
        self.prediction_backend_value = QLabel("-")
        self.generator_model_value = QLabel("-")
        self.generator_backend_value = QLabel("-")
        self.fallback_applied_value = QLabel("-")

        layout.addRow("Reported:", self.reported_text_value)
        layout.addRow("Mode:", self.report_mode_value)
        layout.addRow("Concentration:", self.concentration_value)
        layout.addRow("ULOQ:", self.uloq_value)
        layout.addRow("Model:", self.model_mode_value)
        layout.addRow("Backend:", self.backend_value)
        layout.addRow("Prediction Model:", self.prediction_model_value)
        layout.addRow("Prediction Backend:", self.prediction_backend_value)
        layout.addRow("Spectrum Generator:", self.generator_model_value)
        layout.addRow("Generator Backend:", self.generator_backend_value)
        layout.addRow("Fallback Applied:", self.fallback_applied_value)

    def clear_result(self):
        for label in (
            self.reported_text_value,
            self.report_mode_value,
            self.concentration_value,
            self.uloq_value,
            self.model_mode_value,
            self.backend_value,
            self.prediction_model_value,
            self.prediction_backend_value,
            self.generator_model_value,
            self.generator_backend_value,
            self.fallback_applied_value,
        ):
            label.setText("-")

    def set_result(self, result):
        self.reported_text_value.setText(str(result.reported_text))
        self.report_mode_value.setText(str(result.report_mode))
        self.concentration_value.setText(f"{float(result.predicted_concentration_ng_ml):.4f} ng/ml")
        self.uloq_value.setText("-" if result.uloq_ng_ml is None else f"{float(result.uloq_ng_ml):.4f}")
        self.model_mode_value.setText(str(result.model_mode))
        self.backend_value.setText(str(result.backend))
        self.prediction_model_value.setText(str(getattr(result, "prediction_model_mode", result.model_mode)))
        self.prediction_backend_value.setText(str(getattr(result, "prediction_backend", result.backend)))
        self.generator_model_value.setText(str(getattr(result, "generator_model_mode", "-")))
        self.generator_backend_value.setText(str(getattr(result, "generator_backend", "-")))
        self.fallback_applied_value.setText("Yes" if bool(getattr(result, "fallback_applied", False)) else "No")
