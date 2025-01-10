from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu, QAction
from PyQt5.QtCore import QTimer, Qt, QRect
from PyQt5.QtGui import QIcon, QMouseEvent, QPixmap, QColor, QPainter, QCursor
from PyQt5.QtCore import pyqtSignal
from utils.BytesEncoder import bytes_to_pixmap

from DataTypes import CardMetadata, StdMetadata

class PreviewPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Прозрачность для событий мыши
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # Окно не получает фокус

        self.label = QLabel(self)

        self.id_label = QLabel("ID: ", self)
        self.id_label.setStyleSheet("font-size: 11pt; font-weight: bold")
        self.note_label = QLabel("Заметка: ", self)
        self.note_label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.id_label)
        layout.addWidget(self.note_label)
        self.setLayout(layout)

    def set_content(self, pixmap: QPixmap, obj_id: int, note: str):
        self.label.setPixmap(pixmap)

        self.id_label.setText(f"ID: {obj_id}")
        self.note_label.setText(f"{note}")
        self.note_label.setVisible(bool(note))

        self.adjustSize()
        
class CardWidget(QWidget):
    card_clicked_event = pyqtSignal(CardMetadata)
    edit_card_requested = pyqtSignal(CardMetadata)
    delete_card_requested = pyqtSignal(CardMetadata)

    def __init__(self, metadata: CardMetadata, parent: QWidget = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.pressPos = None
        self.metadata = metadata

        self.preview_popup = PreviewPopup(self)
        
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.show_preview)

        self.set_up_ui()

    def set_up_ui(self):
        pixmap = bytes_to_pixmap(self.metadata.card_image)
        w, h = int(pixmap.width()/5), int(pixmap.height()/5)
        self.pixmap_small = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Подгонка размера

        self.card_label = QLabel(self)
        self.card_label.setPixmap(self.pixmap_small)

        gen_layout = QVBoxLayout(self)
        gen_layout.addWidget(self.card_label)
        self.setLayout(gen_layout)

        # Создаем контекстное меню
        self.context_menu = QMenu(self)
        edit_action = QAction("Редактировать", self)
        self.delete_action = QAction("Удалить", self)
        self.context_menu.addAction(edit_action)
        self.context_menu.addAction(self.delete_action)

        if isinstance(self.metadata, StdMetadata):
            edit_action.setEnabled(False)
            self.delete_action.setEnabled(False)

        # Подключаем обработчики событий для контекстного меню
        edit_action.triggered.connect(self.editActionClicked)
        self.delete_action.triggered.connect(self.deleteActionClicked)

    def contextMenuEvent(self, event):
        # Обработчик события отображения контекстного меню при ПКМ
        self.context_menu.exec_(event.globalPos())
        
    def editActionClicked(self):
        self.edit_card_requested.emit(self.metadata)

    def deleteActionClicked(self):
        self.delete_card_requested.emit(self.metadata)

    def enterEvent(self, event):
        self.setHighlighted(True)
        
        self.hover_timer.start(1500)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setHighlighted(False)

        self.hover_timer.stop()
        self.preview_popup.hide()
        super().leaveEvent(event)

    def show_preview(self):
        preview = bytes_to_pixmap(self.metadata.card_image)
        
        scaled_width = int(preview.width() / 3)
        scaled_height = int(preview.height() / 3)
        scaled_pixmap = preview.scaled(
            scaled_width, 
            scaled_height, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.preview_popup.set_content(scaled_pixmap, self.metadata.id, self.metadata.comment)
        cursor_pos = QCursor.pos()
        self.preview_popup.move(cursor_pos.x() + 10, cursor_pos.y() + 10)
        self.preview_popup.show()

    def setHighlighted(self, highlighted):
        # Метод для установки подсветки (добавление прозрачного белого прямоугольника)
        if highlighted:
            highlight_pixmap = self.addHighlightRectangle(self.pixmap_small)
            self.card_label.setPixmap(highlight_pixmap)
        else:
            self.card_label.setPixmap(self.pixmap_small)

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