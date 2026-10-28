from fastapi import FastAPI
from app.routers import auth, books, genres, reader

app = FastAPI(
    title='Онлайн-библиотека "ЧитайГород" REST API',
    description="Лабораторная работа 2",
    version="1.0.0",
)

# Подключение роутеров на корневом уровне и с префиксом /api/v1 (для Nginx Reverse Proxy).
# include_in_schema скрывает дубликаты в сваггере
for prefix in ("", "/api/v1"):
    show_in_docs = prefix == ""
    app.include_router(auth.router, prefix=prefix, include_in_schema=show_in_docs)
    app.include_router(genres.router, prefix=prefix, include_in_schema=show_in_docs)
    app.include_router(books.router, prefix=prefix, include_in_schema=show_in_docs)
    app.include_router(reader.router, prefix=prefix, include_in_schema=show_in_docs)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "service": "library-api"}