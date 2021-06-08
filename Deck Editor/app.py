from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QMainWindow
import init
import main_arena

class win(QMainWindow):
    def __init__(self):
        super(win, self).__init__()
        self.setWindowTitle("HUI")
        self.buttom = QPushButton("G")
        self.l1 = QHBoxLayout()
        self.l1.addWidget(self.buttom)
        self.
        self.setLayout(self.l1)

