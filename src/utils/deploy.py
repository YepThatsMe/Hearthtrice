import os
import json
import hashlib
import subprocess
import tarfile
import sys

# Добавляем корневую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.main import VERSION_MAJOR, VERSION_MINOR
import credentials

def calculate_file_hash(file_path: str, hash_algorithm="sha256") -> str:
    """Вычисляет хеш файла."""
    hasher = hashlib.new(hash_algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_version_json(directory: str, output_file="dist/version.json") -> None:
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
        "version": f"{VERSION_MAJOR}.{VERSION_MINOR}",  # Замените на актуальную версию
        "files": {}
    }

    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            
            # Относительный путь (для сохранения в JSON)
            rel_path = os.path.relpath(file_path, directory)
            
            # Замена разделителей путей на / (для кроссплатформенности)
            rel_path = rel_path.replace("\\", "/")
            
            # Вычисляем хеш
            file_hash = calculate_file_hash(file_path)
            version_data["files"][rel_path] = file_hash

    # Сохраняем в JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(version_data, f, indent=4, ensure_ascii=False)

    print(f"Хэш успешно записан в {output_file}")

def remote_prepare_build(remote_user, remote_host):
    # Очистка только главной директории hearth-build
    ssh_cmd = [
        "ssh",
        f"{remote_user}@{remote_host}",
        "rm -rf ~/hearth-build/*"
    ]
    subprocess.run(ssh_cmd, check=True)

def scp_deploy(source_dir, arcname, version_json, remote_user="user", remote_host="host"):
    """
    Архивирует всю папку source_dir в tar.gz (arcname - имя подпапки), отправляет архив и version.json на сервер,
    распаковывает архив в ~/hearth-build/, очищает временные файлы.
    """
    import sys
    import shutil

    if not os.path.exists(source_dir):
        print(f"Папка {source_dir} не найдена!")
        sys.exit(1)

    archive_name = f"{arcname}.tar.gz"
    archive_path = os.path.join("dist", archive_name)

    print(f"Создание архива {archive_name}...")
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(source_dir, arcname=arcname)

    # Отправка архива
    scp_tar_cmd = [
        "scp",
        archive_path,
        f"{remote_user}@{remote_host}:~/hearth-build/"
    ]
    subprocess.run(scp_tar_cmd, check=True)

    # Распаковка архива на сервере (в корень hearth-build)
    ssh_untar_cmd = [
        "ssh",
        f"{remote_user}@{remote_host}",
        f"tar -xzf ~/hearth-build/{archive_name} -C ~/hearth-build/"
    ]
    subprocess.run(ssh_untar_cmd, check=True)

    # Удаление архива на сервере
    ssh_rm_tar_cmd = [
        "ssh",
        f"{remote_user}@{remote_host}",
        f"rm ~/hearth-build/{archive_name}"
    ]
    subprocess.run(ssh_rm_tar_cmd, check=True)

    # Отправка version.json, если он существует
    if os.path.exists(version_json):
        scp_json_cmd = [
            "scp",
            version_json,
            f"{remote_user}@{remote_host}:~/hearth-build/"
        ]
        subprocess.run(scp_json_cmd, check=True)
        # Удаление локального version.json после отправки
        os.remove(version_json)
    else:
        print(f"Файл {version_json} не найден")

    # Удаление локального архива
    if os.path.exists(archive_path):
        os.remove(archive_path)

    print(f"Done: {arcname}")

if __name__ == "__main__":
    REMOTE_USER = "root"
    REMOTE_HOST = credentials.IP
    
    print("[1] - только Hearthtrice")
    print("[2] - только Cockatrice") 
    print("[3] - оба")
    
    while True:
        choice = input("Введите номер (1, 2 или 3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("Неверный ввод. Введите 1, 2 или 3.")
    
    remote_prepare_build(REMOTE_USER, REMOTE_HOST)

    if choice in ['1', '3']:
        # Hearthtrice
        SOURCE_DIR_1 = fr"dist\HearthTrice"
        VERSION_JSON_1 = r"dist/version.json"
        generate_version_json(SOURCE_DIR_1, VERSION_JSON_1)
        scp_deploy(SOURCE_DIR_1, "Hearthtrice", VERSION_JSON_1, REMOTE_USER, REMOTE_HOST)

    if choice in ['2', '3']:
        # Cockatrice
        SOURCE_DIR_2 = fr"dist\Cockatrice"
        VERSION_JSON_2 = r"dist/version_cockatrice.json"
        generate_version_json(SOURCE_DIR_2, VERSION_JSON_2)
        scp_deploy(SOURCE_DIR_2, "Cockatrice", VERSION_JSON_2, REMOTE_USER, REMOTE_HOST)
