from PyQt5.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QWidget, QGridLayout, QPushButton, QLabel

class ScrollableGrid(QFrame):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        self.scrollArea = QScrollArea(self)
        self.scrollAreaWidgetContents = QWidget()
        self.grid_layout = QGridLayout(self.scrollAreaWidgetContents)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollArea.setWidgetResizable(True)

        self.layout.addWidget(self.scrollArea)
