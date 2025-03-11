import os
import time
from PyQt5.QtCore import QThread, pyqtSignal, QObject

class Worker(QThread):
    card_from_library_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_path = os.path.join(os.getenv("LOCALAPPDATA"), "Hearthtrice")
        self.request_file = os.path.join(self.base_path, "request.txt")
        self.response_file = os.path.join(self.base_path, "response.txt")
        self._running = True

    def run(self):
        while self._running:
            os.makedirs(self.base_path, exist_ok=True)

            while self._running and not os.path.exists(self.request_file):
                time.sleep(0.2)

            if not self._running:
                break

            with open(self.request_file, "r") as file:
                message = file.read().strip()
                self.parse_request(message) 
            os.remove(self.request_file)

    def stop(self):
        self._running = False
        self.quit()
        self.wait()

    def parse_request(self, message: str):
        """Пример парсинга запроса"""
        if "Activate:" in message:
            card_name = message.split("Activate:")[1].strip()
            self.card_from_library_requested.emit(card_name)
        return None


class GameListener(QObject):
    card_from_library_requested = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self.worker = Worker()

        self.worker.card_from_library_requested.connect(self.card_from_library_requested)
        self.worker.start()

    def respond(self, response: str):
        with open(self.worker.response_file, "w") as file:
            file.write(response)

    def stop(self):
        self.worker.stop()


# & 
# || дополнительная команда

# RND{5,2,7}x1 - рандом между опредленными ID

# RND[class,type,mana,tribe,rarity]x1 - рандом по фильтру
# RND[mage,minion,5,mech,legendary]x1
# RND[any,any,2,any,any]x1

# Команда:
# zone,card_id,count,face_down||...
# hand,27,2,0