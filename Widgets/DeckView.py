from modulefinder import ReplacePackage
import sys
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit, \
    QPushButton, QComboBox
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSettings, pyqtSignal
from typing import List

from Widgets.components.DataTypes import Deck, DeckCard, Response
from Widgets.components.DeckListDialog import DeckListDialog


class MyTreeWidgetItem(QTreeWidgetItem):
    def __lt__(self, other):
        if not isinstance(other, MyTreeWidgetItem):
            return super(MyTreeWidgetItem, self).__lt__(other)

        tree = self.treeWidget()
        if not tree:
            column = 0
        else:
            column = tree.sortColumn()

        return self.sortData(column) < other.sortData(column)

    def __init__(self, *args):
        super(MyTreeWidgetItem, self).__init__(*args)
        self._sortData = {}

    def sortData(self, column):
        return self._sortData.get(column, self.text(column))

    def setSortData(self, column, data):
        self._sortData[column] = data


class MyTreeWidget(QTreeWidget):
    def __init__(self):
        super().__init__()
            
        self.header().setStyleSheet("QHeaderView::section {\
                                                        color: black;\
                                                        padding: 2px;\
                                                        height: 20px;\
                                                        border: 0px solid #567dbc;\
                                                        border-left:0px;\
                                                        border-right:0px;\
                                                        background: #D7D7D7;\
                                                    }");

        self.setColumnCount(4)
        self.setHeaderLabels(["Count", "ID", "Name", "Manacost"])
        self.header().setSortIndicator(3, 0)
        
        width = self.width()

        self.setColumnWidth(0, width/12)
        self.setColumnWidth(1, width/12)
        self.setColumnWidth(2, width/5)
        self.setColumnWidth(3, width/12)

        self.bfont = self.font()
        self.bfont.setBold(1)

        # level: item
        self.levels = {}

        # id: item
        self.items_by_id = {}

        self.itemDoubleClicked.connect(self.on_item_double_clicked)

        self.clear()

    def clear(self):
        super().clear()

        self.parent_item1 = MyTreeWidgetItem(["", "Deck", "", ""])
        self.addTopLevelItem(self.parent_item1)

        self.parent_item2 = MyTreeWidgetItem(["", "Sideboard", "", ""])
        self.addTopLevelItem(self.parent_item2)

        for i in range(4):
            self.parent_item1.setBackground(i, QColor("#bfffbf"))
            self.parent_item2.setBackground(i, QColor("#bfffbf"))
            self.parent_item1.setFont(i, self.bfont)
            self.parent_item2.setFont(i, self.bfont)
        
        
        # level: item
        self.levels = {self.parent_item1.text(1): self.parent_item1,
                       self.parent_item2.text(1): self.parent_item2}

        # id: item
        self.items_by_id = {}


    def add_item(self, id: int, name: str, manacost: int):
        level = "Deck"

        existing_item: MyTreeWidgetItem = self.items_by_id.get(id)

        if existing_item and level == existing_item.parent().text(1):
            quantity = int(existing_item.text(0)) + 1
            existing_item.setText(0, str(quantity))
            existing_item.setSortData(3, existing_item.text(3))
        else:
            new_item = MyTreeWidgetItem(["1", str(id), str(name), str(manacost)])
            new_item.setSortData(3, new_item.text(3))
            new_item.setFont(0, self.bfont)
            new_item.setFont(2, self.bfont)
            new_item.setFont(3, self.bfont)
            new_item.setForeground(1, QColor("#f9f9f9"))
            new_item.setForeground(3, QColor("#4b00b3"))
            new_item.setBackground(3, QColor("#e6e6e6"))
            self.items_by_id[id] = new_item
            self.levels[level].addChild(new_item)

        self.expandItem(self.levels[level])
        self.sortItems(3, 0)

    def on_item_double_clicked(self, item, column):
        if item is not None:
            print(f"Double clicked on item: {item.text(column)}")

    def get_name_by_id(self, id_value):
        item = self.items_by_id.get(id_value)
        if item:
            return item.text(2)
        return ""


class DeckView(QWidget):
    get_decks_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Product List")
        self.deck_list_dialog = DeckListDialog(self)
        self.current_deck: Deck = None

        self.settings = QSettings("HearthTrice")
        self.login = self.settings.value("login")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        control_layout = QVBoxLayout()
        control_layout_inlay1 = QHBoxLayout()

        self.tree_widget = MyTreeWidget()

        new_deck_button = QPushButton("Новая колода", self)
        new_deck_button.clicked.connect(self.new_deck)

        load_deck_button = QPushButton("Загрузить колоду", self)
        load_deck_button.clicked.connect(lambda: self.get_decks_requested.emit(self.login))

        self.current_deck_label = QLabel("", self)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_deck)

        export_button = QPushButton("Экспорт")
        export_button.clicked.connect(self.export_items)
        
        control_layout_inlay1.addWidget(new_deck_button)
        control_layout_inlay1.addWidget(load_deck_button)
        control_layout.addLayout(control_layout_inlay1)
    
        layout.addLayout(control_layout)
        layout.addWidget(self.current_deck_label)
        layout.addWidget(self.tree_widget)
        layout.addWidget(save_button)
        layout.addWidget(export_button)
        #layout.addWidget(graph)

    def add_item(self, id: int, name: str, manacost: int) -> Response:
        if not self.current_deck:
            return Response(False, "Колода не выбрана")
     
        self.tree_widget.add_item(id, name, manacost)

        return Response(True)

    def save_deck(self):
        pass

    def new_deck(self):
        pass

    def load_deck(self):
        pass

    def set_updated_decks(self, decks: List[Deck]):
        self.deck_list_dialog.populate_list(decks)
        self.deck_list_dialog.exec()
        deck_id = self.deck_list_dialog.selected_row
        current_deck_label = self.deck_list_dialog.selected_label
        if deck_id == -1:
            return
        
        self.current_deck = decks[deck_id]
        self.current_deck_label.setText(current_deck_label)
        self.tree_widget.clear()
        for card in self.current_deck.cards:
            self.add_item(card.id, card.name, card.manacost)

    def export_items(self):
        export_list = []
        for id_value, item in self.tree_widget.items_by_id.items():
            quantity = int(item.text(0))
            #price = int(self.tree_widget.get_price_by_id(id_value))
            #export_list.append((id_value, quantity, self.tree_widget.get_name_by_id(id_value), price))

        print("Exported items:")
        for item in export_list:
            print(item)

        return export_list

from PyQt5.QtGui import QColor, QFont
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = DeckView()

    window.show()
    sys.exit(app.exec_())
