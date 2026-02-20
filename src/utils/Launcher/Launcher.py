import os
import hashlib
import requests
from pathlib import Path
import time
import sys
import subprocess

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
LAUNCHER_EXE_NAME = "HearthtriceLauncher.exe"
LAUNCHER_VERSION_JSON = "launcher_version.json"
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
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

def check_launcher_update():
    """Если есть новая версия лаунчера на сервере — скачивает, запускает bat-апдейтер и выходит."""
    if not getattr(sys, "frozen", False):
        return
    try:
        response = requests.get(f"{SERVER_URL}/{LAUNCHER_VERSION_JSON}", timeout=10)
        response.raise_for_status()
        server_data = response.json()
    except Exception:
        return
    files = server_data.get("files", {})
    server_hash = files.get(LAUNCHER_EXE_NAME)
    if not server_hash:
        return
    current_exe = Path(sys.executable)
    if current_exe.name != LAUNCHER_EXE_NAME:
        return
    local_hash = get_file_hash(current_exe)
    if local_hash == server_hash:
        return
    new_exe_path = BASE_DIR / "HearthtriceLauncher_new.exe"
    try:
        download_file(f"{SERVER_URL}/Launcher/{LAUNCHER_EXE_NAME}", new_exe_path)
    except Exception:
        return
    bat = BASE_DIR / "launcher_updater.bat"
    bat.write_text(
        "@echo off\n"
        ":wait\n"
        "tasklist /FI \"IMAGENAME eq " + LAUNCHER_EXE_NAME + "\" 2>NUL | find /I \"" + LAUNCHER_EXE_NAME + "\" >NUL\n"
        "if not errorlevel 1 (timeout /t 1 /nobreak >NUL & goto wait)\n"
        "move /Y \"HearthtriceLauncher_new.exe\" \"" + LAUNCHER_EXE_NAME + "\"\n"
        "start \"\" \"" + LAUNCHER_EXE_NAME + "\"\n"
        "del \"%~f0\"\n",
        encoding="utf-8"
    )
    creationflags = 0x08000000 if sys.platform == "win32" else 0
    subprocess.Popen(
        [str(bat)],
        cwd=str(BASE_DIR),
        creationflags=creationflags
    )
    sys.exit(0)

def check_updates():
    """Сравнивает файлы с сервером и качает обновления для всех приложений."""
    check_launcher_update()
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
        subprocess.Popen([str(exe_path)], cwd=str(BASE_DIR / "Hearthtrice"))
        time.sleep(5)
    except Exception as e:
        print(f"Не удалось запустить Hearthtrice.exe: {e}")
        os.system('pause')

if __name__ == "__main__":
    check_updates()
