# nanosense/gui/onboarding.py
"""
通用气泡式新手指引组件 OnboardingTour。

用法：
    steps = [
        {"target": some_widget, "title": "标题", "text": "说明"},
        {"target": "objectName_string", "title": "...", "text": "..."},
        {"target": None, "title": "结束", "text": "..."},  # 居中显示
    ]
    tour = OnboardingTour(host_window, steps)
    tour.start()
"""

from typing import Any, Dict, List, Optional, Union

from PyQt5.QtCore import QEvent, QPoint, QRect, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


HIGHLIGHT_PADDING = 6
HIGHLIGHT_RADIUS = 10
TIP_WIDTH = 360
GAP = 14


class _Bubble(QFrame):
    """浮窗气泡：标题 + 正文 + 三个按钮（上一步/下一步/跳过）。"""

    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    skip_clicked = pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("onboardingBubble")
        self.setFixedWidth(TIP_WIDTH)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            """
            #onboardingBubble {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 10px;
            }
            #onboardingBubble QLabel { color: #F7FAFC; background: transparent; }
            #onboardingTitle { font-size: 15px; font-weight: bold; }
            #onboardingBody  { font-size: 13px; }
            #onboardingStep  { color: #A0AEC0; font-size: 12px; }
            #onboardingBubble QPushButton {
                background-color: #3182CE; color: white; border: none;
                border-radius: 6px; padding: 6px 14px; font-size: 13px;
            }
            #onboardingBubble QPushButton:hover { background-color: #2B6CB0; }
            #onboardingBubble QPushButton#onboardingPrev,
            #onboardingBubble QPushButton#onboardingSkip {
                background-color: #4A5568;
            }
            #onboardingBubble QPushButton#onboardingPrev:hover,
            #onboardingBubble QPushButton#onboardingSkip:hover {
                background-color: #2D3748;
            }
            """
        )

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.title_label = QLabel(self)
        self.title_label.setObjectName("onboardingTitle")
        self.title_label.setWordWrap(True)

        self.step_label = QLabel(self)
        self.step_label.setObjectName("onboardingStep")

        self.body_label = QLabel(self)
        self.body_label.setObjectName("onboardingBody")
        self.body_label.setWordWrap(True)

        self.prev_button = QPushButton(self)
        self.prev_button.setObjectName("onboardingPrev")
        self.prev_button.clicked.connect(self.prev_clicked)

        self.skip_button = QPushButton(self)
        self.skip_button.setObjectName("onboardingSkip")
        self.skip_button.clicked.connect(self.skip_clicked)

        self.next_button = QPushButton(self)
        self.next_button.setObjectName("onboardingNext")
        self.next_button.clicked.connect(self.next_clicked)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.addWidget(self.title_label, 1)
        header.addWidget(self.step_label, 0, Qt.AlignRight | Qt.AlignTop)
        layout.addLayout(header)

        layout.addWidget(self.body_label)

        button_row = QHBoxLayout()
        button_row.addWidget(self.skip_button)
        button_row.addStretch(1)
        button_row.addWidget(self.prev_button)
        button_row.addWidget(self.next_button)
        layout.addLayout(button_row)

    def set_content(
        self,
        title: str,
        body: str,
        step_text: str,
        prev_label: str,
        next_label: str,
        skip_label: str,
        show_prev: bool,
    ) -> None:
        self.title_label.setText(title)
        self.body_label.setText(body)
        self.step_label.setText(step_text)
        self.prev_button.setText(prev_label)
        self.next_button.setText(next_label)
        self.skip_button.setText(skip_label)
        self.prev_button.setVisible(show_prev)
        self.adjustSize()


class OnboardingTour(QWidget):
    """半透明遮罩 + 镂空高亮 + 浮窗气泡的分步指引。"""

    finished = pyqtSignal(bool)  # True 表示完成走完，False 表示用户跳过

    def __init__(self, host: QWidget, steps: List[Dict[str, Any]]):
        super().__init__(host)
        self.host = host
        self.steps = steps
        self.index = 0
        self._highlight_rect: Optional[QRect] = None

        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAutoFillBackground(False)

        self.bubble = _Bubble(self)
        self.bubble.prev_clicked.connect(self._on_prev)
        self.bubble.next_clicked.connect(self._on_next)
        self.bubble.skip_clicked.connect(self._on_skip)

        host.installEventFilter(self)

    # ---------- public ----------
    def start(self) -> None:
        if not self.steps:
            self.finished.emit(True)
            self.deleteLater()
            return
        self.index = 0
        self._fit_to_host()
        self.show()
        self.raise_()
        self._render_step()

    # ---------- event handling ----------
    def eventFilter(self, obj, event):
        if obj is self.host and event.type() in (QEvent.Resize, QEvent.Move, QEvent.Show):
            self._fit_to_host()
            self._render_step()
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._on_skip()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Right):
            self._on_next()
        elif event.key() == Qt.Key_Left:
            self._on_prev()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # 点击高亮区域外不穿透；点击高亮区域内也不穿透（避免误触发）。
        # 用户必须使用气泡上的按钮推进。
        event.accept()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        full_path = QPainterPath()
        full_path.addRect(QRectF(0, 0, self.width(), self.height()))

        if self._highlight_rect is not None and not self._highlight_rect.isEmpty():
            highlight_rectf = QRectF(self._highlight_rect)
            hole_path = QPainterPath()
            hole_path.addRoundedRect(
                highlight_rectf, HIGHLIGHT_RADIUS, HIGHLIGHT_RADIUS
            )
            full_path = full_path.subtracted(hole_path)

            pen = QPen(QColor(255, 215, 0, 220))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                highlight_rectf, HIGHLIGHT_RADIUS, HIGHLIGHT_RADIUS
            )

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 150))
        painter.drawPath(full_path)

    # ---------- internals ----------
    def _fit_to_host(self) -> None:
        self.setGeometry(0, 0, self.host.width(), self.host.height())

    def _resolve_target(self, target: Union[QWidget, str, None]) -> Optional[QWidget]:
        if target is None:
            return None
        if isinstance(target, QWidget):
            return target if target.isVisible() else None
        if isinstance(target, str):
            widget = self.host.findChild(QWidget, target)
            if widget and widget.isVisible():
                return widget
        return None

    def _render_step(self) -> None:
        if self.index < 0 or self.index >= len(self.steps):
            return
        step = self.steps[self.index]
        target = self._resolve_target(step.get("target"))

        if target is not None:
            top_left = target.mapTo(self.host, QPoint(0, 0))
            rect = QRect(top_left, target.size())
            rect = rect.adjusted(
                -HIGHLIGHT_PADDING, -HIGHLIGHT_PADDING,
                HIGHLIGHT_PADDING, HIGHLIGHT_PADDING,
            )
            self._highlight_rect = rect
        else:
            self._highlight_rect = None

        total = len(self.steps)
        prev_label = self.tr("Previous")
        next_label = self.tr("Finish") if self.index == total - 1 else self.tr("Next")
        skip_label = self.tr("Skip")
        step_text = f"{self.index + 1} / {total}"

        self.bubble.set_content(
            title=step.get("title", ""),
            body=step.get("text", ""),
            step_text=step_text,
            prev_label=prev_label,
            next_label=next_label,
            skip_label=skip_label,
            show_prev=self.index > 0,
        )

        self._place_bubble()
        self.update()

    def _place_bubble(self) -> None:
        host_w = self.width()
        host_h = self.height()
        bw = self.bubble.width()
        bh = self.bubble.height()

        if self._highlight_rect is None:
            x = (host_w - bw) // 2
            y = (host_h - bh) // 2
            self.bubble.move(x, y)
            return

        rect = self._highlight_rect
        # 优先放在目标下方；不够放就放上方；再不够就放右侧/左侧；最后兜底居中。
        if rect.bottom() + GAP + bh <= host_h:
            y = rect.bottom() + GAP
            x = min(max(rect.left(), 10), host_w - bw - 10)
        elif rect.top() - GAP - bh >= 0:
            y = rect.top() - GAP - bh
            x = min(max(rect.left(), 10), host_w - bw - 10)
        elif rect.right() + GAP + bw <= host_w:
            x = rect.right() + GAP
            y = min(max(rect.top(), 10), host_h - bh - 10)
        elif rect.left() - GAP - bw >= 0:
            x = rect.left() - GAP - bw
            y = min(max(rect.top(), 10), host_h - bh - 10)
        else:
            x = (host_w - bw) // 2
            y = (host_h - bh) // 2

        self.bubble.move(x, y)

    def _on_next(self) -> None:
        if self.index >= len(self.steps) - 1:
            self._close(completed=True)
            return
        self.index += 1
        self._render_step()

    def _on_prev(self) -> None:
        if self.index <= 0:
            return
        self.index -= 1
        self._render_step()

    def _on_skip(self) -> None:
        self._close(completed=False)

    def _close(self, completed: bool) -> None:
        self.host.removeEventFilter(self)
        self.hide()
        self.finished.emit(completed)
        self.deleteLater()
