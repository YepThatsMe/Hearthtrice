import re

def sanitize(filename: str, replacement: str = "") -> str:
    """
    Очищает строку от символов, запрещённых в названиях файлов.
    
    :param filename: Исходное имя файла.
    :param replacement: Символ, на который будут заменены запрещённые символы.
    :return: Очищенное имя файла.
    """
    # Запрещённые символы для Windows
    forbidden_chars = r'[<>:"/\\|?*]'
    
    # Замена запрещённых символов
    return re.sub(forbidden_chars, replacement, filename)

if __name__ == "__main__":
    print(sanitize("Problem?!!:"))