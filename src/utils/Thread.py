from PyQt5.QtCore import QThread, pyqtSignal, QLockFile
from DataTypes import Response


def send_to_thread(parent, func, handler=None, args=None, kwargs=None):
    thread = Thread(func, args, kwargs, parent)
    if handler:
        thread.finished.connect(handler)
    thread.finished.connect(thread.deleteLater)
    thread.start()


class Thread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, func, args=None, kwargs=None, parent=None):
        super().__init__(parent)
        self.to_run = func
        self.args = args if args else []
        self.kwargs = kwargs if kwargs else {}

    def run(self):
        try:
            data = self.to_run(*self.args, **self.kwargs)
            self.finished.emit(data)
        except Exception as e:
            error_msg = f"Ошибка: {str(e)}"
            self.finished.emit(Response(False, error_msg))
        finally:
            self.quit()