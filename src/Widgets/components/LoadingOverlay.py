from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        self.dots_count = 0
        self.base_text = "Загрузка"
        
        self.text_label = QLabel(self.base_text, self)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("""
            background: transparent;
            color: white;
            font-size: 18pt;
            font-weight: bold;
            font-family: Arial;
        """)
        
        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.text_label, alignment=Qt.AlignCenter)
        layout.addStretch()
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_dots)
        
        self.hide()

    def show_overlay(self, text: str = "Загрузка"):
        self.base_text = text.rstrip('.')
        self.dots_count = 0
        self.text_label.setText(self.base_text)
        self.raise_()
        self.show()
        self.anim_timer.start(400)

    def hide_overlay(self):
        self.anim_timer.stop()
        self.hide()
    
    def _animate_dots(self):
        self.dots_count = (self.dots_count + 1) % 4
        self.text_label.setText(self.base_text + "." * self.dots_count)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
