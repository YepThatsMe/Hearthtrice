from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QFrame, QButtonGroup, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
import os
import sys


class ExclusiveButtonGroup(QFrame):
    button_clicked = pyqtSignal()

    def __init__(self, count, icon_path, is_vertical=0, fixed_size=1, parent=None, icon_files=None):
        super().__init__(parent)
        self.count = count

        if is_vertical:
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignCenter)
        else:
            layout = QHBoxLayout(self)
            layout.setAlignment(Qt.AlignCenter)

        layout.setContentsMargins(0, 0, 0, 0)
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        self.buttons = []
        for i in range(count):
            button = QPushButton(self)
            pixmap = None
            if icon_files is not None:
                if icon_files[i]:
                    pixmap = self._load_pixmap(icon_files[i])
                    if not pixmap.isNull():
                        button.setIcon(QIcon(pixmap))
            elif icon_path:
                pixmap = self._load_pixmap(f"{icon_path}/icon_{i}.png")
                if not pixmap.isNull():
                    button.setIcon(QIcon(pixmap))

            if fixed_size:
                button.setFixedSize(64, 64)
                button.setIconSize(button.size())
            else:
                if pixmap is None or pixmap.isNull():
                    button.setFixedSize(64, 64)
                else:
                    scale = 2.2
                    resized_pixmap = pixmap.scaled(
                        max(1, int(pixmap.width() / scale)),
                        max(1, int(pixmap.height() / scale)),
                    )
                    button.setFixedSize(resized_pixmap.size())
                    button.setIconSize(resized_pixmap.size())

            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 2px solid transparent;
                }
                QPushButton:checked {
                    background-color: #e1e1e1;
                    border: 2px solid #555555;
                }
            """)
            self.button_group.addButton(button, i)
            self.buttons.append(button)
            layout.addWidget(button)
            button.setCheckable(True)
        self.buttons[0].setChecked(True)

        layout.addStretch()
        self.button_group.buttonClicked.connect(self.on_button_clicked)

        if is_vertical:
            min_h = sum(b.height() for b in self.buttons) + layout.spacing() * max(0, count - 1)
            self.setMinimumHeight(min_h)
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        else:
            min_w = sum(b.width() for b in self.buttons) + layout.spacing() * max(0, count - 1)
            self.setMinimumWidth(min_w)
            self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    @staticmethod
    def _load_pixmap(path) -> QPixmap:
        path = str(path).replace("\\", "/")
        pixmap = QPixmap(path)
        if pixmap.isNull() and path.startswith(":"):
            rel = path.lstrip(":").replace("/", os.sep)
            if getattr(sys, "frozen", False):
                disk = os.path.join(sys._MEIPASS, "assets", rel)
            else:
                disk = os.path.join("src", "assets", rel)
            pixmap = QPixmap(disk)
        if pixmap.isNull() and not path.startswith(":"):
            disk = path if os.path.isabs(path) else os.path.join("src", "assets", path)
            pixmap = QPixmap(disk)
        return pixmap

    def on_button_clicked(self, button):
        for b in self.buttons:
            if b != button:
                b.setChecked(False)
            else:
                b.setChecked(True)

        self.button_clicked.emit()

    def get_checked_button_index(self) -> int:
        for i in range(len(self.buttons)):
            if self.buttons[i].isChecked():
                return i

    def set_checked_button_index(self, index: int):
        for i in range(len(self.buttons)):
            self.buttons[i].setChecked(False)
        self.buttons[index].setChecked(True)
