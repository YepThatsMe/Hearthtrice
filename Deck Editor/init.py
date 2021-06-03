from PyQt5.QtWidgets import (QMainWindow, QWidget, QDesktopWidget, QApplication, QAction,
                             QMessageBox, QFileDialog, QListWidget, QComboBox, QHBoxLayout,
                             QVBoxLayout, QScrollArea, QLabel, QLineEdit, QCompleter, QGridLayout,
                             QTableWidget, QProgressBar)

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

        # Выпадающий список для выбора героя
        self.hero_list = QComboBox()
        self.hero_list.addItems(['Маг', 'Чернокнижник', 'Друид',
                                 'Палдин', 'Воин', 'Разбойник',
                                 'Жрец', 'Шаман', 'Охотник', 'Охотник на демонов'])
        self.hero_list.currentIndexChanged.connect(self.hero_)

        # Список карт
        self.list_cards = QListWidget()
        self.list_cards.currentRowChanged.connect(self.print_card)

        # Картинка для текущей карты
        self.image = QPixmap("icons/start_card.png")

        # Виджет с изображением карты
        self.card = QLabel()
        self.card.setPixmap(self.image)

        # Фильтры

        self.name = QLineEdit()  # Имя
        self.name.setFixedWidth(200)
        self.name.setPlaceholderText('Имя карты')
        self.cards = []
        self.completer = QCompleter(self.cards)
        self.name.setCompleter(self.completer)

        self.class_ = QComboBox()   # Класс
        self.class_.setFixedWidth(130)
        self.class_.addItems(['Жабы', 'Змеи', "Учиха", "Узумаки", "Джинчурики"])

        self.type = QComboBox()  # Тип
        self.type.setFixedWidth(130)
        self.type.addItems(['Существо', 'Заклинание', 'Оружие', 'Герой', 'Земля'])

        self.set = QComboBox()  # Cет
        self.set.setFixedWidth(115)
        self.set.addItems(['HT', 'TK', 'Standart'])

        # Progressbar
        self.progress = QProgressBar()
        self.progress.setMaximum(40)
        self.progress.setProperty("value", 0)
        self.progress.setFormat("%v/40")
        self.progress.setFixedWidth(300)

        # Колода
        self.deckList = QTableWidget()
        self.deckList.setFixedWidth(300)

        # Создание layout и размещение виджетов
        self.lo1 = QGridLayout()
        self.lo1.addWidget(self.set, 0, 0, Qt.AlignLeft)
        self.lo1.addWidget(self.hero_list, 0, 1, Qt.AlignLeft)
        self.lo1.addWidget(self.name, 0, 2, Qt.AlignLeft)
        self.lo1.addWidget(self.class_, 0, 3, Qt.AlignLeft)
        self.lo1.addWidget(self.type, 0, 4, Qt.AlignLeft)


        self.grid2 = QGridLayout()

        self.grid2.addWidget(self.list_cards, 0, 0)
        self.grid2.addWidget(self.card, 0, 1, Qt.AlignTop)

        self.deckListlayout = QVBoxLayout()
        self.deckListlayout.addWidget(self.deckList)
        self.deckListlayout.addWidget(self.progress, Qt.AlignBottom)


        self.right = QHBoxLayout()
        self.right.addLayout(self.grid2)
        self.right.addLayout(self.deckListlayout)


        self.gen_layout = QVBoxLayout()

        self.gen_layout.addLayout(self.lo1)
        self.gen_layout.addLayout(self.right)


        self.centralwidget.setLayout(self.gen_layout)
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

        esc = func.read(self.library)
        self.cards = list(map(lambda x: x[:x.rfind('.png')], list(esc.keys())))
        self.list_cards.addItems(self.cards)

        self.completer = QCompleter(self.cards)
        self.name.setCompleter(self.completer)


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
