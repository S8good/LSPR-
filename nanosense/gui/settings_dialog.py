import os

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QDoubleSpinBox,
)

from nanosense.core.database_manager import DatabaseManager


class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(560)
        self.settings = current_settings.copy()

        self._init_ui()
        self._connect_signals()
        self._populate_initial_values()
        self._retranslate_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        self.paths_group = QGroupBox()
        paths_layout = QFormLayout(self.paths_group)

        self.save_path_edit = QLineEdit()
        self.save_path_browse_btn = QPushButton()
        save_path_layout = QHBoxLayout()
        save_path_layout.addWidget(self.save_path_edit)
        save_path_layout.addWidget(self.save_path_browse_btn)
        self.save_path_label = QLabel()
        paths_layout.addRow(self.save_path_label, save_path_layout)

        self.load_path_edit = QLineEdit()
        self.load_path_browse_btn = QPushButton()
        load_path_layout = QHBoxLayout()
        load_path_layout.addWidget(self.load_path_edit)
        load_path_layout.addWidget(self.load_path_browse_btn)
        self.load_path_label = QLabel()
        paths_layout.addRow(self.load_path_label, load_path_layout)

        self.analysis_group = QGroupBox()
        analysis_layout = QFormLayout(self.analysis_group)

        self.wl_start_spinbox = QDoubleSpinBox()
        self.wl_end_spinbox = QDoubleSpinBox()
        for spinbox in (self.wl_start_spinbox, self.wl_end_spinbox):
            spinbox.setDecimals(1)
            spinbox.setRange(200.0, 2000.0)
            spinbox.setSingleStep(10.0)
            spinbox.setSuffix(" nm")

        self.wl_start_label = QLabel()
        self.wl_end_label = QLabel()
        analysis_layout.addRow(self.wl_start_label, self.wl_start_spinbox)
        analysis_layout.addRow(self.wl_end_label, self.wl_end_spinbox)

        self.theme_group = QGroupBox()
        theme_layout = QFormLayout(self.theme_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")
        self.theme_label = QLabel()
        theme_layout.addRow(self.theme_label, self.theme_combo)

        self.db_group = QGroupBox()
        db_layout = QFormLayout(self.db_group)
        self.db_path_edit = QLineEdit()
        self.db_path_browse_btn = QPushButton()
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_edit)
        db_path_layout.addWidget(self.db_path_browse_btn)
        self.db_path_label = QLabel()
        db_layout.addRow(self.db_path_label, db_path_layout)
        self.init_db_button = QPushButton()
        db_layout.addRow(self.init_db_button)

        self.lspr_group = QGroupBox("LSPR AI")
        lspr_layout = QFormLayout(self.lspr_group)

        self.lspr_master_root_edit = QLineEdit()
        self.lspr_master_root_browse_btn = QPushButton()
        lspr_root_layout = QHBoxLayout()
        lspr_root_layout.addWidget(self.lspr_master_root_edit)
        lspr_root_layout.addWidget(self.lspr_master_root_browse_btn)
        self.lspr_master_root_label = QLabel()
        lspr_layout.addRow(self.lspr_master_root_label, lspr_root_layout)

        self.lspr_default_model_mode_combo = QComboBox()
        self.lspr_default_model_mode_combo.addItem("Auto", "auto")
        self.lspr_default_model_mode_combo.addItem("In-process", "inprocess")
        self.lspr_default_model_mode_combo.addItem("Subprocess", "subprocess")
        self.lspr_default_model_mode_label = QLabel()
        lspr_layout.addRow(self.lspr_default_model_mode_label, self.lspr_default_model_mode_combo)

        self.lspr_default_artifact_dir_edit = QLineEdit()
        self.lspr_default_artifact_dir_browse_btn = QPushButton()
        artifact_layout = QHBoxLayout()
        artifact_layout.addWidget(self.lspr_default_artifact_dir_edit)
        artifact_layout.addWidget(self.lspr_default_artifact_dir_browse_btn)
        self.lspr_default_artifact_dir_label = QLabel()
        lspr_layout.addRow(self.lspr_default_artifact_dir_label, artifact_layout)

        self.lspr_batch_export_dir_edit = QLineEdit()
        self.lspr_batch_export_dir_browse_btn = QPushButton()
        batch_export_layout = QHBoxLayout()
        batch_export_layout.addWidget(self.lspr_batch_export_dir_edit)
        batch_export_layout.addWidget(self.lspr_batch_export_dir_browse_btn)
        self.lspr_batch_export_dir_label = QLabel()
        lspr_layout.addRow(self.lspr_batch_export_dir_label, batch_export_layout)

        self.lspr_enable_digital_twin_overlay_checkbox = QCheckBox()
        self.lspr_enable_digital_twin_overlay_label = QLabel()
        lspr_layout.addRow(
            self.lspr_enable_digital_twin_overlay_label,
            self.lspr_enable_digital_twin_overlay_checkbox,
        )

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        main_layout.addWidget(self.paths_group)
        main_layout.addWidget(self.analysis_group)
        main_layout.addWidget(self.theme_group)
        main_layout.addWidget(self.db_group)
        main_layout.addWidget(self.lspr_group)
        main_layout.addWidget(self.button_box)

    def _connect_signals(self):
        self.save_path_browse_btn.clicked.connect(lambda: self._browse_folder(self.save_path_edit))
        self.load_path_browse_btn.clicked.connect(lambda: self._browse_folder(self.load_path_edit))
        self.db_path_browse_btn.clicked.connect(self._browse_db_file)
        self.init_db_button.clicked.connect(self._initialize_db)
        self.lspr_master_root_browse_btn.clicked.connect(lambda: self._browse_folder(self.lspr_master_root_edit))
        self.lspr_default_artifact_dir_browse_btn.clicked.connect(
            lambda: self._browse_folder(self.lspr_default_artifact_dir_edit)
        )
        self.lspr_batch_export_dir_browse_btn.clicked.connect(
            lambda: self._browse_folder(self.lspr_batch_export_dir_edit)
        )
        self.button_box.accepted.connect(self._save_and_accept)
        self.button_box.rejected.connect(self.reject)

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self._retranslate_ui()
        super().changeEvent(event)

    def _retranslate_ui(self):
        browse_text = self.tr("Browse...")
        self.setWindowTitle(self.tr("Customize Parameters"))

        self.paths_group.setTitle(self.tr("Default Paths"))
        self.save_path_label.setText(self.tr("Default Save/Export Path:"))
        self.load_path_label.setText(self.tr("Default Load/Import Path:"))
        self.save_path_browse_btn.setText(browse_text)
        self.load_path_browse_btn.setText(browse_text)

        self.analysis_group.setTitle(self.tr("Batch Data Analysis Parameters"))
        self.wl_start_label.setText(self.tr("Peak Analysis Start Wavelength:"))
        self.wl_end_label.setText(self.tr("Peak Analysis End Wavelength:"))

        self.theme_group.setTitle(self.tr("Theme Settings"))
        self.theme_label.setText(self.tr("Application Theme:"))

        self.db_group.setTitle(self.tr("Database Settings"))
        self.db_path_label.setText(self.tr("Database File Path:"))
        self.db_path_browse_btn.setText(browse_text)
        self.init_db_button.setText(self.tr("Initialize/Create Database"))

        self.lspr_group.setTitle(self.tr("LSPR AI"))
        self.lspr_master_root_label.setText(self.tr("LSPR Master Root:"))
        self.lspr_default_model_mode_label.setText(self.tr("Default Backend Mode:"))
        self.lspr_default_artifact_dir_label.setText(self.tr("Artifact Directory:"))
        self.lspr_batch_export_dir_label.setText(self.tr("Batch Export Directory:"))
        self.lspr_enable_digital_twin_overlay_label.setText(self.tr("Enable Digital Twin Overlay:"))
        self.lspr_master_root_browse_btn.setText(browse_text)
        self.lspr_default_artifact_dir_browse_btn.setText(browse_text)
        self.lspr_batch_export_dir_browse_btn.setText(browse_text)

        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("OK"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.tr("Cancel"))

    def _browse_folder(self, line_edit):
        directory = QFileDialog.getExistingDirectory(self, self.tr("Select Folder"), line_edit.text())
        if directory:
            line_edit.setText(directory)

    def _browse_db_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Select Database File"),
            self.db_path_edit.text(),
            "SQLite Database (*.db)",
        )
        if path:
            self.db_path_edit.setText(path)

    def _initialize_db(self):
        db_path = self.db_path_edit.text()
        if not db_path:
            QMessageBox.warning(self, self.tr("Warning"), self.tr("Database path cannot be empty."))
            return
        try:
            DatabaseManager(db_path)
            QMessageBox.information(
                self,
                self.tr("Success"),
                self.tr("Database successfully initialized at:\n{0}").format(db_path),
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Failed to initialize database: {0}").format(str(exc)),
            )

    def _populate_initial_values(self):
        self.save_path_edit.setText(self.settings.get("default_save_path", os.path.expanduser("~")))
        self.load_path_edit.setText(self.settings.get("default_load_path", os.path.expanduser("~")))
        self.wl_start_spinbox.setValue(self.settings.get("analysis_wl_start", 450.0))
        self.wl_end_spinbox.setValue(self.settings.get("analysis_wl_end", 750.0))

        theme = self.settings.get("theme", "dark")
        theme_index = self.theme_combo.findData(theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)

        default_db_path = os.path.join(os.path.expanduser("~"), ".nanosense", "nanosense_data.db")
        self.db_path_edit.setText(self.settings.get("database_path", default_db_path))

        self.lspr_master_root_edit.setText(self.settings.get("lspr_master_root", ""))
        model_mode = self.settings.get("lspr_default_model_mode", "auto")
        mode_index = self.lspr_default_model_mode_combo.findData(model_mode)
        if mode_index >= 0:
            self.lspr_default_model_mode_combo.setCurrentIndex(mode_index)
        self.lspr_default_artifact_dir_edit.setText(self.settings.get("lspr_default_artifact_dir", ""))
        self.lspr_batch_export_dir_edit.setText(self.settings.get("lspr_batch_export_dir", ""))
        self.lspr_enable_digital_twin_overlay_checkbox.setChecked(
            bool(self.settings.get("lspr_enable_digital_twin_overlay", True))
        )

    def _save_and_accept(self):
        self.settings["default_save_path"] = self.save_path_edit.text()
        self.settings["default_load_path"] = self.load_path_edit.text()
        self.settings["analysis_wl_start"] = self.wl_start_spinbox.value()
        self.settings["analysis_wl_end"] = self.wl_end_spinbox.value()
        self.settings["theme"] = self.theme_combo.currentData()
        self.settings["database_path"] = self.db_path_edit.text()
        self.settings["lspr_master_root"] = self.lspr_master_root_edit.text()
        self.settings["lspr_default_model_mode"] = self.lspr_default_model_mode_combo.currentData()
        self.settings["lspr_default_artifact_dir"] = self.lspr_default_artifact_dir_edit.text()
        self.settings["lspr_batch_export_dir"] = self.lspr_batch_export_dir_edit.text()
        self.settings["lspr_enable_digital_twin_overlay"] = (
            self.lspr_enable_digital_twin_overlay_checkbox.isChecked()
        )
        self.accept()

    def get_settings(self):
        return self.settings
