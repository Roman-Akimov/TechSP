from fastapi import FastAPI
from app.routers import auth, books, genres, reader

app = FastAPI(
    title='Онлайн-библиотека "ЧитайГород" REST API',
    description="Лабораторная работа 2",
    version="1.0.0",
)

# подключение роутеров с префиксом /api/v1 (для Nginx Reverse Proxy) и на корневом уровне
for prefix in ("", "/api/v1"):
    app.include_router(auth.router, prefix=prefix)
    app.include_router(genres.router, prefix=prefix)
    app.include_router(books.router, prefix=prefix)
    app.include_router(reader.router, prefix=prefix)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "service": "library-api"}