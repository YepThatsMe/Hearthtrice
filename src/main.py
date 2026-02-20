from PyQt5.QtWidgets import QApplication, QMessageBox

import sys

VERSION_MAJOR = 2
VERSION_MINOR = 8

DEBUG = 0

def main():
    
    app = QApplication(sys.argv)

    try:
        from Widgets.MainMediator import MainMediator
    except ImportError as e:
        QMessageBox.warning(None, "Ошибка импорта", str(e))
        return
    
    window = MainMediator()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
