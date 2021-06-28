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

from Arena import Arena
from CardImport import CardImport
from DeckEditor import DeckEditor

class HearthTrice_Main(QMainWindow):
    def __init__(self):
        super().__init__()

        self.win1 = DeckEditor()
        self.win2 = Arena()
        self.win3 = CardImport()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.win1)
        self.stack.addWidget(self.win2)
        self.stack.addWidget(self.win3)


        # ToolBar
        openFile = QAction(QIcon("assets/icons/file.jpg"), "&Open library...", self)  # Открытие существующей
        openFile.setShortcut("Ctrl+O")  # библиотеки карт
        openFile.setStatusTip("Open card's library")
        #openFile.triggered.connect(self.open)

        # login = QAction(QIcon("assets/icons/naruto_min.png"), "&Login...", self)  # Открытие Hearthcards
        # login.setShortcut("Alt+Shift+L")
        # login.setStatusTip("Login to HearthCards...")
        # login.triggered.connect(func.login)

        # choose_deck = QAction(QIcon("assets/icons/deck.jpg"), "&Open deck...", self)  # Открытие колоды
        # choose_deck.setShortcut("Alt+D")
        # choose_deck.setStatusTip("Open deck")
        # choose_deck.triggered.connect(self.openDeck)

        ran_ = QAction(QIcon("assets/icons/Jiraiya.jpg"), "&Arena", self)
        ran_.setShortcut("Ctrl+2")
        ran_.setStatusTip("Open Arena")
        ran_.triggered.connect(self.Arena)

        editor = QAction(QIcon("assets/icons/icon.jpg"), "&Editor", self)
        editor.setShortcut("Ctrl+1")
        editor.setStatusTip("Open Deck Editor")
        editor.triggered.connect(self.Editor_)

        import_module = QAction(QIcon("assets/icons/error2.png"), "&Import", self)
        import_module.setStatusTip("Open Card Import")
        import_module.setShortcut("Ctrl+3")
        import_module.triggered.connect(self.ImportModule)
        

        self.toolbar = self.addToolBar("Login")
        self.toolbar.addAction(openFile)
        # self.toolbar.addAction(login)
        # self.toolbar.addAction(choose_deck)
        self.toolbar.addAction(ran_)
        self.toolbar.addAction(editor)
        self.toolbar.addAction(import_module)
        self.toolbar.setIconSize(QSize(150,35))
        self.toolbar.setMovable(0)


        self.centralwidget = QWidget()
        self.setCentralWidget(self.stack)

        self.Editor_()

        #self.setupUI()


    def Editor_(self):
        self.stack.setCurrentWidget(self.win1)

    def Arena(self):
        self.stack.setCurrentWidget(self.win2)

    def ImportModule(self):
        self.stack.setCurrentWidget(self.win3)

    

def main():
    app = QApplication(sys.argv)  # Новый экземпляр QApplication
    window = HearthTrice_Main()  # Создаем объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec()


if __name__ == '__main__':
    main()
