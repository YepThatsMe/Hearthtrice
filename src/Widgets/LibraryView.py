import os
import random
from typing import List

from PyQt5.QtWidgets import QFrame, QApplication, QProgressBar, QGridLayout, QLineEdit, QComboBox, QCheckBox, QMessageBox, QDialog, QVBoxLayout, QLabel, QStackedWidget, QFileDialog, QWidget, QScrollArea, QSizePolicy, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt, QThread, QTimer, QDir, QByteArray, QSize, QSettings
from PyQt5.QtGui import QIcon
from Widgets.DeckView import DeckView
from Widgets.components.ToggleButton import ToggleButton
from Widgets.components.ScrollableGrid import ScrollableGrid
from Widgets.components.IconFilterGroup import IconFilterGroup
from Widgets.InfoBase import InfoBaseWidget

from utils.BytesEncoder import bytes_to_pixmap
from Widgets.components.CardWidget import CardWidget
from Widgets.components.NotificationWidget import NotificationWidget
from DataTypes import CardMetadata, Deck, Response, CardType, Rarity, ClassType, StdMetadata
from utils.XMLGenerator import XMLGenerator
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
    rename_deck_requested = pyqtSignal(tuple)
    duplicate_deck_requested = pyqtSignal()
    delete_deck_requested = pyqtSignal(int)

    finished_loading = pyqtSignal(bool)
    infobase_load_requested = pyqtSignal()
    infobase_save_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.card_widgets: List[CardWidget] = []
        self.std_card_widgets: List[CardWidget] = []
        self.original_positions = {}
        self.std_original_positions= {}
        self.deck_view = DeckView()
        self.settings = QSettings("HearthTrice")
        self.pending_initial_filter = False
        self.set_up_ui()
        self.set_up_connections()

    def set_up_connections(self):
        self.deck_view.get_decks_requested.connect(self.get_decks_requsted)

        self.refresh_button.clicked.connect(self.update)
        self.export_button.clicked.connect(self.on_export_clicked)
        self.deck_view.create_new_deck_requested.connect(self.create_new_deck_requested)
        self.deck_view.update_deck_requested.connect(self.update_deck_requested)
        self.deck_view.rename_deck_requested.connect(self.rename_deck_requested)
        self.deck_view.duplicate_deck_requested.connect(self.duplicate_deck_requested)
        self.deck_view.delete_deck_requested.connect(self.delete_deck_requested)

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
        self.infobase_toggle = ToggleButton("", self, icon=":icons/info_icon.png")
        self.infobase_toggle.setFixedSize(36, 36)
        self.infobase_toggle.setIconSize(QSize(32, 32))
        self.infobase_toggle.setToolTip("База знаний")
        self.infobase_toggle.toggled.connect(self.on_infobase_toggled)
        self.control_layout.addWidget(self.infobase_toggle)
        self.control_layout.addStretch()

        self.export_button = QPushButton("Экспорт библиотеки", self)
        self.control_layout.addWidget(self.export_button)

        self.export_std_checkbox = ToggleButton("Вместе со стандартными", self)
        self.control_layout.addWidget(self.export_std_checkbox)

        self.main_gallery_grid = ScrollableGrid(self)
        self.std_gallery_grid = ScrollableGrid(self)

        self.stack = QStackedWidget(self)
        self.stack.addWidget(self.main_gallery_grid)
        self.stack.addWidget(self.std_gallery_grid)

        self.infobase_widget = InfoBaseWidget(self)
        self.infobase_widget.save_requested.connect(self.infobase_save_requested.emit)

        self.content_stack = QStackedWidget(self)
        self.content_stack.addWidget(self.stack)
        self.content_stack.addWidget(self.infobase_widget)

        self.filter_outer = QHBoxLayout()
        self.filter_outer.setContentsMargins(0, 0, 0, 0)
        self.filter_outer.setSpacing(6)

        self.filter_layout = QVBoxLayout()
        self.filter_layout.setContentsMargins(8, 8, 0, 8)
        self.filter_layout.setSpacing(6)

        self.filter_top_row = QHBoxLayout()
        self.filter_mana_row = QHBoxLayout()
        self.filter_class_row = QHBoxLayout()
        self.filter_rarity_row = QHBoxLayout()

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

        self.manacost_filter = IconFilterGroup(
            IconFilterGroup.make_mana_icons(44),
            button_width=48,
            button_height=48,
            tooltips=[str(i) for i in range(10)] + ["10+"],
            parent=self,
        )
        self.manacost_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.classtype_filter = IconFilterGroup(
            [f":icons/classicons/icon_{i}.png" for i in range(10)],
            button_width=56,
            button_height=52,
            tooltips=["Neutral", "Mage", "Hunter", "Paladin", "Warrior",
                      "Druid", "Rogue", "Priest", "Warlock", "Shaman"],
            parent=self,
        )
        self.classtype_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.rarity_filter = IconFilterGroup(
            [
                None,
                ":Cardbuilder/MINION/Card_Inhand_MINION_Gem_Common.png",
                ":Cardbuilder/MINION/Card_Inhand_MINION_Gem_Rare.png",
                ":Cardbuilder/MINION/Card_Inhand_MINION_Gem_Epic.png",
                ":Cardbuilder/MINION/Card_Inhand_MINION_Gem_Legendary.png",
            ],
            button_width=64,
            button_height=48,
            tooltips=["None", "Common", "Rare", "Epic", "Legendary"],
            parent=self,
        )
        self.rarity_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.cardtype_filter = IconFilterGroup(
            [
                "icons/minion_icon.png",
                "icons/spell_icon.png",
                "icons/weapon_icon.png",
                "icons/hero_icon.png",
            ],
            button_width=64,
            button_height=56,
            tooltips=["Minion", "Spell", "Weapon", "Hero"],
            vertical=True,
            parent=self,
        )
        self.cardtype_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.no_tokens_toggle = ToggleButton("Без токенов", self)
        self.no_tokens_toggle.toggled.connect(self.on_filter_changed)

        self.standard_only_toggle = ToggleButton("Стандартные", self)
        self.standard_only_toggle.toggled.connect(self.switch_to_standard_grid)

        self.filter_top_row.addWidget(self.reset_filter_button)
        self.filter_top_row.addWidget(self.name_filter, stretch=1)
        self.filter_top_row.addWidget(self.roll_button)
        self.filter_top_row.addWidget(self.no_tokens_toggle)
        self.filter_top_row.addWidget(self.standard_only_toggle)

        self.filter_mana_row.addWidget(self.manacost_filter, stretch=1)
        self.filter_class_row.addWidget(self.classtype_filter, stretch=1)
        self.filter_rarity_row.addWidget(self.rarity_filter, stretch=1)

        self.filter_layout.addLayout(self.filter_top_row)
        self.filter_layout.addLayout(self.filter_mana_row)
        self.filter_layout.addLayout(self.filter_class_row)
        self.filter_layout.addLayout(self.filter_rarity_row)

        self.filter_outer.addLayout(self.filter_layout, stretch=1)
        self.filter_outer.addWidget(self.cardtype_filter)

        self.filter_container = QWidget(self)
        self.filter_container.setLayout(self.filter_outer)
        self.filter_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.filter_container.setMinimumHeight(230)

        gallery_min_h = 280 * 2 + 24
        self.content_stack.setMinimumHeight(gallery_min_h)
        self.content_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_gallery_grid.setMinimumHeight(gallery_min_h)
        self.std_gallery_grid.setMinimumHeight(gallery_min_h)
        self.stack.setMinimumHeight(gallery_min_h)

        self.sub_gen_layout.addLayout(self.control_layout, stretch=0)
        self.sub_gen_layout.addWidget(self.content_stack, stretch=1)
        self.sub_gen_layout.addWidget(self.filter_container, stretch=0)
        self.sub_gen_layout.setStretch(0, 0)
        self.sub_gen_layout.setStretch(1, 1)
        self.sub_gen_layout.setStretch(2, 0)

        self.sub_gen_layout_2.addWidget(self.deck_view)
        self.sub_gen_layout_2.addWidget(self.launch_button)

        self.gen_layout.addLayout(self.sub_gen_layout, stretch=5)
        self.gen_layout.addLayout(self.sub_gen_layout_2, stretch=2)
        self.setLayout(self.gen_layout)

    def switch_to_standard_grid(self):
        if self.standard_only_toggle.isChecked:
            self.stack.setCurrentIndex(1)
            self._ensure_std_default_class()
            if not self.no_tokens_toggle.isChecked:
                self.no_tokens_toggle.blockSignals(True)
                self.no_tokens_toggle.setChecked(True)
                self.no_tokens_toggle.blockSignals(False)
        else:
            self.stack.setCurrentIndex(0)
        self.on_filter_changed()

    def _ensure_std_default_class(self):
        if not self.standard_only_toggle.isChecked:
            return
        if self.classtype_filter.currentIndex() == 0:
            self.classtype_filter.blockSignals(True)
            self.classtype_filter.setCurrentIndex(ClassType.NEUTRAL)
            self.classtype_filter.blockSignals(False)
    def on_infobase_toggled(self, checked: bool):
        if checked:
            self.content_stack.setCurrentIndex(1)
            self.filter_container.hide()
            self.refresh_button.setEnabled(False)
            self.export_button.setEnabled(False)
            self.infobase_load_requested.emit()
        else:
            self.content_stack.setCurrentIndex(0)
            self.filter_container.show()
            self.refresh_button.setEnabled(True)
            self.export_button.setEnabled(True)
            self.infobase_widget.ensure_read_only()

    def set_infobase_content(self, html: str):
        self.infobase_widget.set_content(html or "")

    def _apply_initial_filter(self):
        if not self.isVisible():
            return
        self.pending_initial_filter = False
        for row in range(self.main_gallery_grid.grid_layout.rowCount()):
            self.main_gallery_grid.grid_layout.setRowMinimumHeight(row, 280)
        self.main_gallery_grid.updateGeometry()
        QApplication.processEvents()
        self.on_filter_changed()
    
    def on_filter_changed(self):
        if self.standard_only_toggle.isChecked and self.classtype_filter.currentIndex() == 0:
            self._ensure_std_default_class()

        main_scrollbar = self.main_gallery_grid.scrollArea.verticalScrollBar()
        std_scrollbar = self.std_gallery_grid.scrollArea.verticalScrollBar()
        
        main_old_value = main_scrollbar.value()
        main_old_max = main_scrollbar.maximum()
        main_ratio = main_old_value / main_old_max if main_old_max > 0 else 0
        
        std_old_value = std_scrollbar.value()
        std_old_max = std_scrollbar.maximum()
        std_ratio = std_old_value / std_old_max if std_old_max > 0 else 0
        
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
        
        for row in range(self.main_gallery_grid.grid_layout.rowCount()):
            self.main_gallery_grid.grid_layout.setRowMinimumHeight(row, 0)
        
        max_row_main = -1
        for i in range(self.main_gallery_grid.grid_layout.count()):
            item = self.main_gallery_grid.grid_layout.itemAt(i)
            if item and item.widget() and item.widget().isVisible():
                row, col, _, _ = self.main_gallery_grid.grid_layout.getItemPosition(i)
                max_row_main = max(max_row_main, row)
                self.main_gallery_grid.grid_layout.setRowMinimumHeight(row, 280)
        
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
        
        for row in range(self.std_gallery_grid.grid_layout.rowCount()):
            self.std_gallery_grid.grid_layout.setRowMinimumHeight(row, 0)
        
        max_row_std = -1
        for i in range(self.std_gallery_grid.grid_layout.count()):
            item = self.std_gallery_grid.grid_layout.itemAt(i)
            if item and item.widget() and item.widget().isVisible():
                row, col, _, _ = self.std_gallery_grid.grid_layout.getItemPosition(i)
                max_row_std = max(max_row_std, row)
                self.std_gallery_grid.grid_layout.setRowMinimumHeight(row, 130)
        
        QApplication.processEvents()
        
        if self.standard_only_toggle.isChecked:
            std_new_max = std_scrollbar.maximum()
            if std_new_max > 0:
                std_scrollbar.setValue(int(std_ratio * std_new_max))
        else:
            main_new_max = main_scrollbar.maximum()
            if main_new_max > 0:
                main_scrollbar.setValue(int(main_ratio * main_new_max))

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
        self.rarity_filter.setCurrentIndex(0)
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
        if not is_loading:
            self.stack.setCurrentIndex(0)
            self.standard_only_toggle.setChecked(False)
            self.setEnabled(True)

        self.finished_loading.emit(not is_loading)

        self.deck_view.setEnabled(not is_loading)
        infobase_on = self.infobase_toggle.isChecked
        self.refresh_button.setEnabled(not is_loading and not infobase_on)
        self.export_button.setEnabled(not is_loading and not infobase_on)

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
            self.no_tokens_toggle.blockSignals(True)
            self.no_tokens_toggle.toggleState()
            self.no_tokens_toggle.blockSignals(False)
        
        self.pending_initial_filter = True
        if self.isVisible():
            QTimer.singleShot(50, self._apply_initial_filter)
        self.set_loading(False)
        print("LibraryView updated")

    def set_updated_std_library(self, cards: List[CardMetadata]):
        self.clear_std_grid()
        if not cards:
            print("Cannot update std library view: empty")
            self.set_loading(False)
            return

        cards = sorted(
            cards,
            key=lambda c: (
                c.manacost if c.manacost is not None else 10**9,
                c.name or "",
            ),
        )

        pos = 0
        for card in cards:
            if not card.card_image:
                print(f"Skipped std card [{card.id}]: no image")
                continue
            if not isinstance(card, StdMetadata):
                std_meta = StdMetadata()
                std_meta.__dict__ = dict(card.__dict__)
                card = std_meta
            card_widget = CardWidget(card, self)
            card_widget.card_clicked_event.connect(self.on_card_clicked)
            card_widget.edit_card_requested.connect(self.edit_card_requested)
            card_widget.delete_card_requested.connect(self.delete_card_requested)
            card_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
            self.std_gallery_grid.grid_layout.addWidget(card_widget, pos // 4, pos % 4)
            self.std_original_positions[card_widget] = (pos // 4, pos % 4)
            self.std_card_widgets.append(card_widget)
            pos += 1

        for row in range(self.std_gallery_grid.grid_layout.rowCount()):
            self.std_gallery_grid.grid_layout.setRowMinimumHeight(row, 130)

        if self.standard_only_toggle.isChecked:
            self._ensure_std_default_class()

        self.pending_initial_filter = True
        if self.isVisible():
            QTimer.singleShot(50, self._apply_initial_filter)
        self.set_loading(False)
        print("Loaded", len(self.std_card_widgets), "standard cards.")

    def clear_grid(self):
        while self.main_gallery_grid.grid_layout.count():
            child = self.main_gallery_grid.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.card_widgets.clear()
        self.original_positions.clear()

    def clear_std_grid(self):
        while self.std_gallery_grid.grid_layout.count():
            child = self.std_gallery_grid.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.std_card_widgets.clear()
        self.std_original_positions.clear()

    def on_export_clicked(self, metas: List[CardMetadata] = None, all_cached_cards: List[CardMetadata] = None):
        if not metas and not self.card_widgets:
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
        if all_cached_cards:
            metas_list = all_cached_cards
        else:
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
            main_window = self.window()
            NotificationWidget(main_window, "Библиотека выгружена.", "success")
        
        QApplication.instance().activeWindow()

    def on_card_clicked(self, metadata: CardMetadata):
        response = self.deck_view.add_item(metadata.id, metadata.name, metadata.manacost, metadata.istoken)
        if not response.ok:
            main_window = self.window()
            NotificationWidget(main_window, response.msg, "warning")
            return

        ### Sideboard is temporarily disabled
        # if metadata.tokens:
        #     token_card_ids = list(map(int, metadata.tokens.split(',')))
        #     for card_id in token_card_ids:
        #         token_meta = self.get_card_metadata_by_id(card_id, deck_fields_only=True)
        #         if not token_meta:
        #             continue
        #         self.deck_view.add_item(card_id, token_meta.name, token_meta.manacost, True)

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
        for card_widget in self.std_card_widgets:
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
            if card_widget.metadata.id == card_metadata.id and not isinstance(card_widget.metadata, StdMetadata):
                new_card = CardWidget(card_metadata, self)
                new_card.card_clicked_event.connect(self.on_card_clicked)
                new_card.edit_card_requested.connect(self.edit_card_requested)
                new_card.delete_card_requested.connect(self.delete_card_requested)
                x, y = self.original_positions[card_widget]
                self.original_positions.pop(card_widget)
                self.original_positions[new_card] = x, y

                new_x, new_y = x, y
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

        for i, card_widget in enumerate(self.std_card_widgets):
            if card_widget.metadata.id == card_metadata.id:
                if not isinstance(card_metadata, StdMetadata):
                    std_meta = StdMetadata()
                    std_meta.__dict__ = dict(card_metadata.__dict__)
                    card_metadata = std_meta
                new_card = CardWidget(card_metadata, self)
                new_card.card_clicked_event.connect(self.on_card_clicked)
                new_card.edit_card_requested.connect(self.edit_card_requested)
                new_card.delete_card_requested.connect(self.delete_card_requested)
                x, y = self.std_original_positions[card_widget]
                self.std_original_positions.pop(card_widget)
                self.std_original_positions[new_card] = x, y

                new_x, new_y = x, y
                if self.no_tokens_toggle.isChecked:
                    for j in range(self.std_gallery_grid.grid_layout.count()):
                        item = self.std_gallery_grid.grid_layout.itemAt(j)
                        if item.widget() == card_widget:
                            new_x, new_y, _, _ = self.std_gallery_grid.grid_layout.getItemPosition(j)

                self.std_gallery_grid.grid_layout.removeWidget(card_widget)
                self.std_gallery_grid.grid_layout.addWidget(new_card, new_x, new_y)

                self.std_card_widgets[i] = new_card
                card_widget.deleteLater()
                return

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
                                     tribe: str, rarity: str, std_only: bool, no_tokens: bool) -> int:
        self.reset_filter()

        if cardtype != "any": self.cardtype_filter.setCurrentIndex(CardType.get_value(cardtype)) 
        if classtype != "any": self.classtype_filter.setCurrentIndex(ClassType.get_value(classtype))
        if manacost != "any": self.manacost_filter.setCurrentIndex(int(manacost) + 1)
        if tribe != "any": self.name_filter.setText(tribe)
        if rarity != "any": self.rarity_filter.setCurrentIndex(Rarity.get_value(rarity))
        self.standard_only_toggle.setChecked(int(std_only))
        self.no_tokens_toggle.setChecked(int(no_tokens))
        
        chosen_id = self.roll()
        self.reset_filter()
        return chosen_id

    def showEvent(self, event):
        super().showEvent(event)
        if self.pending_initial_filter:
            self.pending_initial_filter = False
            QTimer.singleShot(50, self._apply_initial_filter)
    
    def resizeEvent(self, a0) -> None:
        return super().resizeEvent(a0)
