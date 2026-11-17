import asyncio
import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from collections import defaultdict

import pika
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [NOTIFICATION] %(message)s")
log = logging.getLogger("notification-service")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
QUEUE = os.getenv("RABBITMQ_QUEUE", "library_events")


class ConnectionManager:
    def __init__(self):
        self.clients = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.clients[user_id].add(websocket)
        log.info("WebSocket подключен: user_id=%s, подключений=%s",
                 user_id, len(self.clients[user_id]))

    def disconnect(self, user_id: int, websocket: WebSocket):
        self.clients[user_id].discard(websocket)
        if not self.clients[user_id]:
            self.clients.pop(user_id, None)
        log.info("WebSocket отключен: user_id=%s", user_id)

    async def send_to_user(self, user_id: int, message: dict):
        clients = list(self.clients.get(user_id, set()))
        if not clients:
            log.info("Нет подключённых клиентов для user_id=%s; уведомление не доставлено", user_id)
            return
        dead = []
        for client in clients:
            try:
                await client.send_json(message)
            except Exception:
                dead.append(client)
        for client in dead:
            self.disconnect(user_id, client)
        log.info("Уведомление отправлено клиентам user_id=%s (количество=%s)",
                 user_id, len(clients) - len(dead))


manager = ConnectionManager()
event_loop = None
stop_event = threading.Event()


def format_notification(event: dict) -> dict:
    event_type = event.get("event_type")
    payload = event.get("payload") or {}
    if event_type == "favorite_added":
        text = f'Книга «{payload.get("book_title", "Без названия")}» добавлена в избранное.'
    else:
        text = f'Получено событие: {event_type}'
    return {
        "type": "notification",
        "title": "ЧитайГород",
        "message": text,
        "event_type": event_type,
        "user_id": event.get("user_id"),
        "created_at": event.get("created_at"),
    }


def consume_events():
    """Отдельный поток-потребитель RabbitMQ с повторным подключением."""
    while not stop_event.is_set():
        connection = None
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            params.heartbeat = 30
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE, durable=True)
            channel.basic_qos(prefetch_count=10)
            log.info("Подписка на очередь RabbitMQ: %s", QUEUE)

            def callback(ch, method, properties, body):
                try:
                    event = json.loads(body.decode("utf-8"))
                    log.info("Получено событие из RabbitMQ: %s", event)
                    notification = format_notification(event)
                    user_id = int(notification["user_id"])
                    if event_loop and event_loop.is_running():
                        future = asyncio.run_coroutine_threadsafe(
                            manager.send_to_user(user_id, notification), event_loop
                        )
                        future.result(timeout=10)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    log.exception("Ошибка обработки сообщения; сообщение будет подтверждено")
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=QUEUE, on_message_callback=callback)
            channel.start_consuming()
        except Exception:
            if not stop_event.is_set():
                log.exception("RabbitMQ недоступен, повторная попытка через 5 секунд")
                time.sleep(5)
        finally:
            if connection and connection.is_open:
                connection.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_loop
    event_loop = asyncio.get_running_loop()
    stop_event.clear()
    worker = threading.Thread(target=consume_events, daemon=True, name="rabbitmq-consumer")
    worker.start()
    log.info("Notification Service запущен")
    yield
    stop_event.set()
    log.info("Notification Service остановлен")


app = FastAPI(title="Notification Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notification-service"}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Поддерживаем соединение; клиент может отправлять ping.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
