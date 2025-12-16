from PyQt5.QtWidgets import QLineEdit, QFileDialog, QMessageBox, QDialog, QTextEdit, QLabel, QVBoxLayout, QComboBox, QFrame, QHBoxLayout, QPushButton, QSpinBox, QSizePolicy
from PyQt5.QtGui import QIcon, QFont, QPixmap, QImage, QKeySequence
from PyQt5.QtCore import Qt, QIODevice, pyqtSignal
from enum import IntEnum, auto
import win32clipboard
from io import BytesIO
from PIL import Image

from CacheManager import CacheManager
from utils.BytesEncoder import bytes_to_pixmap, pil_to_bytes, pixmap_to_bytes, pil_to_pixmap
from DataTypes import CardMetadata, CardType
from Widgets.components.FormView import FormView
from Widgets.components.CardPreview import CardPreview
from ImageGenerator.CardImageGenerator import GenerationError
from ImageGenerator.MinionImageGenerator import MinionImageGenerator
from ImageGenerator.SpellImageGenerator import SpellImageGenerator
from ImageGenerator.WeaponImageGenerator import WeaponImageGenerator


class CardBuilderView(QFrame):
    class UploadMode(IntEnum):
        NEW: int = auto()
        EDIT: int = auto()

    upload_clicked = pyqtSignal()
    upload_requested = pyqtSignal(object)
    upload_edit_requested = pyqtSignal(object)

    def __init__(self, cache_manager: CacheManager, parent=None):
        super().__init__(parent)
        self.upload_mode = CardBuilderView.UploadMode.NEW
        self.cache_manager = cache_manager

        self.picture = QPixmap()
        self.card_metadata = CardMetadata()
        self.card_previous_version = CardMetadata()

        self.card_image_generator = MinionImageGenerator()
        self.card_image_generator_spell = SpellImageGenerator()
        self.card_image_generator_weapon = WeaponImageGenerator()

        self.set_up_ui()
        self.set_up_connections()

        self.reset()

    def set_up_connections(self):
        self.card_preview.picture_imported.connect(self.on_picture_imported)

        self.card_preview.picture_moved.connect(self.generate)
        self.card_preview.picture_moving.connect(self.generate)
        self.form.class_button_group.button_clicked.connect(self.generate)
        self.form.cardtype_button_group.button_clicked.connect(self.generate)
        
        self.form.name_form.textChanged.connect(self.generate)
        self.form.description_form.textChanged.connect(self.generate)
        self.form.mana_form.valueChanged.connect(self.generate)
        self.form.attack_form.valueChanged.connect(self.generate)
        self.form.health_form.valueChanged.connect(self.generate)
        self.form.rarity_form.currentIndexChanged.connect(self.generate)
        self.form.tribe_form.textChanged.connect(self.generate)

        self.upload_button.clicked.connect(self.upload_button_clicked)
        self.download_button.clicked.connect(self.download_button_clicked)
        self.copy_button.clicked.connect(self.copy_image_to_clipboard)
        self.reset_button.clicked.connect(self.reset)

    def set_up_ui(self):
        self.gen_layout = QHBoxLayout(self)

        self.preview_layout = QVBoxLayout()
        self.form_layout = QVBoxLayout()
        self.form_layout_inlay1 = QHBoxLayout()
        self.form_layout_inlay2 = QHBoxLayout()
        self.control_layout = QVBoxLayout()
        self.control_layout_inlay1 = QHBoxLayout()

        self.card_preview = CardPreview(self)

        self.form = FormView(self)
        self.form.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.reset_button = QPushButton("Очистить", self)
        self.reset_button.setFont(QFont("Arial", 16))
        self.reset_button.setMinimumHeight(35)
        self.reset_button.setStyleSheet('QPushButton{background-color: #bcbcbc;}')

        self.copy_button = QPushButton("Копировать", self)
        self.copy_button.setFont(QFont("Arial", 16))
        self.copy_button.setMinimumHeight(35)
        self.copy_button.setStyleSheet('QPushButton{background-color: #bcbcbc;}')

        self.upload_button = QPushButton("Загрузить в библиотеку", self)
        self.upload_button.setFont(QFont("Arial", 22))
        self.upload_button.setMinimumHeight(50)

        self.download_button = QPushButton("Сохранить как...", self)
        self.download_button.setFont(QFont("Arial", 16))
        self.download_button.setMinimumHeight(35)
        self.download_button.setStyleSheet('QPushButton{background-color: #bcbcbc;}')
        
        self.preview_layout.addWidget(self.card_preview)
        self.preview_layout.addLayout(self.control_layout)

        self.control_layout_inlay1.addWidget(self.reset_button)
        self.control_layout_inlay1.addWidget(self.copy_button)
        self.control_layout_inlay1.addWidget(self.download_button)

        self.form_layout_inlay2.addWidget(self.form)
        self.form_layout_inlay2.addStretch()

        self.form_layout.addLayout(self.form_layout_inlay1)
        self.form_layout.addLayout(self.form_layout_inlay2)

        self.control_layout.addWidget(self.upload_button)
        self.control_layout.addLayout(self.control_layout_inlay1)

        self.gen_layout.addLayout(self.preview_layout)
        self.gen_layout.addLayout(self.form_layout)

        self.setLayout(self.gen_layout)

    def block_form_signals(self, block: bool):
        self.form.name_form.blockSignals(block)
        self.form.description_form.blockSignals(block)
        self.form.mana_form.blockSignals(block)
        self.form.attack_form.blockSignals(block)
        self.form.health_form.blockSignals(block)
        self.form.rarity_form.blockSignals(block)
        self.form.tribe_form.blockSignals(block)
        self.form.class_button_group.button_group.blockSignals(block)
        self.form.cardtype_button_group.button_group.blockSignals(block)

    def gather_form_data(self):
        meta_data = self.form.get_form_data()
        self.card_metadata.update(meta_data)
        
    def generate(self):
        self.setCursor(Qt.WaitCursor)

        self.gather_form_data()
        self.card_metadata.picture = pixmap_to_bytes(self.picture)

        self.card_metadata.move_x = self.card_preview.move_x
        self.card_metadata.move_y = self.card_preview.move_y
        self.card_metadata.zoom = self.card_preview.zoom
        try:
            if self.card_metadata.cardtype == CardType.MINION:
                self._current_pil_image = self.card_image_generator.generate(self.card_metadata)
            elif self.card_metadata.cardtype == CardType.SPELL:
                self._current_pil_image = self.card_image_generator_spell.generate(self.card_metadata)
            elif self.card_metadata.cardtype == CardType.WEAPON:
                self._current_pil_image = self.card_image_generator_weapon.generate(self.card_metadata)
        except GenerationError as e:
            QMessageBox.warning(None, "Ошибка генерации", str(e))
            return

        self.update_card_preview(pil_to_pixmap(self._current_pil_image))

        self.setCursor(Qt.ArrowCursor)
    
    def _finalize_card_image(self):
        if hasattr(self, '_current_pil_image') and self._current_pil_image:
            self.card_metadata.card_image = pil_to_bytes(self._current_pil_image)

    def upload_button_clicked(self):
        self.gather_form_data()
        if not self.card_metadata.name:
            QMessageBox.warning(self, "Ошибка", "Имя карты не может быть пустым.")
            return

        self._finalize_card_image()
        self.card_metadata.hash = self.cache_manager.calculate_hash(self.card_metadata)

        if self.upload_mode == CardBuilderView.UploadMode.NEW:
            self.upload_requested.emit(self.card_metadata)
        elif self.upload_mode == CardBuilderView.UploadMode.EDIT:
            if(QMessageBox.question(self, "Редактирование", f"Карта ID:{self.card_metadata.id} '{self.card_metadata.name}' будет изменена. Перезаписать?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes):
                self.upload_edit_requested.emit([self.card_metadata, self.card_previous_version])
    
    def update_card_preview(self, pixmap: QPixmap):
        self.card_preview.set_preview_image(pixmap)

    def on_picture_imported(self, image: QPixmap):
        self.picture = image

        self.generate()

    def download_button_clicked(self) -> bool:
        file_path, _ = QFileDialog.getSaveFileName(None, "Save Image", "Image.png", "Images (*.png *.jpg *.bmp);;All Files (*)")

        if file_path:
            if not hasattr(self, '_current_pil_image') or not self._current_pil_image:
                QMessageBox.warning(self, "Ошибка", "Некорректное изображение.")
                return False
            self._current_pil_image.save(file_path)
        else:
            QMessageBox.warning(self, "Предупреждение", "Не удалось сохранить изображение.")
            return False
        return True

    def on_edit_card_requested(self, metadata: CardMetadata):
        self.block_form_signals(True)
        
        self.upload_mode = CardBuilderView.UploadMode.EDIT
        self.card_metadata = CardMetadata()
        self.card_metadata.update(metadata.dict())
        self.card_previous_version = CardMetadata()
        self.card_previous_version.update(metadata.dict())

        self.upload_button.setText("Изменить")
        self.upload_button.setStyleSheet('QPushButton{background-color: #FFF68F;}')
        self.picture = bytes_to_pixmap(metadata.picture)
        self.card_preview.move_x = metadata.move_x
        self.card_preview.move_y = metadata.move_y
        self.card_preview.zoom = metadata.zoom
        self.form.class_button_group.set_checked_button_index(metadata.classtype-1)
        self.form.cardtype_button_group.set_checked_button_index(metadata.cardtype-1)
        self.form.name_form.setText(metadata.name)
        self.form.description_form.setText(metadata.description)
        self.form.attack_form.setValue(metadata.attack)
        self.form.health_form.setValue(metadata.health)
        self.form.mana_form.setValue(metadata.manacost)
        self.form.rarity_form.setCurrentIndex(metadata.rarity-1)
        self.form.tribe_form.setText(metadata.tribe)
        self.form.comment_form.setText(metadata.comment)
        self.form.activation_command_line.setText(metadata.command)
        self.form.istoken_form.setChecked(metadata.istoken)
        self.form.tokenstable_form.populate_table(metadata.tokens)
        
        self.block_form_signals(False)
        
        self.generate()
    
    def copy_image_to_clipboard(self):
        if not hasattr(self, '_current_pil_image') or not self._current_pil_image:
            return
        output = BytesIO()
        self._current_pil_image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()

    def reset(self):
        self.form.reset()

        self.upload_mode = CardBuilderView.UploadMode.NEW
        self.upload_button.setText("Загрузить в библиотеку")
        self.upload_button.setStyleSheet('QPushButton{background-color: #B2B2FF;}')
        self.card_preview.move_x = 0
        self.card_preview.move_y = 0
        self.card_preview.zoom = 0
        self.update_card_preview(QPixmap(r":start_card.png"))
        self.picture = QPixmap()
        self.card_metadata = CardMetadata()
        self.card_previous_version = CardMetadata()
        self._current_pil_image = None