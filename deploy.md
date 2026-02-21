# Развертывание апдейтера на сервере:

```bash
sudo mkdir /root/hearth-build/

sudo vim /etc/systemd/system/hearth-update-server.service
```

```
[Unit]
Description=Hearthtrice Update Server
After=network.target

[Service]
User=root
WorkingDirectory=/root/hearth-build/
ExecStart=/usr/bin/python3 -m http.server 8887 --directory /root/hearth-build/
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable hearth-update-server.service
sudo systemctl restart hearth-update-server.service
```

Запустить скрипт 
```
.venv\Scripts\python.exe deploy.py
```

# Развертывание БД POSTGRE SQL

```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql.service
sudo systemctl status postgresql.service

echo "listen_addresses = '*'"| tee -a /etc/postgresql/16/main/postgresql.conf
sudo sed -i 's/^ssl = on/ssl = off/' /etc/postgresql/16/main/postgresql.conf
echo "host all all 0.0.0.0/0 md5"| tee -a /etc/postgresql/16/main/pg_hba.conf

sudo -i -u postgres
createuser --pwprompt --superuser --createdb --createrole --login --echo [NAME]
# [ввести пароль]
```

В PgAdmin:
- Server Name:          Ubuntu
- Host name/address:    [IP]
- Port:                 5432
- Database:             postgres
- User:                 [NAME]
- Password:             [password]

### Экспорт/импорт БД

Установить клиент 17 версии (если ещё не установлен):

```bash
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /usr/share/keyrings/postgresql-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/postgresql-archive-keyring.gpg] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
sudo apt update
sudo apt install -y postgresql-client-17
```

Экспорт:

```bash
sudo -u postgres /usr/lib/postgresql/17/bin/pg_dump --dbname=hearth_db --format=custom --file=/var/lib/postgresql/hearth_db_$(date +%Y%m%d).bk
```

Импорт:
1. Создать базу данных (если не существует): 
```
sudo -u postgres createdb hearth_db
````
2. Восстановить из бэкапа:

```bash
sudo -u postgres /usr/lib/postgresql/17/bin/pg_restore --dbname=hearth_db --verbose --clean --if-exists "/var/lib/postgresql/hearth_db_.bk"
```

Файл бэкапа должен лежать в `/var/lib/postgresql/` (у пользователя postgres есть доступ). Версия pg_restore должна быть не ниже версии, которой делали бэкап.



# Установка сервера Cockatrice
## Сборка
```
sudo apt-get update
sudo apt-get install -y build-essential cmake git libprotobuf-dev protobuf-compiler \
  qtbase5-dev qttools5-dev qttools5-dev-tools libqt5websockets5-dev
```

```
git clone git@github.com:YepThatsMe/Cockatrice.git
cd Cockatrice && git checkout hearthtrice
```

```
mkdir build && cd build
cmake .. -DWITH_SERVER=1 -DWITH_CLIENT=0 -DWITH_ORACLE=0 -DWITH_DBCONVERTER=0
make -j$(nproc)
make install
```

```
cp ../servatrice/servatrice.ini.example servatrice/servatrice.ini
```

(если есть ufw)
```
sudo ufw allow 4747/tcp
sudo ufw allow 4748/tcp
sudo ufw reload
```

## Запуск:
```
cd servatrice 
./servatrice --config servatrice.ini
```

## Сервис:
```
mkdir /opt/servatrice
sudo cp /root/Cockatrice/build/servatrice/servatrice /opt/servatrice
sudo cp /root/Cockatrice/build/servatrice/servatrice.ini /opt/servatrice
ls -l /opt/servatrice
```

```
sudo vim /etc/systemd/system/servatrice.service
```
```
[Unit]
Description=Cockatrice Servatrice game server
After=network.target

[Service]
Type=simple
User=servatrice
Group=servatrice
WorkingDirectory=/opt/servatrice
ExecStart=/opt/servatrice/servatrice --config /opt/servatrice/servatrice.ini --log-to-console
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```
sudo useradd -r -s /bin/false servatrice
sudo chown -R servatrice:servatrice /opt/servatrice
```

```
sudo systemctl daemon-reload && sudo systemctl enable --now servatrice
sudo systemctl start servatrice
```
## Подключение 
```
Cockatrice -> Connect
Server: New Host
Name: [Любое имя]
IP: Адрес сервера
Port: 4747

Login:
Player Name: [Имя игрока]
Password: не нужен
```