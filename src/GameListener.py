import os
import time
import re
import random

from Widgets.LibraryView import LibraryView
from PyQt5.QtCore import QThread, pyqtSignal, QObject

class Helpers:
    def __init__(self, library: LibraryView):
        self.library = library

    def select_subcommand(self, input_string: str, subcommand_number: int = 0) -> str:
        if not input_string:
            return None
        
        if not '||' in input_string:
            return input_string
        
        subs = input_string.split('||')
        return subs[subcommand_number]
        
    def process_rnd_with_ids(self, input_string: str) -> str:
        if not input_string:
            return None
        pattern = r'RND\{\s*([\d\s;]+)\s*\}' 
        match = re.search(pattern, input_string)

        if not match:
            return input_string

        content = match.group(1)

        if not re.fullmatch(r'[\d\s;]+', content):
            print("process_rnd_with_ids:: wrong pattern", content)
            return None

        numbers = [int(num) for num in re.findall(r'\d+', content)]

        random_id = random.choice(numbers)

        if not random_id:
            print("process_rnd_with_ids:: random card ID = 0")
            return None

        output_string = re.sub(pattern, str(random_id), input_string)

        return output_string
    
    def process_rnd_with_filters(self, input_string: str) -> str:
        if not input_string:
            return None
        pattern = r'RND\[\s*([^]]+)\s*\]'
        match = re.search(pattern, input_string)

        if not match:
            return input_string

        content = match.group(1)
        filter_words = [word.strip() for word in content.split(';')]

        if len(filter_words) != 6:
            print("process_rnd_with_filters:: filter count mismatch")
            return None
        
        random_id = self.library.get_random_card_by_filter(*filter_words)

        if not random_id:
            print("process_rnd_with_filters:: random card ID = 0")
            return None

        output_string = re.sub(pattern, str(random_id), input_string)

        return output_string
    
    def convert_ids_to_names(self, input_string: str) -> str:
        if not input_string:
            return None
        patterns = input_string.split('&')
        results = []

        for pattern in patterns:
            parts = pattern.split(';')
            
            if len(parts) != 4:
                print("convert_ids_to_names:: invalid format", parts)
                return None
            
            try:
                card_id = int(parts[1])
            except ValueError:
                print("convert_ids_to_names:: is not a proper value", parts[1])
                return None
            
            card_name = self.library.get_card_name_by_id(card_id)
            if not card_name:
                print("convert_ids_to_names:: failed to retrive card name by id", card_id, card_name)
                return None
            parts[1] = card_name
            results.append(';'.join(parts))
        
        return '&'.join(results)
    
    def get_name_and_zone_for_filter_cmd(self, input_string: str) -> str:
        if not input_string:
            return None
        command = input_string.split(';')

        if len(command) != 4:
            print("get_name_only_for_filter_cmd:: invalid format", command)
            return None
        
        card_zone = command[0]
        card_name = command[1]

        if not card_name or not card_zone:
            print("get_name_only_for_filter_cmd:: mismatch", command)
            return None
        
        command = f"{card_zone};{card_name}"

        return command
    
    def final_check(self, input_string: str) -> str:
        if not input_string:
            return None
        if "RND[" in input_string or "RND{" in input_string:
            print("final_check:: mismatch")
            return None
        
        return input_string
    

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
    switch_to_library = pyqtSignal()

    def __init__(self, library: LibraryView, parent=None) -> None:
        super().__init__(parent)
        self.worker = Worker()
        self.library = library
        self.helpers = Helpers(self.library)

        self.worker.game_request_accepted.connect(self.parse_request)
        self.worker.start()
        
    def parse_request(self, message: str):
        self.switch_to_library.emit()
        command = ""
        if "Activate:" in message:
            card_name = message.split("Activate:")[1]
            card_command = self.library.get_card_command_by_name(card_name)
            if card_command:
                command = self.process_activation_comand(card_command, 0)
        if "ActivateSub:" in message:
            card_name = message.split("ActivateSub:")[1]
            card_command = self.library.get_card_command_by_name(card_name)
            if card_command:
                command = self.process_activation_comand(card_command, 1)
        if "Filter:" in message:
            filters = message.split("Filter:")[1]
            if filters:
                command = self.process_filter_command(filters)

        if not command:
            return
        
        self.respond(command)

    def respond(self, response: str):
        with open(self.worker.response_file, "w") as file:
            file.write(response)

    def process_activation_comand(self, command: str, subcommand_number: int = 0) -> str:
        """
        Activation command examples:
        1) hand,5,1,0&table,6,2,0                           - Adds token #5 into hand and summons two tokens #6 on the field
        2) hand,RND{5,6,7},2,0                              - Randomly chooses one of #5 #6 #7 tokens and adds two copies into hand
        3) hand,RND[minion,mage,5,mech,legendary,1],1,0     - Add a random 5-cost legendary mage mech minion into hand (1=standard only)
        4) hand,RND[any,any,5,any,any,0],1,0                - Add a random 5-cost card into your hand (0=custom only)
        5) hand,5,1,0&table,6,2,0||table,7,1,0              - Activation command 1 or Activation command 2
        
        Command then gets converted and sent into Cockatrice client as:
        hand,Murasame,1,0
        """
        command = self.helpers.select_subcommand(command, subcommand_number)
        command = self.helpers.process_rnd_with_ids(command)
        command = self.helpers.process_rnd_with_filters(command)
        command = self.helpers.convert_ids_to_names(command)
        command = self.helpers.final_check(command)

        print(f"Activation command: {command}")
        return command

    def process_filter_command(self, command: str) -> str:
        """
        Activation command examples:
        1) hand,RND[any,any,5,any,any,0],1,0                - Add a random 5-cost card into your hand (0=custom only)
        """
        command = self.helpers.process_rnd_with_filters(command)
        command = self.helpers.convert_ids_to_names(command)
        command = self.helpers.get_name_and_zone_for_filter_cmd(command)

        print(f"Filter command: {command}")
        return command