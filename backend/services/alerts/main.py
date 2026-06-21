import asyncio
import logging
from threading import Event, Thread

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from shared.auth.routes import router as auth_router
from shared.config.settings import settings
from shared.kafka.consumer import create_consumer
from shared.kafka.topics import KAFKA_TOPICS
from shared.middleware.logging import StructuredLoggingMiddleware
from shared.utils.dependencies import get_dependency_report
from shared.utils.migrations import run_migrations
from shared.utils.sentry import init_sentry

logger = logging.getLogger("alerts-service")

app = FastAPI(title="alerts-service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(StructuredLoggingMiddleware)
app.include_router(auth_router)


class NotificationManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
        self._main_loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._main_loop = loop

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

    def _broadcast_sync(self, message: dict) -> None:
        if self._main_loop is None or self._main_loop.is_closed():
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(message), self._main_loop)


manager = NotificationManager()
_stop_events: list[Event] = []


def _consume_topic(topic: str, group_id: str, event_type: str, stop: Event) -> None:
    consumer = create_consumer(topic, group_id)
    logger.info("Consumer started for %s (group=%s)", topic, group_id)
    try:
        for msg in consumer:
            if stop.is_set():
                break
            try:
                manager._broadcast_sync({"type": event_type, "data": msg.value})
            except Exception:
                logger.exception("Failed to broadcast %s message", event_type)
    finally:
        consumer.close()
        logger.info("Consumer stopped for %s", topic)


def start_kafka_consumers() -> None:
    configs = [
        (KAFKA_TOPICS["violations_raw"], "notification-group", "violation"),
        (KAFKA_TOPICS["zones_scored"], "notification-scored-group", "zone_scored"),
    ]
    for topic, group, event_type in configs:
        stop = Event()
        _stop_events.append(stop)
        thread = Thread(
            target=_consume_topic,
            args=(topic, group, event_type, stop),
            name=f"consumer-{topic}",
            daemon=True,
        )
        thread.start()


@app.on_event("startup")
async def startup():
    run_migrations()
    init_sentry(settings.SERVICE_NAME)
    manager.set_loop(asyncio.get_event_loop())
    thread = Thread(target=start_kafka_consumers, name="kafka-consumers", daemon=True)
    thread.start()


@app.on_event("shutdown")
def shutdown():
    logger.info("Signalling consumers to stop...")
    for stop in _stop_events:
        stop.set()


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
    deps = get_dependency_report()
    all_healthy = all(d["status"] == "healthy" for d in deps.values())
    return {
        "status": "ok" if all_healthy else "degraded",
        "service": "alerts-service",
        "dependencies": deps,
    }
