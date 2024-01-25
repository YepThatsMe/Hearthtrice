# HearthTrice Manager
Менеджер для создания пользовательских Hearthstone карт для платформы Cockatrice. 

## Зависимости

Для генерации изображений необходим установленный ImageMagick-7.1.1.
Для связи с сервером необходим установленный драйвер SQL Server Native Client 11.0.


## Генерация ресурсов

```sh
pyrcc5 src\assets\resource_list.qrc -o src\resources.py
```
