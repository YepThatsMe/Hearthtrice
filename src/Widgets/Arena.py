import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTableWidgetItem, QInputDialog, QDialog, QAction, QFileDialog, QMessageBox

from functools import partial
from configparser import ConfigParser
import xml.etree.ElementTree as ET
import os

from Widgets.Arena_UI import UI_MainWindow

class Roll:

    def read(path):

        hs = ET.parse(path)
        enter = hs.findall("cards/card[type = 'Minion']") + hs.findall("cards/card[type = 'Spell']") + hs.findall(
            "cards/card[type = 'Weapon']") + hs.findall("cards/card[type = 'Hero']")
        esc = {i[0].text + ".png": "".join(i[2].attrib.values()) for i in enter}
        # count = int(input('Введите число карт:\n'))
        return esc



    def loadPic(esc, path):
        import requests
        import os
        from PIL import Image
        from io import BytesIO
        a = []
        for i in esc.keys():
            a.append(i)

        # ! Закоментил chdir потому что она меняет расположение программы и ломает остальные пути, надо как то пофиксить
        # os.chdir(path)

        # Обрываю инициализацию арены, если не найден путь к картинкам. Надо как-то решить.
        try:
            l = os.listdir(path=path)
        except FileNotFoundError as e:
            print('Не найден путь к картинкам', path)
            return
        
        if len(esc) == len(l):
            return
        if len(a) < len(l):
            diff = set(l).difference(set(a))
            diff = list(diff)

            for j in diff:
                print(j)
                print(esc)
                if j in esc:
                    r = requests.get(esc[j])
                    im = Image.open(BytesIO(r.content))
                    im.save(f'{path}{j}.png')

        if len(a) > len(l):
            diff = set(a).difference(set(l))
            diff = list(diff)

            for j in diff:
                if j in esc:
                    r = requests.get(esc[j])
                    im = Image.open(BytesIO(r.content))
                    im.save(f'{path}{j}.png')


    def roll(esc):
        import numpy.random as rnd
        roll = rnd.choice(list(esc.keys()), size=3, replace=False)
        return roll

    def roll_std(Hero, path_std):
        import numpy.random as rnd
        import os
        heroes = {'Маг': 'Mage', 'Друид': "Druid", "Охотник": "Hunter", "Паладин": "Paladin",
                "Жрец": "Priest", "Разбойник": "Rogue", "Шаман": "Shaman",
                "Чернокнижник": "Warlock", "Воин": "Warrior"}
        path = f"{path_std}{heroes[Hero]}"
        cards = os.listdir(path=path)
        roll_std_l = rnd.choice(cards, size=3, replace=False)
        return roll_std_l


    def create(names, cnt, deck_name, esc):
        import xml.etree.ElementTree as ET
        deck = ET.Element('cockatrice_deck')
        deck.set('version', '1')
        main = ET.Element('zone')
        main.set('name', 'main')

        def add_card(names, cnt, ind):
            # global esc
            if names[ind] in esc:
                ET.SubElement(main, 'card', attrib={'number': f'{cnt[ind]}', 'name': names[ind][:-4]})
            else:
                ET.SubElement(main, 'card', attrib={'number': f'{cnt[ind]}', 'name': names[ind]})
        for i in range(len(names)):
            add_card(names, cnt, i)

        deck.append(main)
        deck = ET.ElementTree(deck)
        deck.write(f'{deck_name}.cod')


class Arena(QtWidgets.QMainWindow, UI_MainWindow):
    def __init__(self):

        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна)

        self.esc = None

        self.menu.setNativeMenuBar(True)
        # openlib = QAction('Open library...', self)
        # openlib.setShortcut("Ctrl+O")
        # openlib.triggered.connect(self.open_lib)

        savedeck = QAction("Save as...")
        savedeck.setShortcut("Ctrl+S")
        # savedeck.triggered.connect(self.save_deck)

        # openlibrary = self.menu.addMenu("&File")
        # openlibrary.addAction(openlib)

        g = self.menu.addMenu("&Test")
        g.addAction(savedeck)

        self.data_name = []
        self.row = self.tableWidget.rowCount()
        self.data_cnt = []
        # self.path_HT = rf'prog\\Cache\\'
        # self.path_std = r"data\\pics\\"

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

    # def open_lib(self):
    #     self.path_l = QFileDialog.getOpenFileName(self, "Open library")[0]
    #     self.esc = Roll.read(self.path_l)
    #     Roll.loadPic(self.esc, self.path_l)
    #     os.chdir(self.path_l[:self.path_l.rfind('/')])
    #     self.path_HT = '../pics/downloadedPics/HT/'
    #     self.path_std = '../pics/'
    #     self.k = Roll.roll(self.esc)

    def config_update(self):

        self.config = ConfigParser()
        self.config.read('assets/config.ini')
        self.path_l = self.config.get('GENERAL', 'LIB_PATH')
        self.path_std = self.config.get('GENERAL', 'PIC_PATH')
        self.path_HT = self.path_std + '/downloadedPics/HT/'
        self.path_deck = self.config.get('GENERAL', 'DECK_PATH')

        self.esc = Roll.read(self.path_l)
        if not Roll.loadPic(self.esc, self.path_HT):
            self.esc = 'NoPicPath'
            return # Завершаем если loadPic завершился в except'е
        # os.chdir(self.path_l[:self.path_l.rfind('/')])
        self.k = Roll.roll(self.esc)

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

                self.k = Roll.roll(self.esc)
                self.Card1.setIcon(QtGui.QIcon(rf'{self.path_HT}{self.k[0]}'))
                self.Card1.setIconSize(QtCore.QSize(231, 311))
                self.Card2.setIcon(QtGui.QIcon(rf'{self.path_HT}{self.k[1]}'))
                self.Card2.setIconSize(QtCore.QSize(231, 311))
                self.Card3.setIcon(QtGui.QIcon(rf'{self.path_HT}{self.k[2]}'))
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

                self.k = Roll.roll_std(self.hero, self.path_std)
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
        elif self.esc == 'NoPicPath':
            QMessageBox.about(self, "Ошибка",
                            "Не найден путь к изображениям карт")
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
        self.Card1.setIcon(QtGui.QIcon(rf'{self.path_HT}{self.k[0]}'))
        self.Card1.setIconSize(QtCore.QSize(231, 311))
        self.Card2.setIcon(QtGui.QIcon(rf'{self.path_HT}{self.k[1]}'))
        self.Card2.setIconSize(QtCore.QSize(231, 311))
        self.Card3.setIcon(QtGui.QIcon(rf'{self.path_HT}{self.k[2]}'))
        self.Card3.setIconSize(QtCore.QSize(231, 311))
        self.Card1.setEnabled(True)
        self.Card2.setEnabled(True)
        self.Card3.setEnabled(True)

    def complete(self):

        if self.esc is None:
            QMessageBox.about(self, "Ошибка",
                              "Библиотека карт недоступна, вы не можете сейчас сохранить")
            return
        elif self.esc == 'NoPicPath':
            QMessageBox.about(self, "Ошибка",
                              "Не найден путь к изображениям карт")
            return

        deck_name, ok = QInputDialog.getText(self, 'Ваша колода готова', 'Введите название колоды')
        deck_name = self.path_deck + f"/{deck_name}"


        Roll.create(self.data_name, self.data_cnt, deck_name, self.esc)


# Roll.loadPic(Roll.esc)


def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаем объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec()


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
