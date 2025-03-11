from genericpath import isdir, isfile
import os
import random
from turtle import isvisible
from typing import List
import json

from PyQt5.QtWidgets import QFrame, QApplication, QProgressBar, QGridLayout, QLineEdit, QComboBox, QCheckBox, QMessageBox, QDialog, QVBoxLayout, QLabel, QStackedWidget, QFileDialog, QWidget, QScrollArea, QSizePolicy, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt, QThread, QTimer, QDir, QByteArray, QFile, QTextStream, QSize, QSettings, QIODevice
from PyQt5.QtGui import QMovie, QIcon
from Widgets.DeckView import DeckView
from Widgets.components.ToggleButton import ToggleButton
from Widgets.components.ScrollableGrid import ScrollableGrid

from utils.BytesEncoder import bytes_to_pixmap
from Widgets.components.CardWidget import CardWidget
from DataTypes import CardMetadata, Deck, Response, CardType, Rarity, ClassType, StdMetadata
from utils.XMLGenerator import XMLGenerator
from GameListener import GameListener
from utils.string import sanitize

class ExportThread(QThread):
    update_progress = pyqtSignal(int)  # Сигнал для обновления прогресса
    finished_export = pyqtSignal()     # Сигнал о завершении работы

    def __init__(self, metas, card_widgets, custom_pics_dir, parent=None):
        super().__init__(parent)
        self.metas = metas
        self.card_widgets = card_widgets
        self.custom_pics_dir = custom_pics_dir

    def run(self):
        """Выполняет экспорт данных в фоновом потоке."""
        progress = 0
        if not self.metas:
            self.update_progress.emit(0)
            for card in self.card_widgets:
                img = bytes_to_pixmap(card.metadata.card_image)
                img.save(os.path.join(self.custom_pics_dir, sanitize(card.metadata.name) + ".png"))
                progress += 1
                self.update_progress.emit(progress)
        else:
            self.update_progress.emit(0)
            for meta in self.metas:
                img = bytes_to_pixmap(meta.card_image)
                img.save(os.path.join(self.custom_pics_dir, sanitize(meta.name) + ".png"))
                progress += 1
                self.update_progress.emit(progress)
        self.finished_export.emit()

class LibraryView(QFrame):

    update_library_requested = pyqtSignal()
    edit_card_requested = pyqtSignal(object)
    delete_card_requested = pyqtSignal(object)
    get_decks_requsted = pyqtSignal(str)
    create_new_deck_requested = pyqtSignal(str)
    update_deck_requested = pyqtSignal(tuple)

    finished_loading = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.card_widgets: List[CardWidget] = []
        self.std_card_widgets: List[CardWidget] = []
        self.original_positions = {}
        self.std_original_positions= {}
        self.deck_view = DeckView()
        self.settings = QSettings("HearthTrice")
        self.set_up_ui()
        self.set_up_connections()

        try:
            import resources_std
            self.load_standard_cards()
        except ImportError as e:
            self.export_std_checkbox.setEnabled(False)
            self.standard_only_toggle.setEnabled(False)

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
        self.sub_gen_layout_2 = QVBoxLayout()
        self.control_layout = QHBoxLayout()

        self.launch_button = QPushButton("Запуск Cockatrice")
        self.launch_button.setStyleSheet('QPushButton{ background-color: #bfffbf; font-weight: bold; }')
        self.launch_button.clicked.connect(self.launch_cockatrice)

        self.refresh_button = QPushButton("Refresh", self)
        self.control_layout.addWidget(self.refresh_button)
        self.control_layout.addStretch()

        self.export_button = QPushButton("Экспорт библиотеки", self)
        self.control_layout.addWidget(self.export_button)

        self.export_std_checkbox = ToggleButton("Вместе со стандартными", self)
        self.control_layout.addWidget(self.export_std_checkbox)

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

        self.roll_button = QPushButton("", self)
        self.roll_button.setIcon(QIcon(":icons/roll_icon.png"))
        self.roll_button.setMaximumWidth(64)
        self.roll_button.setToolTip("Выбрать случайную из отфильтрованных")
        self.roll_button.clicked.connect(self.roll)

        self.name_filter = QLineEdit(self)
        self.name_filter.setPlaceholderText("Поиск...")
        self.name_filter.textChanged.connect(self.on_filter_changed)

        self.cardtype_filter = QComboBox(self)
        self.cardtype_filter.addItems(["Тип", "Minion", "Spell", "Weapon", "Hero"])
        self.cardtype_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.rarity_filter = QComboBox(self)
        self.rarity_filter.addItems(["Редкость", "None", "Common", "Rare", "Epic", "Legendary"])
        self.rarity_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.classtype_filter = QComboBox(self)
        self.classtype_filter.addItems(["Класс", "Neutral", "Mage", "Hunter", "Paladin", "Warrior", "Druid", "Rogue", "Priest", "Warlock", "Shaman"])
        self.classtype_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.manacost_filter = QComboBox(self)
        self.manacost_filter.addItems(["Мана", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10+"])
        self.manacost_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.no_tokens_toggle = ToggleButton("Без токенов", self)
        self.no_tokens_toggle.toggled.connect(self.on_filter_changed)
        
        self.standard_only_toggle = ToggleButton("Стандартные", self)
        self.standard_only_toggle.toggled.connect(self.switch_to_standard_grid)
        
        self.filter_layout.addWidget(self.reset_filter_button)
        self.filter_layout.addWidget(self.name_filter)
        self.filter_layout.addWidget(self.roll_button)
        self.filter_layout.addWidget(self.manacost_filter)
        self.filter_layout.addWidget(self.rarity_filter)
        self.filter_layout.addWidget(self.classtype_filter)
        self.filter_layout.addWidget(self.cardtype_filter)
        self.filter_layout.addWidget(self.no_tokens_toggle)
        self.filter_layout.addWidget(self.standard_only_toggle)

        self.sub_gen_layout.addLayout(self.control_layout)
        self.sub_gen_layout.addWidget(self.stack)
        self.sub_gen_layout.addLayout(self.filter_layout)

        self.sub_gen_layout_2.addWidget(self.deck_view)
        self.sub_gen_layout_2.addWidget(self.launch_button)

        self.gen_layout.addLayout(self.sub_gen_layout, stretch=5)
        self.gen_layout.addLayout(self.sub_gen_layout_2, stretch=2)
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
        pos = 0
        for card in self.std_card_widgets:
            if self.filter_is_empty():
                self.std_gallery_grid.grid_layout.removeWidget(card)
                x, y = self.std_original_positions[card]
                self.std_gallery_grid.grid_layout.addWidget(card, x, y)
                card.setVisible(True)
            else: 
                self.std_gallery_grid.grid_layout.removeWidget(card)
                if self.check_filter_conditions(card):
                    self.std_gallery_grid.grid_layout.addWidget(card, pos//4, pos%4)
                    card.setVisible(True)
                    pos+=1
                else:
                    card.setVisible(False)
        if self.standard_only_toggle.isChecked:
            self.std_gallery_grid.scrollToTop()
        else:
            self.main_gallery_grid.scrollToTop()

    def filter_is_empty(self) -> bool:
        is_empty = True
        is_empty = is_empty & ( not self.name_filter.text() )
        is_empty = is_empty & ( not self.rarity_filter.currentIndex() )
        is_empty = is_empty & ( not self.cardtype_filter.currentIndex() )
        is_empty = is_empty & ( not self.classtype_filter.currentIndex() )
        is_empty = is_empty & ( not self.manacost_filter.currentIndex() )
        is_empty = is_empty & ( not self.no_tokens_toggle.isChecked )
        is_empty = is_empty & ( not self.standard_only_toggle.isChecked )
        return is_empty

    def check_filter_conditions(self, card: CardWidget) -> bool:
        match = True

        tribe = card.metadata.tribe if card.metadata.tribe else ""

        match = match & ( self.name_filter.text().upper() in card.metadata.name.upper() or 
                         self.name_filter.text().upper() in tribe.upper())
        if self.cardtype_filter.currentIndex():
            match = match & ( self.cardtype_filter.currentIndex() == card.metadata.cardtype )
        if self.rarity_filter.currentIndex():
            match = match & ( self.rarity_filter.currentIndex() == card.metadata.rarity )
        if self.classtype_filter.currentIndex():
            match = match & ( self.classtype_filter.currentIndex() == card.metadata.classtype )
        if self.manacost_filter.currentIndex():
            if self.manacost_filter.currentIndex() >= 11:
                match = match & ( card.metadata.manacost >= 10 )
            else:
                match = match & ( self.manacost_filter.currentIndex() == card.metadata.manacost + 1 )
        if self.no_tokens_toggle.isChecked:
            match = match & ( not card.metadata.istoken )

        return match

    def reset_filter(self):
        self.name_filter.clear()
        self.cardtype_filter.setCurrentIndex(0)
        self.classtype_filter.setCurrentIndex(0)
        self.manacost_filter.setCurrentIndex(0)
        if self.standard_only_toggle.isChecked:
            self.standard_only_toggle.toggleState()

    def roll(self) -> int:
        card_widgets = self.std_card_widgets if self.standard_only_toggle.isChecked else self.card_widgets
        filtered_cards = []
        for card_widget in card_widgets:
            if card_widget.isVisible():
                filtered_cards.append(card_widget)

        if not filtered_cards:
            return 0

        random_card = random.choice(filtered_cards)
        random_card.setHighlightedPing(3)

        if self.standard_only_toggle.isChecked:
            self.std_gallery_grid.ensureWidgetVisible(random_card)
        else:
            self.main_gallery_grid.ensureWidgetVisible(random_card)

        return random_card.metadata.id
    
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

        self.finished_loading.emit(not is_loading)

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
        print("LibraryView updated")

    def clear_grid(self):
        while self.main_gallery_grid.grid_layout.count():
            child = self.main_gallery_grid.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.card_widgets.clear()
        self.original_positions.clear()

    def on_export_clicked(self, metas: List[CardMetadata] = None):
        # Get path
        if not self.card_widgets:
            print("Empty library")
            return
        game_dir = self.settings.value("path")
        if not game_dir:
            QMessageBox.information("Экспорт", "Укажите директоирю Cockatrice в настройках")
            # game_dir = os.getcwd()

        pics_dir = os.path.join(game_dir, "data", "pics")
        if not os.path.isdir(pics_dir):
            pics_dir = os.path.join(os.getenv('LOCALAPPDATA'), "Cockatrice", "Cockatrice", "pics")

        custom_pics_dir = os.path.join(pics_dir, "CUSTOM")
        os.makedirs(custom_pics_dir, exist_ok=True)

        if not metas:
            os.startfile(custom_pics_dir) # Windows only

        dialog = QDialog(self)
        dialog.setWindowTitle("Экспорт")
        dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        layout = QVBoxLayout()
        label = QLabel("Выгрузка библиотеки...")
        if metas:
            label.setText("Обновление экспорта...")
        layout.addWidget(label)
        label.setAlignment(Qt.AlignCenter)

        progress = QProgressBar()
        layout.addWidget(progress)
        progress.setRange(0, len(self.card_widgets))
        if metas:
            progress.setRange(0, len(metas))
            
        dialog.setLayout(layout)
        dialog.setModal(True)

        export_thread = ExportThread(metas, self.card_widgets, custom_pics_dir)
        export_thread.update_progress.connect(progress.setValue)
        export_thread.finished_export.connect(dialog.accept)

        dialog.show()
        export_thread.start()

        dialog.exec_()

        # Save custom xml
        metas_list = []
        for card_widget in self.card_widgets:
            meta = card_widget.metadata
            metas_list.append(meta)

        customsets_dir = os.path.join(game_dir, "data", "customsets")
        if not os.path.isdir(customsets_dir):
            customsets_dir = os.path.join(os.getenv('LOCALAPPDATA'), "Cockatrice", "Cockatrice", "customsets")
        os.makedirs(customsets_dir, exist_ok=True)

        lib_xml_path = os.path.join(customsets_dir, "TK.xml")
        XMLGenerator.generate_xml_library(lib_xml_path, metas_list)

        ## STD
        # Export standard set
        if self.export_std_checkbox.isChecked and self.std_card_widgets:
            label.setText("Выгрузка стандартных карт...")
            progress.setRange(0, len(self.std_card_widgets))
            export_thread = ExportThread(None, self.std_card_widgets, custom_pics_dir)
            export_thread.update_progress.connect(progress.setValue)
            export_thread.finished_export.connect(dialog.accept)

            dialog.show()
            export_thread.start()

            dialog.exec_()

            # Save std xml
            metas_list = []
            for card_widget in self.std_card_widgets:
                meta = card_widget.metadata
                metas_list.append(meta)

            os.makedirs(customsets_dir, exist_ok=True)

            lib_xml_path = os.path.join(customsets_dir, "TK_STD.xml")
            XMLGenerator.generate_xml_library(lib_xml_path, metas_list)

        if not metas:
            QMessageBox.information(self, "Готово", "Библиотека выгружена.")
        
        QApplication.instance().activeWindow()

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
                self.deck_view.add_item(card_id, token_meta.name, token_meta.manacost, True)

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
    
    def update_uploaded_card(self, card_metadata: CardMetadata):
        new_card = CardWidget(card_metadata, self)
        new_card.card_clicked_event.connect(self.on_card_clicked)
        new_card.edit_card_requested.connect(self.edit_card_requested)
        new_card.delete_card_requested.connect(self.delete_card_requested)

        self.no_tokens_toggle.setChecked(False)
        count = self.main_gallery_grid.grid_layout.count()
        self.main_gallery_grid.grid_layout.addWidget(new_card, count // 4, count % 4)
        self.original_positions[new_card] = (count //4, count % 4)
        self.card_widgets.append(new_card)

    def update_edited_card(self, card_metadata: CardMetadata):
        for i, card_widget in enumerate(self.card_widgets):
            if card_widget.metadata.id == card_metadata.id:
                new_card = CardWidget(card_metadata, self)
                new_card.card_clicked_event.connect(self.on_card_clicked)
                new_card.edit_card_requested.connect(self.edit_card_requested)
                new_card.delete_card_requested.connect(self.delete_card_requested)
                x, y = self.original_positions[card_widget]
                self.original_positions.pop(card_widget)
                self.original_positions[new_card] = x, y

                new_x, new_y = x,y
                if self.no_tokens_toggle.isChecked:
                    for j in range(self.main_gallery_grid.grid_layout.count()):
                        item = self.main_gallery_grid.grid_layout.itemAt(j)
                        if item.widget() == card_widget:
                            new_x, new_y, _, _ = self.main_gallery_grid.grid_layout.getItemPosition(j)

                self.main_gallery_grid.grid_layout.removeWidget(card_widget)
                self.main_gallery_grid.grid_layout.addWidget(new_card, new_x, new_y)
                
                self.card_widgets[i] = new_card
                card_widget.deleteLater()
                return

    def load_standard_cards(self) -> Response:
        try:
            json_path = ':std/std_metadata.json'
            file = QFile(json_path)
            if not file.open(QFile.ReadOnly | QFile.Text):
                print(f"Cannot open file: {json_path}")
                return None
            text_stream = QTextStream(file)
            json_text = text_stream.readAll()
            file.close()
            std_metadata = json.loads(str(json_text))

            for new_id, entry in enumerate(std_metadata):
                std_meta = StdMetadata()
                std_meta.id = -new_id-10
                std_meta.name = entry["name"]
                std_meta.description = entry["description"]
                std_meta.manacost = entry["manacost"]
                std_meta.rarity = entry["rarity"]
                std_meta.cardtype = entry["cardtype"]
                std_meta.classtype = entry["classtype"]
                std_meta.attack = entry["attack"]
                std_meta.health = entry["health"]
                std_meta.tribe = entry["tribe"]
                std_meta.istoken = entry["istoken"]
                std_meta.card_image_path = entry["card_image_path"]

                file = QFile(f":{std_meta.card_image_path}")
                if file.open(QIODevice.ReadOnly):
                    bytes_data = file.readAll()
                    file.close()
                    std_meta.card_image = bytes_data
                std_card = CardWidget(std_meta, self)
                self.std_card_widgets.append(std_card)
            print("Loaded", len(self.std_card_widgets), "standard cards.")

            pos = 0
            for card_widget in self.std_card_widgets:
                card_widget.card_clicked_event.connect(self.on_card_clicked)
                card_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
                self.std_gallery_grid.grid_layout.addWidget(card_widget, pos//4, pos%4)
                self.std_original_positions[card_widget] = (pos//4, pos%4)
                pos+=1
                
            for row in range(self.std_gallery_grid.grid_layout.rowCount()):
                self.std_gallery_grid.grid_layout.setRowMinimumHeight(row, 130)
        except Exception as e:
            print("Unable to load std cards", e)
            return Response(False, str(e))
    
    def launch_cockatrice(self):
        game_dir = self.settings.value("path")
        exe_path = os.path.join(game_dir, "cockatrice.exe")
        if not os.path.isfile(exe_path):
            QMessageBox.warning(self, "Ошибка", f"cockatrice.exe не найден в {game_dir}")
            return
        
        os.startfile(exe_path)        

    def get_card_name_by_id(self, id: int) -> str:
        for card_widget in self.card_widgets + self.std_card_widgets:
            if card_widget.metadata.id == id:
                return card_widget.metadata.name
        return ""

    def get_card_command_by_name(self, card_name: str) -> str:
        for card_widget in self.card_widgets + self.std_card_widgets:
            if card_widget.metadata.name == card_name:
                return card_widget.metadata.command
        return ""
    
    def get_random_card_among_ids(self, ids: List[int]) -> str:
        chosen_id = int(random.choice(ids))
        for card_widget in self.card_widgets + self.std_card_widgets:
            if card_widget.metadata.id == chosen_id:
                return card_widget.metadata.name
        return ""

    def get_random_card_by_filter(self, cardtype: str, classtype: str, manacost: str,
                                     tribe: str, rarity: str, std_only: bool) -> int:
        self.reset_filter()
        self.no_tokens_toggle.setChecked(True)

        if cardtype != "any": self.cardtype_filter.setCurrentIndex(CardType.get_value(cardtype)) 
        if classtype != "any": self.classtype_filter.setCurrentIndex(ClassType.get_value(classtype))
        if manacost != "any": self.manacost_filter.setCurrentIndex(int(manacost) + 1)
        if tribe != "any": self.name_filter.setText(tribe)
        if rarity != "any": self.manacost_filter.setCurrentIndex(Rarity.get_value(rarity))
        self.standard_only_toggle.setChecked(std_only)
        
        chosen_id = self.roll()
        return chosen_id

    def resizeEvent(self, a0) -> None:
        return super().resizeEvent(a0)
