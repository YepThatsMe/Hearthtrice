import PyInstaller.__main__
import shutil
import os

app_name = "HearthtriceLauncher"

pyinstaller_args = [
    'src/utils/Launcher/Launcher.py',
    '--noconfirm',
    '--onefile',
    '--name=' + app_name,
    '--icon=src/assets/icons/icon.ico',
    '--add-data=credentials.py;.',
]

print("Running PyInstaller for launcher...")
PyInstaller.__main__.run(pyinstaller_args)

if os.path.exists('build'):
    shutil.rmtree('build')

spec_file = f"{app_name}.spec"
if os.path.exists(spec_file):
    os.remove(spec_file) 