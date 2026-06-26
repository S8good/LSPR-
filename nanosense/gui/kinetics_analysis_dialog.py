import time
import numpy as np
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox,
                             QGroupBox, QFormLayout, QLabel, QDoubleSpinBox, QTabWidget, QWidget,
                             QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QEvent
import pyqtgraph as pg

from nanosense.algorithms.kinetics import fit_association, fit_dissociation
from nanosense.core.kinetics_export import export_kinetics_fit_report
from nanosense.core.kinetics_metadata import get_biomarker_by_key
from nanosense.utils.config_manager import load_settings
from nanosense.utils.plot_theme import apply_plot_theme, get_plot_theme


class KineticsAnalysisDialog(QDialog):
    def __init__(self, time_data, y_data, parent=None, biomarker=None):
        super().__init__(parent)
        self.main_window = parent
        self.setObjectName("KineticsAnalysisDialog")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setGeometry(200, 200, 900, 600)

        self.time_data = np.array(time_data)
        self.y_data = np.array(y_data)
        self.biomarker = self._normalize_biomarker(biomarker)
        self.last_results_data = None
        self.last_export_payload = None

        self._init_ui()
        self._apply_theme()
        self.calculate_button.clicked.connect(self._perform_analysis)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.save_to_db_button.clicked.connect(self._save_results_to_db)
        self.save_local_button.clicked.connect(self._save_results_locally)

        self._retranslate_ui()

    def _normalize_biomarker(self, biomarker):
        if isinstance(biomarker, dict):
            normalized = get_biomarker_by_key(biomarker.get("key"))
            normalized.update({key: value for key, value in biomarker.items() if value is not None})
            return normalized
        return get_biomarker_by_key(None)

    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        left_panel = QWidget()
        left_panel.setObjectName("kineticsAnalysisSidePanel")
        left_panel.setAttribute(Qt.WA_StyledBackground, True)
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)

        self.conc_group = QGroupBox()
        conc_layout = QFormLayout()
        self.biomarker_label_title = QLabel()
        self.biomarker_value_label = QLabel(self.biomarker.get("label", "1 CEA"))
        self.biomarker_value_label.setObjectName("analysisValueLabel")
        self.concentration_input = QDoubleSpinBox()
        self.concentration_input.setDecimals(5)
        self.concentration_input.setRange(0, 1e9)
        self.concentration_input.setValue(1.0)
        self.conc_label = QLabel()
        conc_layout.addRow(self.biomarker_label_title, self.biomarker_value_label)
        conc_layout.addRow(self.conc_label, self.concentration_input)
        self.conc_group.setLayout(conc_layout)
        self.result_group = QGroupBox()
        self.result_layout = QFormLayout()
        self.k_obs_label_title = QLabel()
        self.k_obs_label = QLabel("N/A")
        self.k_obs_err_label_title = QLabel()
        self.k_obs_err_label = QLabel("N/A")
        self.assoc_r2_label_title = QLabel()
        self.assoc_r2_label = QLabel("N/A")
        self.k_d_label_title = QLabel()
        self.k_d_label = QLabel("N/A")
        self.k_d_err_label_title = QLabel()
        self.k_d_err_label = QLabel("N/A")
        self.dissoc_r2_label_title = QLabel()
        self.dissoc_r2_label = QLabel("N/A")
        self.k_a_label_title = QLabel()
        self.k_a_label = QLabel("N/A")
        self.KD_label_title = QLabel()
        self.KD_label = QLabel("N/A")
        for label in (
            self.k_obs_label,
            self.k_obs_err_label,
            self.assoc_r2_label,
            self.k_d_label,
            self.k_d_err_label,
            self.dissoc_r2_label,
            self.k_a_label,
            self.KD_label,
        ):
            label.setObjectName("analysisValueLabel")
        self.result_layout.addRow(self.k_obs_label_title, self.k_obs_label)
        self.result_layout.addRow(self.k_obs_err_label_title, self.k_obs_err_label)
        self.result_layout.addRow(self.assoc_r2_label_title, self.assoc_r2_label)
        self.result_layout.addRow(self.k_d_label_title, self.k_d_label)
        self.result_layout.addRow(self.k_d_err_label_title, self.k_d_err_label)
        self.result_layout.addRow(self.dissoc_r2_label_title, self.dissoc_r2_label)
        self.result_layout.addRow(self.k_a_label_title, self.k_a_label)
        self.result_layout.addRow(self.KD_label_title, self.KD_label)

        self.save_to_db_button = QPushButton()
        self.save_to_db_button.setEnabled(False)
        self.result_layout.addRow(self.save_to_db_button)
        self.save_local_button = QPushButton()
        self.save_local_button.setEnabled(False)
        self.result_layout.addRow(self.save_local_button)

        self.result_group.setLayout(self.result_layout)
        self.calculate_button = QPushButton()

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        left_layout.addWidget(self.conc_group)
        left_layout.addWidget(self.calculate_button)
        left_layout.addWidget(self.result_group)
        left_layout.addStretch()
        left_layout.addWidget(self.button_box)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("kineticsAnalysisTabs")

        self._create_main_fit_tab()
        self._create_deviation_tab()
        self._create_self_exponent_tab()
        self._create_residual_tab()

        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.tabs, stretch=1)

    def _create_main_fit_tab(self):
        tab = QWidget()
        tab.setObjectName("kineticsAnalysisTab")
        tab.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(tab)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.setLabel('left', 'Response (nm)')
        self.measured_points = self.plot_widget.plot(
            self.time_data,
            self.y_data,
            pen=None,
            symbol='o',
            symbolSize=5,
        )
        t_max = float(self.time_data[-1]) if len(self.time_data) else 1.0
        self.assoc_start_line = pg.InfiniteLine(pos=t_max * 0.1, angle=90, movable=True, pen='g')
        self.assoc_end_line = pg.InfiniteLine(pos=t_max * 0.4, angle=90, movable=True, pen='g')
        self.dissoc_start_line = pg.InfiniteLine(pos=t_max * 0.5, angle=90, movable=True, pen='r')
        self.dissoc_end_line = pg.InfiniteLine(pos=t_max * 0.8, angle=90, movable=True, pen='r')
        self.plot_widget.addItem(self.assoc_start_line)
        self.plot_widget.addItem(self.assoc_end_line)
        self.plot_widget.addItem(self.dissoc_start_line)
        self.plot_widget.addItem(self.dissoc_end_line)
        self.assoc_fit_curve = self.plot_widget.plot(pen=pg.mkPen('c', width=2))
        self.dissoc_fit_curve = self.plot_widget.plot(pen=pg.mkPen('y', width=2))
        self._style_plot(self.plot_widget)
        layout.addWidget(self.plot_widget)
        self.tabs.addTab(tab, "")

    def _create_deviation_tab(self):
        tab = QWidget()
        tab.setObjectName("kineticsAnalysisTab")
        tab.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(tab)
        self.dev_plot = pg.PlotWidget()
        self.dev_plot.setLabel('bottom', 'Time (s)')
        self.dev_plot.setLabel('left', 'ΔResponse / Δt')
        self.dev_curve = self.dev_plot.plot()
        self._style_plot(self.dev_plot)
        layout.addWidget(self.dev_plot)
        self.tabs.addTab(tab, "")

    def _create_self_exponent_tab(self):
        tab = QWidget()
        tab.setObjectName("kineticsAnalysisTab")
        tab.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(tab)
        self.exp_plot = pg.PlotWidget()
        self.exp_plot.setLabel('bottom', 'Normalized Response')
        self.exp_plot.setLabel('left', 'ΔResponse / Δt')
        self.exp_points = self.exp_plot.plot(pen=None, symbol='o', symbolSize=5)
        self._style_plot(self.exp_plot)
        layout.addWidget(self.exp_plot)
        self.tabs.addTab(tab, "")

    def _create_residual_tab(self):
        tab = QWidget()
        tab.setObjectName("kineticsAnalysisTab")
        tab.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(tab)
        self.res_plot = pg.PlotWidget()
        self.res_plot.setLabel('bottom', 'Time (s)')
        self.res_plot.setLabel('left', 'Residual (Actual - Fit)')
        self.res_points = self.res_plot.plot(pen=None, symbol='o', symbolSize=5)
        self._style_plot(self.res_plot)
        layout.addWidget(self.res_plot)
        self.tabs.addTab(tab, "")

    def _style_plot(self, plot_widget):
        apply_plot_theme(plot_widget, load_settings().get('theme', 'dark'))

    def _apply_theme(self):
        # 根据主题设置不同的样式表
        settings = load_settings()
        theme = settings.get('theme', 'dark')
        
        if theme == 'light':
            # 浅色主题样式
            self.setStyleSheet("""
#KineticsAnalysisDialog {
    background-color: #F0F0F0;
    color: #000000;
    font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
    font-size: 13px;
}
#kineticsAnalysisSidePanel {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 12px;
    padding: 16px;
}
#kineticsAnalysisSidePanel QGroupBox {
    background-color: #FAFAFA;
    border: 1px solid #DDDDDD;
    border-radius: 10px;
    margin-top: 12px;
    padding: 16px;
}
#kineticsAnalysisSidePanel QGroupBox::title {
    color: #000000;
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 4px;
    font-weight: 600;
}
#kineticsAnalysisSidePanel QLabel {
    color: #000000;
}
QLabel#analysisValueLabel {
    color: #1E90FF;
    font-weight: 600;
}
QPushButton {
    background-color: #1E90FF;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    color: #FFFFFF;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #187BCD;
}
QPushButton:pressed {
    background-color: #1565C0;
}
QPushButton:disabled {
    background-color: #CCCCCC;
    color: #666666;
}
QDialogButtonBox QPushButton {
    min-width: 90px;
}
QDoubleSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    padding: 6px;
    color: #000000;
}
QDoubleSpinBox::up-button,
QDoubleSpinBox::down-button {
    background-color: #EEEEEE;
    border: none;
    width: 16px;
}
QTabWidget#kineticsAnalysisTabs::pane {
    background-color: #FAFAFA;
    border: 1px solid #DDDDDD;
    border-radius: 12px;
    padding: 12px;
}
QTabWidget#kineticsAnalysisTabs QWidget {
    background-color: transparent;
}
QTabBar::tab {
    background-color: #FFFFFF;
    color: #000000;
    padding: 8px 18px;
    border: 1px solid #CCCCCC;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 6px;
}
QTabBar::tab:selected {
    background-color: #1E90FF;
    color: #FFFFFF;
    border-color: #187BCD;
}
QTabBar::tab:hover {
    background-color: #187BCD;
}
QMessageBox {
    background-color: #FFFFFF;
    color: #000000;
}
QMessageBox QLabel {
    color: #000000;
}
QMessageBox QPushButton {
    background-color: #1E90FF;
    padding: 6px 18px;
    border-radius: 6px;
}
            """)
        else:
            # 深色主题样式
            self.setStyleSheet("""
#KineticsAnalysisDialog {
    background-color: #1A202C;
    color: #E2E8F0;
    font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
    font-size: 13px;
}
#kineticsAnalysisSidePanel {
    background-color: #2D3748;
    border: 1px solid #4A5568;
    border-radius: 12px;
    padding: 16px;
}
#kineticsAnalysisSidePanel QGroupBox {
    background-color: #1F2735;
    border: 1px solid #39475A;
    border-radius: 10px;
    margin-top: 12px;
    padding: 16px;
}
#kineticsAnalysisSidePanel QGroupBox::title {
    color: #E2E8F0;
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 4px;
    font-weight: 600;
}
#kineticsAnalysisSidePanel QLabel {
    color: #E2E8F0;
}
QLabel#analysisValueLabel {
    color: #63B3ED;
    font-weight: 600;
}
QPushButton {
    background-color: #3182CE;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    color: #FFFFFF;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2B6CB0;
}
QPushButton:pressed {
    background-color: #245A86;
}
QPushButton:disabled {
    background-color: #4A5568;
    color: #A0AEC0;
}
QDialogButtonBox QPushButton {
    min-width: 90px;
}
QDoubleSpinBox {
    background-color: #1F2735;
    border: 1px solid #39475A;
    border-radius: 6px;
    padding: 6px;
    color: #E2E8F0;
}
QDoubleSpinBox::up-button,
QDoubleSpinBox::down-button {
    background-color: #2D3748;
    border: none;
    width: 16px;
}
QTabWidget#kineticsAnalysisTabs::pane {
    background-color: #1F2735;
    border: 1px solid #39475A;
    border-radius: 12px;
    padding: 12px;
}
QTabWidget#kineticsAnalysisTabs QWidget {
    background-color: transparent;
}
QTabBar::tab {
    background-color: #2D3748;
    color: #E2E8F0;
    padding: 8px 18px;
    border: 1px solid #39475A;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 6px;
}
QTabBar::tab:selected {
    background-color: #3182CE;
    color: #FFFFFF;
    border-color: #2B6CB0;
}
QTabBar::tab:hover {
    background-color: #2B6CB0;
}
QMessageBox {
    background-color: #2D3748;
    color: #E2E8F0;
}
QMessageBox QLabel {
    color: #E2E8F0;
}
QMessageBox QPushButton {
    background-color: #3182CE;
    padding: 6px 18px;
    border-radius: 6px;
}
            """)
        self._apply_curve_theme()

    def _apply_curve_theme(self):
        theme = load_settings().get('theme', 'dark')
        if theme == 'light':
            measured_color = '#374151'
            assoc_color = '#00897B'
            dissoc_color = '#D32F2F'
            derivative_color = '#374151'
            exponent_color = '#1E88E5'
            residual_color = '#8E24AA'
        else:
            measured_color = '#E2E8F0'
            assoc_color = '#4DB6AC'
            dissoc_color = '#FF8A80'
            derivative_color = '#E2E8F0'
            exponent_color = '#63B3ED'
            residual_color = '#CE93D8'

        self.measured_points.setPen(None)
        self.measured_points.setSymbolPen(pg.mkPen(measured_color, width=1))
        self.measured_points.setSymbolBrush(pg.mkBrush(measured_color))

        assoc_pen = pg.mkPen(assoc_color, width=2)
        dissoc_pen = pg.mkPen(dissoc_color, width=2)
        marker_assoc_pen = pg.mkPen(assoc_color, width=1.5, style=Qt.DashLine)
        marker_dissoc_pen = pg.mkPen(dissoc_color, width=1.5, style=Qt.DashLine)

        self.assoc_fit_curve.setPen(assoc_pen)
        self.dissoc_fit_curve.setPen(dissoc_pen)
        self.assoc_start_line.setPen(marker_assoc_pen)
        self.assoc_end_line.setPen(marker_assoc_pen)
        self.dissoc_start_line.setPen(marker_dissoc_pen)
        self.dissoc_end_line.setPen(marker_dissoc_pen)

        self.dev_curve.setPen(pg.mkPen(derivative_color, width=1.5))
        self.exp_points.setPen(None)
        self.exp_points.setSymbolPen(pg.mkPen(exponent_color, width=1))
        self.exp_points.setSymbolBrush(pg.mkBrush(exponent_color))
        self.res_points.setPen(None)
        self.res_points.setSymbolPen(pg.mkPen(residual_color, width=1))
        self.res_points.setSymbolBrush(pg.mkBrush(residual_color))

    def _reset_result_labels(self):
        for label in (
            self.k_obs_label,
            self.k_obs_err_label,
            self.assoc_r2_label,
            self.k_d_label,
            self.k_d_err_label,
            self.dissoc_r2_label,
            self.k_a_label,
            self.KD_label,
        ):
            label.setText(self.tr("N/A"))
        self.last_results_data = None
        self.last_export_payload = None
        self.save_to_db_button.setEnabled(False)
        self.save_local_button.setEnabled(False)

    def _build_results_data(self, parameters, time_data, response_data):
        time_series = [
            {"time_s": float(t), "peak_nm": float(y)}
            for t, y in zip(time_data, response_data)
            if np.isfinite(t) and np.isfinite(y)
        ]
        results_data = {
            "biomarker_key": self.biomarker.get("key"),
            "biomarker_name": self.biomarker.get("name"),
            "biomarker_label": self.biomarker.get("label"),
            "k_obs": f"{parameters['k_obs']:.4e}",
            "k_obs_err": f"{parameters['k_obs_err']:.4e}",
            "association_r2": f"{parameters['association_r2']:.4f}",
            "k_d": f"{parameters['k_d']:.4e}",
            "k_d_err": f"{parameters['k_d_err']:.4e}",
            "dissociation_r2": f"{parameters['dissociation_r2']:.4f}",
            "k_a": f"{parameters['k_a']:.4e}",
            "KD": f"{parameters['KD']:.4e}",
            "Analyte_Concentration_nM": float(self.concentration_input.value()),
        }
        if time_series:
            results_data["time_series"] = time_series
        return results_data

    def _build_export_payload(
            self,
            parameters,
            regions,
            time_data,
            response_data,
            assoc_time,
            assoc_y,
            assoc_fit_results,
            dissoc_time,
            dissoc_y,
            dissoc_fit_results,
            diagnostics,
    ):
        return {
            "biomarker": dict(self.biomarker),
            "concentration_nM": float(self.concentration_input.value()),
            "parameters": dict(parameters),
            "regions": dict(regions),
            "series": [
                {"time_s": float(t), "peak_nm": float(y)}
                for t, y in zip(time_data, response_data)
                if np.isfinite(t) and np.isfinite(y)
            ],
            "association": {
                "time_s": assoc_time.astype(float).tolist(),
                "response_nm": assoc_y.astype(float).tolist(),
                "fit_time_s": np.asarray(assoc_fit_results["t_fit"], dtype=float).tolist(),
                "fit_response_nm": np.asarray(assoc_fit_results["y_fit"], dtype=float).tolist(),
                "residual_nm": np.asarray(assoc_fit_results["residuals"], dtype=float).tolist(),
            },
            "dissociation": {
                "time_s": dissoc_time.astype(float).tolist(),
                "response_nm": dissoc_y.astype(float).tolist(),
                "fit_time_s": np.asarray(dissoc_fit_results["t_fit"], dtype=float).tolist(),
                "fit_response_nm": np.asarray(dissoc_fit_results["y_fit"], dtype=float).tolist(),
                "residual_nm": np.asarray(dissoc_fit_results["residuals"], dtype=float).tolist(),
            },
            "diagnostics": diagnostics,
        }

    def _perform_analysis(self):
        """执行拟合流程：选区 -> 拟合 -> 计算 -> 显示结果"""
        try:
            self.last_results_data = None
            self.last_export_payload = None
            self.save_to_db_button.setEnabled(False)
            self.save_local_button.setEnabled(False)

            # 1. 复制并清洗原始数据，避免后续过程修改 self.time_data / self.y_data
            time_data = np.array(self.time_data, dtype=float)
            response_data = np.array(self.y_data, dtype=float)

            finite_mask = np.isfinite(time_data) & np.isfinite(response_data)
            if not np.all(finite_mask):
                time_data = time_data[finite_mask]
                response_data = response_data[finite_mask]

            if time_data.size < 5 or response_data.size < 5:
                self._reset_result_labels()
                QMessageBox.warning(
                    self,
                    self.tr("Insufficient Data"),
                    self.tr("Not enough valid data points to perform kinetic analysis. Please collect more measurements.")
                )
                self.save_to_db_button.setEnabled(False)
                return

            order = np.argsort(time_data)
            time_data = time_data[order]
            response_data = response_data[order]

            assoc_start_t = self.assoc_start_line.value()
            assoc_end_t = self.assoc_end_line.value()
            dissoc_start_t = self.dissoc_start_line.value()
            dissoc_end_t = self.dissoc_end_line.value()

            if assoc_start_t >= assoc_end_t or dissoc_start_t >= dissoc_end_t:
                self._reset_result_labels()
                QMessageBox.warning(
                    self,
                    self.tr("Invalid Region"),
                    self.tr("Please make sure the association and dissociation vertical markers define valid ranges (start < end).")
                )
                self.save_to_db_button.setEnabled(False)
                return

            assoc_mask = (time_data >= assoc_start_t) & (time_data <= assoc_end_t)
            dissoc_mask = (time_data >= dissoc_start_t) & (time_data <= dissoc_end_t)

            if np.sum(assoc_mask) < 4 or np.sum(dissoc_mask) < 4:
                self._reset_result_labels()
                QMessageBox.warning(
                    self,
                    self.tr("Insufficient Data"),
                    self.tr("Selected association or dissociation region has fewer than 4 points. Please adjust the vertical markers.")
                )
                self.save_to_db_button.setEnabled(False)
                return

            dissoc_time = time_data[dissoc_mask]
            dissoc_y = response_data[dissoc_mask]
            dissoc_fit_results = fit_dissociation(dissoc_time, dissoc_y)
            if dissoc_fit_results is None:
                self._reset_result_labels()
                self.k_d_label.setText(self.tr("Fit Failed"))
                self.save_to_db_button.setEnabled(False)
                QMessageBox.warning(
                    self,
                    self.tr("Fit Failed"),
                    self.tr("Unable to fit the dissociation segment. Try widening the time window or smoothing the data.")
                )
                return

            k_d = abs(dissoc_fit_results['k_off'])
            self.k_d_label.setText(f"{k_d:.4e}")
            self.k_d_err_label.setText(f"{dissoc_fit_results['k_off_err']:.4e}")
            self.dissoc_r2_label.setText(f"{dissoc_fit_results['r2']:.4f}")
            self.dissoc_fit_curve.setData(dissoc_fit_results["t_fit"], dissoc_fit_results["y_fit"])

            assoc_time = time_data[assoc_mask]
            assoc_y = response_data[assoc_mask]
            assoc_fit_results = fit_association(assoc_time, assoc_y)
            if assoc_fit_results is None:
                self._reset_result_labels()
                self.k_obs_label.setText(self.tr("Fit Failed"))
                self.save_to_db_button.setEnabled(False)
                QMessageBox.warning(
                    self,
                    self.tr("Fit Failed"),
                    self.tr("Unable to fit the association segment. Please adjust the markers or check the signal quality.")
                )
                return

            k_obs = abs(assoc_fit_results['k_obs'])
            self.k_obs_label.setText(f"{k_obs:.4e}")
            self.k_obs_err_label.setText(f"{assoc_fit_results['k_obs_err']:.4e}")
            self.assoc_r2_label.setText(f"{assoc_fit_results['r2']:.4f}")
            self.assoc_fit_curve.setData(assoc_fit_results["t_fit"], assoc_fit_results["y_fit"])

            concentration_M = self.concentration_input.value() * 1e-9
            if concentration_M == 0:
                self.k_a_label.setText(self.tr("Concentration cannot be zero"))
                self.KD_label.setText(self.tr("Calculation Error"))
                self.save_to_db_button.setEnabled(False)
                QMessageBox.warning(
                    self,
                    self.tr("Invalid Concentration"),
                    self.tr("Analyte concentration cannot be zero when calculating kinetic constants.")
                )
                return

            if k_obs <= k_d:
                self.k_a_label.setText(self.tr("Calculation Error (k_obs <= k_d)"))
                self.KD_label.setText(self.tr("Calculation Error"))
                self.save_to_db_button.setEnabled(False)
                QMessageBox.warning(
                    self,
                    self.tr("Calculation Error"),
                    self.tr("k_obs must be greater than k_d. Adjust the association window or verify the data.")
                )
                return

            k_a = (k_obs - k_d) / concentration_M
            KD = k_d / k_a
            self.k_a_label.setText(f"{k_a:.4e}")
            self.KD_label.setText(f"{KD:.4e}")

            delta_y = np.diff(response_data)
            delta_t = np.diff(time_data)
            if len(delta_t) == 0 or np.allclose(delta_t, 0):
                derivative = np.zeros_like(delta_t)
            else:
                derivative = delta_y / (delta_t + 1e-9)

            if len(derivative) > 0:
                self.dev_curve.setData(time_data[:-1], derivative)

            y_range = response_data.max() - response_data.min()
            normalized_y = np.array([], dtype=float)
            if y_range > 0 and len(response_data) > 1:
                normalized_y = (response_data - response_data.min()) / y_range
                self.exp_points.setData(normalized_y[:-1], derivative)

            residual_time = np.concatenate([assoc_time, dissoc_time])
            residual_values = np.concatenate([assoc_fit_results["residuals"], dissoc_fit_results["residuals"]])
            self.res_points.setData(
                residual_time,
                residual_values
            )

            parameters = {
                "k_obs": float(k_obs),
                "k_obs_err": float(assoc_fit_results["k_obs_err"]),
                "association_r2": float(assoc_fit_results["r2"]),
                "k_d": float(k_d),
                "k_d_err": float(dissoc_fit_results["k_off_err"]),
                "dissociation_r2": float(dissoc_fit_results["r2"]),
                "k_a": float(k_a),
                "KD": float(KD),
            }
            regions = {
                "association_start_s": float(assoc_start_t),
                "association_end_s": float(assoc_end_t),
                "dissociation_start_s": float(dissoc_start_t),
                "dissociation_end_s": float(dissoc_end_t),
            }
            diagnostics = {
                "derivative_time_s": time_data[:-1].astype(float).tolist(),
                "derivative_nm_per_s": derivative.astype(float).tolist(),
                "normalized_response": normalized_y[:-1].astype(float).tolist() if normalized_y.size else [],
                "self_exponent_derivative": derivative.astype(float).tolist(),
                "residual_time_s": residual_time.astype(float).tolist(),
                "residual_nm": residual_values.astype(float).tolist(),
            }
            self.last_results_data = self._build_results_data(parameters, time_data, response_data)
            self.last_export_payload = self._build_export_payload(
                parameters,
                regions,
                time_data,
                response_data,
                assoc_time,
                assoc_y,
                assoc_fit_results,
                dissoc_time,
                dissoc_y,
                dissoc_fit_results,
                diagnostics,
            )
            self.save_to_db_button.setEnabled(True)
            self.save_local_button.setEnabled(True)

        except Exception as exc:
            self.save_to_db_button.setEnabled(False)
            self.save_local_button.setEnabled(False)
            self._reset_result_labels()
            QMessageBox.critical(
                self,
                self.tr("Unexpected Error"),
                self.tr("An unexpected error occurred during kinetic analysis:\n{0}").format(str(exc))
            )

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self._retranslate_ui()
        super().changeEvent(event)

    def _retranslate_ui(self):
        self.setWindowTitle(self.tr("Kinetics and Affinity Analysis"))

        self.conc_group.setTitle(self.tr("Experiment Parameters"))
        self.biomarker_label_title.setText(self.tr("Cancer Biomarker:"))
        self.biomarker_value_label.setText(self.biomarker.get("label", "1 CEA"))
        self.conc_label.setText(self.tr("Analyte Concentration [A] (nM):"))
        self.result_group.setTitle(self.tr("Kinetics Calculation Results"))
        self.k_obs_label_title.setText(self.tr("k_obs (1/s):"))
        self.k_obs_err_label_title.setText(self.tr("k_obs Error (1/s):"))
        self.assoc_r2_label_title.setText(self.tr("Association R²:"))
        self.k_d_label_title.setText(self.tr("k_d (1/s):"))
        self.k_d_err_label_title.setText(self.tr("k_d Error (1/s):"))
        self.dissoc_r2_label_title.setText(self.tr("Dissociation R²:"))
        self.k_a_label_title.setText(self.tr("k_a (1/M·s):"))
        self.KD_label_title.setText(self.tr("KD (M):"))
        self.calculate_button.setText(self.tr("Calculate Kinetic Constants"))
        self.save_to_db_button.setText(self.tr("Save Results to Database"))
        self.save_local_button.setText(self.tr("Save Results Locally..."))
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("OK"))

        # Tab页和图表
        self.tabs.setTabText(0, self.tr("Main Fit Plot"))
        self.tabs.setTabText(1, self.tr("Deviation Plot"))
        self.tabs.setTabText(2, self.tr("Self-Exponent Plot"))
        self.tabs.setTabText(3, self.tr("Residual Plot"))

        self.plot_widget.setTitle(
            self.tr("Drag vertical lines to select Association (green) & Dissociation (red) regions"),
            color=get_plot_theme(load_settings().get('theme', 'dark')).title,
            size="12pt",
        )
        self.plot_widget.setLabel('bottom', self.tr('Time (s)'))
        self.plot_widget.setLabel('left', self.tr('Response (nm)'))

        palette = get_plot_theme(load_settings().get('theme', 'dark'))
        self.dev_plot.setTitle(self.tr("Deviation Plot"), color=palette.title, size="12pt")
        self.res_plot.setTitle(self.tr("Residual Plot"), color=palette.title, size="12pt")
        self.exp_plot.setTitle(self.tr("Self-Exponent Plot"), color=palette.title, size="12pt")
        for plot in (self.plot_widget, self.dev_plot, self.res_plot, self.exp_plot):
            apply_plot_theme(plot, palette.name)
        self._apply_curve_theme()

    def _save_results_to_db(self):
        """将当前显示的动力学分析结果保存到数据库。"""
        if not self.main_window or not self.main_window.db_manager:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Database is not available."))
            return
        if not self.last_results_data:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("No completed kinetics fit is available to save. Please calculate first.")
            )
            return

        try:
            experiment_id = self.main_window.get_or_create_current_experiment_id()
            if experiment_id is None:
                return

            results_data = dict(self.last_results_data)
            if self.tr("Fit Failed") in results_data.values() or self.tr("Calculation Error") in results_data.values():
                QMessageBox.warning(self, self.tr("Warning"),
                                    self.tr("Cannot save, the calculation has failed or contains errors."))
                return

            self.main_window.db_manager.save_analysis_result(
                experiment_id=experiment_id,
                analysis_type='Kinetics_Fit',
                result_data=results_data
            )

            QMessageBox.information(self, self.tr("Success"),
                                    self.tr("Kinetics analysis results have been saved to the database."))
            self.save_to_db_button.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, self.tr("Database Error"),
                                 self.tr("An error occurred while saving to the database:\n{0}").format(str(e)))

    def _save_results_locally(self):
        if not self.last_export_payload:
            QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("No completed kinetics fit is available to export. Please calculate first.")
            )
            return

        settings = load_settings()
        default_path = settings.get("default_save_path", "")
        if self.main_window is not None and hasattr(self.main_window, "app_settings"):
            default_path = self.main_window.app_settings.get("default_save_path", default_path)

        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.tr("Select Kinetics Export Folder"),
            default_path,
        )
        if not folder_path:
            return

        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            result = export_kinetics_fit_report(self.last_export_payload, folder_path, timestamp)
            QMessageBox.information(
                self,
                self.tr("Local Export Complete"),
                self.tr("Kinetics fit report exported to:\n{0}").format(result["export_dir"])
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.tr("Local Export Failed"),
                self.tr("An error occurred while exporting kinetics results:\n{0}").format(str(exc))
            )


