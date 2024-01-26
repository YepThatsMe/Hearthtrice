from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QFrame, QItemDelegate, QLineEdit
from PyQt5.QtGui import QIntValidator

class OnlyNumbersDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super(OnlyNumbersDelegate, self).createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            editor.setValidator(QIntValidator())
        return editor

class TokensTable(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.table = QTableWidget(1, 1)
        self.table.setHorizontalHeaderLabels(["ID"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setItem(0, 0, QTableWidgetItem(""))
        self.table.itemChanged.connect(self.item_changed)

        self.table.setItemDelegate(OnlyNumbersDelegate())

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

    def item_changed(self, item):
        row = item.row()
        col = item.column()

        if row == self.table.rowCount() - 1 and item.text():
            self.table.insertRow(self.table.rowCount())
        elif not item.text():
            self.table.removeRow(row)
            if self.table.rowCount() == 0:
                self.table.insertRow(0)
                self.table.setItem(0, 0, QTableWidgetItem(""))

    def get_tokens_string(self) -> str:
        items = []
        for row in range(self.table.rowCount() - 1):  # последняя строка всегда пустая
            item = self.table.item(row, 0)
            if item and item.text():
                items.append(item.text())
        return ','.join(items)

    def populate_table(self, tokens_string: str):
        self.table.itemChanged.disconnect(self.item_changed)
        self.table.clearContents()
        self.table.setRowCount(0)
        for number in tokens_string.split(','):
            trimmed_number = number.strip()
            if trimmed_number.isdigit():
                row_count = self.table.rowCount()
                self.table.insertRow(row_count)
                self.table.setItem(row_count, 0, QTableWidgetItem(trimmed_number))
        self.table.insertRow(self.table.rowCount())
        self.table.itemChanged.connect(self.item_changed)