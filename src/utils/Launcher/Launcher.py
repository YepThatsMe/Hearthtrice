import os
import json
import hashlib
import requests
from pathlib import Path
import time
import sys
import subprocess

LAUNCHER_DIR = Path(__file__).resolve().parent
SCRIPT_ROOT = Path(__file__).resolve().parents[3]

if getattr(sys, 'frozen', False):
    import credentials
    BASE_DIR = Path(sys.executable).parent
else:
    sys.path.append(str(SCRIPT_ROOT))
    import credentials
    BASE_DIR = SCRIPT_ROOT / "dist"

LAUNCHER_EXE_NAME = "HearthtriceLauncher.exe"
LAUNCHER_MANIFEST_NAME = "launcher_version.json"
MANIFEST_DIR_NAME = "launcher"

APPS = [
    {
        "name": "Hearthtrice",
        "manifest": "version.json",
        "exe": "Hearthtrice.exe"
    },
    {
        "name": "Cockatrice",
        "manifest": "version_cockatrice.json",
        "exe": "Cockatrice.exe"
    }
]

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
GRAY = "\033[90m"


def enable_ansi():
    if sys.platform == "win32":
        try:
            import ctypes
            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass


def log_step(msg):
    print(f"{CYAN}[*]{RESET} {msg}", flush=True)


def log_ok(msg):
    print(f"{GREEN}[+]{RESET} {msg}", flush=True)


def log_warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}", flush=True)


def log_err(msg):
    print(f"{RED}[-]{RESET} {msg}", flush=True)


def get_server_url(ip, port):
    return f"http://{ip}:{port}"


def ping_server(ip):
    log_step(f"Ping сервера {ip}...")
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "3000", ip],
            capture_output=True,
            text=True,
            creationflags=0x08000000 if sys.platform == "win32" else 0,
        )
        if result.returncode == 0:
            log_ok(f"Сервер {ip} отвечает на ping")
            return True
        log_warn(f"Сервер {ip} не отвечает на ping")
        return False
    except Exception as e:
        log_warn(f"Не удалось выполнить ping: {e}")
        return False


def test_server_connection(server_url):
    log_step(f"Проверка сервера обновлений {server_url}...")
    try:
        response = requests.get(f"{server_url}/{LAUNCHER_MANIFEST_NAME}", timeout=10)
        response.raise_for_status()
        log_ok("Сервер обновлений доступен")
        return True
    except Exception as e:
        log_err(f"Сервер обновлений недоступен: {e}")
        return False


def prompt_new_server(current_ip, current_port):
    print()
    log_warn("Не удалось подключиться к серверу обновлений.")
    print(f"{GRAY}Введите новые данные сервера.{RESET}")
    ip = input(f"IP сервера [{current_ip}]: ").strip()
    if not ip:
        ip = current_ip
    port = input(f"Порт обновлений [{current_port}]: ").strip()
    if not port:
        port = current_port
    return ip, port


def resolve_server_url():
    ip = credentials.IP
    port = str(credentials.UPDATER_PORT)
    server_url = get_server_url(ip, port)

    log_step("Запуск Hearthtrice Launcher")
    log_step(f"Сервер: {ip}:{port}")

    ping_ok = ping_server(ip)

    if test_server_connection(server_url):
        return server_url, ip, port

    if ping_ok:
        log_warn("Ping проходит, но сервер обновлений не отвечает")
    else:
        log_warn("Сервер недоступен, возможно изменился адрес")

    while True:
        ip, port = prompt_new_server(ip, port)
        server_url = get_server_url(ip, port)
        ping_server(ip)
        if test_server_connection(server_url):
            return server_url, ip, port
        log_err("Подключение не удалось, проверьте данные и попробуйте снова")


def get_manifest_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Hearthtrice" / MANIFEST_DIR_NAME
    return BASE_DIR / MANIFEST_DIR_NAME


def get_app_manifest_path(app_name: str) -> Path:
    return get_manifest_dir() / f"{app_name.lower()}.manifest.json"


def get_launcher_manifest_path() -> Path:
    return get_manifest_dir() / "launcher.manifest.json"


def migrate_legacy_manifest(new_path: Path, legacy_path: Path):
    if new_path.exists() or not legacy_path.exists():
        return
    try:
        data = json.loads(legacy_path.read_text(encoding="utf-8"))
        save_manifest(new_path, data)
        legacy_path.unlink()
    except Exception:
        pass


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_manifest(path: Path, manifest: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_manifest(server_url: str, manifest_name: str) -> dict:
    response = requests.get(f"{server_url}/{manifest_name}", timeout=30)
    response.raise_for_status()
    return response.json()


def manifests_match(server_manifest: dict, local_manifest: dict) -> bool:
    server_hash = server_manifest.get("manifest_hash")
    local_hash = local_manifest.get("manifest_hash")
    if server_hash and local_hash:
        return server_hash == local_hash
    return server_manifest.get("files") == local_manifest.get("files")


def manifest_files_present(manifest: dict, base_dir: Path) -> bool:
    for rel_path in manifest.get("files", {}):
        if not (base_dir / rel_path).exists():
            return False
    return True


def file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_file(url: str, save_path: Path):
    """Скачивает файл с сервера, создавая папки при необходимости, с прогресс-баром."""
    save_path.parent.mkdir(parents=True, exist_ok=True)
    log_step(f"Загрузка {save_path.name}...")
    response = requests.get(url, stream=True, timeout=60)
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
                    print(f"\r{CYAN}[*]{RESET} {save_path.name}: [{bar}] {percent}%", end='', flush=True)
    print(flush=True)
    log_ok(f"Загружено: {save_path.name}")


def sync_from_manifest(server_url: str, app_name: str, manifest_name: str, app_dir: Path):
    server_manifest = fetch_manifest(server_url, manifest_name)
    manifest_path = get_app_manifest_path(app_name)
    migrate_legacy_manifest(manifest_path, app_dir / ".manifest.json")
    local_manifest = load_manifest(manifest_path)

    if app_name == "Hearthtrice" and "version" in server_manifest:
        log_ok(f"{app_name}: версия на сервере {server_manifest['version']}")

    if not local_manifest and manifest_files_present(server_manifest, app_dir):
        save_manifest(manifest_path, server_manifest)
        log_ok(f"{app_name}: актуально")
        return

    if manifests_match(server_manifest, local_manifest) and manifest_files_present(server_manifest, app_dir):
        log_ok(f"{app_name}: актуально")
        return

    server_files = server_manifest.get("files", {})
    local_files = local_manifest.get("files", {})
    for rel_path, server_hash in server_files.items():
        local_path = app_dir / rel_path
        if local_files.get(rel_path) == server_hash and local_path.exists():
            continue
        download_file(f"{server_url}/{app_name}/{rel_path}", local_path)

    save_manifest(manifest_path, server_manifest)


def check_launcher_update(server_url):
    """Если есть новая версия лаунчера на сервере — скачивает, запускает bat-апдейтер и выходит."""
    if not getattr(sys, "frozen", False):
        log_step("Режим скрипта, пропуск самообновления лаунчера")
        return
    log_step("Проверка обновления лаунчера...")
    try:
        server_manifest = fetch_manifest(server_url, LAUNCHER_MANIFEST_NAME)
    except Exception as e:
        log_warn(f"Не удалось проверить версию лаунчера: {e}")
        return

    manifest_path = get_launcher_manifest_path()
    migrate_legacy_manifest(manifest_path, BASE_DIR / ".launcher_manifest.json")
    local_manifest = load_manifest(manifest_path)
    launcher_path = Path(sys.executable)
    if launcher_path.name != LAUNCHER_EXE_NAME:
        return

    if not local_manifest and launcher_path.exists():
        server_hash = server_manifest.get("files", {}).get(LAUNCHER_EXE_NAME)
        if server_hash and file_sha256(launcher_path) == server_hash:
            save_manifest(manifest_path, server_manifest)
            log_ok("Лаунчер актуален")
            return

    if manifests_match(server_manifest, local_manifest) and launcher_path.exists():
        log_ok("Лаунчер актуален")
        return

    log_warn("Доступна новая версия лаунчера, загрузка...")
    new_exe_path = BASE_DIR / "HearthtriceLauncher_new.exe"
    try:
        download_file(f"{server_url}/Launcher/{LAUNCHER_EXE_NAME}", new_exe_path)
    except Exception as e:
        log_err(f"Не удалось скачать новый лаунчер: {e}")
        return

    save_manifest(manifest_path, server_manifest)
    log_step("Запуск обновления лаунчера...")
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
    log_ok("Лаунчер будет перезапущен после обновления")
    sys.exit(0)


def check_updates():
    """Сравнивает манифесты с сервером и качает обновления для всех приложений."""
    enable_ansi()
    if not getattr(sys, "frozen", False):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        os.chdir(BASE_DIR)
        log_step(f"Режим скрипта, папка обновлений: {BASE_DIR}")
    server_url, ip, port = resolve_server_url()
    check_launcher_update(server_url)
    had_error = False
    for app in APPS:
        app_dir = BASE_DIR / app["name"]
        log_step(f"Проверка манифеста {app['name']}...")
        try:
            sync_from_manifest(server_url, app["name"], app["manifest"], app_dir)
        except requests.exceptions.RequestException as e:
            log_err(f"Ошибка подключения к серверу для {app['name']}: {e}")
            os.system('pause')
            had_error = True
        except Exception as e:
            log_err(f"Ошибка для {app['name']}: {e}")
            os.system('pause')
            had_error = True

    if not had_error:
        log_ok("Проверка обновлений завершена")

    print("┌─────────────────────────────────────┐")
    print("│         Запуск Hearthtrice...       │")
    print("└─────────────────────────────────────┘")
    exe_path = BASE_DIR / "Hearthtrice" / "Hearthtrice.exe"
    if not exe_path.exists():
        log_err(f"Файл не найден: {exe_path}")
        os.system('pause')
        return
    try:
        subprocess.Popen([str(exe_path)], cwd=str(BASE_DIR / "Hearthtrice"))
        time.sleep(5)
    except Exception as e:
        log_err(f"Не удалось запустить Hearthtrice.exe: {e}")
        os.system('pause')


if __name__ == "__main__":
    check_updates()
