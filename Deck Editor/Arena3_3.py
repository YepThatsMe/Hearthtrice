from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.resize(1047, 628)

        self.menu = MainWindow.menuBar()

        self.centralwidget = QtWidgets.QWidget(MainWindow)

        self.gen_lo = QtWidgets.QHBoxLayout(self.centralwidget)
        self.lo5 = QtWidgets.QHBoxLayout()
        self.lo4 = QtWidgets.QVBoxLayout()
        self.lo3 = QtWidgets.QVBoxLayout()
        self.lo2 = QtWidgets.QHBoxLayout()
        self.lo1 = QtWidgets.QHBoxLayout()


        self.Card3 = QtWidgets.QPushButton(self.centralwidget)
        self.Card3.setMinimumSize(QtCore.QSize(231, 311))
        self.Card3.setAutoFillBackground(False)


        self.Card2 = QtWidgets.QPushButton(self.centralwidget)
        self.Card2.setMinimumSize(QtCore.QSize(231, 311))
        self.Card2.setAutoFillBackground(False)

        self.Card1 = QtWidgets.QPushButton(self.centralwidget)
        self.Card1.setMinimumSize(QtCore.QSize(231, 311))
        self.Card1.setAutoFillBackground(False)
        self.Card1.setEnabled(False)



        self.label_limit = QtWidgets.QLabel(self.centralwidget)
        self.label_limit.setMaximumSize(QtCore.QSize(16777215, 30))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label_limit.setFont(font)



        self.horizontalSlider = QtWidgets.QSlider(self.centralwidget)
        self.horizontalSlider.setMaximumSize(QtCore.QSize(250, 16777215))
        self.horizontalSlider.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.horizontalSlider.setInputMethodHints(QtCore.Qt.ImhPreferNumbers)
        self.horizontalSlider.setMaximum(30)
        self.horizontalSlider.setPageStep(5)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.horizontalSlider.setTickInterval(1)


        self.card_cnt = QtWidgets.QLabel(self.centralwidget)
        self.card_cnt.setMaximumSize(QtCore.QSize(200, 16777215))
        font = QtGui.QFont()
        font.setPointSize(11)
        
        font.setWeight(50)
        self.card_cnt.setFont(font)


        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setEnabled(True)
        self.comboBox.setMinimumSize(QtCore.QSize(0, 0))
        self.comboBox.setMaximumSize(QtCore.QSize(150, 16777215))
        font = QtGui.QFont()
        # font.setFamily("Arial")
        font.setPointSize(9)
        # font.setBold(False)
        # font.setItalic(False)
        # font.setUnderline(False)
        font.setWeight(50)
        # font.setKerning(True)
        self.comboBox.setFont(font)
        self.comboBox.setFocusPolicy(QtCore.Qt.WheelFocus)
        # self.comboBox.setToolTip("")
        # self.comboBox.setStatusTip("")
        # self.comboBox.setWhatsThis("")
        # self.comboBox.setAccessibleName("")
        # self.comboBox.setAccessibleDescription("")
        self.comboBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.comboBox.setInputMethodHints(QtCore.Qt.ImhPreferNumbers)
        # self.comboBox.setEditable(False)
        
        self.comboBox.addItems(['Маг', 'Воин', 'Жрец', 'Охотник', 'Разбойник', 'Друид', 'Шаман', 'Чернокнижник', 'Паладин', 'Охотник на демонов'])
        self.comboBox.setCurrentIndex(0)

        self.setting_button = QtWidgets.QPushButton(self.centralwidget)
        self.setting_button.setMaximumSize(QtCore.QSize(70, 16777215))
        self.setting_button.setText('Готово')


        self.Enter = QtWidgets.QPushButton(self.centralwidget)
        self.Enter.setMinimumSize(QtCore.QSize(0, 31))
        self.Enter.setAutoFillBackground(True)
        self.Enter.setText('Готово')



        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setMinimumSize(QtCore.QSize(291, 561))
        self.tableWidget.setAutoFillBackground(True)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tableWidget.setGridStyle(QtCore.Qt.SolidLine)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(0)
        self.tableWidget.horizontalHeader().setVisible(True)
        self.tableWidget.horizontalHeader().setCascadingSectionResizes(False)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(150)
        self.tableWidget.horizontalHeader().setMinimumSectionSize(50)
        self.tableWidget.verticalHeader().setVisible(True)
        self.tableWidget.verticalHeader().setCascadingSectionResizes(False)
        self.tableWidget.verticalHeader().setHighlightSections(True)


        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setMinimumSize(QtCore.QSize(301, 31))
        self.progressBar.setAutoFillBackground(True)
        self.progressBar.setMaximum(30)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setAlignment(QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setFormat("%v/30")


        # Вложение виджетов
        self.lo1.addWidget(self.Card3)
        self.lo1.addWidget(self.Card2)
        self.lo1.addWidget(self.Card1)

        self.lo3.addLayout(self.lo1)
        self.lo3.addWidget(self.label_limit)

        self.lo2.addWidget(self.horizontalSlider)
        self.lo2.addWidget(self.card_cnt)
        self.lo2.addWidget(self.comboBox)
        self.lo2.addWidget(self.setting_button)
        self.lo3.addLayout(self.lo2)
        self.lo3.addWidget(self.Enter)

        self.lo5.addLayout(self.lo3)
        self.lo4.addWidget(self.tableWidget)
        self.lo4.addWidget(self.progressBar)
        self.lo5.addLayout(self.lo4)

        self.gen_lo.addLayout(self.lo5)


        MainWindow.setCentralWidget(self.centralwidget)

        self.comboBox.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)