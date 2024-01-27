from PyQt5.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QSettings, pyqtSignal, Qt
from DataPresenter import DataPresenter
from utils.Thread import send_to_thread
from Widgets.components.SettingsButton import SettingsButton
from DataTypes import Response

class ConnectionSettingsDialog(QDialog):
    connection_response_received = pyqtSignal()
    def __init__(self, data_presenter: DataPresenter, parent=None):
        super(ConnectionSettingsDialog, self).__init__(parent)
        self.data_presenter = data_presenter
        self.settings_button = SettingsButton()
        
        self.settings = QSettings('HearthTrice')

        self.set_up_ui()
        send_to_thread(self, self.connect_action, self.connection_response_received.emit)

    def set_up_ui(self):
        self.setWindowFlags(self.windowFlags()^ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Настройки")
        self.server_label = QLabel("Сервер:")
        self.server_edit = QLineEdit()
        self.server_edit.setText(self.settings.value("server"))

        self.login_label = QLabel("Логин:")
        self.login_edit = QLineEdit()
        self.login_edit.setText(self.settings.value("login"))

        self.password_label = QLabel("Пароль:")
        self.password_edit = QLineEdit()
        self.password_edit.setText(self.settings.value("password"))
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.connect_button = QPushButton("Подключиться")
        self.connect_button.clicked.connect(self.on_connect_clicked)

        self.game_path_label = QLabel("Директория игры")
        path_lo = QHBoxLayout()
        self.game_path_edit = QLineEdit()
        self.game_path_edit.setReadOnly(True)
        self.game_path_edit.setText(self.settings.value("path"))
        self.game_path_edit.textChanged.connect(self.on_game_path_changed)
        self.game_path_browse = QPushButton("Обзор")
        self.game_path_browse.clicked.connect(self.on_browse_clicked)
        path_lo.addWidget(self.game_path_edit)
        path_lo.addWidget(self.game_path_browse)

        layout = QVBoxLayout()
        layout.addWidget(self.game_path_label)
        layout.addLayout(path_lo)
        layout.addWidget(self.server_label)
        layout.addWidget(self.server_edit)
        layout.addWidget(self.login_label)
        layout.addWidget(self.login_edit)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.connect_button)

        self.setLayout(layout)

    def on_browse_clicked(self):       
        directory_path = QFileDialog.getExistingDirectory(None, "Выберите папку", ".", )
        self.game_path_edit.setText(directory_path)

    def on_game_path_changed(self, current_text):
        self.settings.setValue("path", current_text)
        print("Path changed to", current_text)

    def on_connect_clicked(self):
        response = self.connect_action()
        if(response.ok):
            QMessageBox.information(self, "Подключено", "Соединение установлено.")
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Ошибка подключения: " + response.msg)


    def connect_action(self) -> Response:
        server = self.server_edit.text()
        login = self.login_edit.text()
        password = self.password_edit.text()
        self.setEnabled(False)
        if server and login and password:
            self.settings.setValue("server", server)
            self.settings.setValue("login", login)
            self.settings.setValue("password", password)
            response = self.data_presenter.comm.set_connection(server, login, password)
            self.data_presenter.login = login
            self.set_connected(response.ok)
            return response
            
        self.set_connected(False)
        return Response(False, "Данные не предоставлены")
    
    def set_connected(self, is_connected: bool):
        self.setEnabled(True)
        self.settings_button.set_connected(is_connected)