import os
from typing import List

from PyQt5.QtWidgets import QFrame, QGridLayout, QLineEdit, QComboBox, QCheckBox, QMessageBox, QDialog, QVBoxLayout, QLabel, QStackedWidget, QFileDialog, QWidget, QScrollArea, QSizePolicy, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, QSize, QSettings
from PyQt5.QtGui import QMovie, QResizeEvent
from Widgets.DeckView import DeckView
from Widgets.components.ToggleButton import ToggleButton
from Widgets.components.ScrollableGrid import ScrollableGrid

from utils.BytesEncoder import bytes_to_pixmap
from Widgets.components.CardWidget import CardWidget
from DataTypes import CardMetadata, Deck
from utils.XMLGenerator import XMLGenerator

class LibraryView(QFrame):

    update_library_requested = pyqtSignal()
    edit_card_requested = pyqtSignal(object)
    delete_card_requested = pyqtSignal(object)
    get_decks_requsted = pyqtSignal(str)
    create_new_deck_requested = pyqtSignal(str)
    update_deck_requested = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.card_widgets: List[CardWidget] = []
        self.original_positions = {}
        self.deck_view = DeckView()
        self.settings = QSettings("HearthTrice")
        self.set_up_ui()
        self.set_up_connections()

    def set_up_connections(self):
        self.deck_view.get_decks_requested.connect(self.get_decks_requsted)

        self.refresh_button.clicked.connect(self.update)
        self.export_button.clicked.connect(self.on_export_clicked)
        self.deck_view.create_new_deck_requested.connect(self.create_new_deck_requested)
        self.deck_view.update_deck_requested.connect(self.update_deck_requested)

    def set_up_ui(self):
        self.setEnabled(False)
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.gen_layout = QHBoxLayout(self)
        self.sub_gen_layout = QVBoxLayout()
        self.control_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh", self)
        self.control_layout.addWidget(self.refresh_button)

        self.export_button = QPushButton("Экспорт", self)
        self.control_layout.addWidget(self.export_button)

        self.loading_label = QLabel(self)
        self.loading_animation = QMovie(r":loading_animation.gif")
        self.loading_label.setMovie(self.loading_animation)

        self.main_gallery_grid = ScrollableGrid(self)
        self.std_gallery_grid = ScrollableGrid(self)

        self.stack = QStackedWidget(self)
        self.stack.addWidget(self.main_gallery_grid)
        self.stack.addWidget(self.std_gallery_grid)
        self.stack.addWidget(self.loading_label)

        self.filter_layout = QHBoxLayout()
        self.reset_filter_button = QPushButton("Очистить", self)
        self.reset_filter_button.clicked.connect(self.reset_filter)

        self.name_filter = QLineEdit(self)
        self.name_filter.setPlaceholderText("Поиск...")
        self.name_filter.textChanged.connect(self.on_filter_changed)

        self.cardtype_filter = QComboBox(self)
        self.cardtype_filter.addItems(["Тип", "Minion", "Spell", "Weapon", "Hero"])
        self.cardtype_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.no_tokens_toggle = ToggleButton("Без токенов", self)
        self.no_tokens_toggle.toggled.connect(self.on_filter_changed)
        
        self.standard_only_toggle = ToggleButton("Стандартные", self)
        self.standard_only_toggle.toggled.connect(self.switch_to_standard_grid)
        
        self.filter_layout.addWidget(self.reset_filter_button)
        self.filter_layout.addWidget(self.name_filter)
        self.filter_layout.addWidget(self.cardtype_filter)
        self.filter_layout.addWidget(self.no_tokens_toggle)
        self.filter_layout.addWidget(self.standard_only_toggle)

        self.sub_gen_layout.addLayout(self.control_layout)
        self.sub_gen_layout.addWidget(self.stack)
        self.sub_gen_layout.addLayout(self.filter_layout)
        self.gen_layout.addLayout(self.sub_gen_layout, stretch=5)
        self.gen_layout.addWidget(self.deck_view, stretch=2)
        self.setLayout(self.gen_layout)

    def switch_to_standard_grid(self):
        if self.standard_only_toggle.isChecked:
            self.stack.setCurrentIndex(1)
        else:
            self.stack.setCurrentIndex(0)

    def on_filter_changed(self):
        pos = 0
        for card in self.card_widgets:
            if self.filter_is_empty():
                self.main_gallery_grid.grid_layout.removeWidget(card)
                x, y = self.original_positions[card]
                self.main_gallery_grid.grid_layout.addWidget(card, x, y)
                card.setVisible(True)
            else: 
                self.main_gallery_grid.grid_layout.removeWidget(card)
                if self.check_filter_conditions(card):
                    self.main_gallery_grid.grid_layout.addWidget(card, pos//4, pos%4)
                    card.setVisible(True)
                    pos+=1
                else:
                    card.setVisible(False)

    def filter_is_empty(self) -> bool:
        is_empty = True
        is_empty = is_empty & ( not self.name_filter.text() )
        is_empty = is_empty & ( not self.cardtype_filter.currentIndex() )
        is_empty = is_empty & ( not self.no_tokens_toggle.isChecked )
        is_empty = is_empty & ( not self.standard_only_toggle.isChecked )
        return is_empty

    def check_filter_conditions(self, card: CardWidget) -> bool:
        match = True

        match = match & ( self.name_filter.text().upper() in card.metadata.name.upper() )
        if self.cardtype_filter.currentIndex():
            match = match & ( self.cardtype_filter.currentIndex() == card.metadata.cardtype )
        if self.no_tokens_toggle.isChecked:
            match = match & ( not card.metadata.istoken )

        return match

    def reset_filter(self):
        self.name_filter.clear()
        self.cardtype_filter.setCurrentIndex(0)
        if self.no_tokens_toggle.isChecked:
            self.no_tokens_toggle.toggleState()
        if self.standard_only_toggle.isChecked:
            self.standard_only_toggle.toggleState()

    def update(self):
        self.set_loading(True)
        self.update_library_requested.emit()

    def set_loading(self, is_loading: bool):
        if is_loading:
            self.loading_animation.start()
            self.stack.setCurrentIndex(2)
        else:
            self.stack.setCurrentIndex(0)
            self.standard_only_toggle.setChecked(False)
            self.loading_animation.stop()
            self.setEnabled(True)

        self.deck_view.setEnabled(not is_loading)
        self.refresh_button.setEnabled(not is_loading)
        self.export_button.setEnabled(not is_loading)

    def set_updated_library(self, cards: List[CardMetadata]):
        if not cards:
            print("Cannot update library view")
            return
        self.clear_grid()

        pos = 0
        for card in cards:
            if not card.card_image:
                print(f"Skipped card [{card.id}]: no image")
                continue
            card_widget = CardWidget(card, self)
            card_widget.card_clicked_event.connect(self.on_card_clicked)
            card_widget.edit_card_requested.connect(self.edit_card_requested)
            card_widget.delete_card_requested.connect(self.delete_card_requested)
            card_widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.main_gallery_grid.grid_layout.addWidget(card_widget, pos//4, pos%4)
            self.original_positions[card_widget] = (pos//4, pos%4)

            self.card_widgets.append(card_widget)
            pos+=1
            
        if not self.no_tokens_toggle.isChecked:
            self.no_tokens_toggle.toggleState()
        for row in range(self.main_gallery_grid.grid_layout.rowCount()):
            self.main_gallery_grid.grid_layout.setRowMinimumHeight(row, 280)
        self.set_loading(False)
        print("Library view updated")

    def clear_grid(self):
        while self.main_gallery_grid.grid_layout.count():
            child = self.main_gallery_grid.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.card_widgets.clear()
        self.original_positions.clear()

    
    def on_export_clicked(self):
        if not self.card_widgets:
            print("Empty library")
            return
        game_dir = self.settings.value("path")
        if not game_dir:
            game_dir = os.getcwd()
        pics_dir = os.path.join(game_dir, "data", "pics", "CUSTOM")
        os.makedirs(pics_dir, exist_ok=True)
        for card in self.card_widgets:
            img = bytes_to_pixmap(card.metadata.card_image)
            img.save(os.path.join(pics_dir, card.metadata.name + ".png"))
            os.startfile(pics_dir) # Windows only

        metas_list = []
        for card_widget in self.card_widgets:
            meta = card_widget.metadata
            metas_list.append(meta)
        customsets_dir = os.path.join(game_dir, "data", "customsets")
        os.makedirs(customsets_dir, exist_ok=True)

        lib_xml_path = os.path.join(customsets_dir, "HearthTrice Customset.xml")
        XMLGenerator.generate_xml_library(lib_xml_path, metas_list)

        QMessageBox.information(self, "Готово", "Библиотека выгружена.")

    def open_deck_view(self):
        dialog = QDialog(self)
        self.deck_view.setParent(dialog)
        self.deck_view.show()
        geometry = self.geometry()
        dialog.setGeometry(geometry.right(), geometry.top(), 200, self.height())
        dialog.exec_()

    def on_card_clicked(self, metadata: CardMetadata):
        response = self.deck_view.add_item(metadata.id, metadata.name, metadata.manacost, metadata.istoken)
        if not response.ok:
            QMessageBox.warning(self, "Ошибка", response.msg)
            return
        
        if metadata.tokens:
            token_card_ids = list(map(int, metadata.tokens.split(',')))
            for card_id in token_card_ids:
                token_meta = self.get_card_metadata_by_id(card_id, deck_fields_only=True)
                if not token_meta:
                    continue
                self.deck_view.add_item(card_id, token_meta.name, token_meta.manacost, token_meta.istoken)

    def set_updated_decks(self, decks: List[Deck]):
        if not decks:
            print("Cannot update decks")
            return
        
        # TODO: switch to map
        for deck in decks:
            for card in deck.cards:
                partial_meta = self.get_card_metadata_by_id(card.id, deck_fields_only=True)
                if partial_meta:
                    card.name = partial_meta.name
                    card.manacost = partial_meta.manacost
                    card.istoken = partial_meta.istoken
                else:
                    card.name = "|Not Found|"
                    card.manacost = -1
                    card.istoken = 0
        self.deck_view.set_updated_decks(decks)
            
    def get_card_metadata_by_id(self, id: int, deck_fields_only: bool = False) -> CardMetadata:
        for card_widget in self.card_widgets:
            if card_widget.metadata.id == id:
                if not deck_fields_only:
                    return card_widget.metadata
                partial_meta = CardMetadata()
                partial_meta.name = card_widget.metadata.name
                partial_meta.manacost = card_widget.metadata.manacost
                partial_meta.istoken = card_widget.metadata.istoken
                return partial_meta
        return None
        
    def resizeEvent(self, a0) -> None:
        return super().resizeEvent(a0)
