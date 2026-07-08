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


def compute_manifest_hash(files: dict) -> str:
    hasher = hashlib.sha256()
    for path in sorted(files.keys()):
        hasher.update(f"{path}:{files[path]}\n".encode("utf-8"))
    return hasher.hexdigest()


def generate_manifest(directory: str, output_file: str, version: str = None) -> None:
    """Генерирует манифест приложения для лаунчера."""
    files = {}
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename in (".manifest.json", ".launcher_manifest.json"):
                continue
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, directory).replace("\\", "/")
            files[rel_path] = calculate_file_hash(file_path)

    manifest = {
        "version": version or f"{VERSION_MAJOR}.{VERSION_MINOR}",
        "files": files,
    }
    manifest["manifest_hash"] = compute_manifest_hash(files)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)

    print(f"Манифест записан в {output_file} ({len(files)} файлов)")

def remote_prepare_build(remote_user, remote_host, remote_port=None):
    ssh_cmd = ["ssh"]
    if remote_port:
        ssh_cmd.extend(["-p", str(remote_port)])
    ssh_cmd.extend([
        f"{remote_user}@{remote_host}",
        "rm -rf ~/hearth-build/*"
    ])
    subprocess.run(ssh_cmd, check=True)

def remote_clean_app(remote_user, remote_host, app_name, version_file, remote_port=None):
    ssh_cmd = ["ssh"]
    if remote_port:
        ssh_cmd.extend(["-p", str(remote_port)])
    ssh_cmd.extend([
        f"{remote_user}@{remote_host}",
        f"rm -rf ~/hearth-build/{app_name} ~/hearth-build/{version_file}"
    ])
    subprocess.run(ssh_cmd, check=True)

def scp_deploy(source_dir, arcname, version_json, remote_user="user", remote_host="host", remote_port=None):
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

    scp_tar_cmd = ["scp"]
    if remote_port:
        scp_tar_cmd.extend(["-P", str(remote_port)])
    scp_tar_cmd.extend([
        archive_path,
        f"{remote_user}@{remote_host}:~/hearth-build/"
    ])
    subprocess.run(scp_tar_cmd, check=True)

    ssh_untar_cmd = ["ssh"]
    if remote_port:
        ssh_untar_cmd.extend(["-p", str(remote_port)])
    ssh_untar_cmd.extend([
        f"{remote_user}@{remote_host}",
        f"tar -xzf ~/hearth-build/{archive_name} -C ~/hearth-build/"
    ])
    subprocess.run(ssh_untar_cmd, check=True)

    ssh_rm_tar_cmd = ["ssh"]
    if remote_port:
        ssh_rm_tar_cmd.extend(["-p", str(remote_port)])
    ssh_rm_tar_cmd.extend([
        f"{remote_user}@{remote_host}",
        f"rm ~/hearth-build/{archive_name}"
    ])
    subprocess.run(ssh_rm_tar_cmd, check=True)

    if os.path.exists(version_json):
        scp_json_cmd = ["scp"]
        if remote_port:
            scp_json_cmd.extend(["-P", str(remote_port)])
        scp_json_cmd.extend([
            version_json,
            f"{remote_user}@{remote_host}:~/hearth-build/"
        ])
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
    REMOTE_PORT = getattr(credentials, "SSH_PORT", None)

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
        remote_prepare_build(REMOTE_USER, REMOTE_HOST, REMOTE_PORT)
    elif choice == '1':
        remote_clean_app(REMOTE_USER, REMOTE_HOST, "Hearthtrice", "version.json", REMOTE_PORT)
    elif choice == '2':
        remote_clean_app(REMOTE_USER, REMOTE_HOST, "Cockatrice", "version_cockatrice.json", REMOTE_PORT)
    elif choice == '3':
        remote_clean_app(REMOTE_USER, REMOTE_HOST, "Launcher", LAUNCHER_VERSION_JSON, REMOTE_PORT)

    if choice in ['1', '4']:
        SOURCE_DIR_1 = os.path.join(ROOT, "dist", "HearthTrice")
        VERSION_JSON_1 = os.path.join(ROOT, "dist", "version.json")
        generate_manifest(SOURCE_DIR_1, VERSION_JSON_1)
        scp_deploy(SOURCE_DIR_1, "Hearthtrice", VERSION_JSON_1, REMOTE_USER, REMOTE_HOST, REMOTE_PORT)

    if choice in ['2', '4']:
        SOURCE_DIR_2 = os.path.join(ROOT, "dist", "Cockatrice")
        VERSION_JSON_2 = os.path.join(ROOT, "dist", "version_cockatrice.json")
        generate_manifest(SOURCE_DIR_2, VERSION_JSON_2)
        scp_deploy(SOURCE_DIR_2, "Cockatrice", VERSION_JSON_2, REMOTE_USER, REMOTE_HOST, REMOTE_PORT)

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
            generate_manifest(launcher_dir, VERSION_JSON_LAUNCHER)
            scp_deploy(launcher_dir, "Launcher", VERSION_JSON_LAUNCHER, REMOTE_USER, REMOTE_HOST, REMOTE_PORT)
