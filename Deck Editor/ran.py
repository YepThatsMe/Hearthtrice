from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout

class win(QWidget):
    def __init__(self):
        super(win, self).__init__()
        self.setWindowTitle("HUI")
        self.buttom = QPushButton("G")
        self.l1 = QHBoxLayout()
        self.l1.addWidget(self.buttom)
        self.setLayout(self.l1)


