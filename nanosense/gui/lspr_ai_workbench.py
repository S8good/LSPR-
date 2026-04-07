from PyQt5.QtWidgets import QMainWindow, QTabWidget

from .lspr_single_prediction_widget import LSPRSinglePredictionWidget
from .lspr_spectrum_comparison_widget import LSPRSpectrumComparisonWidget
from ..ml.lspr_ai_service import LSPRAIService


class LSPRAIWorkbench(QMainWindow):
    def __init__(self, config=None, service=None, parent=None):
        super().__init__(parent)
        self.config = config or {}
        self._service = service

        self.setWindowTitle("LSPR AI Workbench")
        self.resize(1100, 760)

        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.single_spectrum_tab = LSPRSinglePredictionWidget(self._get_service, config=self.config, parent=self)
        self.spectrum_comparison_tab = LSPRSpectrumComparisonWidget(parent=self)
        self.single_spectrum_tab.comparison_ready.connect(self.spectrum_comparison_tab.set_comparison_result)

        self.tab_widget.addTab(self.single_spectrum_tab, "Single Spectrum")
        self.tab_widget.addTab(self.spectrum_comparison_tab, "Spectrum Comparison")

    def _get_service(self):
        if self._service is None:
            self._service = LSPRAIService(config=self.config)
        return self._service

    def set_input_spectrum(self, wavelengths, intensities, metadata=None):
        self.single_spectrum_tab.set_input_spectrum(wavelengths, intensities, metadata=metadata)
        self.tab_widget.setCurrentWidget(self.single_spectrum_tab)
