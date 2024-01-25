
from PyQt5.QtWidgets import QLabel, QApplication, QFrame
from PyQt5.QtGui import QPixmap, QKeySequence, QImage
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QTimer

class CardPreview(QLabel):
    picture_imported = pyqtSignal(QPixmap)
    picture_moved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(600)
        self.move_x = 0
        self.move_y = 0
        self.zoom = 0

        self.import_picturef(r"assets/start_card.png")

        self.setFocusPolicy(Qt.StrongFocus)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setStyleSheet("QLabel:focus { border: 0.8px solid black; }")
        self.setFrameStyle(QFrame.Sunken | QFrame.StyledPanel)

        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.picture_moved)
        
    def rescaled(self, pixmap) -> QPixmap:
        if pixmap.width() > self.maximumWidth() or pixmap.height() > self.maximumHeight():
            pixmap = pixmap.scaled(self.maximumSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap

    def set_preview_image(self, pixmap: QPixmap):
        pixmap = self.rescaled(pixmap)
        self.setPixmap(pixmap)
        
    def import_picturef(self, filepath: str):
        picture = QPixmap(filepath)
        self.import_picture(picture)
    
    def import_picture(self, pixmap: QPixmap):
        self.move_x = 0
        self.move_y = 0
        self.zoom = 0
        self.picture_imported.emit(pixmap)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Paste):
            clipboard = QApplication.clipboard()
            if clipboard.mimeData().hasImage():
                image = clipboard.image()
                pixmap = QPixmap.fromImage(image)
                self.import_picture(pixmap)
            elif clipboard.mimeData().hasUrls():
                url = clipboard.mimeData().urls()[0]
                if url.isLocalFile():
                    image_path = url.toLocalFile()
                    image = QImage(image_path)
                    if not image.isNull():
                        pixmap = QPixmap.fromImage(image)
                        self.import_picture(pixmap)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0] # type: QUrl
            self.import_picturef(url.toLocalFile())
            event.accept()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Calculate the distance of the drag
            distance_x = event.pos().x() - self.drag_start_position.x()
            distance_y = event.pos().y() - self.drag_start_position.y()

            self.move_x -= distance_x
            self.move_y -= distance_y

        if distance_x or distance_y:
            self.picture_moved.emit()
    
    def wheelEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            self.scroll_timer.start(250)
            
            self.zoom += event.angleDelta().y()
            
        else:
            super().wheelEvent(event)