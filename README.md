# Лабораторная работа №3 — gRPC-сервис рекомендаций для онлайн-библиотеки «ЧитайГород»

Проект основан на лабораторной работе №2 (FastAPI REST API + PostgreSQL).
Добавлен отдельный микросервис рекомендаций, взаимодействующий с API по gRPC
с контрактом Protocol Buffers (`grpc_service/recommendation.proto`).

Проект реализует слой доступа к PostgreSQL через SQLAlchemy 2.x, CRUD для основных сущностей,
тестовые сценарии и миграции Alembic.

## Основа из Л/Р №0

В Л/Р №0 предметная область — электронная библиотека: пользователи, книги, жанры,
избранное, отзывы и индивидуальный прогресс чтения. В схеме есть связи M:N
`books <-> genres` через `book_genres` и `users <-> books` через `favorites`.
Также используется `reading_progress` для сохранения последней страницы.

В текстовой части Л/Р №0 упомянуты авторы, однако в представленной физической схеме
отдельной таблицы `authors` нет. Поэтому этот вариант Л/Р №1 реализует именно
представленную схему, не добавляя новую сущность.

## Важное замечание по схеме

В диаграмме `users` роль задаётся через `role_id -> roles(id)`, а в отдельной таблице
ограничений для `users` показано поле `role VARCHAR(20)` с CHECK. Это расхождение
Л/Р №0. В коде выбран вариант из ER-диаграммы: `users.role_id` как внешний ключ
на `roles.id`, поскольку таблица `roles` и связь явно присутствуют на диаграмме.

## Запуск

1. Установить Python 3.11+.
2. Создать окружение и установить зависимости:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

3. Запустить PostgreSQL:

```bash
docker compose up -d
```

4. Создать `.env` из `.env.example`.

5. Применить миграции:

```bash
alembic upgrade head
```

6. Заполнить БД тестовыми данными:

```bash
python scripts/seed.py
```

7. Продемонстрировать работу:

```bash
python scripts/demo.py
```

8. Запустить тесты:

```bash
pytest -q
```

## Полезные команды Alembic

Создание новой миграции:

```bash
alembic revision --autogenerate -m "описание изменений"
```

Применение:

```bash
alembic upgrade head
```

Откат одной миграции:

```bash
alembic downgrade -1
```

Текущая версия:

```bash
alembic current
```


## Лабораторная работа №3: gRPC

### Что добавлено

- `grpc_service/recommendation.proto` — контракт gRPC.
- `grpc_service/server.py` — отдельный gRPC-сервер на порту `50051`.
- `grpc_service/recommendation_pb2.py` и `recommendation_pb2_grpc.py` — классы Protocol Buffers и gRPC-клиента/сервера.
- `app/grpc_client.py` — gRPC-клиент, используемый FastAPI.
- `GET /recommendations` — персональные рекомендации книг для авторизованного пользователя.

Микросервис получает от API предпочтительные жанры пользователя и список книг-кандидатов
с их жанрами и средним рейтингом. Он рассчитывает оценку: `10 * количество совпавших жанров + средний рейтинг`,
сортирует книги и возвращает список рекомендаций с объяснением. API получает результат по gRPC
и дополняет его данными книг из PostgreSQL.

### Запуск через Docker Compose (два отдельных процесса)

```bash
docker compose up --build
```

Compose запускает PostgreSQL, API Service, отдельный gRPC Service и Nginx.
Логи можно наблюдать командой:

```bash
docker compose logs -f api grpc
```

### Локальный запуск без Docker для приложений

Установить зависимости `pip install -r requirements.txt`, запустить PostgreSQL и применить миграции.
В первом терминале из корня проекта:

```bash
python -m grpc_service.server
```

Во втором терминале:

```bash
uvicorn app.main:app --reload
```

При локальном запуске клиент API по умолчанию подключается к `localhost:50051`.
Для другого адреса задайте `GRPC_RECOMMENDATION_TARGET`.

### Демонстрация

1. Заполнить БД: `python scripts/seed.py`.
2. Запустить API и gRPC-сервис в отдельных терминалах (или через Compose).
3. Авторизоваться через `POST /auth/login` с `reader@example.com` / `password123`.
4. Передать полученный Bearer-токен в Swagger (`/docs`).
5. Выполнить `GET /recommendations`.

В консоли API появятся сообщения о запросе рекомендаций и отправке gRPC-вызова.
В консоли gRPC появятся сообщения о полученном запросе, количестве кандидатов и сформированных ID рекомендаций.
Это наглядно показывает цепочку: пользователь → FastAPI → gRPC → FastAPI → пользователь.

### gRPC-контракт

RPC-метод: `RecommendationService.GetRecommendations`.
Вход: `RecommendationRequest` (предпочтительные ID жанров, кандидаты, лимит).
Выход: `RecommendationResponse` (ID книги, название, рассчитанный балл и причина рекомендации).


## Лабораторная работа №4: RabbitMQ и WebSocket

### Что реализовано

- API Service при добавлении книги в избранное (`POST /favorites/{book_id}`) публикует событие `favorite_added` в очередь `library_events` RabbitMQ.
- Notification Service (`notification_service/main.py`) — отдельное FastAPI-приложение. Оно потребляет сообщения из RabbitMQ в отдельном потоке, формирует текст уведомления и отправляет его по WebSocket всем подключениям соответствующего `user_id`.
- Клиент уведомлений — `static/notifications.html`. Он подключается к WebSocket через Nginx и показывает поступившие сообщения.
- WebSocket-адрес напрямую: `ws://localhost:8001/ws/{user_id}`. Через Nginx: `ws://localhost/notify-ws/{user_id}`.

Схема: пользователь → API Service → RabbitMQ (`library_events`) → Notification Service → WebSocket → клиент.

### Запуск всего проекта

Из каталога `Techsp Lab3`:

```bash
docker compose up --build -d
```

Проверить процессы:

```bash
docker compose ps
```

Посмотреть логи всех участников:

```bash
docker compose logs -f api notification rabbitmq
```

Остановить:

```bash
docker compose down
```

Остановить и удалить данные PostgreSQL:

```bash
docker compose down -v
```

### Демонстрация уведомления

1. Запустить Compose и дождаться запуска `db`, `rabbitmq`, `api` и `notification`.
2. Если база пустая, заполнить её тестовыми данными: `docker compose exec api python scripts/seed.py`. Команда выведет ID тестового читателя и книг.
3. Открыть `http://localhost/notifications.html`.
4. Ввести ID читателя из вывода seed (обычно `1`) и нажать «Подключиться». В логах `notification` появится запись о WebSocket-подключении.
5. Открыть `http://localhost/docs`, выполнить `POST /auth/login` с данными `reader@example.com` / `password123` и скопировать `access_token`.
6. Нажать Authorize в Swagger и вставить токен (при необходимости с префиксом `Bearer `).
7. Выполнить `GET /books`, выбрать книгу, которая ещё не добавлена в избранное (в seed это обычно книга с ID `2`).
8. Выполнить `POST /favorites/{book_id}`. В браузере без обновления появится уведомление «Книга … добавлена в избранное».

### Что должно быть видно в консоли

- API: пользователь добавил книгу, событие опубликовано в RabbitMQ.
- RabbitMQ: очередь `library_events` и счётчики сообщений доступны в `http://localhost:15672` (логин/пароль `guest`/`guest`).
- Notification Service: подписка на очередь, получение события и отправка уведомления клиенту.
- Клиент: новое уведомление появляется на странице без обновления.

### Локальный запуск без Docker для Python-сервисов

Нужны запущенные PostgreSQL и RabbitMQ. Установить зависимости:

```bash
pip install -r requirements.txt
```

В отдельных терминалах из каталога проекта:

```bash
python -m grpc_service.server
```

```bash
uvicorn notification_service.main:app --host 0.0.0.0 --port 8001
```

```bash
uvicorn app.main:app --reload --port 8000
```

Для локального запуска задайте `RABBITMQ_URL=amqp://guest:guest@localhost:5672/%2F`. Клиентскую страницу можно открыть через Nginx (Compose) либо использовать прямой WebSocket `ws://localhost:8001/ws/{user_id}`.
