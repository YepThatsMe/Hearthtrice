from PyQt5.QtWidgets import QApplication

import sys

from Widgets.MainMediator import MainMediator

def main():
    app = QApplication(sys.argv)
    window = MainMediator()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
