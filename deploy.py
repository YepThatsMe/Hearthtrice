import os
import json
import hashlib
import subprocess
import tarfile
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from src.main import VERSION_MAJOR, VERSION_MINOR
import credentials

LAUNCHER_EXE_NAME = "HearthtriceLauncher.exe"
LAUNCHER_VERSION_JSON = "launcher_version.json"

def calculate_file_hash(file_path: str, hash_algorithm="sha256") -> str:
    """Вычисляет хеш файла."""
    hasher = hashlib.new(hash_algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_version_json(directory: str, output_file: str) -> None:
    """
    Генерирует JSON с хешами всех файлов в директории.
    Формат:
    {
      "version": "1.0",
      "files": {
        "file1.exe": "a1b2c3...",
        "subdir/file2.dll": "d4e5f6..."
      }
    }
    """
    version_data = {
        "version": f"{VERSION_MAJOR}.{VERSION_MINOR}",
        "files": {}
    }

    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, directory)
            rel_path = rel_path.replace("\\", "/")
            file_hash = calculate_file_hash(file_path)
            version_data["files"][rel_path] = file_hash

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(version_data, f, indent=4, ensure_ascii=False)

    print(f"Хэш успешно записан в {output_file}")

def remote_prepare_build(remote_user, remote_host):
    ssh_cmd = [
        "ssh",
        f"{remote_user}@{remote_host}",
        "rm -rf ~/hearth-build/*"
    ]
    subprocess.run(ssh_cmd, check=True)

def remote_clean_app(remote_user, remote_host, app_name, version_file):
    ssh_cmd = [
        "ssh",
        f"{remote_user}@{remote_host}",
        f"rm -rf ~/hearth-build/{app_name} ~/hearth-build/{version_file}"
    ]
    subprocess.run(ssh_cmd, check=True)

def scp_deploy(source_dir, arcname, version_json, remote_user="user", remote_host="host"):
    """
    Архивирует всю папку source_dir в tar.gz (arcname - имя подпапки), отправляет архив и version.json на сервер,
    распаковывает архив в ~/hearth-build/, очищает временные файлы.
    """
    if not os.path.exists(source_dir):
        print(f"Папка {source_dir} не найдена!")
        sys.exit(1)

    archive_name = f"{arcname}.tar.gz"
    archive_path = os.path.join(ROOT, "dist", archive_name)

    print(f"Создание архива {archive_name}...")
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(source_dir, arcname=arcname)

    scp_tar_cmd = [
        "scp",
        archive_path,
        f"{remote_user}@{remote_host}:~/hearth-build/"
    ]
    subprocess.run(scp_tar_cmd, check=True)

    ssh_untar_cmd = [
        "ssh",
        f"{remote_user}@{remote_host}",
        f"tar -xzf ~/hearth-build/{archive_name} -C ~/hearth-build/"
    ]
    subprocess.run(ssh_untar_cmd, check=True)

    ssh_rm_tar_cmd = [
        "ssh",
        f"{remote_user}@{remote_host}",
        f"rm ~/hearth-build/{archive_name}"
    ]
    subprocess.run(ssh_rm_tar_cmd, check=True)

    if os.path.exists(version_json):
        scp_json_cmd = [
            "scp",
            version_json,
            f"{remote_user}@{remote_host}:~/hearth-build/"
        ]
        subprocess.run(scp_json_cmd, check=True)
        os.remove(version_json)
    else:
        print(f"Файл {version_json} не найден")

    if os.path.exists(archive_path):
        os.remove(archive_path)

    print(f"Done: {arcname}")

if __name__ == "__main__":
    REMOTE_USER = "root"
    REMOTE_HOST = credentials.IP

    print("[1] - только Hearthtrice")
    print("[2] - только Cockatrice")
    print("[3] - только Launcher")
    print("[4] - всё")

    while True:
        choice = input("Введите номер (1, 2, 3 или 4): ").strip()
        if choice in ['1', '2', '3', '4']:
            break
        print("Неверный ввод. Введите 1, 2, 3 или 4.")

    if choice == '4':
        remote_prepare_build(REMOTE_USER, REMOTE_HOST)
    elif choice == '1':
        remote_clean_app(REMOTE_USER, REMOTE_HOST, "Hearthtrice", "version.json")
    elif choice == '2':
        remote_clean_app(REMOTE_USER, REMOTE_HOST, "Cockatrice", "version_cockatrice.json")
    elif choice == '3':
        remote_clean_app(REMOTE_USER, REMOTE_HOST, "Launcher", LAUNCHER_VERSION_JSON)

    if choice in ['1', '4']:
        SOURCE_DIR_1 = os.path.join(ROOT, "dist", "HearthTrice")
        VERSION_JSON_1 = os.path.join(ROOT, "dist", "version.json")
        generate_version_json(SOURCE_DIR_1, VERSION_JSON_1)
        scp_deploy(SOURCE_DIR_1, "Hearthtrice", VERSION_JSON_1, REMOTE_USER, REMOTE_HOST)

    if choice in ['2', '4']:
        SOURCE_DIR_2 = os.path.join(ROOT, "dist", "Cockatrice")
        VERSION_JSON_2 = os.path.join(ROOT, "dist", "version_cockatrice.json")
        generate_version_json(SOURCE_DIR_2, VERSION_JSON_2)
        scp_deploy(SOURCE_DIR_2, "Cockatrice", VERSION_JSON_2, REMOTE_USER, REMOTE_HOST)

    if choice in ['3', '4']:
        launcher_exe = os.path.join(ROOT, "dist", LAUNCHER_EXE_NAME)
        if not os.path.exists(launcher_exe):
            print(f"Соберите лаунчер: {launcher_exe} не найден")
        else:
            launcher_dir = os.path.join(ROOT, "dist", "Launcher")
            os.makedirs(launcher_dir, exist_ok=True)
            dest_exe = os.path.join(launcher_dir, LAUNCHER_EXE_NAME)
            if dest_exe != launcher_exe:
                shutil.copy2(launcher_exe, dest_exe)
            VERSION_JSON_LAUNCHER = os.path.join(ROOT, "dist", LAUNCHER_VERSION_JSON)
            generate_version_json(launcher_dir, VERSION_JSON_LAUNCHER)
            scp_deploy(launcher_dir, "Launcher", VERSION_JSON_LAUNCHER, REMOTE_USER, REMOTE_HOST)
