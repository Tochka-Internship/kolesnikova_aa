# IT-стажировка для сотрудников Sales

В данном репозитории реализована приёмка заданий на IT-стажировку в Точке


Познакомиться с тестовым заданием можно по ссылке: [Техническое задание Python](https://drive.google.com/file/d/1Yz0oDS-tGirjjmhQHZaTvHKhOEwbyem3/view)


Sales Dev 2024

### Запуск приложения
1. Создать виртуальное окружение и установить зависимости
2. Вызвать в терминале `python3 marketplace/main.py`


### Примечания
Ссылка на swagger - http://127.0.0.1:8000/docs
Ссылка на redoc - http://127.0.0.1:8000/redoc
Ссылка на openapi.json - http://127.0.0.1:8000/openapi.json

### Работа с миграциями БД (Alembic)
Автогенерация файла миграции с изменениями
(Убедитесь, что файл миграции содержит нужные изменения)
```shell
alembic revision --autogenerate -m "your comment"
```

Применение определенной миграции
(your_revision_number подставить из нужной миграции - внутри миграции есть поле revision)
```shell
alembic upgrade <your_revision_number>
```

Откат до определенной миграции
(your_revision_number подставить из нужной миграции - внутри миграции есть поле revision)
```shell
alembic upgrade <your_revision_number>
```

Применение всех миграции
```shell
alembic upgrade head
```

Откатить все миграции:
```shell
alembic downgrade base
```

#### Прочее
Инициализация alembic'a для для асинхронного драйвера
```shell
alembic init -t async migrations
```

### Линтеры
#### ruff
Проверка всех замечаний
```shell
ruff .
```
Автоисправление всех замечаний
```shell
ruff --fix .
```

### Известные ошибки и как их исправить
- Q: При откате и накате миграции пишет ошибку, что тип уже существует
- A: Это происходит с такими типами как enum, удалить тип из БД руками и добавить в миграцию в downgrade `op.execute("DROP TYPE")` 