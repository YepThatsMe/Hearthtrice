from Hearthtrice.Hearthtrice import MainWindow
import Hearthtrice

class IM(Hearthtrice.MainWindow, QMainWindow):


    def rofl():

        with open(resource_path('assets\how_to_use.txt'), 'r') as b:
                text = b.read()
        a = QMessageBox.about(self, 'Help', text)

    