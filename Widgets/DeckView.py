import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit, \
    QPushButton, QComboBox
from PyQt5.QtGui import QColor, QFont
import random


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
        self.setHeaderLabels(["Quantity", "ID", "Name", "Price"])
        self.header().setSortIndicator(3, 0)

        self.parent_item1 = MyTreeWidgetItem(["", "Level 1", "", ""])
        self.addTopLevelItem(self.parent_item1)

        self.parent_item2 = MyTreeWidgetItem(["", "Level 2", "", ""])
        self.addTopLevelItem(self.parent_item2)

        self.bfont = self.font()
        self.bfont.setBold(1)

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

        self.itemDoubleClicked.connect(self.on_item_double_clicked)

    def add_item(self, level, id_value):
        existing_item: MyTreeWidgetItem = self.items_by_id.get(id_value)

        if existing_item and level == existing_item.parent().text(1):
            quantity = int(existing_item.text(0)) + 1
            existing_item.setText(0, str(quantity))
            existing_item.setSortData(3, existing_item.text(3))
        else:
            new_item = MyTreeWidgetItem(["1", str(id_value), "", str(self.get_random_price())])
            new_item.setSortData(3, new_item.text(3))
            new_item.setFont(3, self.bfont)
            new_item.setForeground(3, QColor("#4b00b3"))
            new_item.setBackground(3, QColor("#e6e6e6"))
            self.items_by_id[id_value] = new_item
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

    def get_price_by_id(self, id_value):
        # Возвращает случайное число от 1 до 10
        return str(self.get_random_price())

    def get_random_price(self):
        return random.randint(1, 10)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Product List")
        self.setGeometry(100, 100, 500, 400)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.tree_widget = MyTreeWidget()

        level_label = QLabel("Select Level:")
        self.level_combobox = QComboBox()
        self.level_combobox.addItems(["Level 1", "Level 2"])

        id_label = QLabel("ID:")
        self.id_input = QLineEdit()

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.add_item)

        export_button = QPushButton("Экспорт")
        export_button.clicked.connect(self.export_items)
        srt = QPushButton("srt")
        srt.clicked.connect(lambda: self.tree_widget.sortItems(3,0))

        layout.addWidget(level_label)
        layout.addWidget(self.level_combobox)
        layout.addWidget(self.tree_widget)
        layout.addWidget(id_label)
        layout.addWidget(self.id_input)
        layout.addWidget(add_button)
        layout.addWidget(export_button)
        layout.addWidget(srt)

        self.setLayout(layout)

    def add_item(self):
        level = self.level_combobox.currentText()
        id_value = self.id_input.text()

        self.tree_widget.add_item(level, id_value)

        #self.id_input.clear()

    def export_items(self):
        export_list = []
        for id_value, item in self.tree_widget.items_by_id.items():
            quantity = int(item.text(0))
            price = int(self.tree_widget.get_price_by_id(id_value))
            export_list.append((id_value, quantity, self.tree_widget.get_name_by_id(id_value), price))

        print("Exported items:")
        for item in export_list:
            print(item)

        return export_list

from PyQt5.QtGui import QColor, QFont
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = MainWindow()

    window.show()
    sys.exit(app.exec_())
