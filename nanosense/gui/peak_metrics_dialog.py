# nanosense/gui/peak_metrics_dialog.py

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QDialogButtonBox, QHeaderView)
from PyQt5.QtCore import QEvent  # 新增 QEvent
import numpy as np


def normalize_peak_metric_data(peak_data):
    """Normalize peak table payloads while keeping legacy wavelength keys working."""
    peak_data = peak_data or {}
    positions = peak_data.get('positions', peak_data.get('wavelengths', []))
    return {
        'positions': list(positions),
        'heights': list(peak_data.get('heights', [])),
        'fwhms': list(peak_data.get('fwhms', [])),
        'position_label': peak_data.get('position_label', 'Peak Wavelength (nm)'),
        'fwhm_label': peak_data.get('fwhm_label', 'FWHM (nm)'),
    }


class PeakMetricsDialog(QDialog):
    """
    一个以表格形式显示所有峰值详细参数的对话框。
    """

    def __init__(self, peak_data, parent=None):
        super().__init__(parent)
        self.setGeometry(250, 250, 500, 300)

        self.peak_data = normalize_peak_metric_data(peak_data)  # 保存数据以便重新翻译

        self._init_ui()
        self._retranslate_ui()  # 设置初始文本

    def _init_ui(self):
        """
        创建并布局所有UI控件。
        """
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self._populate_table()
        layout.addWidget(self.table)

        # 添加OK按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)

    def changeEvent(self, event):
        """
        响应语言变化事件。
        """
        if event.type() == QEvent.LanguageChange:
            self._retranslate_ui()
        super().changeEvent(event)

    def _retranslate_ui(self):
        """
        重新翻译此控件内的所有UI文本。
        """
        self.setWindowTitle(self.tr("Peak Metrics"))
        self.table.setHorizontalHeaderLabels([
            self.tr(self.peak_data.get('position_label', "Peak Wavelength (nm)")),
            self.tr("Peak Intensity"),
            self.tr(self.peak_data.get('fwhm_label', "FWHM (nm)"))
        ])
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("OK"))

    def _populate_table(self):
        """用寻峰结果填充表格。"""
        if not self.peak_data:
            return

        self.table.setRowCount(len(self.peak_data['positions']))

        for i, (position, height, fwhm) in enumerate(zip(
                self.peak_data['positions'],
                self.peak_data['heights'],
                self.peak_data['fwhms']
        )):
            self.table.setItem(i, 0, QTableWidgetItem(f"{position:.4f}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{height:.4f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{fwhm:.4f}"))
