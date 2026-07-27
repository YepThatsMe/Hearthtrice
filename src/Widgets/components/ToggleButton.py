from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon

class ToggleButton(QPushButton):
    toggled = pyqtSignal(bool)

    def __init__(self, text="", parent=None, icon=None, accent="green"):
        super().__init__(text, parent)
        self.accent = accent
        if icon is not None:
            if isinstance(icon, str):
                self.setIcon(QIcon(icon))
            else:
                self.setIcon(icon)
        self.setCheckable(True)
        self.isChecked = False
        self.updateStyle()
        self.clicked.connect(self.toggleState)

    def toggleState(self):
        self.isChecked = not self.isChecked
        self.updateStyle()
        self.toggled.emit(self.isChecked)

    def setChecked(self, isChecked: bool):
        if isChecked and not self.isChecked:
            self.toggleState()
        if not isChecked and self.isChecked:
            self.toggleState()

    def updateStyle(self):
        if self.isChecked:
            if self.accent == "yellow":
                self.setStyleSheet("""
                    QPushButton {
                        background-color: #ffe566;
                        border: 2px solid #c9a000;
                    }
                    QPushButton:hover {
                        background-color: #ffef99;
                    }
                    QPushButton:pressed {
                        background-color: #e6c200;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QPushButton {
                        background-color: lightgreen;
                        border: 2px solid green;
                    }
                    QPushButton:hover {
                        background-color: lightblue;
                    }
                    QPushButton:pressed {
                        background-color: darkgreen;
                    }
                """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: lightgray;
                    border: 2px solid gray;
                }
                QPushButton:hover {
                    background-color: lightblue;
                }
                QPushButton:pressed {
                    background-color: darkgray;
                }
            """)
