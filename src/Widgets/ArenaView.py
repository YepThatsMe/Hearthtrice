from math import floor
import os
import random
from typing import List
import json

from PyQt5.QtWidgets import QFrame, QGridLayout, QLayout, QSpacerItem, QProgressBar, QSlider, QLineEdit, QComboBox, QCheckBox, QMessageBox, QDialog, QVBoxLayout, QLabel, QStackedWidget, QFileDialog, QWidget, QScrollArea, QSizePolicy, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt, QDir, QByteArray, QFile, QTextStream, QSize, QSettings, QIODevice
from PyQt5.QtGui import QMovie, QPixmap, QIcon, QImage
from Widgets import LibraryView
from Widgets.DeckView import DeckView
from Widgets.components.ToggleButton import ToggleButton
from Widgets.components.ScrollableGrid import ScrollableGrid

from utils.BytesEncoder import bytes_to_pixmap
from Widgets.components.CardWidget import CardWidget
from Widgets.components.NotificationWidget import NotificationWidget
from DataTypes import CardMetadata, ClassType, Deck, Rarity, Response, StdMetadata
from utils.XMLGenerator import XMLGenerator

DEFAULT_LEGENDARY_COUNT = 0.3
DEFAULT_CUSTOM_MORPH_CHANCE = 33
DEFAULT_CUSTOM_MORPH_CHANCE_LEGENDARY = 80

class ClassButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, icon_id: int,  parent=None):
        super(ClassButton, self).__init__(parent)

        self.id = icon_id

        self.setFixedSize(128, 128)

        self.button = QPushButton(self)
        self.button.setFixedSize(128,128)
        
        pixmap = QPixmap(rf":icons/classicons/icon_{self.id}.png")
        pixmap = pixmap.scaled(128, 128)
        self.button.setIcon(QIcon(pixmap))
        self.button.setIconSize(pixmap.size())
        self.button.clicked.connect(self.clicked)


class ArenaView(QFrame):
    
    def __init__(self, library: LibraryView, parent=None):
        super().__init__(parent)

        self.library_view = library        
        self.deck_view = DeckView()
        self.deck_view.new_deck_button.hide()
        self.deck_view.load_deck_button.hide()
        self.deck_view.save_button.hide()
        self.deck_view.hide_deck_action_buttons = True

        self.max_cards = 30
        self.round = 0
        self.chosen_classtype = None
        self.filtered_library = []
        
        self.set_up_ui()
        self.set_up_connections()

    def set_up_connections(self):
        self.library_view.finished_loading.connect(lambda b: self.setEnabled(b))

    def set_up_ui(self):
        self.setEnabled(False)
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.gen_layout = QHBoxLayout(self)
        self.sub_gen_layout = QVBoxLayout()
        self.sub_gen_layout_2 = QVBoxLayout()

        self.stack = QStackedWidget(self)
        
        # Class selection Widget
        self.class_select_widget = QFrame()
        self.class_select_lo = QVBoxLayout()
        self.class_select_grid_lo = QGridLayout()

        self.class_select_control_gen = QVBoxLayout()
        self.class_select_control_1 = QHBoxLayout()
        self.class_select_control_1.setSizeConstraint(QLayout.SetMinimumSize)
        self.class_select_control_2 = QHBoxLayout()
        self.class_select_control_2.setSizeConstraint(QLayout.SetMinimumSize)
        self.class_select_control_3 = QHBoxLayout()
        self.class_select_control_3.setSizeConstraint(QLayout.SetMinimumSize)
        self.class_select_control_4 = QHBoxLayout()
        self.class_select_control_4.setSizeConstraint(QLayout.SetMinimumSize)

        self.card_count_label = QLabel("Количество карт: ")
        self.card_count_label_int = QLabel(str(self.max_cards))
        self.card_count_slider = QSlider(self)
        self.card_count_slider.setOrientation(Qt.Horizontal)
        self.card_count_slider.setTickPosition(QSlider.TicksAbove)
        self.card_count_slider.setRange(10, 60)
        self.card_count_slider.setSingleStep(1)
        self.card_count_slider.setValue(self.max_cards)
        self.card_count_slider.setMaximumWidth(200)
        self.card_count_slider.valueChanged.connect(lambda x: self.card_count_label_int.setText(str(x)))
        self.card_count_slider.valueChanged.connect(lambda x: self.update_max_cards(x))
        self.card_count_slider.valueChanged.connect(lambda x: self.legendary_count_slider.setRange(0, x))

        self.legendary_count_label = QLabel("Количество легендарных:")
        self.legendary_count_label_int = QLabel("[Нормально]")
        self.legendary_count_slider = QSlider(self)
        self.legendary_count_slider.setOrientation(Qt.Horizontal)
        self.legendary_count_slider.setTickPosition(QSlider.TicksAbove)
        self.legendary_count_slider.setRange(0, self.max_cards)
        self.legendary_count_slider.setSingleStep(1)
        self.legendary_count_slider.setValue(1)
        self.legendary_count_slider.setMaximumWidth(200)
        self.legendary_count_slider.setVisible(False)
        self.legendary_count_slider.valueChanged.connect(lambda x: self.legendary_count_label_int.setText(str(x)))
        self.legendary_count_custom_checkbox = QCheckBox(self)
        self.legendary_count_custom_checkbox.clicked.connect(
            lambda: self.legendary_count_slider.setVisible(self.legendary_count_custom_checkbox.isChecked())
        )
        self.legendary_count_custom_checkbox.clicked.connect(
            lambda: self.legendary_count_label_int.setText(str(self.legendary_count_slider.value())) if self.legendary_count_custom_checkbox.isChecked() else self.legendary_count_label_int.setText("[Нормально]")
        )

        self.custom_morph_chance_label = QLabel("Шанс нелегендарной быть кастомной:")
        self.custom_morph_chance_label_int = QLabel("[Нормально]")
        self.custom_morph_chance_slider = QSlider(self)
        self.custom_morph_chance_slider.setOrientation(Qt.Horizontal)
        self.custom_morph_chance_slider.setTickPosition(QSlider.TicksAbove)
        self.custom_morph_chance_slider.setRange(0, 100)
        self.custom_morph_chance_slider.setSingleStep(1)
        self.custom_morph_chance_slider.setValue(1)
        self.custom_morph_chance_slider.setMaximumWidth(200)
        self.custom_morph_chance_slider.setVisible(False)
        self.custom_morph_chance_slider.valueChanged.connect(lambda x: self.custom_morph_chance_label_int.setText(str(x)))
        self.custom_morph_chance_custom_checkbox = QCheckBox(self)
        self.custom_morph_chance_custom_checkbox.clicked.connect(
            lambda: self.custom_morph_chance_slider.setVisible(self.custom_morph_chance_custom_checkbox.isChecked())
        )
        self.custom_morph_chance_custom_checkbox.clicked.connect(
            lambda: self.custom_morph_chance_label_int.setText(str(self.custom_morph_chance_slider.value())) if self.custom_morph_chance_custom_checkbox.isChecked() else self.custom_morph_chance_label_int.setText("[Нормально]")
        )

        self.custom_morph_chance_legendary_label = QLabel("Шанс легендарной быть кастомной:")
        self.custom_morph_chance_legendary_label_int = QLabel("[Нормально]")
        self.custom_morph_chance_legendary_slider = QSlider(self)
        self.custom_morph_chance_legendary_slider.setOrientation(Qt.Horizontal)
        self.custom_morph_chance_legendary_slider.setTickPosition(QSlider.TicksAbove)
        self.custom_morph_chance_legendary_slider.setRange(0, 100)
        self.custom_morph_chance_legendary_slider.setSingleStep(1)
        self.custom_morph_chance_legendary_slider.setValue(1)
        self.custom_morph_chance_legendary_slider.setMaximumWidth(200)
        self.custom_morph_chance_legendary_slider.setVisible(False)
        self.custom_morph_chance_legendary_slider.valueChanged.connect(lambda x: self.custom_morph_chance_legendary_label_int.setText(str(x)))
        self.custom_morph_chance_legendary_custom_checkbox = QCheckBox(self)
        self.custom_morph_chance_legendary_custom_checkbox.clicked.connect(
            lambda: self.custom_morph_chance_legendary_slider.setVisible(self.custom_morph_chance_legendary_custom_checkbox.isChecked())
        )
        self.custom_morph_chance_legendary_custom_checkbox.clicked.connect(
            lambda: self.custom_morph_chance_legendary_label_int.setText(str(self.custom_morph_chance_legendary_slider.value())) if self.custom_morph_chance_legendary_custom_checkbox.isChecked() else self.custom_morph_chance_legendary_label_int.setText("[Нормально]")
        )

        self.launch_button = QPushButton("Запуск Cockatrice")
        self.launch_button.setStyleSheet('QPushButton{ background-color: #bfffbf; font-weight: bold; }')
        self.launch_button.clicked.connect(self.library_view.launch_cockatrice)

        self.class_select_control_1.addWidget(self.card_count_label)
        self.class_select_control_1.addWidget(self.card_count_label_int)
        self.class_select_control_1.addWidget(self.card_count_slider)
        self.class_select_control_1.addStretch()

        self.class_select_control_2.addWidget(self.legendary_count_custom_checkbox)
        self.class_select_control_2.addWidget(self.legendary_count_label)
        self.class_select_control_2.addWidget(self.legendary_count_label_int)
        self.class_select_control_2.addWidget(self.legendary_count_slider)
        self.class_select_control_2.addStretch()

        self.class_select_control_3.addWidget(self.custom_morph_chance_custom_checkbox)
        self.class_select_control_3.addWidget(self.custom_morph_chance_label)
        self.class_select_control_3.addWidget(self.custom_morph_chance_label_int)
        self.class_select_control_3.addWidget(self.custom_morph_chance_slider)
        self.class_select_control_3.addStretch()

        self.class_select_control_4.addWidget(self.custom_morph_chance_legendary_custom_checkbox)
        self.class_select_control_4.addWidget(self.custom_morph_chance_legendary_label)
        self.class_select_control_4.addWidget(self.custom_morph_chance_legendary_label_int)
        self.class_select_control_4.addWidget(self.custom_morph_chance_legendary_slider)
        self.class_select_control_4.addStretch()

        self.class_select_control_gen.addLayout(self.class_select_control_2)
        self.class_select_control_gen.addLayout(self.class_select_control_4)
        self.class_select_control_gen.addLayout(self.class_select_control_3)

        self.class_select_control_gen_frame = QFrame()
        self.class_select_control_gen_frame.setLayout(self.class_select_control_gen)
        self.class_select_control_gen_frame.setVisible(False)

        self.advanced_settings_btn = ToggleButton("Дополнительные настройки", self)
        self.advanced_settings_btn.setMaximumWidth(200)
        self.advanced_settings_btn.toggled.connect(lambda b: self.class_select_control_gen_frame.setVisible(b))
        
        self.class_select_lo.addLayout(self.class_select_grid_lo)
        self.class_select_lo.addLayout(self.class_select_control_1)
        self.class_select_lo.addWidget(self.advanced_settings_btn)
        self.class_select_lo.addWidget(self.class_select_control_gen_frame)

        self.class_select_widget.setLayout(self.class_select_lo)

        # Arena Widget
        self.card_select_widget = QFrame()
        self.select_gen_lo = QVBoxLayout()
        self.card_select_widget.setLayout(self.select_gen_lo)

        self.stack.addWidget(self.class_select_widget)
        self.stack.addWidget(self.card_select_widget) 

        ###

        # Arena View
        self.control_layout = QHBoxLayout()
        self.control_layout2 = QHBoxLayout()
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)
        self.progress_bar = QProgressBar()
        self.progress_bar.setOrientation(Qt.Horizontal)
        self.progress_bar.setRange(1, self.max_cards)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v")
        self.control_layout2.addWidget(self.progress_bar)
        self.class_pic = QLabel()
        self.control_layout.addWidget(self.class_pic)
        self.control_layout.addStretch()
        self.control_layout.addWidget(self.reset_button)

        self.select_lo = QHBoxLayout()

        self.select_gen_lo.addLayout(self.control_layout, stretch=1)
        self.select_gen_lo.addLayout(self.select_lo,stretch=5)
        self.select_gen_lo.addSpacerItem(QSpacerItem(100, 200))
        self.select_gen_lo.addLayout(self.control_layout2,stretch=1)

        #############################################
        self.stack.setCurrentWidget(self.class_select_widget)

        pos = 0
        for i in range(1,10):
            btn = ClassButton(i)
            btn.clicked.connect(self.start)
            self.class_select_grid_lo.addWidget(btn, pos//3, pos%3)
            pos+=1

        self.sub_gen_layout.addWidget(self.stack)
        self.sub_gen_layout_2.addWidget(self.deck_view)
        self.sub_gen_layout_2.addWidget(self.launch_button)

        self.gen_layout.addLayout(self.sub_gen_layout, stretch=5)
        self.gen_layout.addLayout(self.sub_gen_layout_2, stretch=2)
        self.setLayout(self.gen_layout)

    def start(self):
        self.stack.setCurrentIndex(1)

        self.deck_view.new_virtual_deck()
        self.chosen_classtype = self.sender().id + 1

        pixmap = QPixmap(rf":icons/classicons/icon_{self.sender().id}.png")
        self.class_pic.setPixmap(pixmap)

        self.legendary_count = floor(DEFAULT_LEGENDARY_COUNT * self.max_cards) if \
            not self.legendary_count_custom_checkbox.isChecked() else \
            self.legendary_count_slider.value()

        self.custom_morph_chance = DEFAULT_CUSTOM_MORPH_CHANCE if \
            not self.custom_morph_chance_custom_checkbox.isChecked() else \
            self.custom_morph_chance_slider.value()
        
        self.custom_morph_chance_legendary = DEFAULT_CUSTOM_MORPH_CHANCE_LEGENDARY if \
            not self.custom_morph_chance_legendary_custom_checkbox.isChecked() else \
            self.custom_morph_chance_legendary_slider.value()
        
        self.legendary_map = [0] * self.max_cards
        for i in random.sample(range(self.max_cards), self.legendary_count):
            self.legendary_map[i] = 1

        for card_widget in self.library_view.card_widgets + self.library_view.std_card_widgets:
            if card_widget.metadata.istoken:
                continue
            
            if (type(card_widget.metadata) == StdMetadata):
                if card_widget.metadata.classtype == self.chosen_classtype \
                   or card_widget.metadata.classtype == ClassType.NEUTRAL:
                    self.filtered_library.append(card_widget)
                else:
                    continue
            else:
                self.filtered_library.append(card_widget)

        self.populate_arena()
    
    def populate_arena(self):
        self.select_lo.addSpacerItem(QSpacerItem(80,1))

        chosen_cards = set()
        for _ in range(3):
            is_legendary = self.legendary_map[self.round]
            is_custom = False
            if is_legendary:
                is_custom = random.randint(0,100) < self.custom_morph_chance_legendary
            else:
                is_custom = random.randint(0,100) < self.custom_morph_chance

            random_card = self.choose_random_card(is_legendary, is_custom)
            retries = 0
            while random_card in chosen_cards and retries < 10:
                random_card = self.choose_random_card(is_legendary, is_custom)
                retries += 1
                print("Retry...", retries)
            chosen_cards.add(random_card)
    
            dup_card = CardWidget(random_card.metadata, self)
            dup_card.card_clicked_event.connect(self.on_card_clicked)
            dup_card.context_menu.removeAction(dup_card.delete_action)
            
            self.select_lo.addWidget(dup_card)
        
    def choose_random_card(self, is_legendary: bool, is_custom: bool) -> CardWidget:
        second_filtered_library = [
            card_widget for card_widget in self.filtered_library
            if (card_widget.metadata.rarity == Rarity.LEGENDARY) == is_legendary
            and (type(card_widget.metadata)!= StdMetadata) == is_custom
        ]
        return random.choice(second_filtered_library or self.filtered_library)

    def clear_grid(self):
        while self.select_lo.count():
            child = self.select_lo.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

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
        #         token_meta = self.library_view.get_card_metadata_by_id(card_id, deck_fields_only=True)
        #         if not token_meta:
        #             continue
        #         self.deck_view.add_item(card_id, token_meta.name, token_meta.manacost, True)

        self.round += 1
        self.progress_bar.setValue(self.round)

        self.clear_grid()
        if self.round < self.max_cards:
            self.populate_arena()

    def update_max_cards(self, value: int):
        self.max_cards = value
        self.progress_bar.setRange(0, value)

    def reset(self):
        self.deck_view.clear()
        self.deck_view.current_deck = None
        self.progress_bar.setValue(0)
        self.clear_grid()
        self.chosen_classtype = None
        self.filtered_library.clear()
        self.round = 0

        self.stack.setCurrentIndex(0)