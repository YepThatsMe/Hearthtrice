from PyQt5.QtWidgets import QApplication, QMessageBox

import sys


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
