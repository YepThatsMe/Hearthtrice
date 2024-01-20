from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu, QAction
from PyQt5.QtCore import QTimer, Qt, QRect
from PyQt5.QtGui import QIcon, QMouseEvent, QPixmap, QColor, QPainter
from PyQt5.QtCore import pyqtSignal
from Widgets.components.BytesEncoder import bytes_to_pixmap

from Widgets.components.DataTypes import CardMetadata

class CardWidget(QWidget):
    card_clicked_event = pyqtSignal(CardMetadata)
    edit_card_requested = pyqtSignal(CardMetadata)
    delete_card_requested = pyqtSignal(CardMetadata)

    def __init__(self, metadata: CardMetadata, parent: QWidget = None):
        super().__init__(parent)
        self.metadata = metadata

        self.set_up_ui()

    def set_up_ui(self):
        self.pixmap = bytes_to_pixmap(self.metadata.card_image)
        w, h = int(self.pixmap.width()/4), int(self.pixmap.height()/4)
        self.pixmap = self.pixmap.scaled(w,h)

        self.card_label = QLabel(self)
        self.card_label.setPixmap(self.pixmap)

        gen_layout = QVBoxLayout(self)
        gen_layout.addWidget(self.card_label)
        self.setLayout(gen_layout)

        # Создаем контекстное меню
        self.context_menu = QMenu(self)
        edit_action = QAction("Редактировать", self)
        delete_action = QAction("Удалить", self)
        self.context_menu.addAction(edit_action)
        self.context_menu.addAction(delete_action)

        # Подключаем обработчики событий для контекстного меню
        edit_action.triggered.connect(self.editActionClicked)
        delete_action.triggered.connect(self.deleteActionClicked)

    def contextMenuEvent(self, event):
        # Обработчик события отображения контекстного меню при ПКМ
        self.context_menu.exec_(event.globalPos())
        
    def editActionClicked(self):
        self.edit_card_requested.emit(self.metadata)

    def deleteActionClicked(self):
        self.delete_card_requested.emit(self.metadata)

    def enterEvent(self, event):
        # Событие при наведении мыши
        self.setHighlighted(True)

    def leaveEvent(self, event):
        # Событие при уходе мыши
        self.setHighlighted(False)

    def setHighlighted(self, highlighted):
        # Метод для установки подсветки (добавление прозрачного белого прямоугольника)
        if highlighted:
            highlight_pixmap = self.addHighlightRectangle(self.pixmap)
            self.card_label.setPixmap(highlight_pixmap)
        else:
            self.card_label.setPixmap(self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressPos = event.pos()

    def mouseReleaseEvent(self, event):
        # ensure that the left button was pressed *and* released within the
        # geometry of the widget; if so, emit the signal;
        if (self.pressPos is not None and 
            event.button() == Qt.LeftButton and 
            event.pos() in self.rect()):
                self.card_clicked_event.emit(self.metadata)
        self.pressPos = None

    def addHighlightRectangle(self, pixmap):
        # Метод для добавления прозрачного белого прямоугольника
        highlight_pixmap = QPixmap(pixmap)
        painter = QPainter(highlight_pixmap)

        # Рисуем прозрачный белый прямоугольник поверх всего изображения
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.fillRect(QRect(0, 0, highlight_pixmap.width(), highlight_pixmap.height()), QColor(255, 255, 255, 100))

        painter.end()
        return highlight_pixmap