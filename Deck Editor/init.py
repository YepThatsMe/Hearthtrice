from PyQt5.QtWidgets import (QMainWindow, QWidget, QDesktopWidget, QApplication, QAction,
                             QMessageBox, QFileDialog, QListWidget, QComboBox, QHBoxLayout,
                             QVBoxLayout)

from PyQt5.QtGui import QIcon, QPixmap

import sys
import os

import func

class Editor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.iconPath = os.getcwd() + '/icons'
        print(self.iconPath)
        self.setupUI()

    def setupUI(self):

        # Настроки окна
        self.setGeometry(0, 0, 1080, 720)
        self.setWindowTitle("Deck Editor")
        self.setWindowIcon(QIcon("icons/icon.jpg"))
        self.center()  # Центрирование окна
        self.statusBar().showMessage("Ready")

        self.centralwidget = QWidget(self)

        # ToolBar
        openFile = QAction(QIcon("icons/file.jpg"), "&Open deck...", self)  # Открытие существующей
        openFile.setShortcut("Alt+Q")                                       # библиотеки карт
        openFile.setStatusTip("Open card's library")
        openFile.triggered.connect(self.open)

        login = QAction(QIcon("icons/naruto_min.png"), "&Login...", self)  # Открытие Hearthcards
        login.setShortcut("Alt+Shift+L")
        login.setStatusTip("Login to HearthCards...")
        login.triggered.connect(func.login)

        self.toolbar = self.addToolBar("Login")
        self.toolbar.addAction(openFile)
        self.toolbar.addAction(login)

        # Добавление Виджетов

        self.hero_list = QComboBox()
        self.hero_list.addItems(['Маг', 'Чернокнижник', 'Друид',
                                 'Палдин', 'Воин', 'Разбойник',
                                 'Жрец', 'Шаман', 'Охотник', 'Охитник на демонов'])

        # Создание layout и размещение виджетов
        self.lo1 = QHBoxLayout(self.centralwidget)
        self.lo1.addSpacing(1)

        self.lo1.addWidget(self.hero_list)

        self.setCentralWidget(self.centralwidget)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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
