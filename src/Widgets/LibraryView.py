import os
from typing import List

from PyQt5.QtWidgets import QFrame, QGridLayout, QMessageBox, QDialog, QVBoxLayout, QLabel, QStackedWidget, QFileDialog, QWidget, QScrollArea, QSizePolicy, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtGui import QMovie, QResizeEvent
from Widgets.DeckView import DeckView

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
        self.deck_view = DeckView()
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

        self.scroll_stack = QStackedWidget(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setMinimumWidth(CardWidget.minimumWidth(self) * 6)
        
        self.loading_label = QLabel(self)
        self.loading_animation = QMovie(r":loading_animation.gif")
        self.loading_label.setMovie(self.loading_animation)

        self.scroll_stack.addWidget(self.scroll_area)
        self.scroll_stack.addWidget(self.loading_label)
        self.scroll_stack.setCurrentIndex(0)

        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scrollable_widget = QWidget(self.scroll_area)
        self.grid_layout = QGridLayout(self.scrollable_widget)
        self.scroll_area.setWidget(self.scrollable_widget)
        self.scroll_area.setWidgetResizable(True)

        self.sub_gen_layout.addLayout(self.control_layout)
        self.sub_gen_layout.addWidget(self.scroll_stack)
        self.gen_layout.addLayout(self.sub_gen_layout, stretch=5)
        self.gen_layout.addWidget(self.deck_view, stretch=2)
        self.setLayout(self.gen_layout)

    def update(self):
        self.set_loading(True)
        self.update_library_requested.emit()

    def set_loading(self, is_loading: bool):
        if is_loading:
            self.scroll_stack.setCurrentIndex(1)
            self.loading_label.resize(self.scroll_area.size())
            self.loading_label.setStyleSheet(self.scrollable_widget.styleSheet())
            self.loading_animation.start()
        else:
            self.scroll_stack.setCurrentIndex(0)
            self.loading_animation.stop()
            self.setEnabled(True)

        self.deck_view.setEnabled(not is_loading)
        self.refresh_button.setEnabled(not is_loading)
        self.export_button.setEnabled(not is_loading)

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
            self.grid_layout.addWidget(card_widget, pos//4, pos%4)
            self.card_widgets.append(card_widget)
            pos+=1
            
        
        self.scrollable_widget.setMinimumWidth(self.scroll_area.width())
        self.scrollable_widget.setMinimumHeight(self.scroll_area.height())
        print("Library view updated")
        self.set_loading(False)
        self.resizeEvent(QResizeEvent(QSize(0,0), QSize(0,0)))

    def clear_grid(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    
    def on_export_clicked(self):
        if not self.card_widgets:
            print("Empty library")
            return
        
        directory_path = QFileDialog.getExistingDirectory(None, "Выберите папку", ".", )
        if directory_path:
            for card in self.card_widgets:
                img = bytes_to_pixmap(card.metadata.card_image)
                img.save(os.path.join(directory_path, card.metadata.name + ".png"))
            # Windows only
            os.startfile(directory_path)

        meta_list = []
        for card_widget in self.card_widgets:
            meta = card_widget.metadata
            #meta.card_image = None
            #meta.picture = None
            meta_list.append(meta)
        XMLGenerator.generate_xml_library(meta_list)

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

    def resizeEvent(self, a0) -> None:
        self.scrollable_widget.resize(self.scroll_area.size())
        return super().resizeEvent(a0)
