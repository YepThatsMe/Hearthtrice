from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
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

        self.detail_label = QLabel("", self)
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setStyleSheet("""
            background: transparent;
            color: #dddddd;
            font-size: 12pt;
            font-family: Arial;
        """)
        self.detail_label.hide()

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedWidth(360)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #333333;
                border: 1px solid #666666;
                border-radius: 4px;
                color: white;
                text-align: center;
                min-height: 18px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        self.progress_bar.hide()

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.text_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.detail_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        layout.addStretch()

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_dots)

        self.hide()

    def show_overlay(self, text: str = "Загрузка"):
        self.base_text = text.rstrip('.')
        self.dots_count = 0
        self.text_label.setText(self.base_text)
        self.detail_label.clear()
        self.detail_label.hide()
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        self.raise_()
        self.show()
        self.anim_timer.start(400)

    def set_progress(self, current: int, total: int, card_id=None):
        if total <= 0:
            return
        self.progress_bar.show()
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.detail_label.show()
        if card_id is not None:
            self.detail_label.setText(f"ID: {card_id}  ({current}/{total})")
        else:
            self.detail_label.setText(f"{current}/{total}")

    def hide_overlay(self):
        self.anim_timer.stop()
        self.progress_bar.hide()
        self.detail_label.hide()
        self.hide()

    def _animate_dots(self):
        self.dots_count = (self.dots_count + 1) % 4
        self.text_label.setText(self.base_text + "." * self.dots_count)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
