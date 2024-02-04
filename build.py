
import PyInstaller.__main__
import shutil
import os
from src.main import VERSION_MAJOR, VERSION_MINOR


print("Generating resources...")
os.system(r"pyrcc5 src\assets\resource_list.qrc -o src\resources.py")
os.system(r"pyrcc5 src\assets\resource_list_std.qrc -o src\resources_std.py")

app_name = f"HearthTrice {VERSION_MAJOR}.{VERSION_MINOR}"

pyinstaller_args = [
    'src/main.py',
    '--noconfirm',
    '--windowed',
    '--name=' + app_name,
    '--icon=src/assets/icons/icon.ico',
    '--add-data=src/assets/fonts/Belwe Bd BT Bold.ttf;fonts/',
    '--add-data=src/assets/fonts/Arial.ttf;fonts/',
    '--add-data=src/assets/fonts/FRAMDCN.ttf;fonts/',
    '--add-data=src/assets/fonts/FRADMCN.ttf;fonts/'
]

print("Running PyInstaller...")
PyInstaller.__main__.run(pyinstaller_args)

if os.path.exists('build'):
    shutil.rmtree('build')

spec_file = f"{app_name}.spec"
if os.path.exists(spec_file):
    os.remove(spec_file)
