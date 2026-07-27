from PyQt5.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QWidget, QGridLayout, QSizePolicy
from PyQt5.QtCore import Qt


class ScrollableGrid(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setFrameShape(QFrame.NoFrame)

        self.scrollAreaWidgetContents = QWidget()
        self.grid_layout = QGridLayout(self.scrollAreaWidgetContents)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.layout.addWidget(self.scrollArea)

    def scrollToTop(self):
        self.scrollArea.verticalScrollBar().setValue(0)

    def ensureWidgetVisible(self, widget: QWidget):
        self.scrollArea.ensureWidgetVisible(widget)
