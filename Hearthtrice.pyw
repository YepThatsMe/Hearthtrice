import sys
import os
import urllib.request
from functools import partial

import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, Qt, QThread, QTimer
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import *

# Тест ветки PowerOfPelmenei
# hui
# fdgfg
#in collect dl_2 write xml builder with sets=folders.. +move folders to CUSTOM and change path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class Collector():
    def collect(num):      # ВОЗВРАЩАЕТ СПИСОК С URL-ССЫЛКАМИ НА КАРТОНКИ
        #input('номер : ')

        URL = f'http://www.hearthcards.net/mycards/?cards={num}'
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')

        implist = []

        for gay in soup.find_all('img'):
            if gay.has_attr('classname'):
                pass
            else:
                #            gay.get('src'))  
                #            gay.attrs['src']) - возвращает значение атрибута src
                link = gay.attrs['src']
                
                if '../cards/' in link:
                    unpermanent = 'http://hearthcards.net' + link[2:]
                    implist.append(unpermanent)
                else:
                    implist.append((link)) # добавляет значение атрибута src в список

        if not implist:
            print("Incorrect ID or library is empty")
            return 'Error'
        else:
            print("Data collected successfully...")
            return implist


    def scan_xml(filepath, filename):
        path = filepath
        name = filename
        spisok = []
        spisok2 = []

        with open(path + '/' + name) as a:
            soup = BeautifulSoup(a, 'xml')


        find = soup.find_all('name')
        for i in find:
            spisok += i

        for gayy in soup.find_all('set'):
            spisok2.append(gayy.attrs['picURL'])

        return spisok, spisok2

    def delete_entry(entry, path, name):

        f = open(path + name, 'r')
        soup = BeautifulSoup(f, 'xml')

        searchstring = entry
        item = soup.find_all('name')

        for n in item:
            foundstring = n.text
            if searchstring == foundstring:
                print('Match!')
                tag1 = n.next_sibling.next_sibling.next_sibling.next_sibling.decompose()
                tag2 = n.next_sibling.next_sibling.decompose()
                tag3 = n.parent.decompose()
                tag = n.decompose()

                break

        a = str(soup)

        f = open(path + name, 'w')
        f.write(a)
        f.close()



class Card:
    def __init__(self, cardName, urlName, type, manacost, color, rarity, syspath, filename):
        if type == 'Token':
            self.urlName = '\t\t\t<set picURL="' + urlName + '">TK</set>\n'
            self.tk = '\t\t\t<token>1</token>\n'
            self.type = '\t\t\t<type>' + type + '</type>\n'
        elif type == 'None':
            self.urlName =  '\t\t\t<set picURL="' + urlName + '">HT</set>\n'
            self.tk = ''
            self.type = '\t\t\t<type></type>\n'
        else:
            self.urlName =  '\t\t\t<set picURL="' + urlName + '">HT</set>\n'
            self.tk = ''
            self.type = '\t\t\t<type>' + type + '</type>\n'
        
        self.cardName = '\t\t\t<name>' + cardName + '</name>\n'
        self.rarity = '\t\t\t<rarity>' + rarity + '</rarity>\n' if rarity != 'None' else '\t\t\t<rarity></rarity>\n'
        self.manacost = '\t\t\t<manacost>' + manacost + '</manacost>\n' if manacost != 'None' else '\t\t\t<manacost></manacost>\n'
        self.color = '\t\t\t<color>' + color + '</color>\n' if color != 'None' else '\t\t\t<color></color>\n'
        self.ls = ['\t\t<card>\n', self.cardName, self.tk, self.type, self.manacost, self.color, self.rarity, self.urlName, '\t\t</card> \n']
        self.a = []
        self.syspath = syspath
        self.path = filename
    def open(self):
        f = open(self.syspath + self.path, 'r')
        self.a = f.readlines()
        f.close()
        while '\n' in self.a:
            self.a.remove('\n')
    def enter(self):
        self.a.pop(-2)
        self.a.pop(-1)
        self.a = self.a + self.ls+ ['\t</cards>\n', '</cockatrice_carddatabase>']
    def write(self):
        f = open(self.syspath + self.path, 'w')
        for i in self.a:
            f.write(i)
        f.close()

class Cacher(QObject):
    resultsChanged2 = pyqtSignal(object)
    @pyqtSlot(str)
    def cache(self, key_and_url):
        key = key_and_url[0]
        url = key_and_url[1]

        img = requests.get(url).content
    
        data_tuple = (key, img)
        self.resultsChanged2.emit(data_tuple)
        print(f'sending converted data tuple: {key}, (bytes)')


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Hearthtrice Manager")
        self.setFixedSize(520,650)
        self.setWindowIcon(QIcon(resource_path('assets/icon.ico')))
        self.syspath = os.getcwd()
        self.filename = 'newcardset.xml'
        

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(300,200)
        
        # Add tabs
        self.tabs.addTab(self.tab1,"Tab 1")
        self.tabs.addTab(self.tab2,"Tab 2")

        ## Create first tab
        self.tab2.layout = QVBoxLayout()
        self.pushButton1 = QPushButton("PyQt5 button")
        self.tab2.layout.addWidget(self.pushButton1)
        self.tab2.setLayout(self.tab2.layout)

        openFile = QAction('Open...', self)
        openFile.setShortcut('Ctrl+O')
        openFile.triggered.connect(self.showdialog)

        newFile = QAction('Create blank...', self)
        newFile.setShortcut('Ctrl+N')
        newFile.triggered.connect(self.showdialog2)

        self.openDirectory = QAction('Open XML folder', self)
        self.openDirectory.setShortcut('Ctrl+D')
        self.openDirectory.triggered.connect(self.showdialog3)
        self.openDirectory.setEnabled(False)

        askhelp = QAction('How to use', self)
        askhelp.setShortcut('Ctrl+H')
        askhelp.triggered.connect(self.dialog)

        menu = self.menuBar()
        fileMenu = menu.addMenu('&File')
        fileMenu.addAction(newFile)
        fileMenu.addAction(openFile)
        fileMenu.addAction(self.openDirectory)
        helpMenu = menu.addMenu('&Help')
        helpMenu.addAction(askhelp)

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

        self.buttonImport = QPushButton('Import', self)
        self.buttonImport.setMaximumWidth(80)
        self.buttonImport.setToolTip('Load library from hearthcards.net/')
        self.buttonImport.setEnabled(False)
        self.buttonImport.pressed.connect(self.ImportDropList)

        self.progressBar = QProgressBar(self)
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

        self.tab1.setLayout(gen1st_layout)

        self.setCentralWidget(self.tabs)
    
    @pyqtSlot(bytes)
    def on_cacheChanged(self, data_tuple):
        key = data_tuple[0]
        pic_byte = data_tuple[1]

        self.picByteDict[key] = pic_byte   
        print(len(self.picByteDict))

        self.completed +=  (1 /  self.expectedDicLen) * 100
        self.progressBar.setValue(self.completed)

        if len(self.picByteDict) == self.expectedDicLen:
            self.widgetList.setEnabled(True)
            self.progressBar.hide()
            self.completed = 0
            print('ready')

    # def closeEvent(self, event):
    #     self.threadx.quit()
    #     self.threadx.wait()
    #     super().closeEvent(event)

    def dialog(self):

        with open(resource_path('assets/how_to_use.txt'), 'r') as b:
            text = b.read()
        a = QMessageBox.about(self, 'Help', text)


    def display(self, ix):

        if ix == -1:
            pass
        else:
            pic = self.picByteDict[ix+1]
            self.pixmap.loadFromData(pic)
            self.widgetIMG.setPixmap(self.pixmap.scaledToHeight(380))


    def Display2(self):
        name = self.currentLibraryList.currentItem().text()
        print(name)

        try:
            file = str(os.path.dirname(os.path.dirname(self.syspath))) + f'/pics/downloadedPics/HT/{name}.png'

            with open(file, 'rb') as c:
                pic = c.read()
                self.pixmap.loadFromData(pic)
                self.widgetIMG.setPixmap(self.pixmap.scaledToHeight(380))
        except FileNotFoundError as e:
            try:
                file = str(os.path.dirname(os.path.dirname(self.syspath))) + f'/pics/downloadedPics/TK/{name}.png'
                with open(file, 'rb') as c:
                    pic = c.read()
                self.pixmap.loadFromData(pic)
                self.widgetIMG.setPixmap(self.pixmap.scaledToHeight(380))
            except FileNotFoundError as e2:
                print(f'File not found, {e}')

    def FilterLibraryList(self):
        filter_text = self.serachLibraryField.text()

        self.currentLibraryList.clear()
        for f in self.opennamelist:
            if filter_text.lower() in f.lower():
                QListWidgetItem(f, self.currentLibraryList)


    def ImportDropList(self):
        print('Importing... \n')

        a = self.impblank.text()
        if not a:
            return
        self.impblank.setText('')
        self.widgetList.clear()
        self.idxmax = 0

        
        self.cardsList = Collector.collect(a)
        if self.cardsList == 'Error':
            self.widgetIMG.setPixmap(QPixmap(resource_path('assets/error_card.png')))
            return
        self.widgetList.addItems(self.cardsList)

        self.progressBar.show()
        self.completed = 0
        
        self.enableWidgets(allb=1)
        self.widgetList.currentIndexChanged.connect(self.display)

        self.dic = {}
        for n, karta in enumerate(self.cardsList):
            self.dic[n] = karta
        self.idx_max = len(self.dic) - 1
        

        self.expectedDicLen = len(self.dic)
        print('expected url count:', self.expectedDicLen)
        for i in range(len(self.dic)):
            print(f'starting thread {i}/{self.expectedDicLen}')
             
            self.threadx = QThread(self)
            self.threadx.start()

            self.cacherx = Cacher()
            self.cacherx.moveToThread(self.threadx)
            self.cacherx.resultsChanged2.connect(self.on_cacheChanged)

            data = (i+1, self.dic[i])
            wrapper = partial(self.cacherx.cache, data)
            QTimer.singleShot(0, wrapper)

    def NameInput(self):
        a = self.nameline.text()
        index = self.widgetList.currentIndex()
        indexmax = self.idx_max

        if not a:
            pass
        else:
            typo = self.cardtype.currentText()
            name = a
            url = self.widgetList.currentText()

            manacost = self.manacostline.text()
            color = self.colorline.text()
            rarity = self.cardrarity.currentText()

            pathh = self.syspath
            filenam = self.filename

            # удаление старой версии карты из коллекции.xml при дублировании
            print(f'scanning through {self.currentLibraryList.count()} cards')
            for x in range(self.currentLibraryList.count()):
                print('searching for:', a, 'current: ', self.currentLibraryList.item(x).text(), 'iteration:', x)
                
                if self.currentLibraryList.item(x).text() == a:

                    print('Replacing old entry..')
                    Collector.delete_entry(name, self.syspath, self.filename)
                    self.DeckListRefresh()
                    self.FilterLibraryList()
                    self.removeEntry(x)

                    break
                    
            

            # запись карты в коллекцию
            filo = Card(name, url, typo, manacost, color, rarity, pathh, filenam)
            filo.open()
            filo.enter()
            filo.write()

            # кеширование картинок в pics

            key = self.widgetList.currentIndex() + 1
            pic = self.picByteDict[key]

            try:
                path_typo = 'TK' if typo == 'Token' else 'HT'
                dlPath = str(os.path.dirname(os.path.dirname(self.syspath))) + f'/pics/downloadedPics/{path_typo}'
                with open(f'{dlPath}/{name}.png', 'wb') as c:
                    c.write(pic)
            except FileNotFoundError:
                print('Error: could not download image into', f'{dlPath}/{name}.png')

           
            self.nameline.setText('')
            self.manacostline.setText('')
            self.colorline.setText('')
            self.DeckListRefresh()
            if index != indexmax:
                self.widgetList.setCurrentIndex(index+1)
            else:
                pass
       

    def DeckListRefresh(self):

        self.currentLibraryList.clear()
        self.opennamelist = Collector.scan_xml(self.syspath, self.filename)[0]
        self.currentLibraryList.addItems(self.opennamelist)


    def removeEntry(self, specific = None):
        if not self.currentLibraryList:
            return
        # удаление кешированной картинки из pics
        try:
            delPath = str(os.path.dirname(os.path.dirname(self.syspath))) + f'/pics/downloadedPics/HT/{self.currentLibraryList.currentItem().text()}.png'
            os.remove(delPath)
            print('deleteing', delPath)
        except (OSError, AttributeError):
            try:
                delPath = str(os.path.dirname(os.path.dirname(self.syspath))) + f'/pics/downloadedPics/TK/{self.currentLibraryList.currentItem().text()}.png'
                os.remove(delPath)
                print('deleteing', delPath)
            except (OSError, AttributeError):
                print('ERROR: could not remove cached image')

        # удаление записи из коллекции.xml
        idx = self.currentLibraryList.currentRow() if not specific else specific
        try:
            name = self.currentLibraryList.currentItem().text()
        except AttributeError as e:
            print('removeEntry() exception AttributeError: ', e)
            return
        Collector.delete_entry(name, self.syspath, self.filename)
        self.currentLibraryList.takeItem(idx)
        self.DeckListRefresh()
        self.FilterLibraryList()


        print(f'removing entry {name} by idx {idx}')

        

    def showdialog(self):

        fname = QFileDialog.getOpenFileName(self, 'Open XML')[0]
        if fname == '':
            return
        a = fname.split('/')
        name = a[-1]

        self.syspath = ''
        for x in a[:-1]:
            self.syspath += x + '/'
        self.filename = name

        self.DeckListRefresh()
        self.enableWidgets()
    
    def showdialog2(self):
        dirbr = QFileDialog.getExistingDirectory(self, "Select Folder")
        path = str(dirbr)
        name = self.filename
        if not path:
            return
        
        i, okPressed = QInputDialog.getText(self, "File name","Custom set name:")
        if okPressed:
            name = i + '.xml'
        else:
            return
        
        b = open(path + '/' + name, 'w')
        b.write('<cockatrice_carddatabase version="3">\n\t<cards>\n\t</cards>\n</cockatrice_carddatabase>')
        b.close

        self.syspath = path + '/'
        self.filename = name
        self.enableWidgets()

    def enableWidgets(self, allb=0):
        self.impblank.setEnabled(True)
        self.buttonImport.setEnabled(True)
        self.buttonRemove.setEnabled(True)
        self.openDirectory.setEnabled(True)
        self.serachLibraryField.setEnabled(True)
        if allb:
            self.cardtype.setEnabled(True)
            self.cardrarity.setEnabled(True)
            self.manacostline.setEnabled(True)
            self.colorline.setEnabled(True)
            self.nameline.setEnabled(True)
            self.buttonAdd.setEnabled(True)

        

    def showdialog3(self):
        path = os.path.realpath(self.syspath)
        os.startfile(path)

    def showdialog4(self):
        pass





if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
