from PyQt5.QtWidgets import (QMainWindow, QWidget, QApplication, QAction, QStackedWidget, QFileDialog)

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
import sys

from Arena import Arena
from CardImport import CardImport
from DeckEditor import DeckEditor

import config

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

        tb_openLibrary = QAction(QIcon("assets/icons/file.jpg"), "&Open library...", self)
        tb_openLibrary.setShortcut("Ctrl+O")
        tb_openLibrary.setStatusTip("Open card's library")
        tb_openLibrary.triggered.connect(self.open_Library) 

        tb_arena = QAction(QIcon("assets/icons/Jiraiya.jpg"), "&Arena", self)
        tb_arena.setShortcut("Ctrl+2")
        tb_arena.setStatusTip("Open Arena")
        tb_arena.triggered.connect(self.switch_Arena)

        tb_deckEditor = QAction(QIcon("assets/icons/icon.jpg"), "&Editor", self)
        tb_deckEditor.setShortcut("Ctrl+1")
        tb_deckEditor.setStatusTip("Open Deck Editor")
        tb_deckEditor.triggered.connect(self.switch_DeckEditor)

        tb_importModule = QAction(QIcon("assets/icons/error2.png"), "&Import", self)
        tb_importModule.setStatusTip("Open Card Import")
        tb_importModule.setShortcut("Ctrl+3")
        tb_importModule.triggered.connect(self.switch_ImportModule)
        

        self.toolbar = self.addToolBar("Login")
        self.toolbar.addAction(tb_openLibrary)
        self.toolbar.addAction(tb_arena)
        self.toolbar.addAction(tb_deckEditor)
        self.toolbar.addAction(tb_importModule)
        self.toolbar.setIconSize(QSize(150,35))
        self.toolbar.setMovable(0)


        self.centralwidget = QWidget()
        self.setCentralWidget(self.stack)

        self.switch_DeckEditor()



    def open_Library(self):

        fname = QFileDialog.getOpenFileName(self, 'Open XML library...')[0]
        if fname == '' or not fname:
            return
        a = fname.split('/')
        name = a[-1]

        self.syspath = ''
        for x in a[:-1]:
            self.syspath += x + '/'
        self.library = name

        print(self.library, fname, config.LIBRARY_PATH)
        config.set_path(fname)
        print(self.library, fname, config.LIBRARY_PATH)

    def switch_DeckEditor(self):
        self.stack.setCurrentWidget(self.win1)

    def switch_Arena(self):
        self.stack.setCurrentWidget(self.win2)

    def switch_ImportModule(self):
        self.stack.setCurrentWidget(self.win3)

    

if __name__ == '__main__':

    app = QApplication(sys.argv)  # Новый экземпляр QApplication
    window = HearthTrice_Main()  # Создаем объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec()