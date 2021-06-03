from PyQt5.QtWidgets import (QMainWindow, QWidget, QDesktopWidget, QApplication, QAction,
                             QMessageBox, QFileDialog, QListWidget, QComboBox, QHBoxLayout,
                             QVBoxLayout, QLabel, QLineEdit, QCompleter, QGridLayout,
                             QTableWidget, QProgressBar, QPushButton)

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
import sys
class win(QWidget):
    def __init__(self):
        super(win, self).__init__()
        self.setWindowTitle("HUI")
        self.buttom = QPushButton("G")
        self.l1 = QHBoxLayout()
        self.l1.addWidget(self.buttom)
        self.setLayout(self.l1)


