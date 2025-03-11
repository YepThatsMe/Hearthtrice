import os
import time
import re

from src.Widgets.LibraryView import LibraryView
from PyQt5.QtCore import QThread, pyqtSignal, QObject

class Worker(QThread):
    game_request_accepted = pyqtSignal(object)

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
                self.game_request_accepted.emit(message)
            os.remove(self.request_file)

    def stop(self):
        self._running = False
        self.quit()
        self.wait()

class GameListener(QObject):
    card_command_requested = pyqtSignal(object)

    def __init__(self, library: LibraryView, parent=None) -> None:
        super().__init__(parent)
        self.worker = Worker()
        self.library = library

        self.worker.game_request_accepted.connect(self.parse_request)
        self.worker.start()
        
    def parse_request(self, message: str):
        """Пример парсинга запроса"""
        if "Activate:" in message:
            card_name = message.split("Activate:")[1]
            card_command = self.library.get_card_command_by_name(card_name)

        return None

    def respond(self, response: str):
        with open(self.worker.response_file, "w") as file:
            file.write(response)

    def stop(self):
        self.worker.stop()


    def process_comand(self, command: str) -> str:
        def process_rnd_with_ids(input_string: str) -> str:
            pattern = r'RND\{\s*([\d\s,]+)\s*\}' 
            match = re.search(pattern, input_string)

            if not match:
                return input_string

            content = match.group(1)

            if not re.fullmatch(r'[\d\s,]+', content):
                print("process_rnd_with_ids:: wrong pattern", content)
                return None

            numbers = [int(num) for num in re.findall(r'\d+', content)]

            random_id = self.library.get_random_card_among_ids(numbers)

            if not random_id:
                print("process_rnd_with_ids:: random card ID = 0")
                return None

            output_string = re.sub(pattern, str(random_id), input_string)

            return output_string
        
        def process_rnd_with_filters(input_string: str) -> str:
            pattern = r'RND\[\s*([^]]+)\s*\]'
            match = re.search(pattern, input_string)

            if not match:
                return input_string

            content = match.group(1)
            filter_words = [word.strip() for word in content.split(',')]

            if len(filter_words) != 6:
                print("process_rnd_with_filters:: filter count mismatch")
                return None
            
            random_id = self.library.get_random_card_by_filter(*filter_words)

            if not random_id:
                print("process_rnd_with_filters:: random card ID = 0")
                return None

            output_string = re.sub(pattern, str(random_id), input_string)

            return output_string
        
        def convert_ids_to_names(self, command: str) -> str:
            pass
        
        def final_check(input_string: str) -> str:
            if "RND[" in input_string or "RND{" in input_string:
                print("final_check:: mismatch")
                return None
            
        command = process_rnd_with_ids(command)
        if command: command = process_rnd_with_filters(command)
        if command: command = final_check(command)

        print(command)

# & 
# || дополнительная команда

# RND{5,2,7}x1 - рандом между опредленными ID

# RND[type,class,mana,tribe,rarity,std_only]x1 - рандом по фильтру
# RND[minion,mage,5,mech,legendary,1]x1
# RND[any,any,2,any,any]x1

# Команда:
# zone,card_id,count,face_down||...
# hand,27,2,0