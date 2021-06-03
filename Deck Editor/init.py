from PyQt5.QtWidgets import (QMainWindow, QWidget, QDesktopWidget, QApplication, QAction,
                             QMessageBox, QFileDialog, QListWidget, QComboBox, QHBoxLayout,
                             QVBoxLayout)

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
import sys
import os

import func


class Editor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.iconPath = os.getcwd() + '/icons'
        print(self.iconPath)
        self.setupUI()

        self.hero = 'Маг'

    def setupUI(self):

        # Настроки окна
        self.setGeometry(0, 0, 1080, 720)
        self.setWindowTitle("Deck Editor")
        self.setWindowIcon(QIcon("icons/icon.jpg"))
        self.center()  # Центрирование окна
        self.statusBar().showMessage("Ready")

        self.centralwidget = QWidget(self)

        # ToolBar
        openFile = QAction(QIcon("icons/file.jpg"), "&Open library...", self)  # Открытие существующей
        openFile.setShortcut("Alt+Q")  # библиотеки карт
        openFile.setStatusTip("Open card's library")
        openFile.triggered.connect(self.open)

        login = QAction(QIcon("icons/naruto_min.png"), "&Login...", self)  # Открытие Hearthcards
        login.setShortcut("Alt+Shift+L")
        login.setStatusTip("Login to HearthCards...")
        login.triggered.connect(func.login)

        choose_deck = QAction(QIcon("icons/deck.jpg"), "&Open deck...", self)  # Открытие колоды
        choose_deck.setShortcut("Alt+D")
        choose_deck.setStatusTip("Open deck")
        choose_deck.triggered.connect(self.openDeck)

        self.toolbar = self.addToolBar("Login")
        self.toolbar.addAction(openFile)
        self.toolbar.addAction(login)
        self.toolbar.addAction(choose_deck)

        # Добавление Виджетов

        self.hero_list = QComboBox()  # Выпадающий список для выбора героя
        self.hero_list.addItems(['Маг', 'Чернокнижник', 'Друид',
                                 'Палдин', 'Воин', 'Разбойник',
                                 'Жрец', 'Шаман', 'Охотник', 'Охитник на демонов'])
        self.hero_list.currentIndexChanged.connect(self.hero_)

        # Создание layout и размещение виджетов
        self.lo1 = QHBoxLayout()
        self.lo1.addWidget(self.hero_list, 1, Qt.AlignLeft | Qt.AlignTop)

        self.lo2 = QVBoxLayout()
        self.lo2.addStretch(0)
        self.lo2.addLayout(self.lo1, Qt.AlignTop)

        self.centralwidget.setLayout(self.lo2)
        self.setCentralWidget(self.centralwidget)

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
        print(self.path)
        os.chdir(self.path)
        try:
            os.chdir('../pics/downloadedPics/')
            self.pics_main = os.getcwd() + '/HT'
            self.pics_token = os.getcwd() + '/TK'
        except:
            QMessageBox.about(self, "Ошибка", "Не найдена папка с изображением карт")

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


def main():
    app = QApplication(sys.argv)  # Новый экземпляр QApplication
    window = Editor()  # Создаем объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec()


if __name__ == '__main__':
    main()
