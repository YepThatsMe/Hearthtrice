import imp
from PyQt5.QtWidgets import QLabel


class FormLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        
        self.setStyleSheet("font-size: 10pt; font-weight: bold; font-family: Calibri")