# nanosense/gui/welcome_widget.py

import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QGraphicsDropShadowEffect, QHBoxLayout, QComboBox, QSizePolicy
from PyQt5.QtGui import QFont, QIcon, QPainter, QPixmap, QColor
from PyQt5.QtCore import QSize, QTimer, pyqtSignal, Qt

from ..utils.config_manager import load_settings, save_settings


# --- 【新增】创建一个自定义的按钮类来处理悬停效果 ---
class HoverButton(QPushButton):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self._setup_style()  # 设置按钮的基础样式（背景图等）

        # 创建一个辉光效果，并默认设置为禁用
        self.glow_effect = QGraphicsDropShadowEffect(self)
        self.glow_effect.setBlurRadius(25)
        self.glow_effect.setColor(QColor(255, 255, 150, 160))  # 柔和的淡金色
        self.glow_effect.setOffset(0, 0)
        self.glow_effect.setEnabled(False)  # 关键：默认不显示
        self.setGraphicsEffect(self.glow_effect)

    def _setup_style(self):
        """设置按钮的基础样式"""
        if os.path.exists(self.image_path):
            style_path = self.image_path.replace('\\', '/')
            self.setStyleSheet(f"""
                QPushButton {{
                    border-image: url({style_path});
                    background-repeat: no-repeat;
                    background-position: center;
                    border: none;
                    padding: 0px;
                    border-radius: 8px;
                }}
            """)

    def enterEvent(self, event):
        """当鼠标光标进入按钮区域时，此方法被调用"""
        self.glow_effect.setEnabled(True)  # 启用辉光效果
        super().enterEvent(event)

    def leaveEvent(self, event):
        """当鼠标光标离开按钮区域时，此方法被调用"""
        self.glow_effect.setEnabled(False)  # 禁用辉光效果
        super().leaveEvent(event)


class WelcomeWidget(QWidget):
    mode_selected = pyqtSignal(str, bool, str) # str: 模式名, bool: 是否使用真实硬件, str: 硬件厂商('ideaoptics'/'ocean'/'mock')

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(self.tr("Welcome - Nanophotonics sensing detection data visualization analysis system"))
        icon_path = os.path.join(
            os.path.dirname(__file__), 'assets', 'app_icon.ico'
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setFixedSize(1080, 620)
        self.setObjectName("welcomeWidget")

        self.background_pixmap = None
        background_image_path = os.path.join(
            os.path.dirname(__file__), 'assets', 'background.png'
        )
        if os.path.exists(background_image_path):
            self.background_pixmap = QPixmap(background_image_path)

        self.init_ui()

    def paintEvent(self, event):
        if self.background_pixmap and not self.background_pixmap.isNull():
            painter = QPainter(self)
            painter.drawPixmap(self.rect(), self.background_pixmap)

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "_onboarding_auto_checked", False):
            return
        self._onboarding_auto_checked = True
        try:
            settings = load_settings()
        except Exception:
            settings = {}
        if not settings.get("onboarding_welcome_done", False):
            QTimer.singleShot(250, self._start_onboarding_tour)

    def _start_onboarding_tour(self):
        from .onboarding_tours import run_welcome_tour

        def _on_finished(_completed):
            try:
                settings = load_settings()
            except Exception:
                settings = {}
            settings["onboarding_welcome_done"] = True
            try:
                save_settings(settings)
            except Exception:
                pass

        run_welcome_tour(self, on_finished=_on_finished)

    def init_ui(self):
        self.setStyleSheet("""
                #welcomeWidget QLabel { background: transparent; color: #E2E8F0; font-weight: bold; }
                #mainTitleLabel { color: white; }
                #subtitleLabel { color: #E0E0E0; }
            """)

        main_layout = QVBoxLayout(self)

        # --- Hardware Mode Switch ---
        top_layout = QHBoxLayout()
        top_layout.addStretch()

        self.onboarding_button = QPushButton(self.tr("Onboarding"))
        self.onboarding_button.setObjectName("onboardingButton")
        self.onboarding_button.setStyleSheet(
            """
            QPushButton#onboardingButton {
                color: white;
                font-weight: bold;
                background-color: #3182CE;
                border: 1px solid #2B6CB0;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton#onboardingButton:hover { background-color: #2B6CB0; }
            """
        )
        self.onboarding_button.clicked.connect(self._start_onboarding_tour)
        top_layout.addWidget(self.onboarding_button)

        self.hardware_mode_combo = QComboBox()

        self.hardware_mode_combo.setStyleSheet("""
                QComboBox { 
                    color: white; 
                    font-weight: bold; 
                    background-color: #2D3748;
                    border: 1px solid #4A5568;
                    border-radius: 4px;
                    padding: 4px 8px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    /* (这里可以添加一个白色向下箭头的图标路径) */
                    /* image: url(path/to/your/arrow.svg); */
                }
                /* 这一段是关键，它定义了下拉列表的样式 */
                QComboBox QAbstractItemView {
                    background-color: #2D3748;
                    color: white;
                    border: 1px solid #4A5568;
                    selection-background-color: #3182CE; /* 选中项的背景色 */
                }
            """)

        top_layout.addWidget(self.hardware_mode_combo)
        main_layout.addLayout(top_layout)

        # --- Titles ---
        self.title_label = QLabel()
        self.title_label.setObjectName("mainTitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        font = self.title_label.font();
        font.setBold(True);
        font.setPointSize(font.pointSize() + 8);
        self.title_label.setFont(font)

        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("subtitleLabel")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_font = self.subtitle_label.font();
        subtitle_font.setPointSize(subtitle_font.pointSize() + 5);
        self.subtitle_label.setFont(subtitle_font)

        title_shadow = QGraphicsDropShadowEffect(self);
        title_shadow.setBlurRadius(20);
        title_shadow.setColor(QColor(255, 255, 255, 100));
        title_shadow.setOffset(0, 0);
        self.title_label.setGraphicsEffect(title_shadow)
        subtitle_shadow = QGraphicsDropShadowEffect(self);
        subtitle_shadow.setBlurRadius(15);
        subtitle_shadow.setColor(QColor(224, 224, 224, 90));
        subtitle_shadow.setOffset(0, 0);
        self.subtitle_label.setGraphicsEffect(subtitle_shadow)

        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.subtitle_label)

        # --- Button Grid ---
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(40)
        grid_layout.setVerticalSpacing(25)
        grid_layout.setContentsMargins(60, 10, 60, 10)
        for col in range(3):
            grid_layout.setColumnStretch(col, 1)

        # 【核心修改】移除了 self.mode_labels 列表
        self.mode_buttons = []

        # 【修改】使用相对路径加载图标
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets', 'icons')
        self.buttons_info = [
            ("Absorbance", os.path.join(assets_dir, "absorbance.png")),
            ("Transmission", os.path.join(assets_dir, "transmission.png")),
            ("Reflectance", os.path.join(assets_dir, "reflectance.png")),
            ("Raman", os.path.join(assets_dir, "raman.png")),
            ("Fluorescence", os.path.join(assets_dir, "fluorescence.png")),
            ("Color", os.path.join(assets_dir, "color.png")),
        ]

        for index, (text_key, icon_path) in enumerate(self.buttons_info):
            row = index // 3
            column = index % 3
            button = HoverButton(icon_path)
            button.setFixedHeight(140)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.clicked.connect(lambda checked, mode=text_key: self.mode_selected.emit(
                mode,
                self._is_real_hardware_selected(),
                self._current_vendor(),
            ))
            grid_layout.addWidget(button, row, column)

            self.mode_buttons.append(button)

        main_layout.addLayout(grid_layout)
        self.setLayout(main_layout)

        # 最后调用一次翻译方法来设置所有初始文本
        self._retranslate_ui()

    # (此代码块应放在 welcome_widget.py 的 WelcomeWidget 类中)
    def _retranslate_ui(self):
        """
        重新翻译此控件内的所有UI文本。
        """
        self.setWindowTitle(self.tr("Welcome - Nanophotonics sensing detection data visualization analysis system"))

        # 重新翻译标题
        self.title_label.setText(self.tr("Nanophotonics sensing detection data visualization analysis system"))
        self.subtitle_label.setText(self.tr("Sensors and Microsystems Laboratory"))

        if hasattr(self, "onboarding_button"):
            self.onboarding_button.setText(self.tr("Onboarding"))

        # 重新翻译下拉框（保留当前 vendor 选择，避免语言切换后回到默认项）
        previous_vendor = self._current_vendor() if self.hardware_mode_combo.count() else 'ideaoptics'

        self.hardware_mode_combo.blockSignals(True)
        self.hardware_mode_combo.clear()
        # (label, vendor) — Mock 不区分厂商
        self._hardware_mode_items = [
            (self.tr("Real Hardware (IdeaOptics)"), 'ideaoptics'),
            (self.tr("Real Hardware (Ocean Optics)"), 'ocean'),
            (self.tr("Mock API"), 'mock'),
        ]
        for label, _vendor in self._hardware_mode_items:
            self.hardware_mode_combo.addItem(label)

        # 还原上一次选择
        target_index = next(
            (i for i, (_l, v) in enumerate(self._hardware_mode_items) if v == previous_vendor),
            0,
        )
        self.hardware_mode_combo.setCurrentIndex(target_index)
        self.hardware_mode_combo.blockSignals(False)
        self._current_vendor_cache = self._current_vendor()

        # 【核心修改】只更新按钮的悬停提示 (Tooltip)
        for i in range(len(self.buttons_info)):
            text_key = self.buttons_info[i][0]
            translated_text = self.tr(text_key)
            self.mode_buttons[i].setToolTip(translated_text)

    def changeEvent(self, event):
        """
        响应语言变化事件。
        """
        if event.type() == event.LanguageChange:
            self._retranslate_ui()
        super().changeEvent(event)

    # ── 硬件模式辅助方法 ─────────────────────────────────────
    def _current_vendor(self) -> str:
        """返回 ComboBox 当前选中的厂商: 'ideaoptics' / 'ocean' / 'mock'。"""
        items = getattr(self, "_hardware_mode_items", None)
        if not items:
            return 'ideaoptics'
        idx = max(0, self.hardware_mode_combo.currentIndex())
        idx = min(idx, len(items) - 1)
        return items[idx][1]

    def _is_real_hardware_selected(self) -> bool:
        return self._current_vendor() != 'mock'

    def set_hardware_vendor(self, vendor: str):
        """外部接口：按 vendor 字符串选中对应项。"""
        items = getattr(self, "_hardware_mode_items", [])
        for i, (_label, v) in enumerate(items):
            if v == vendor:
                self.hardware_mode_combo.setCurrentIndex(i)
                self._current_vendor_cache = v
                return
