from operator import is_
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt

class SettingsButton(QWidget):
    def __init__(self, parent=None):
        super(SettingsButton, self).__init__(parent)

        self.setFixedSize(48, 48)

        # Создаем кнопку и устанавливаем иконку
        self.button = QPushButton(self)
        self.button.setFixedSize(48,48)
        # Устанавливаем иконку и делаем ее масштабируемой
        pixmap = QPixmap(r":icons/settings_icon.png")
        pixmap = pixmap.scaled(32, 32)
        self.button.setIcon(QIcon(pixmap))
        self.button.setIconSize(pixmap.size())

    def set_connected(self, is_connected: bool):
        if is_connected:
            self.button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    border: 2px solid #45a049;
                    color: white;
                    padding: 8px 16px;
                    font-size: 14px;
                    border-radius: 4px;
                }
                
                QPushButton:hover {
                    background-color: #45a049;
                }
                
                QPushButton:pressed {
                    background-color: #39843D;
                    border-color: #2F7233;
                }
            """)
        else:
            self.button.setStyleSheet("""
                QPushButton {
                    background-color: #808080;
                    border: 2px solid #696969;
                    color: white;
                    padding: 8px 16px;
                    font-size: 14px;
                    border-radius: 4px;
                }
                
                QPushButton:hover {
                    background-color: #696969;
                }
                
                QPushButton:pressed {
                    background-color: #595959;
                    border-color: #4C4C4C;
                }
            """)

