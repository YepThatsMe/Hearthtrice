from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QFrame, QButtonGroup, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal

class ExclusiveButtonGroup(QFrame):
    button_clicked = pyqtSignal()

    def __init__(self, count, icon_path, is_vertical=0, fixed_size=1, parent=None):
        super().__init__(parent)
        self.count = count

        layout = None
        if is_vertical:
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignCenter)
        else:
            layout = QHBoxLayout(self)
            layout.setAlignment(Qt.AlignCenter)
      
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        self.buttons = []
        for i in range(count):
            button = QPushButton(self)
            if icon_path:
                pixmap = QPixmap(f"{icon_path}/icon_{i}.png")
                icon = QIcon(pixmap)
                button.setIcon(icon)
            
            if fixed_size:
                button.setFixedSize(64, 64)
                button.setIconSize(button.size())
            else:
                scale = 2.2
                resized_pixmap = pixmap.scaled(pixmap.width()/scale, pixmap.height()/scale)
                button.setFixedSize(resized_pixmap.size())
                button.setIconSize(resized_pixmap.size())
            
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 2px solid transparent;
                }
                QPushButton:checked {
                    background-color: #e1e1e1;
                    border: 2px solid #555555;
                }
            """)
            self.button_group.addButton(button, i)
            self.buttons.append(button)
            layout.addWidget(button)
            button.setCheckable(True)
        self.buttons[0].setChecked(True)

        layout.addStretch()

        self.button_group.buttonClicked.connect(self.on_button_clicked)

    def on_button_clicked(self, button):
        for b in self.buttons:
            if b != button:
                b.setChecked(False)
            else:
                b.setChecked(True)
        
        self.button_clicked.emit()


    def get_checked_button_index(self) -> int:
        for i in range(len(self.buttons)):
            if self.buttons[i].isChecked():
                return i
            
    def set_checked_button_index(self, index: int):
        for i in range(len(self.buttons)):
            self.buttons[i].setChecked(False)
        self.buttons[index].setChecked(True)