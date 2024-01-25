from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QSettings, pyqtSignal
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
        self.password_edit.setEchoMode(QLineEdit.Password)  # Скрываем ввод пароля

        self.connect_button = QPushButton("Подключиться")
        self.connect_button.clicked.connect(self.on_button_clicked)

        # Размещение виджетов на вертикальной компоновке
        layout = QVBoxLayout()
        layout.addWidget(self.server_label)
        layout.addWidget(self.server_edit)
        layout.addWidget(self.login_label)
        layout.addWidget(self.login_edit)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.connect_button)

        # Установка компоновки для диалога
        self.setLayout(layout)
    
    def on_button_clicked(self):
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