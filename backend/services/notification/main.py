import asyncio
import threading

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from shared.config.settings import settings
from shared.kafka.consumer import create_consumer
from shared.kafka.topics import KAFKA_TOPICS
from shared.middleware.logging import StructuredLoggingMiddleware

app = FastAPI(title="notification-service", version="1.0.0")
app.add_middleware(StructuredLoggingMiddleware)


class NotificationManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def broadcast(self, message: dict):
        for conn in self.connections[:]:
            try:
                await conn.send_json(message)
            except Exception:
                self.connections.remove(conn)


manager = NotificationManager()


def consume_loop(consumer, handler):
    for msg in consumer:
        handler(msg.key, msg.value)


def start_kafka_consumers():
    def handle_violation(key, value):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(manager.broadcast({"type": "violation", "data": value}))

    def handle_scored_zone(key, value):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            manager.broadcast({"type": "zone_scored", "data": value})
        )

    violation_consumer = create_consumer(
        KAFKA_TOPICS["violations_raw"], "notification-group"
    )
    threading.Thread(
        target=lambda: consume_loop(violation_consumer, handle_violation), daemon=True
    ).start()

    scored_consumer = create_consumer(
        KAFKA_TOPICS["zones_scored"], "notification-scored-group"
    )
    threading.Thread(
        target=lambda: consume_loop(scored_consumer, handle_scored_zone), daemon=True
    ).start()


@app.on_event("startup")
async def startup():
    threading.Thread(target=start_kafka_consumers, daemon=True).start()


@app.websocket(f"{settings.API_V1_PREFIX}/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return {"status": "ok", "service": "notification-service"}
