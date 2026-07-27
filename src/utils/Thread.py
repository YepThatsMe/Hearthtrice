from PyQt5.QtCore import QThread, pyqtSignal, QLockFile
from DataTypes import Response


def send_to_thread(parent, func, handler=None, args=None, kwargs=None):
    thread = Thread(func, args, kwargs, parent)
    if handler:
        thread.finished.connect(handler)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread


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


class CardsDownloadThread(QThread):
    progress = pyqtSignal(int, int, object)
    finished_ok = pyqtSignal(object)

    def __init__(self, fetch_fn, ids, parent=None):
        super().__init__(parent)
        self.fetch_fn = fetch_fn
        self.ids = list(ids or [])

    def run(self):
        result = []
        total = len(self.ids)
        try:
            for i, card_id in enumerate(self.ids):
                self.progress.emit(i + 1, total, card_id)
                cards = self.fetch_fn([card_id])
                if cards:
                    result.extend(cards)
            self.finished_ok.emit(result)
        except Exception as e:
            self.finished_ok.emit(Response(False, str(e)))
        finally:
            self.quit()
