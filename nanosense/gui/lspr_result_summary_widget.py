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

        layout.addRow("Reported:", self.reported_text_value)
        layout.addRow("Mode:", self.report_mode_value)
        layout.addRow("Concentration:", self.concentration_value)
        layout.addRow("ULOQ:", self.uloq_value)
        layout.addRow("Model:", self.model_mode_value)
        layout.addRow("Backend:", self.backend_value)

    def clear_result(self):
        for label in (
            self.reported_text_value,
            self.report_mode_value,
            self.concentration_value,
            self.uloq_value,
            self.model_mode_value,
            self.backend_value,
        ):
            label.setText("-")

    def set_result(self, result):
        self.reported_text_value.setText(str(result.reported_text))
        self.report_mode_value.setText(str(result.report_mode))
        self.concentration_value.setText(f"{float(result.predicted_concentration_ng_ml):.4f} ng/ml")
        self.uloq_value.setText("-" if result.uloq_ng_ml is None else f"{float(result.uloq_ng_ml):.4f}")
        self.model_mode_value.setText(str(result.model_mode))
        self.backend_value.setText(str(result.backend))
