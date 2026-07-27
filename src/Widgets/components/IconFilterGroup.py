from PyQt5.QtGui import (
    QIcon, QPixmap, QPainter, QFont, QFontDatabase, QPen, QColor, QPainterPath, QFontMetrics,
)
from PyQt5.QtWidgets import QFrame, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QSize
import os
import sys


class IconFilterGroup(QFrame):
    currentIndexChanged = pyqtSignal(int)

    _font_family = None

    def __init__(
        self,
        icons,
        button_width=64,
        button_height=48,
        tooltips=None,
        vertical=False,
        expand=True,
        parent=None,
    ):
        super().__init__(parent)
        self._index = 0
        self._button_width = button_width
        self._button_height = button_height
        self._ensure_font()

        if vertical:
            layout = QVBoxLayout(self)
        else:
            layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        self.buttons = []
        for i, icon in enumerate(icons):
            button = QPushButton(self)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            if expand:
                if vertical:
                    button.setMinimumSize(button_width, button_height)
                    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
                else:
                    button.setMinimumSize(button_width, button_height)
                    button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    button.setFixedHeight(button_height)
            else:
                button.setFixedSize(button_width, button_height)
            icon_side = min(button_width, button_height) - 8
            button.setIconSize(QSize(max(icon_side, 24), max(icon_side, 24)))
            button.setStyleSheet("""
                QPushButton {
                    background-color: #d8d8d8;
                    border: 1px solid #777777;
                    border-radius: 0px;
                    padding: 2px;
                }
                QPushButton:checked {
                    background-color: #b6e8b6;
                    border: 3px solid #1f8f1f;
                }
                QPushButton:hover {
                    background-color: #e8e8e8;
                }
                QPushButton:checked:hover {
                    background-color: #a8dfa8;
                    border: 3px solid #1f8f1f;
                }
            """)
            if icon is not None:
                pixmap = self._load_pixmap(icon)
                if not pixmap.isNull():
                    button.setIcon(QIcon(pixmap))
            if tooltips and i < len(tooltips) and tooltips[i]:
                button.setToolTip(tooltips[i])
            button.clicked.connect(lambda checked, idx=i: self._on_button_clicked(idx))
            self.buttons.append(button)
            layout.addWidget(button)

        if vertical:
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            self.setFixedWidth(button_width)
        else:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.setFixedHeight(button_height)

    @staticmethod
    def _load_pixmap(icon) -> QPixmap:
        if isinstance(icon, QPixmap):
            return icon
        if isinstance(icon, QIcon):
            return icon.pixmap(64, 64)
        path = str(icon)
        pixmap = QPixmap(path)
        if pixmap.isNull() and path.startswith(":"):
            rel = path.lstrip(":").replace("/", os.sep).replace("\\", os.sep)
            if getattr(sys, "frozen", False):
                disk = os.path.join(sys._MEIPASS, "assets", rel)
            else:
                disk = os.path.join("src", "assets", rel)
            pixmap = QPixmap(disk)
        if pixmap.isNull() and not path.startswith(":"):
            if getattr(sys, "frozen", False):
                disk = os.path.join(sys._MEIPASS, path)
            else:
                disk = path if os.path.isabs(path) else os.path.join("src", "assets", path)
            pixmap = QPixmap(disk)
        return pixmap

    @classmethod
    def _ensure_font(cls):
        if cls._font_family is not None:
            return
        if getattr(sys, "frozen", False):
            font_path = os.path.join(sys._MEIPASS, "fonts", "Belwe Bd BT Bold.ttf")
        else:
            font_path = os.path.join("src", "assets", "fonts", "Belwe Bd BT Bold.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        families = QFontDatabase.applicationFontFamilies(font_id)
        cls._font_family = families[0] if families else "Arial Black"

    def currentIndex(self) -> int:
        return self._index

    def setCurrentIndex(self, index: int):
        index = max(0, min(len(self.buttons), int(index)))
        if index == self._index:
            self._sync_buttons()
            return
        self._index = index
        self._sync_buttons()
        self.currentIndexChanged.emit(self._index)

    def _sync_buttons(self):
        for i, button in enumerate(self.buttons):
            button.blockSignals(True)
            button.setChecked(self._index == i + 1)
            button.blockSignals(False)

    def _on_button_clicked(self, button_idx: int):
        new_index = button_idx + 1
        if self._index == new_index:
            new_index = 0
        self.setCurrentIndex(new_index)

    @classmethod
    def make_mana_icons(cls, size: int = 48) -> list:
        cls._ensure_font()
        icons = []
        labels = [str(i) for i in range(10)] + ["10+"]
        bg = cls._load_pixmap(":Cardbuilder/MINION/manatexture.png")
        for label in labels:
            canvas = QPixmap(size, size)
            canvas.fill(Qt.transparent)
            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            if not bg.isNull():
                scaled = bg.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                x = (size - scaled.width()) // 2
                y = (size - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
            font = QFont(cls._font_family)
            font.setPixelSize(26 if len(label) < 2 else 18)
            font.setBold(True)
            metrics = QFontMetrics(font)
            tw = metrics.horizontalAdvance(label)
            th = metrics.ascent()
            tx = (size - tw) / 2
            ty = (size + th) / 2 - metrics.descent() / 2
            path = QPainterPath()
            path.addText(tx, ty, font, label)
            painter.strokePath(path, QPen(QColor(0, 0, 0), 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.fillPath(path, QColor(255, 255, 255))
            painter.end()
            icons.append(QIcon(canvas))
        return icons
