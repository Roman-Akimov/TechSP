 ### Лабораторные работы по ТехСП.
 
 ЧитайГород - Онлайн-библиотека для чтения цифровых книг с сохранением прогресса,
избранным и real-time уведомлениями о новинках.

#### Авторы
Студенты группы 6404-010302D:
- Шерстнев В.И.
- Акимов Р.О.

#### Стек
- Backend: FastAPI, SQLAlchemy, Pydantic, JWT
- БД: PostgreSQL
- Межсервисное взаимодействие: gRPC (Protocol Buffers)
- Очереди: RabbitMQ
- Real-time: WebSocket
- Прокси: Nginx
- Frontend: Jinja2 (HTML)

#### Архитектура
Клиент → Nginx → API Service → PostgreSQL
                              ├→ gRPC Service (рекомендации)
                              └→ RabbitMQ → Notification Service → WebSocket → Клиент

#### Роли
- **reader** — поиск, чтение, избранное, рекомендации
- **admin** — управление каталогом, статистика

#### Основной функционал
- Регистрация/вход (JWT)
- Поиск книг по жанрам, авторам, году
- Онлайн-чтение с сохранением страницы
- Избранное и история чтения
- Персональные рекомендации
- Уведомления о новых книгах

#### БД (основные сущности)
users, roles, books, genres, book_genres (M:N), favorites (M:N),
reviews, reading_progress

