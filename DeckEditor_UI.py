from PyQt5.QtWidgets import (QMainWindow, QWidget, QDesktopWidget, QApplication, QAction,
                             QMessageBox, QFileDialog, QStackedWidget, QComboBox, QHBoxLayout,
                             QVBoxLayout, QLabel, QLineEdit, QCompleter, QGridLayout,
                             QTableWidget, QProgressBar, QTableWidgetItem, QAbstractItemView)

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
import xml.etree.ElementTree as ET
import sys
import os
import pickle



class UI_MainWindow(object):

    def setupUI(MW, self):

    # Настроки окна
        MW.setGeometry(0, 0, 1080, 720)
        MW.setWindowTitle("Deck Editor")  
        MW.setWindowIcon(QIcon("icons/icon.jpg"))
        MW.center()  # Центрирование окна
        self.statusBar().showMessage("Ready")

        self.centralwidget = QWidget(MW)

    

        # Добавление Виджетов

        # Выпадающий список для выбора героя
        self.hero_list = QComboBox()
        self.hero_list.addItems(['Маг', 'Чернокнижник', 'Друид',
                                    'Палдин', 'Воин', 'Разбойник',
                                    'Жрец', 'Шаман', 'Охотник', 'Охотник на демонов'])
        self.hero_list.currentIndexChanged.connect(self.hero_)

        # Список карт
        self.list_cards = QTableWidget()
        self.list_cards.setColumnCount(5)
        self.list_cards.setSortingEnabled(True)
        self.list_cards.setHorizontalHeaderLabels(["Имя", "Тип", "Класс", "Редкость", "Стоимость"])
        # self.list_cards.setShowGrid(1)
        self.list_cards.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_cards.setSelectionMode(QAbstractItemView.NoSelection)
        self.list_cards.setGridStyle(Qt.SolidLine)



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
        self.class_.addItems(['Жабы', 'Змеи', "Учиха", "Узумаки", "Джинчурики"]) # Здесь нужно парсить все доступные типы из xml

        self.type = QComboBox()  # Тип
        self.type.setFixedWidth(130)
        self.type.addItems(['Существо', 'Заклинание', 'Оружие', 'Герой', 'Земля'])

        self.set = QComboBox()  # Cет
        self.set.setFixedWidth(115)
        self.set.addItems(['HT', 'TK', 'Standart'])
        self.set.currentIndexChanged.connect(self.relist)

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