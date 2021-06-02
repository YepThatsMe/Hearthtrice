from PyQt5.QtWidgets import (QMainWindow, QWidget, QDesktopWidget, QApplication, QAction,
                             QMessageBox, qApp)
from PyQt5.QtCore import QMetaObject
from PyQt5.QtGui import QIcon

import sys

import func

class Editor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setupUI()

    def setupUI(self):

        # Настроки окна
        self.setGeometry(0, 0, 1080, 720)
        self.setWindowTitle("Deck's Editor")
        self.setWindowIcon(QIcon("icons/icon.jpg"))
        self.center()  # Центрирование окна
        self.statusBar().showMessage("Ready")

        # Настройки меню
        openFile = QAction(QIcon("icons/file.jpg"), "&Open deck...", self)  # Открытие существующей колоды
        openFile.setShortcut("Alt+Q")
        openFile.setStatusTip("Exit application")

        # Меню
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu("&File")
        filemenu.addAction(openFile)

        # ToolBar
        login = QAction(QIcon("icons/naruto_min.png"), "&Login...", self)
        login.setShortcut("Alt+Shift+L")
        login.setStatusTip("Login to HearthCards...")
        login.triggered.connect(func.open)

        self.toolbar = self.addToolBar("Login")
        self.toolbar.addAction(login)

        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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
