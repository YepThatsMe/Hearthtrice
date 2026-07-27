from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPixmap, QFont, QFontDatabase, QPen, QColor, QPainterPath, QFontMetrics,
)
import os
import sys


class IconSpinBox(QWidget):
    valueChanged = pyqtSignal(int)

    _font_family = None

    def __init__(self, icon_path: str, size: int = 72, parent=None,
                 font_size: int = 36, font_size_wide: int = 30, text_offset_x: int = 0):
        super().__init__(parent)
        self._value = 0
        self._minimum = 0
        self._maximum = 99
        self._bg = QPixmap(icon_path)
        self._size = size
        self._font_size = font_size
        self._font_size_wide = font_size_wide
        self._text_offset_x = text_offset_x
        self.setFixedSize(size, size)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self._ensure_font()

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

    def value(self) -> int:
        return self._value

    def setValue(self, value: int):
        value = max(self._minimum, min(self._maximum, int(value)))
        if value == self._value:
            return
        self._value = value
        self.update()
        self.valueChanged.emit(self._value)

    def setRange(self, minimum: int, maximum: int):
        self._minimum = minimum
        self._maximum = maximum
        self.setValue(self._value)

    def minimum(self) -> int:
        return self._minimum

    def maximum(self) -> int:
        return self._maximum

    def stepBy(self, steps: int):
        self.setValue(self._value + steps)

    def wheelEvent(self, event):
        if not self.isEnabled():
            return
        delta = event.angleDelta().y()
        if delta > 0:
            self.stepBy(1)
        elif delta < 0:
            self.stepBy(-1)
        event.accept()

    def keyPressEvent(self, event):
        if not self.isEnabled():
            return
        key = event.key()
        if key in (Qt.Key_Up, Qt.Key_Plus):
            self.stepBy(1)
            event.accept()
        elif key in (Qt.Key_Down, Qt.Key_Minus):
            self.stepBy(-1)
            event.accept()
        elif key == Qt.Key_PageUp:
            self.stepBy(5)
            event.accept()
        elif key == Qt.Key_PageDown:
            self.stepBy(-5)
            event.accept()
        elif Qt.Key_0 <= key <= Qt.Key_9:
            digit = key - Qt.Key_0
            new_val = self._value * 10 + digit
            if new_val > self._maximum:
                new_val = digit
            self.setValue(new_val)
            event.accept()
        elif key in (Qt.Key_Backspace, Qt.Key_Delete):
            self.setValue(0)
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.setFocus(Qt.MouseFocusReason)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        if not self.isEnabled():
            painter.setOpacity(0.4)

        if not self._bg.isNull():
            scaled = self._bg.scaled(
                self._size, self._size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            x = (self._size - scaled.width()) // 2
            y = (self._size - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        text = str(self._value)
        font = QFont(self._font_family)
        font.setPixelSize(self._font_size if self._value < 10 else self._font_size_wide)
        font.setBold(True)

        metrics = QFontMetrics(font)
        tw = metrics.horizontalAdvance(text)
        th = metrics.ascent()
        tx = (self._size - tw) / 2 + self._text_offset_x
        ty = (self._size + th) / 2 - metrics.descent() / 2

        path = QPainterPath()
        path.addText(tx, ty, font, text)

        outline = QPen(QColor(0, 0, 0), 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.strokePath(path, outline)
        painter.fillPath(path, QColor(255, 255, 255))

        if self.hasFocus() and self.isEnabled():
            painter.setOpacity(1.0)
            painter.setPen(QPen(QColor(255, 255, 255, 120), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(1, 1, self._size - 2, self._size - 2, 8, 8)
