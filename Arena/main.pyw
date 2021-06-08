import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTableWidgetItem, QInputDialog, QDialog, QAction, QFileDialog, QMessageBox

import Arena3_3
import roll
from functools import partial
import os


class ExampleApp(QtWidgets.QWidget, Arena3_3.Ui_MainWindow):
    def __init__(self):

        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна)

        self.esc = None

        self.menu.setNativeMenuBar(True)
        openlib = QAction('Open library...', self)
        openlib.setShortcut("Alt+O")
        openlib.triggered.connect(self.open_lib)

        savedeck = QAction("Save as...")
        savedeck.setShortcut("Ctrl+S")
        # savedeck.triggered.connect(self.save_deck)

        openlibrary = self.menu.addMenu("&File")
        g = self.menu.addMenu("&Test")
        openlibrary.addAction(openlib)
        g.addAction(savedeck)


        self.data_name = []
        self.row = self.tableWidget.rowCount()
        self.data_cnt = []
        self.path = rf'prog\\Cache\\'
        self.path_std = r"E:\\CockatricePortable\\data\\pics\\"
        self.k = roll.roll(self.esc)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(55)
        self.tableWidget.horizontalHeader().setMinimumSectionSize(20)
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, 1)
        self.Card1.setEnabled(False)
        self.Card2.setEnabled(False)
        self.Card3.setEnabled(False)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setHorizontalHeaderLabels(['Имя', 'Кол-во'])
        self.tableWidget.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)
        self.tableWidget.horizontalHeaderItem(1).setTextAlignment(Qt.AlignCenter)
        self.Card1.clicked.connect(partial(self.choice, 0))
        self.Card2.clicked.connect(partial(self.choice, 1))
        self.Card3.clicked.connect(partial(self.choice, 2))
        self.Enter.clicked.connect(self.complete)
        self.horizontalSlider.valueChanged.connect(self.number_changed)
        self.card_cnt.setNum(0)
        self.hero = self.comboBox.itemText(0)
        self.comboBox.currentIndexChanged.connect(self.hero_choice)
        self.setting_button.clicked.connect(self.ban)
        self.heroe_list = {'Маг': 'Mage', 'Друид': "Druid", "Охотник": "Hunter", "Паладин": "Paladin",
                           "Жрец": "Priest", "Разбойник": "Rogue", "Шаман": "Shaman",
                           "Чернокнижник": "Warlock", "Воин": "Warrior"}

        self.horizontalSlider.setValue(20)

    def open_lib(self):
        self.path_l = QFileDialog.getOpenFileName(self, "Open library")[0]
        self.esc = roll.read(self.path_l)
        roll.loadPic(self.esc, self.path_l)
        os.chdir(self.path_l[:self.path_l.rfind('/')])
        self.path = '../pics/downloadedPics/HT/'
        self.path_std = '../pics/'
        self.k = roll.roll(self.esc)


    def get_data(self):
        self.data_name = []
        self.data_cnt = []
        for i in range(self.tableWidget.rowCount()):
            self.data_name.append(self.tableWidget.item(i, 0).text())
        for j in range(self.tableWidget.rowCount()):
            self.data_cnt.append(int(self.tableWidget.item(j, 1).text()))

    def choice(self, n):
        self.row = self.tableWidget.rowCount()
        self.progressBar.setValue(sum(self.data_cnt) + 1)
        print(sum(self.data_cnt))
        try:
            if sum(self.data_cnt) + 1 < int(self.card_cnt.text()):

                if self.k[n] not in self.data_name:
                    self.tableWidget.setRowCount(self.row + 1)
                    self.tableWidget.setItem(self.tableWidget.rowCount() - 1, 0, QTableWidgetItem(self.k[n]))
                    self.tableWidget.setItem(self.tableWidget.rowCount() - 1, 1, QTableWidgetItem('1'))
                    self.get_data()

                elif self.k[n] in self.data_name:
                    i = self.data_name.index(self.k[n])
                    self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.data_cnt[i] + 1)))
                    self.get_data()

                self.k = roll.roll(self.esc)
                self.Card1.setIcon(QtGui.QIcon(rf'{self.path}{self.k[0]}'))
                self.Card1.setIconSize(QtCore.QSize(231, 311))
                self.Card2.setIcon(QtGui.QIcon(rf'{self.path}{self.k[1]}'))
                self.Card2.setIconSize(QtCore.QSize(231, 311))
                self.Card3.setIcon(QtGui.QIcon(rf'{self.path}{self.k[2]}'))
                self.Card3.setIconSize(QtCore.QSize(231, 311))

            elif int(self.card_cnt.text()) <= sum(self.data_cnt) + 1 <= 30:

                if self.k[n] not in self.data_name:

                    self.tableWidget.setRowCount(self.row + 1)
                    self.tableWidget.setItem(self.tableWidget.rowCount() - 1, 0, QTableWidgetItem(self.k[n]))
                    self.tableWidget.setItem(self.tableWidget.rowCount() - 1, 1, QTableWidgetItem('1'))
                    self.get_data()

                elif self.k[n] in self.data_name:
                    i = self.data_name.index(self.k[n])
                    self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.data_cnt[i] + 1)))
                    self.get_data()

                self.k = roll.roll_std(self.hero, self.path_std)
                print(self.hero)
                self.Card1.setIcon(QtGui.QIcon(rf'{self.path_std}{self.heroe_list[self.hero]}/{self.k[0]}'))
                self.Card1.setIconSize(QtCore.QSize(231, 311))
                self.Card2.setIcon(QtGui.QIcon(rf'{self.path_std}{self.heroe_list[self.hero]}/{self.k[1]}'))
                self.Card2.setIconSize(QtCore.QSize(231, 311))
                self.Card3.setIcon(QtGui.QIcon(rf'{self.path_std}{self.heroe_list[self.hero]}/{self.k[2]}'))
                self.Card3.setIconSize(QtCore.QSize(231, 311))

            if sum(self.data_cnt) == 30:
                self.label_limit.setText('В вашей колоде уже 30 карт, вы не можете добавить больше')

        except Exception as e:
            print(e)

    def number_changed(self):
        new_value = self.horizontalSlider.value()
        self.card_cnt.setNum(new_value)

    def hero_choice(self):
        self.hero = self.comboBox.currentText()

    def ban(self):

        if self.esc is None:
            QMessageBox.about(self, "Ошибка", "Сначала выберите библиотеку карт")
            return

        self.Dialog = QDialog()
        self.Dialog.setWindowTitle('Подтверждение')
        verticalLayout = QtWidgets.QVBoxLayout(self.Dialog)
        verticalLayout.setObjectName("verticalLayout")
        label = QtWidgets.QLabel(self.Dialog)
        label.setText(f"Вы уверены, что хотите выбрать класс: {self.comboBox.currentText()}")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setObjectName("label")
        verticalLayout.addWidget(label)
        buttonBox = QtWidgets.QDialogButtonBox(self.Dialog)
        buttonBox.setEnabled(True)
        buttonBox.setMinimumSize(QtCore.QSize(100, 0))
        buttonBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        buttonBox.setOrientation(QtCore.Qt.Horizontal)
        buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        buttonBox.setCenterButtons(True)
        buttonBox.setObjectName("buttonBox")
        verticalLayout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(self.Dialog)
        self.Dialog.exec_()

    def accept(self):

        self.comboBox.setEnabled(False)
        self.horizontalSlider.setEnabled(False)
        self.Dialog.close()
        self.setting_button.setEnabled(False)
        self.Card1.setIcon(QtGui.QIcon(rf'{self.path}{self.k[0]}'))
        self.Card1.setIconSize(QtCore.QSize(231, 311))
        self.Card2.setIcon(QtGui.QIcon(rf'{self.path}{self.k[1]}'))
        self.Card2.setIconSize(QtCore.QSize(231, 311))
        self.Card3.setIcon(QtGui.QIcon(rf'{self.path}{self.k[2]}'))
        self.Card3.setIconSize(QtCore.QSize(231, 311))
        self.Card1.setEnabled(True)
        self.Card2.setEnabled(True)
        self.Card3.setEnabled(True)

    def complete(self):

        if self.esc is None:
            QMessageBox.about(self, "Ошибка",
                              "Библиотека карт недоступна, вы не можете сейчас сохранить")
            return

        deck_name, ok = QInputDialog.getText(self, 'Ваша колода готова', 'Введите название колоды')
        deck_name = f"../decks/{deck_name}"


        roll.create(self.data_name, self.data_cnt, deck_name, self.esc)


# roll.loadPic(roll.esc)


def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаем объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec()


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
