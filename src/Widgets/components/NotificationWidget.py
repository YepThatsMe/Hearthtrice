from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QColor, QPainter, QPainterPath
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer, QRectF


class NotificationWidget(QWidget):
    def __init__(self, parent=None, message="", notification_type="info", highlighted_text=""):
        self.message = message
        self.notification_type = notification_type
        self.highlighted_text = highlighted_text
        
        self.main_window = None
        if parent:
            self.main_window = parent
            while self.main_window.parent():
                self.main_window = self.main_window.parent()
        
        if self.main_window:
            super().__init__(self.main_window)
        else:
            super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.init_ui()
        self.setup_animation()
        
        if self.main_window:
            self.setup_position()
        
        self.show()
        self.animate_in()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        
        if self.highlighted_text and self.highlighted_text in self.message:
            html_message = self.message.replace(
                self.highlighted_text,
                f'<span style="color: #FFD700; font-size: 11pt; font-weight: bold;">{self.highlighted_text}</span>'
            )
            self.label = QLabel(html_message, self)
            self.label.setTextFormat(Qt.RichText)
        else:
            self.label = QLabel(self.message, self)
        
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setStyleSheet("color: white; font-size: 9pt; font-weight: bold;")
        
        layout.addWidget(self.label)
        
        colors = {
            "success": "#4CAF50",
            "info": "#2196F3",
            "warning": "#FF9800",
            "error": "#F44336"
        }
        
        self.bg_color = QColor(colors.get(self.notification_type, colors["info"]))
        self.setMinimumWidth(220)
        self.setMaximumWidth(300)
        self.adjustSize()
    
    def setup_position(self):
        if not self.main_window:
            return
        
        self.adjustSize()
        parent_width = self.main_window.width()
        x = parent_width - self.width() - 20
        y = 20
        self.move(x, y)
    
    def setup_animation(self):
        self._opacity = 1.0
        self._x_offset = 0
        
        self.fade_animation = QPropertyAnimation(self, b"opacity", self)
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.slide_animation = QPropertyAnimation(self, b"x_offset", self)
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def animate_in(self):
        self._x_offset = self.width()
        self.slide_animation.setStartValue(self.width())
        self.slide_animation.setEndValue(0)
        self.slide_animation.start()
        
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        duration = 2500
        if self.notification_type == "warning":
            duration = 3000
        elif self.notification_type == "error":
            duration = 5000
        
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(self.animate_out)
        timer.start(duration)
    
    def animate_out(self):
        self.slide_animation.setStartValue(0)
        self.slide_animation.setEndValue(self.width())
        self.slide_animation.start()
        
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()
    
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, value):
        self._opacity = value
        self.update()
    
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def get_x_offset(self):
        return self._x_offset
    
    def set_x_offset(self, value):
        self._x_offset = value
        if not self.main_window:
            return
        
        parent_width = self.main_window.width()
        x = parent_width - self.width() - 20 - value
        y = 20
        self.move(x, y)
    
    x_offset = pyqtProperty(int, get_x_offset, set_x_offset)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._opacity)
        
        path = QPainterPath()
        rect = QRectF(self.rect())
        radius = 4
        path.addRoundedRect(rect, radius, radius)
        
        painter.fillPath(path, self.bg_color)
        
        painter.setPen(QColor(255, 255, 255, 100))
        painter.drawPath(path)

