import json
import logging
import os
from datetime import datetime, timezone

import pika

log = logging.getLogger("library-api")


def publish_event(event_type: str, user_id: int, payload: dict) -> None:
    """Публикует событие в RabbitMQ. Ошибка брокера не отменяет уже выполненную операцию БД."""
    url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
    queue = os.getenv("RABBITMQ_QUEUE", "library_events")
    message = {
        "event_type": event_type,
        "user_id": user_id,
        "payload": payload,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    connection = None
    try:
        params = pika.URLParameters(url)
        params.socket_timeout = 3
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(message, ensure_ascii=False).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
        log.info("[API] Событие опубликовано в RabbitMQ: %s", message)
    except Exception:
        log.exception("[API] Не удалось отправить событие в RabbitMQ")
    finally:
        if connection and connection.is_open:
            connection.close()
