from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSignal

class ToggleButton(QPushButton):
    toggled = pyqtSignal(bool)

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.isChecked = False
        self.updateStyle()
        self.clicked.connect(self.toggleState)

    def toggleState(self):
        self.isChecked = not self.isChecked
        self.updateStyle()
        self.toggled.emit(self.isChecked)

    def updateStyle(self):
        if self.isChecked:
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
