from PyQt5.QtWidgets import QMenu, QMessageBox, QDialog, QHBoxLayout, QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit, \
    QPushButton
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSettings, pyqtSignal, Qt
from typing import List

import os
from DataTypes import Deck, DeckCard, Response
from utils.XMLGenerator import XMLGenerator
from Widgets.components.DeckListDialog import DeckListDialog


class MyTreeWidgetItem(QTreeWidgetItem):    
    def __init__(self, *args):
        super(MyTreeWidgetItem, self).__init__(*args)
        self._sortData = {}

    def __lt__(self, other):
        if not isinstance(other, MyTreeWidgetItem):
            return super(MyTreeWidgetItem, self).__lt__(other)

        tree = self.treeWidget()
        if not tree:
            column = 0
        else:
            column = tree.sortColumn()

        return self.sortData(column) < other.sortData(column)

    def sortData(self, column):
        return self._sortData.get(column, self.text(column))

    def setSortData(self, column, data):
        self._sortData[column] = data

class MyTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
            
        self.header().setStyleSheet("QHeaderView::section {\
                                                        color: black;\
                                                        padding: 2px;\
                                                        height: 20px;\
                                                        border: 0px solid #567dbc;\
                                                        border-left:0px;\
                                                        border-right:0px;\
                                                        background: #D7D7D7;\
                                                    }")

        self.setColumnCount(4)
        self.setHeaderLabels(["Count", "ID", "Name", "Manacost"])
        self.header().setSortIndicator(3, 0)
        self.setColumnWidth(0, 65)
        self.setColumnWidth(1, 40)
        self.setColumnWidth(2, 160)
        self.setColumnWidth(3, 50)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeWidget.InternalMove)


        self.bfont = self.font()
        self.bfont.setBold(True)

        # level: item
        self.levels = {}

        # id: item
        self.items_by_id = {}

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.itemDoubleClicked.connect(self.on_item_double_clicked)

        self.clear()

    def clear(self):
        super().clear()

        self.parent_item1 = MyTreeWidgetItem(["", "", "Deck", ""])
        self.addTopLevelItem(self.parent_item1)

        self.parent_item2 = MyTreeWidgetItem(["", "", "Sideboard", ""])
        self.addTopLevelItem(self.parent_item2)

        self.parent_item3 = MyTreeWidgetItem(["", "", "Tokens", ""])
        self.addTopLevelItem(self.parent_item3)

        self.expandItem(self.parent_item1)
        self.expandItem(self.parent_item2)
        self.expandItem(self.parent_item3)

        for i in range(4):
            self.parent_item1.setBackground(i, QColor("#bfffbf"))
            self.parent_item2.setBackground(i, QColor("#bfffbf"))
            self.parent_item3.setBackground(i, QColor("#bfffbf"))
            self.parent_item1.setFont(i, self.bfont)
            self.parent_item2.setFont(i, self.bfont)
            self.parent_item3.setFont(i, self.bfont)
        
        
        # level: item
        self.levels = {self.parent_item1.text(2): self.parent_item1,
                       self.parent_item2.text(2): self.parent_item2,
                       self.parent_item3.text(2): self.parent_item3}

        # id: item
        self.items_by_id = {}


    def add_item(self, id: int, name: str, manacost: int, istoken: bool = 0, sideboard: bool = 0):
        level = "Deck"
        if istoken:
            level = "Tokens"
        elif sideboard:
            level = "Sideboard"

        existing_item: MyTreeWidgetItem = self.items_by_id.get(id)

        if existing_item and level == existing_item.parent().text(2):
            quantity = int(existing_item.text(0)) + 1
            existing_item.setText(0, str(quantity))
            existing_item.setSortData(3, existing_item.text(3))
        else:
            new_item = MyTreeWidgetItem(["1", str(id), str(name), str(manacost)])
            new_item.setSortData(3, new_item.text(3))
            new_item.setFont(0, self.bfont)
            new_item.setFont(2, self.bfont)
            new_item.setFont(3, self.bfont)
            new_item.setForeground(1, QColor("#e0e0e0"))
            new_item.setForeground(3, QColor("#4b00b3"))
            new_item.setBackground(3, QColor("#e6e6e6"))
            self.items_by_id[id] = new_item
            self.levels[level].addChild(new_item)

        self.sortItems(3, 0)

    def get_name_by_id(self, id_value):
        item = self.items_by_id.get(id_value)
        if item:
            return item.text(2)
        return ""

    def current_decktree_to_str(self) -> str:
        string_deck = ""
        for id_value, item in self.items_by_id.items():
            count = int(item.text(0))
            side = DeckCard.Side.MAINDECK
            if item.parent() == self.parent_item2:
                side = DeckCard.Side.SIDEBOARD
            elif item.parent() == self.parent_item3:
                side = DeckCard.Side.TOKENS
                
            string_deck+= f"{id_value},{count},{side};"
        return string_deck
    
    def current_decktree_to_rich_cardslist(self) -> List[DeckCard]:
        cards = []
        for id_value, item in self.items_by_id.items():
            card = DeckCard()
            card.id = id_value
            card.count = int(item.text(0))
            card.side = DeckCard.Side.MAINDECK
            if item.parent() == self.parent_item2:
                card.side = DeckCard.Side.SIDEBOARD
            elif item.parent() == self.parent_item3:
                card.side = DeckCard.Side.TOKENS
                
            card.name = item.text(2)
            card.manacost = int(item.text(3))
            cards.append(card)
        return cards

    def show_context_menu(self, position):
        item = self.itemAt(position)
        if item and item != self.parent_item1 and item != self.parent_item2 and item != self.parent_item3:
            menu = QMenu(self)

            increase_action = menu.addAction("+1")
            decrease_action = menu.addAction("-1")
            delete_action = menu.addAction("Удалить")

            action = menu.exec_(self.viewport().mapToGlobal(position))
            if action == increase_action:
                self.modify_count(item, 1)
            elif action == decrease_action:
                self.modify_count(item, -1)
            elif action == delete_action:
                self.delete_item(item)

    def modify_count(self, item, amount):
        current_count = int(item.text(0))
        new_count = current_count + amount
        if new_count <= 0:
            self.delete_item(item)
            for id, dict_item in self.items_by_id.items():
                if item == dict_item:
                    self.items_by_id.pop(id)
                    break
        else:
            item.setText(0, str(new_count))
        self.sortItems(3, 0)

    def delete_item(self, item):
        index = self.indexOfTopLevelItem(item)
        if index != -1:
            self.takeTopLevelItem(index)
        else:
            parent = item.parent()
            parent.takeChild(parent.indexOfChild(item))
        for id, dict_item in self.items_by_id.items():
            if item == dict_item:
                self.items_by_id.pop(id)
                break
        self.sortItems(3, 0)


    def on_item_double_clicked(self, item, column):
        if item in [self.parent_item1, self.parent_item2, self.parent_item3]:
            return
        if item.parent() == self.parent_item3:
            return
        
        current_parent = item.parent()
        new_parent = self.parent_item2
        if current_parent == self.parent_item2:
            new_parent = self.parent_item1
            
        index = current_parent.indexOfChild(item)
        current_parent.takeChild(index)
        new_parent.addChild(item)
        self.sortItems(3, 0)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            text = item.text(2)
            if text  == "Deck" or text == "Sideboard" or text == "Tokens":
                return
            super().startDrag(supportedActions)

    def dropEvent(self, event):
        target_item = self.itemAt(event.pos())
        if target_item:
            text = target_item.text(2)
            if text  == "Deck" or text == "Sideboard" or text == "Tokens":
                super().dropEvent(event)
                return
        event.ignore()  # Игнорируем сброс в неподходящий элемент



class DeckView(QWidget):
    get_decks_requested = pyqtSignal(str)
    create_new_deck_requested = pyqtSignal(str)
    update_deck_requested = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Deck Editor")
        self.deck_list_dialog = DeckListDialog(self)
        self.current_deck: Deck = None

        self.settings = QSettings("HearthTrice")
        self.login = self.settings.value("login")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        control_layout = QVBoxLayout()
        control_layout_inlay1 = QHBoxLayout()

        self.tree_widget = MyTreeWidget(self)

        self.new_deck_button = QPushButton("Новая колода", self)
        self.new_deck_button.clicked.connect(self.new_deck)

        self.load_deck_button = QPushButton("Загрузить колоду", self)
        self.load_deck_button.clicked.connect(lambda: self.get_decks_requested.emit(self.login))

        self.current_deck_label = QLabel("", self)
        self.current_deck_label.setStyleSheet("font-size: 10pt; font-weight: bold")

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.update_deck)

        export_button = QPushButton("Экспорт")
        export_button.clicked.connect(self.export_items)
        
        control_layout_inlay1.addWidget(self.new_deck_button)
        control_layout_inlay1.addWidget(self.load_deck_button)
        control_layout.addLayout(control_layout_inlay1)
    
        layout.addLayout(control_layout)
        layout.addWidget(self.current_deck_label)
        layout.addWidget(self.tree_widget)
        layout.addWidget(self.save_button)
        layout.addWidget(export_button)
        #layout.addWidget(graph)

    def add_item(self, id: int, name: str, manacost: int, istoken: bool = 0, sideboard: bool = 0) -> Response:
        if not self.current_deck:
            return Response(False, "Колода не выбрана")
     
        self.tree_widget.add_item(id, name, manacost, istoken, sideboard)

        return Response(True)

    def update_deck(self):
        if not self.current_deck:
            return QMessageBox.warning(self, "Ошибка", "Колода не выбрана")

        string_deck = self.tree_widget.current_decktree_to_str()
        if(QMessageBox.question(self, "Сохранение", f"Колода {self.current_deck.id}: '{self.current_deck.name.upper()}' будет перезаписана. Сохранить?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes):
            return
        if not string_deck:
            if(QMessageBox.warning(self, "Сохранение", f"Обновленная колода не имеет карт. Сохранить пустую колоду?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes):
                return
        self.update_deck_requested.emit((self.current_deck.id, string_deck))
        #current_deck.cards update
        return

    def new_deck(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Создание колоды")

        label = QLabel("Название:")
        line_edit = QLineEdit(dialog)
        line_edit.setMaxLength(35)

        ok_button = QPushButton("ОК", dialog)
        ok_button.clicked.connect(dialog.accept)

        layout = QVBoxLayout(dialog)
        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)

        result = dialog.exec_()

        if result == QDialog.Accepted:
            deck_name = line_edit.text()
            self.create_new_deck_requested.emit(deck_name)
    
    def new_virtual_deck(self):
        virtual_deck = Deck()
        virtual_deck.id = -2
        virtual_deck.name = "Arena"
        virtual_deck.owner = ""
        self.current_deck = virtual_deck

    def on_new_deck_data_received(self, new_deck_data: tuple):
        deck_id, deck_name, owner = new_deck_data
        new_deck = Deck()
        new_deck.id = deck_id
        new_deck.name = deck_name
        new_deck.owner = owner

        self.current_deck = new_deck
        self.current_deck_label.setText(f"ID: {deck_id}\t {deck_name}\t[{owner}]")

    def set_updated_decks(self, decks: List[Deck]):
        self.deck_list_dialog.populate_list(decks)
        self.deck_list_dialog.exec()
        selected_deck_id = self.deck_list_dialog.selected_row
        current_deck_label = self.deck_list_dialog.selected_label
        if selected_deck_id == -1:
            return
        
        self.current_deck = decks[selected_deck_id]
        self.current_deck_label.setText(current_deck_label)
        self.clear()
        for card in self.current_deck.cards:
            for _ in range(card.count):
                sideboard = True if card.side == DeckCard.Side.SIDEBOARD else False
                self.add_item(card.id, card.name, card.manacost, card.istoken, sideboard)
    
    def get_current_rich_deck(self) -> Deck:
        deck = Deck()
        deck.id = self.current_deck.id
        deck.name = self.current_deck.name
        deck.owner = self.current_deck.owner
        deck.cards = self.tree_widget.current_decktree_to_rich_cardslist()
        return deck
    
    def export_items(self):
        if not self.current_deck:
            return QMessageBox.warning(self, "Ошибка", "Колода не выбрана")
        deck = self.get_current_rich_deck()

        game_dir  = self.settings.value("path")
        if not game_dir:
            game_dir = os.getcwd()

        decks_dir = os.path.join(game_dir, "data", "decks")
        if not os.path.isdir(decks_dir):
            decks_dir = os.path.join(os.getenv('LOCALAPPDATA'), "Cockatrice", "Cockatrice", "decks")
        os.makedirs(decks_dir, exist_ok=True)

        full_deck_path = os.path.join(decks_dir, deck.name + ".cod")
        os.startfile(decks_dir) # Windows only
        XMLGenerator.generate_xml_deck(full_deck_path, deck)

        QMessageBox.information(self, "Готово", f"Колода {deck.name.upper()} выгружена.")
    
    def clear(self):
        self.tree_widget.clear()