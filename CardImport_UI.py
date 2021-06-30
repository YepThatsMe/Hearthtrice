import sys, os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import *

# rofl branch
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class UI_MainWindow(object):

    def setupUI(MW, self):

        # MW.setFixedSize(520,650)
        self.syspath = os.getcwd()
        self.filename = 'newcardset.xml'
        

        openFile = QAction('Open...', MW)
        openFile.setShortcut('Ctrl+O')
        openFile.triggered.connect(self.showdialog)

        newFile = QAction('Create blank...', MW)
        newFile.setShortcut('Ctrl+N')
        newFile.triggered.connect(self.showdialog2)

        self.openDirectory = QAction('Open XML folder', MW)
        self.openDirectory.setShortcut('Ctrl+D')
        self.openDirectory.triggered.connect(self.showdialog3)
        self.openDirectory.setEnabled(False)

        self.askhelp = QAction('How to use', MW)
        self.askhelp.setShortcut('Ctrl+H')

        self.login = QAction('Log into Hearthcards.net', MW)
        self.login.setShortcut('Ctrl+L')

        menu = MW.menuBar()
        fileMenu = menu.addMenu('&File')
        fileMenu.addAction(newFile)
        fileMenu.addAction(openFile)
        fileMenu.addAction(self.openDirectory)
        menu.addAction(self.login)
        menu.addAction(self.askhelp)

        #--
        self.picByteDict = {}
        #---        
        

        self.pixmap = QPixmap()

        self.widgetIMG = QLabel(alignment=Qt.AlignHCenter)
        self.widgetIMG.setPixmap(QPixmap(resource_path('assets/start_card.png')))

        self.widgetList = QComboBox()
        self.widgetList.setEnabled(False)
        self.idx_max = 0

        self.impblank = QLineEdit()
        self.impblank.setMaxLength(10)
        self.impblank.setPlaceholderText('Enter gallery ID...')
        self.impblank.setEnabled(False)
        self.impblank.returnPressed.connect(self.ImportDropList)

        self.buttonImport = QPushButton('Import', MW)
        self.buttonImport.setMaximumWidth(80)
        self.buttonImport.setToolTip('Load library from hearthcards.net/')
        self.buttonImport.setEnabled(False)
        self.buttonImport.pressed.connect(self.ImportDropList)

        self.progressBar = QProgressBar(MW)
        self.progressBar.setGeometry(30,40,300,25)
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.hide()
  
        # setting background to color and radius 
        # and bar color and bar radius 



        self.currentLibraryList = QListWidget()
        self.currentLibraryList.itemClicked.connect(self.Display2)

        
        self.serachLibraryField = QLineEdit()
        self.serachLibraryField.setMaxLength(35)
        self.serachLibraryField.setPlaceholderText('Search')
        self.serachLibraryField.setEnabled(False)
        self.serachLibraryField.textChanged.connect(self.FilterLibraryList)


        self.nameline = QLineEdit()
        self.nameline.setMaxLength(35)
        self.nameline.setPlaceholderText('Enter card name')
        self.nameline.setEnabled(False)
        self.nameline.returnPressed.connect(self.NameInput)

        self.colorline = QLineEdit()
        self.colorline.setMaxLength(25)
        self.colorline.setPlaceholderText('Class')
        self.colorline.setEnabled(False)
        self.colorline.returnPressed.connect(self.NameInput)

        self.manacostline = QLineEdit()
        self.manacostline.setMaxLength(2)
        self.manacostline.setPlaceholderText('Manacost')
        self.manacostline.setEnabled(False)
        self.manacostline.returnPressed.connect(self.NameInput)

        self.cardtype = QComboBox()
        self.cardtype.addItems(['None','Minion','Spell','Weapon','Hero','Token'])
        self.cardtype.setEnabled(False)

        self.cardrarity = QComboBox()
        self.cardrarity.addItems(['None','Common','Rare','Epic','Legendary'])
        self.cardrarity.setEnabled(False)

        self.buttonAdd = QPushButton('Add')
        self.buttonAdd.pressed.connect(self.NameInput)
        self.buttonAdd.setEnabled(False)

        self.buttonRemove = QPushButton('Remove')
        self.buttonRemove.setEnabled(False)
        self.buttonRemove.pressed.connect(self.removeEntry)

        ### Layouts ###

        gen1st_layout = QVBoxLayout()
        lo1 = QHBoxLayout()
        lo2 = QVBoxLayout()
        lo3 = QHBoxLayout()
        lo4 = QHBoxLayout()
        lo5 = QHBoxLayout()

        mid_layout = QHBoxLayout()
        left_lo = QVBoxLayout()
        right_lo = QVBoxLayout()
        
        left_lo.addLayout(lo1)
        left_lo.addLayout(lo2)
        left_lo.addLayout(lo3)
        left_lo.addLayout(lo4)
        left_lo.addLayout(lo5)

        mid_layout.addLayout(left_lo)
        mid_layout.addLayout(right_lo)

        lo1.addWidget(self.impblank)
        lo1.addWidget(self.buttonImport)
        lo2.addWidget(self.widgetIMG)
        lo2.addWidget(self.progressBar)
        lo2.addWidget(self.widgetList)
        lo3.addWidget(self.cardtype)
        lo3.addWidget(self.nameline)
        lo4.addWidget(self.cardrarity)
        lo4.addWidget(self.colorline)
        lo4.addWidget(self.manacostline)
        lo5.addWidget(self.buttonAdd)


        right_lo.addWidget(self.serachLibraryField)
        right_lo.addWidget(self.currentLibraryList)
        right_lo.addWidget(self.buttonRemove)

        gen1st_layout.addLayout(mid_layout)

        widget = QWidget()
        widget.setLayout(gen1st_layout)
        self.setCentralWidget(widget)
    



