import os
import hashlib
import requests
from pathlib import Path
import time
import sys

# Импорт credentials в зависимости от режима запуска
if getattr(sys, 'frozen', False):
    # Если запущено из exe - credentials встроен в exe
    import credentials
else:
    # Если запущено как скрипт - добавляем путь к корню проекта
    script_root = Path(__file__).resolve().parents[3]
    sys.path.append(str(script_root))
    import credentials

# Конфигурация
SERVER_URL = f"http://{credentials.IP}:{credentials.UPDATER_PORT}"
if getattr(sys, 'frozen', False):
    # Если запущено из exe
    BASE_DIR = Path(sys.executable).parent
else:
    # Если запущено как скрипт
    BASE_DIR = Path(__file__).parent
LOCAL_DIR = BASE_DIR / "Hearthtrice"

APPS = [
    {
        "name": "Hearthtrice",
        "version_json": "version.json",
        "exe": "Hearthtrice.exe"
    },
    {
        "name": "Cockatrice",
        "version_json": "version_cockatrice.json",
        "exe": "Cockatrice.exe"
    }
]

def get_file_hash(file_path: Path) -> str:
    """Вычисляет SHA-256 хеш файла (если файл существует)."""
    if not file_path.exists():
        return ""  # Файла нет — хеш пустой
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_file(url: str, save_path: Path):
    """Скачивает файл с сервера, создавая папки при необходимости, с прогресс-баром."""
    save_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total = int(response.headers.get('content-length', 0))
    downloaded = 0
    chunk_size = 4096
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    percent = downloaded * 100 // total
                    bar = ('#' * (percent // 2)).ljust(50)
                    print(f"\rЗагрузка {save_path.name}: [{bar}] {percent}%", end='', flush=True)
    
    print(f"\r")

def check_updates():
    """Сравнивает файлы с сервером и качает обновления для всех приложений."""
    had_error = False
    for app in APPS:
        app_dir = BASE_DIR / app["name"]
        try:
            # 1. Получаем список файлов и их хеши с сервера
            response = requests.get(f"{SERVER_URL}/{app['version_json']}")
            response.raise_for_status()
            server_data = response.json()

            # Выводим номер версии на сервере, если есть
            if 'version' in server_data and app['name'] == 'Hearthtrice':
                print(f"{app['name']}: версия на сервере {server_data['version']}\n")

            # 2. Проверяем каждый файл
            for filename, server_hash in server_data["files"].items():
                local_path = app_dir / filename
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_hash = get_file_hash(local_path)
                # Если файла нет или хеш не совпадает — качаем
                if not local_hash or local_hash != server_hash:
                    download_file(f"{SERVER_URL}/{app['name']}/{filename}", local_path)

        except requests.exceptions.RequestException as e:
            print(f"Ошибка подключения к серверу для {app['name']}: {e}")
            os.system('pause')
            had_error = True
        except Exception as e:
            print(f"Ошибка для {app['name']}: {e}")
            os.system('pause')
            had_error = True

    if not had_error:
        print("\nПроверка обновлений завершена.")

    print("┌─────────────────────────────────────┐")
    print("│         Запуск Hearthtrice...       │")
    print("└─────────────────────────────────────┘")
    exe_path = (BASE_DIR / "Hearthtrice" / "Hearthtrice.exe")
    try:
        import subprocess
        subprocess.Popen([str(exe_path)], cwd=str(BASE_DIR / "Hearthtrice"))
        time.sleep(5)
    except Exception as e:
        print(f"Не удалось запустить Hearthtrice.exe: {e}")
        os.system('pause')

if __name__ == "__main__":
    check_updates()
