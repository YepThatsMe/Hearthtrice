from typing import List
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidgetItem, QListWidget, QLabel, QPushButton
from PyQt5.QtGui import QMovie

from Widgets.components.DataTypes import Deck

class DeckListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reset_output()
        self.set_up_ui()

    def set_up_ui(self):
        self.setWindowTitle("Выбор колоды")
        self.gen_layout = QVBoxLayout(self)
        self.loading_label = QLabel(self)
        self.loading_animation = QMovie(r"assets/loading_animation.gif")
        self.loading_label.setMovie(self.loading_animation)
        self.loading_animation.start()

        self.list_widget = QListWidget(self)

        self.select_btn = QPushButton("Выбрать", self)
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.select_deck)

        self.gen_layout.addWidget(self.loading_label)
        self.gen_layout.addWidget(self.list_widget)
        self.gen_layout.addWidget(self.select_btn)

    def reset_output(self):
        self.selected_row = -1
        self.selected_label = "Колода не выбрана"

    def populate_list(self, decks: List[Deck]):
        self.reset_output()
        self.set_loading(True)
        self.list_widget.clear()
        deck: Deck
        for deck in decks:
            label = f"ID: {deck.id}\t {deck.name}\t[{deck.owner}]"
            self.list_widget.addItem(label)
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)
            self.select_btn.setEnabled(True)
        self.set_loading(False)

    def set_loading(self, is_loading: bool):
        self.loading_label.setVisible(is_loading)
        self.list_widget.setVisible(not is_loading)

    def select_deck(self) -> int:
        self.selected_row = self.list_widget.currentRow()
        self.selected_label = self.list_widget.currentItem().text()
        self.accept()
