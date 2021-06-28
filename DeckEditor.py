from PyQt5.QtWidgets import (QMainWindow, QWidget, QDesktopWidget, QApplication, QAction,
                             QMessageBox, QFileDialog, QStackedWidget, QComboBox, QHBoxLayout,
                             QVBoxLayout, QLabel, QLineEdit, QCompleter, QGridLayout,
                             QTableWidget, QProgressBar, QTableWidgetItem)

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
import xml.etree.ElementTree as ET
import sys
import os
import pickle


from DeckEditor_UI import UI_MainWindow


class DeckEditor(QMainWindow, UI_MainWindow):
    def __init__(self):

        super().__init__()
        self.hero = 'Маг'
        self.setupUI(self)  #

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def hero_(self):
        self.hero = self.hero_list.currentText()

    def open(self):
        self.library = QFileDialog.getOpenFileName(self, "Open file")[0]

        if self.library == '':
            return

        self.path = self.library[:self.library.rfind('/')]
        os.chdir(self.path)

        self.relist()

        try:
            os.chdir('../pics/downloadedPics/')
            self.pics_main = os.getcwd() + '/HT'
            self.pics_token = os.getcwd() + '/TK'
        except:
            QMessageBox.about(self, "Ошибка", "Не найдена папка с изображением карт")

    def func_read(path):
        hs = ET.parse(path)
        enter = hs.findall("cards/card[type = 'Minion']") + hs.findall("cards/card[type = 'Spell']") + hs.findall(
            "cards/card[type = 'Weapon']") + hs.findall("cards/card[type = 'Hero']")

        try:
            esc = {i[0].text + ".png": "".join(i[2].attrib.values()) for i in enter}
        except:
            esc = {i[0].text + ".png": "" for i in enter}
        # count = int(input('Введите число карт:\n'))
        return esc

    def relist(self):

        try:
            print(self.library)
            self.library is not None
        except:
            self.open()

        print(self.library)
        try:
            self.library is not None
        except:
            return

        self.list_cards.clear()
        self.list_cards.setRowCount(0)
        self.row = 0

        if self.set.currentText() == 'HT':

            self.esc = self.func_read(self.library)
            self.cards = list(map(lambda x: x[:x.rfind('.png')], list(self.esc.keys())))

            for i in self.cards:
                self.row += 1
                self.list_cards.setRowCount(self.row + 1)
                self.list_cards.setItem(self.row - 1, 0, QTableWidgetItem(i))
                self.list_cards.setItem(self.row - 1, 1, QTableWidgetItem('1'))
                self.list_cards.setItem(self.row - 1, 2, QTableWidgetItem('1'))
                self.list_cards.setItem(self.row - 1, 3, QTableWidgetItem('1'))
                self.list_cards.setItem(self.row - 1, 4, QTableWidgetItem('1'))
            self.list_cards.setRowCount(self.row - 1)

            self.completer = QCompleter(self.cards)
            self.name.setCompleter(self.completer)



        elif self.set.currentText() == 'TK':

            self.esc_TK = self.func_read(self.library[:self.library.rfind('/')] + '/TK.xml')
            self.TK = list(map(lambda x: x[:x.rfind('.png')], list(self.esc_TK.keys())))

            for i in self.TK:
                self.row += 1
                self.list_cards.setRowCount(self.row + 1)
                self.list_cards.setItem(self.row - 1, 0, QTableWidgetItem(i))
                self.list_cards.setItem(self.row - 1, 1, QTableWidgetItem('1'))
                self.list_cards.setItem(self.row - 1, 2, QTableWidgetItem('1'))
                self.list_cards.setItem(self.row - 1, 3, QTableWidgetItem('1'))
                self.list_cards.setItem(self.row - 1, 4, QTableWidgetItem('1'))
            self.list_cards.setRowCount(self.row - 1)

            self.completer = QCompleter(self.TK)
            self.name.setCompleter(self.completer)

        elif self.set.currentText() == 'Standart':

            self.esc_std = self.func_read(self.library[:self.library.rfind('/')] + '/StandardCards.xml')
            self.std = list(map(lambda x: x[:x.rfind('.png')], list(self.esc_std.keys())))

            for i in self.std:
                self.row += 1
                self.list_cards.setRowCount(self.row + 1)
                self.list_cards.setItem(self.row - 1, 0, QTableWidgetItem(i))
                self.list_cards.setItem(self.row - 1, 1, QTableWidgetItem('1'))
                self.list_cards.setItem(self.row - 1, 2, QTableWidgetItem('1'))
                self.list_cards.setItem(self.row - 1, 3, QTableWidgetItem('1'))
                self.list_cards.setItem(self.row - 1, 4, QTableWidgetItem('1'))
            self.list_cards.setRowCount(self.row - 1)

            self.completer = QCompleter(self.std)
            self.name.setCompleter(self.completer)

        else:
            QMessageBox.about(self, "Ошибка", "Не удалось подгрузить карты")


        self.list_cards.setHorizontalHeaderLabels(["Имя", "Тип", "Класс", "Редкость", "Стоимость"])

    def openDeck(self):
        self.deck = QFileDialog.getOpenFileName(self, "Open file")[0]
        print(self.deck)
        if self.deck == '':
            return

    def closeEvent(self, event):

        reply = QMessageBox.question(self, "Message", "Вы уверены что хотите выйти?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = DeckEditor()
    window.show()
    sys.exit(app.exec_())
